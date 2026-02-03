#!/usr/bin/env python3
"""
PR Review Wrapper Script

Simplifies running the PR comment fetcher by automatically reading
configuration and handling all the complexity.
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
    from token_manager import resolve_token, KEYRING_AVAILABLE
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

try:
    from error_messages import config_missing_error, not_a_git_repo_error, token_invalid_error, path_not_found_error
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


def find_script_path():
    """Auto-detect fetch_pr_comments.py relative to this script."""
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


def load_config(config_path):
    """Load and validate configuration."""
    try:
        # Try utf-8-sig first to handle BOM, fallback to utf-8
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
        except:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Only require org, project, repository - paths and token are auto-detected
        required = ['organization', 'project', 'repository']
        missing = [field for field in required if field not in config or not config[field]]

        if missing:
            print(f"ERROR: Missing required fields in config: {', '.join(missing)}", file=sys.stderr)
            return None

        # Auto-fill missing paths
        if not config.get('scriptPath'):
            config['scriptPath'] = find_script_path()
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


def run_fetch_script(config, pr_number, output_file, token):
    """Execute the fetch_pr_comments.py script."""
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


def main():
    parser = argparse.ArgumentParser(
        description='PR Review Wrapper - Fetches Azure DevOps PR comments'
    )
    parser.add_argument('pr_number', type=int, help='Pull request number')
    parser.add_argument('--output', '-o', help='Output file path (default: pr-{NUMBER}-comments.md in current directory)')
    parser.add_argument('--config', help='Path to config file (default: .claude/pr-review.json in project root)')
    parser.add_argument('--token', help='Override token (or use AZURE_DEVOPS_PAT env var)')

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
    config = load_config(config_path)

    if not config:
        sys.exit(1)

    print("[SUCCESS] Configuration validated", file=sys.stderr)

    # Resolve token using layered approach (env > keychain > config > prompt)
    if args.token:
        # Token provided via command line
        token = args.token
        token_source = 'cli'
    else:
        # Use token_manager for layered resolution
        token, token_source = resolve_token(config, prompt_if_missing=True)

    if not token:
        print(token_invalid_error("No token found or provided"), file=sys.stderr)
        sys.exit(1)

    # Log token source (but not the token itself)
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

    print(f"[INFO] Fetching comments for PR #{args.pr_number}...", file=sys.stderr)

    # Run the fetch script
    success = run_fetch_script(config, args.pr_number, output_file, token)

    if success:
        print(f"[SUCCESS] Comments saved to: {output_file}", file=sys.stderr)
        print(str(output_file))  # Output the file path to stdout for parsing
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
