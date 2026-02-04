#!/usr/bin/env python3
"""
PR Review Wrapper Script

Platform-agnostic wrapper that routes to the appropriate PR fetcher
(Azure DevOps or GitHub) based on project configuration.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import token manager and error messages from same directory
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from token_manager import resolve_token, resolve_github_token, KEYRING_AVAILABLE
except ImportError:
    # Fallback if token_manager not available
    KEYRING_AVAILABLE = False

    def resolve_token(config=None, prompt_if_missing=True):  # pyright: ignore[reportRedeclaration]
        token = os.getenv('AZURE_DEVOPS_PAT')
        if token:
            return (token, 'env')
        if config and config.get('token'):
            return (config.get('token'), 'config')
        return (None, 'none')

    def resolve_github_token(prompt_if_missing=True):  # pyright: ignore[reportRedeclaration]
        token = os.getenv('GITHUB_PAT')
        if token:
            return (token, 'env')
        return (None, 'none')

try:
    from error_messages import (
        config_missing_error, not_a_git_repo_error, token_invalid_error,
        path_not_found_error, platform_missing_error
    )
except ImportError:
    # Fallback if error_messages not available
    def config_missing_error(project_root=None):  # pyright: ignore[reportRedeclaration]
        path = f"{project_root}/.claude/pr-review.json" if project_root else ".claude/pr-review.json"
        return f"ERROR: Configuration file not found at {path}"

    def not_a_git_repo_error():  # pyright: ignore[reportRedeclaration]
        return "ERROR: Not in a git repository. Please run this command from within a git project."

    def token_invalid_error(reason):  # pyright: ignore[reportRedeclaration]
        return f"ERROR: Invalid token - {reason}"

    def path_not_found_error(path_type, path):  # pyright: ignore[reportRedeclaration]
        return f"ERROR: {path_type} not found at: {path}"

    def platform_missing_error(project_root=None):  # pyright: ignore[reportRedeclaration]
        return """ERROR: Missing 'platform' field in configuration.

Please run the appropriate setup wizard:
  - For GitHub:      python scripts/setup_github.py
  - For Azure DevOps: python scripts/setup_ado.py"""


def find_script_path(platform: str = 'azure-devops'):
    """Auto-detect the appropriate fetch script relative to this script."""
    if platform == 'github':
        return str(Path(__file__).parent / "fetch_github_pr.py")
    else:
        return str(Path(__file__).parent / "fetch_pr_comments.py")


def find_python_path():
    """Auto-detect Python interpreter."""
    # First try current Python interpreter
    if sys.executable:
        return sys.executable

    # Try to find python3 or python in PATH
    python_cmd = shutil.which('python3') or shutil.which('python')
    if python_cmd:
        return python_cmd

    return None


def find_project_root():
    """Find the project root by searching upward for a .git folder."""
    current = Path.cwd()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Check root directory as well
    if (current / ".git").exists():
        return current

    return None


def find_config_file():
    """Locate the pr-review.json file in the project's .claude folder."""
    project_root = find_project_root()

    if not project_root:
        return None, None

    config_path = project_root / ".claude" / "pr-review.json"

    if config_path.exists():
        return config_path, project_root

    return None, project_root


