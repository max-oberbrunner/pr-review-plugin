#!/usr/bin/env python3
"""
Azure DevOps Setup Wizard for PR Review Plugin

Interactive setup wizard for configuring the PR Review Plugin with Azure DevOps.
For GitHub setup, use setup_github.py instead.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Import from same directory
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from token_manager import (
        save_token_to_keychain, get_token_from_keychain,
        KEYRING_AVAILABLE, KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT
    )
except ImportError:
    KEYRING_AVAILABLE = False
    def save_token_to_keychain(token):
        return False
    def get_token_from_keychain():
        return None


def find_project_root() -> Optional[Path]:
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


# ANSI color codes (work on most terminals)
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors for non-TTY output."""
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.BOLD = ''
        cls.END = ''


# Disable colors if not running in a terminal
if not sys.stdout.isatty():
    Colors.disable()


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.END}")
    print(f"{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.END}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")


def detect_python() -> Tuple[Optional[str], str]:
    """
    Auto-detect Python interpreter.

    Returns:
        Tuple of (path, version_string)
    """
    # Try current Python interpreter
    python_path = sys.executable
    if python_path:
        try:
            result = subprocess.run(
                [python_path, '--version'],
                capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip() or result.stderr.strip()
            return (python_path, version)
        except Exception:
            pass

    # Try python3 in PATH
    python_cmd = shutil.which('python3')
    if python_cmd:
        try:
            result = subprocess.run(
                [python_cmd, '--version'],
                capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip() or result.stderr.strip()
            return (python_cmd, version)
        except Exception:
            pass

    # Try python in PATH
    python_cmd = shutil.which('python')
    if python_cmd:
        try:
            result = subprocess.run(
                [python_cmd, '--version'],
                capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip() or result.stderr.strip()
            return (python_cmd, version)
        except Exception:
            pass

    return (None, "Not found")


def check_dependencies() -> bool:
    """
    Check if required Python packages are installed.

    Returns:
        True if all dependencies are available
    """
    missing = []

    try:
        import requests
    except ImportError:
        missing.append('requests')

    try:
        from dotenv import load_dotenv
    except ImportError:
        missing.append('python-dotenv')

    if missing:
        print_warning(f"Missing dependencies: {', '.join(missing)}")
        print_info(f"Install with: pip install {' '.join(missing)}")
        return False

    return True


def test_token(org: str, token: str) -> bool:
    """
    Test if the PAT token is valid.

    Args:
        org: Azure DevOps organization
        token: PAT token

    Returns:
        True if token is valid
    """
    import base64

    try:
        import requests
    except ImportError:
        print_warning("Cannot test token - requests library not installed")
        return True  # Assume valid

    credentials = f":{token}"
    auth_header = base64.b64encode(credentials.encode()).decode()

    url = f"https://dev.azure.com/{org}/_apis/projects?api-version=7.1"
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print_error("Token authentication failed")
            return False
        elif response.status_code == 403:
            print_error("Token lacks permissions")
            return False
        else:
            print_warning(f"Unexpected response: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_warning("Connection timed out - could not verify token")
        return True  # Assume valid
    except requests.exceptions.RequestException as e:
        print_warning(f"Connection error: {e}")
        return True  # Assume valid


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Get input from user with optional default.

    Args:
        prompt: Prompt text
        default: Default value

    Returns:
        User input or default
    """
    if default:
        display_prompt = f"{prompt} [{default}]: "
    else:
        display_prompt = f"{prompt}: "

    try:
        value = input(display_prompt).strip()
        return value if value else (default or "")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)


def get_secure_input(prompt: str) -> str:
    """
    Get password-style input (hidden).

    Args:
        prompt: Prompt text

    Returns:
        User input
    """
    import getpass
    try:
        return getpass.getpass(prompt + ": ")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """
    Get yes/no input from user.

    Args:
        prompt: Prompt text
        default: Default value

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    try:
        response = input(f"{prompt} ({default_str}): ").strip().lower()
        if not response:
            return default
        return response in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)


def create_config_file(org: str, project: str, repo: str, project_root: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Create the configuration file in the project's .claude folder.

    Args:
        org: Azure DevOps organization
        project: Project name
        repo: Repository name
        project_root: Optional project root path (auto-detected if not provided)

    Returns:
        Tuple of (config_file path, project_root path)
    """
    # Find project root if not provided
    if not project_root:
        project_root = find_project_root()

    if not project_root:
        print_error("Not in a git repository. Please run this command from within a git project.")
        sys.exit(1)

    config_dir = project_root / ".claude"
    config_file = config_dir / "pr-review.json"

    # Create directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)

    # Check if config already exists
    if config_file.exists():
        print_warning(f"Configuration file already exists: {config_file}")
        if not get_yes_no("Overwrite?", default=False):
            print_info("Keeping existing configuration")
            return config_file, project_root

    # Create minimal config (paths are auto-detected)
    config = {
        "comment": "Azure DevOps PR Review Configuration",
        "platform": "azure-devops",
        "organization": org,
        "project": project,
        "repository": repo,
        "debugMode": False,
        "autoFormatForClaudeCode": True
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return config_file, project_root


def run_wizard():
    """Run the interactive setup wizard for Azure DevOps."""
    print_header("PR Review Plugin - Azure DevOps Setup")

    print("This wizard will help you configure the PR Review Plugin.")
    print("Press Ctrl+C at any time to cancel.\n")

    # Step 1: Detect Python
    print_header("Step 1: Python Detection")
    python_path, python_version = detect_python()

    if python_path:
        print_success(f"Found Python: {python_version}")
        print_info(f"Path: {python_path}")
    else:
        print_error("Python not found!")
        print_info("Please install Python 3.8+ and try again.")
        sys.exit(1)

    # Step 2: Check dependencies
    print_header("Step 2: Dependencies")
    if check_dependencies():
        print_success("All dependencies installed")
    else:
        print("")
        if get_yes_no("Install missing dependencies now?"):
            requirements_file = script_dir / "requirements.txt"
            if requirements_file.exists():
                print_info("Installing dependencies...")
                result = subprocess.run(
                    [python_path, '-m', 'pip', 'install', '-r', str(requirements_file)],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print_success("Dependencies installed")
                else:
                    print_error("Failed to install dependencies")
                    print(result.stderr)
            else:
                print_error(f"requirements.txt not found at {requirements_file}")

    # Step 3: Azure DevOps configuration
    print_header("Step 3: Azure DevOps Configuration")
    print("Enter your Azure DevOps details:\n")

    org = get_input("Organization name (e.g., 'contoso')")
    while not org:
        print_error("Organization is required")
        org = get_input("Organization name")

    project = get_input("Project name")
    while not project:
        print_error("Project is required")
        project = get_input("Project name")

    repo = get_input("Repository name")
    while not repo:
        print_error("Repository is required")
        repo = get_input("Repository name")

    # Step 4: Token configuration
    print_header("Step 4: Authentication Token (PAT)")
    print(f"Create a PAT at: https://dev.azure.com/{org}/_usersSettings/tokens")
    print("Required permission: Code (Read)\n")

    # Check for existing token
    existing_token = None
    token_source = None

    # Check environment variable
    env_token = os.getenv('AZURE_DEVOPS_PAT')
    if env_token and len(env_token) >= 20:
        print_success("Found token in environment variable (AZURE_DEVOPS_PAT)")
        existing_token = env_token
        token_source = 'env'

    # Check keychain
    if not existing_token and KEYRING_AVAILABLE:
        keychain_token = get_token_from_keychain()
        if keychain_token:
            print_success("Found token in system keychain")
            existing_token = keychain_token
            token_source = 'keychain'

    if existing_token:
        if get_yes_no(f"Use existing token from {token_source}?"):
            token = existing_token
        else:
            token = get_secure_input("Enter new PAT token (input hidden)")
    else:
        token = get_secure_input("Enter your PAT token (input hidden)")

    while not token or len(token) < 20:
        print_error("Token is required and must be at least 20 characters")
        token = get_secure_input("Enter your PAT token (input hidden)")

    # Test token
    print("")
    print_info("Testing token...")
    if test_token(org, token):
        print_success("Token is valid!")
    else:
        print_warning("Could not verify token. Continuing anyway...")

    # Save token to keychain if available
    if KEYRING_AVAILABLE and token_source != 'keychain':
        print("")
        if get_yes_no("Save token to system keychain for future use?"):
            if save_token_to_keychain(token):
                print_success("Token saved to system keychain")
            else:
                print_error("Failed to save token to keychain")

    # Step 5: Create config file
    print_header("Step 5: Configuration File")
    config_file, project_root = create_config_file(org, project, repo)
    print_success(f"Configuration saved to: {config_file}")

    # Summary
    print_header("Setup Complete!")
    print("Your configuration:")
    print(f"  Organization: {org}")
    print(f"  Project: {project}")
    print(f"  Repository: {repo}")
    print(f"  Project root: {project_root}")
    print(f"  Config file: {config_file}")
    print("")

    if token_source == 'env':
        print_info("Token: Using environment variable (AZURE_DEVOPS_PAT)")
    elif KEYRING_AVAILABLE:
        print_info("Token: Stored in system keychain")
    else:
        print_warning("Token: Not stored (set AZURE_DEVOPS_PAT or install keyring)")
        print_info("  pip install keyring")
        print_info("  python scripts/token_manager.py --save")

    print("")
    print("Next steps:")
    print(f"  1. Start Claude Code: {Colors.BLUE}claude{Colors.END}")
    print(f"  2. Run the command: {Colors.BLUE}/pr-review 12345{Colors.END}")
    print("")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="PR Review Plugin Setup Wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This wizard helps you configure the PR Review Plugin interactively.

It will:
  1. Detect your Python installation
  2. Check/install required dependencies
  3. Prompt for Azure DevOps org/project/repo
  4. Configure PAT token securely (keychain if available)
  5. Create the configuration file

Run without arguments for interactive mode.
        """
    )

    parser.add_argument('--check', action='store_true',
                        help='Check current configuration without making changes')
    parser.add_argument('--non-interactive', action='store_true',
                        help='Run without prompts (requires all options)')
    parser.add_argument('--org', help='Azure DevOps organization (non-interactive)')
    parser.add_argument('--project', help='Project name (non-interactive)')
    parser.add_argument('--repo', help='Repository name (non-interactive)')

    args = parser.parse_args()

    if args.check:
        # Check mode - show current configuration
        print_header("Configuration Check")

        project_root = find_project_root()
        if not project_root:
            print_error("Not in a git repository")
            sys.exit(1)

        print_info(f"Project root: {project_root}")

        config_file = project_root / ".claude" / "pr-review.json"
        if config_file.exists():
            print_success(f"Config file: {config_file}")
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"  Organization: {config.get('organization', 'Not set')}")
                print(f"  Project: {config.get('project', 'Not set')}")
                print(f"  Repository: {config.get('repository', 'Not set')}")
            except Exception as e:
                print_error(f"Failed to read config: {e}")
        else:
            print_error(f"Config file not found at {config_file}")

        # Check token
        print("")
        env_token = os.getenv('AZURE_DEVOPS_PAT')
        if env_token:
            print_success("Token: Found in environment variable")
        elif KEYRING_AVAILABLE:
            keychain_token = get_token_from_keychain()
            if keychain_token:
                print_success("Token: Found in system keychain")
            else:
                print_warning("Token: Not found in keychain")
        else:
            print_warning("Token: Keyring not installed")

        # Check dependencies
        print("")
        if check_dependencies():
            print_success("Dependencies: All installed")
        else:
            print_warning("Dependencies: Some missing")

    elif args.non_interactive:
        # Non-interactive mode
        if not all([args.org, args.project, args.repo]):
            print_error("Non-interactive mode requires --org, --project, and --repo")
            sys.exit(1)

        print_info(f"Creating config for {args.org}/{args.project}/{args.repo}")
        config_file, project_root = create_config_file(args.org, args.project, args.repo)
        print_success(f"Configuration saved to: {config_file}")

    else:
        # Interactive mode
        run_wizard()


if __name__ == '__main__':
    main()