def load_config(config_path, project_root=None):
    """Load and validate configuration for any platform."""
    try:
        # Try utf-8-sig first to handle BOM, fallback to utf-8
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
        except UnicodeDecodeError:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Check for platform field (required)
        platform = config.get('platform')
        if not platform:
            print(platform_missing_error(project_root), file=sys.stderr)
            return None

        # Validate platform value
        if platform not in ['github', 'azure-devops']:
            print(f"ERROR: Invalid platform '{platform}'. Must be 'github' or 'azure-devops'", file=sys.stderr)
            return None

        # Validate required fields based on platform
        if platform == 'github':
            required = ['owner', 'repository']
        else:  # azure-devops
            required = ['organization', 'project', 'repository']

        missing = [field for field in required if field not in config or not config[field]]

        if missing:
            print(f"ERROR: Missing required fields for {platform} in config: {', '.join(missing)}", file=sys.stderr)
            return None

        # Auto-fill missing paths based on platform
        if not config.get('scriptPath'):
            config['scriptPath'] = find_script_path(platform)
            print(f"[INFO] Auto-detected script path: {config['scriptPath']}", file=sys.stderr)

        if not config.get('pythonPath'):
            config['pythonPath'] = find_python_path()
            if config['pythonPath']:
                print(f"[INFO] Auto-detected Python path: {config['pythonPath']}", file=sys.stderr)
            else:
                print("ERROR: Could not auto-detect Python interpreter", file=sys.stderr)
                return None

        # Validate paths exist (if explicitly provided, validate them)
        if config.get('pythonPath') and not Path(config['pythonPath']).exists():
            print(path_not_found_error('Python', config['pythonPath']), file=sys.stderr)
            return None

        if config.get('scriptPath') and not Path(config['scriptPath']).exists():
            print(path_not_found_error('Script', config['scriptPath']), file=sys.stderr)
            return None

        # Token resolution is handled separately in main() using token_manager
        # We don't validate token here anymore - it's done via resolve_token()

        return config

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Failed to read config: {e}", file=sys.stderr)
        return None


def run_ado_fetch_script(config, pr_number, output_file, token):
    """Execute the Azure DevOps fetch_pr_comments.py script."""
    cmd = [
        config['pythonPath'],
        config['scriptPath'],
        '--org', config['organization'],
        '--project', config['project'],
        '--repo', config['repository'],
        '--pr', str(pr_number),
        '--token', token,
        '--output', str(output_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"ERROR: Script failed with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False

        # Print any output from the script
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return True

    except subprocess.TimeoutExpired:
        print("ERROR: Script timed out after 60 seconds", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Failed to execute script: {e}", file=sys.stderr)
        return False


def run_github_fetch_script(config, pr_number, output_file, token):
    """Execute the GitHub fetch_github_pr.py script."""
    cmd = [
        config['pythonPath'],
        config['scriptPath'],
        '--owner', config['owner'],
        '--repo', config['repository'],
        '--pr', str(pr_number),
        '--token', token,
        '--output', str(output_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"ERROR: Script failed with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False

        # Print any output from the script
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return True

    except subprocess.TimeoutExpired:
        print("ERROR: Script timed out after 60 seconds", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Failed to execute script: {e}", file=sys.stderr)
        return False


def run_fetch_script(config, pr_number, output_file, token):
    """Route to the appropriate fetch script based on platform."""
    platform = config.get('platform', 'azure-devops')

    if platform == 'github':
        return run_github_fetch_script(config, pr_number, output_file, token)
    else:
        return run_ado_fetch_script(config, pr_number, output_file, token)


def run_fetch_changed_files(config, pr_number, token, project_root):
    """Execute fetch_changed_files.py and return the results."""
    script_path = Path(__file__).parent / "fetch_changed_files.py"
    python_path = config.get('pythonPath', sys.executable)
    platform = config.get('platform', 'azure-devops')

    cmd = [python_path, str(script_path), '--pr', str(pr_number), '--token', token]

    if platform == 'github':
        cmd.extend(['--platform', 'github', '--owner', config['owner'], '--repo', config['repository']])
    else:
        cmd.extend(['--platform', 'azure-devops', '--org', config['organization'],
                    '--project', config['project'], '--repo', config['repository']])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[WARNING] Failed to fetch changed files: {result.stderr}", file=sys.stderr)
            return None

        # Parse JSON output (stdout contains the JSON, stderr has info messages)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("[WARNING] Fetch changed files timed out", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"[WARNING] Failed to parse changed files output: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARNING] Error fetching changed files: {e}", file=sys.stderr)
        return None


def run_command_runner(config, changed_files_data, project_root):
    """Execute command_runner.py and return the execution plan."""
    script_path = Path(__file__).parent / "command_runner.py"
    python_path = config.get('pythonPath', sys.executable)
    config_path = project_root / ".claude" / "pr-review.json"

    # Write changed files to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(changed_files_data, f)
        temp_file = f.name

    try:
        cmd = [
            python_path, str(script_path),
            '--config', str(config_path),
            '--project-root', str(project_root),
            '--changed-files', temp_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"[WARNING] Command runner failed: {result.stderr}", file=sys.stderr)
            return None

        return json.loads(result.stdout)
    except Exception as e:
        print(f"[WARNING] Error running command runner: {e}", file=sys.stderr)
        return None
    finally:
        # Clean up temp file
        try:
            Path(temp_file).unlink()
        except Exception:
            pass


def enrich_command_plan_with_content(command_plan, project_root):
    """Read command file contents and add them to the execution plan."""
    if not command_plan or not command_plan.get('enabled'):
        return command_plan

    commands = command_plan.get('commands', [])
    enriched_commands = []

    for cmd in commands:
        cmd_path = Path(cmd.get('path', ''))
        if cmd_path.exists():
            try:
                with open(cmd_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                cmd['content'] = content
            except Exception as e:
                cmd['content'] = f"[ERROR] Failed to read: {e}"
                cmd['contentError'] = str(e)
        else:
            cmd['content'] = None
            cmd['contentError'] = "File not found"

        enriched_commands.append(cmd)

    command_plan['commands'] = enriched_commands
    return command_plan


def generate_full_output(pr_number, config, project_root, token, changed_files_data, command_plan, comments_file):
    """Generate comprehensive JSON output with everything Claude needs."""
    platform = config.get('platform', 'azure-devops')

    output = {
        "success": True,
        "pr": pr_number,
        "platform": platform,
        "projectRoot": str(project_root),
        "changedFiles": changed_files_data,
        "commands": command_plan,
        "commentsFile": str(comments_file) if comments_file else None
    }

    # Add PR info summary
    if changed_files_data:
        output["summary"] = {
            "totalFiles": changed_files_data.get('totalFiles', 0),
            "added": changed_files_data.get('summary', {}).get('added', 0),
            "modified": changed_files_data.get('summary', {}).get('modified', 0),
            "deleted": changed_files_data.get('summary', {}).get('deleted', 0)
        }

    if command_plan and command_plan.get('enabled'):
        output["commandsSummary"] = {
            "totalCommands": command_plan.get('totalCommands', 0),
            "totalFilesToAnalyze": command_plan.get('totalFiles', 0),
            "commandNames": [c.get('name') for c in command_plan.get('commands', [])]
        }

    return output


def main():
    parser = argparse.ArgumentParser(
        description='PR Review Wrapper - Fetches PR comments from Azure DevOps or GitHub'
    )
    parser.add_argument('pr_number', type=int, help='Pull request number')
    parser.add_argument('--output', '-o', help='Output file path (default: pr-{NUMBER}-comments.md in current directory)')
    parser.add_argument('--config', help='Path to config file (default: .claude/pr-review.json in project root)')
    parser.add_argument('--token', help='Override token (use AZURE_DEVOPS_PAT or GITHUB_PAT env var based on platform)')
    parser.add_argument('--skip-commands', action='store_true',
        help='Skip command execution, only fetch PR comments')
    parser.add_argument('--commands-only', action='store_true',
        help='Run commands only, skip PR comment fetching')
    parser.add_argument('--json', action='store_true',
        help='Output everything as single JSON (for Claude automation)')

    args = parser.parse_args()

    # Find config file
    if args.config:
        config_path = Path(args.config)
        # When config is explicitly provided, try to find git root but don't require it
        project_root = find_project_root()
        if not project_root:
            # Fallback: derive project root from config path
            if config_path.name == 'pr-review.json' and config_path.parent.name == '.claude':
                project_root = config_path.parent.parent
            else:
                project_root = config_path.parent
    else:
        config_path, project_root = find_config_file()
        # Check if we're in a git repository (only required when auto-discovering config)
        if not project_root:
            print(not_a_git_repo_error(), file=sys.stderr)
            sys.exit(1)

    if not config_path or not config_path.exists():
        print(config_missing_error(project_root), file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Loading configuration from {config_path}", file=sys.stderr)
    config = load_config(config_path, project_root)

    if not config:
        sys.exit(1)

    # Get platform from config
    platform = config.get('platform', 'azure-devops')
    print(f"[INFO] Platform: {platform}", file=sys.stderr)
    print("[SUCCESS] Configuration validated", file=sys.stderr)

    # Resolve token using layered approach based on platform
    if args.token:
        # Token provided via command line
        token = args.token
        token_source = 'cli'
    else:
        # Use token_manager for layered resolution based on platform
        if platform == 'github':
            token, token_source = resolve_github_token(prompt_if_missing=True)
        else:
            token, token_source = resolve_token(config, prompt_if_missing=True)

    if not token:
        env_var = 'GITHUB_PAT' if platform == 'github' else 'AZURE_DEVOPS_PAT'
        print(token_invalid_error(f"No token found or provided. Set {env_var} or use --token"), file=sys.stderr)
        sys.exit(1)

    # Log token source (but not the token itself)
    if platform == 'github':
        source_messages = {
            'env': 'environment variable (GITHUB_PAT)',
            'keychain': 'system keychain',
            'prompt': 'user input',
            'cli': 'command line argument'
        }
    else:
        source_messages = {
            'env': 'environment variable (AZURE_DEVOPS_PAT)',
            'keychain': 'system keychain',
            'config': 'config file (consider migrating to keychain)',
            'prompt': 'user input',
            'cli': 'command line argument'
        }
    print(f"[INFO] Using token from: {source_messages.get(token_source, token_source)}", file=sys.stderr)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path.cwd() / f"pr-{args.pr_number}-comments.md"

    # Check for commands configuration
    commands_config = config.get('commands', {})
    commands_enabled = commands_config.get('enabled', False) and not args.skip_commands

    # Handle command execution if enabled
    changed_files_data = None
    command_plan = None

    if commands_enabled or args.commands_only:
        print(f"[INFO] Fetching changed files for PR #{args.pr_number}...", file=sys.stderr)
        changed_files_data = run_fetch_changed_files(config, args.pr_number, token, project_root)

        if changed_files_data:
            print(f"[INFO] Found {changed_files_data.get('totalFiles', 0)} changed files", file=sys.stderr)

            # Get command execution plan
            command_plan = run_command_runner(config, changed_files_data, project_root)

            if command_plan and command_plan.get('enabled'):
                total_commands = command_plan.get('totalCommands', 0)
                total_files = command_plan.get('totalFiles', 0)
                print(f"[INFO] Command plan: {total_commands} commands, {total_files} files to analyze", file=sys.stderr)

                # Enrich with command file contents
                command_plan = enrich_command_plan_with_content(command_plan, project_root)

                # Output command plan for the workflow to use
                command_plan_file = Path.cwd() / f"pr-{args.pr_number}-commands.json"
                with open(command_plan_file, 'w', encoding='utf-8') as f:
                    json.dump(command_plan, f, indent=2)
                print(f"[COMMANDS] {command_plan_file}", file=sys.stderr)
        else:
            print("[WARNING] Could not fetch changed files, skipping commands", file=sys.stderr)

    # If commands-only mode, exit after command preparation
    if args.commands_only:
        if command_plan and command_plan.get('enabled'):
            print(f"[SUCCESS] Command plan saved to: pr-{args.pr_number}-commands.json", file=sys.stderr)
            sys.exit(0)
        else:
            print("[INFO] No commands to execute", file=sys.stderr)
            sys.exit(0)

    # If --json mode, output full structured data and exit
    if args.json:
        full_output = generate_full_output(
            args.pr_number, config, project_root, token,
            changed_files_data, command_plan, output_file
        )
        print(json.dumps(full_output, indent=2))
        sys.exit(0)

    if platform == 'github':
        print(f"[INFO] Fetching PR #{args.pr_number} from GitHub...", file=sys.stderr)
    else:
        print(f"[INFO] Fetching comments for PR #{args.pr_number} from Azure DevOps...", file=sys.stderr)

    # Run the appropriate fetch script
    success = run_fetch_script(config, args.pr_number, output_file, token)

    if success:
        print(f"[SUCCESS] Output saved to: {output_file}", file=sys.stderr)
        print(str(output_file))  # Output the file path to stdout for parsing
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
