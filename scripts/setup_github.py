#!/usr/bin/env python3
"""
GitHub Setup Wizard for PR Review Plugin

Interactive setup wizard for configuring the PR Review Plugin with GitHub.
For Azure DevOps setup, use setup_ado.py instead.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Import from same directory
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from token_manager import (
        save_github_token_to_keychain, get_github_token_from_keychain,
        KEYRING_AVAILABLE, KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT_GITHUB
    )
except ImportError:
    KEYRING_AVAILABLE = False
    def save_github_token_to_keychain(token):
        return False
    def get_github_token_from_keychain():
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

    if missing:
        print_warning(f"Missing dependencies: {', '.join(missing)}")
        print_info(f"Install with: pip install {' '.join(missing)}")
        return False

    return True


def test_github_token(owner: str, token: str) -> bool:
    """
    Test if the GitHub PAT token is valid.

    Args:
        owner: Repository owner to test access
        token: PAT token

    Returns:
        True if token is valid
    """
    try:
        import requests
    except ImportError:
        print_warning("Cannot test token - requests library not installed")
        return True  # Assume valid

    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print_info(f"Authenticated as: {user_data.get('login', 'unknown')}")
            return True
        elif response.status_code == 401:
            print_error("Token authentication failed")
            return False
        elif response.status_code == 403:
            if 'rate limit' in response.text.lower():
                print_error("Rate limit exceeded")
            else:
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


def create_config_file(owner: str, repo: str, project_root: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Create the configuration file in the project's .claude folder.

    Args:
        owner: Repository owner (user or organization)
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

    # Create config for GitHub
    config = {
        "comment": "GitHub PR Review Configuration",
        "platform": "github",
        "owner": owner,
        "repository": repo
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return config_file, project_root


def run_wizard():
    """Run the interactive setup wizard for GitHub."""
    print_header("PR Review Plugin - GitHub Setup")

    print("This wizard will help you configure the PR Review Plugin for GitHub.")
    print("Press Ctrl+C at any time to cancel.\n")

    # Step 1: Check dependencies
    print_header("Step 1: Dependencies")
    if check_dependencies():
        print_success("All dependencies installed")
    else:
        print("")
        print_info("Please install missing dependencies and run again.")
        sys.exit(1)

    # Step 2: GitHub configuration
    print_header("Step 2: GitHub Repository Configuration")
    print("Enter your GitHub repository details:\n")

    owner = get_input("Repository owner (username or organization)")
    while not owner:
        print_error("Owner is required")
        owner = get_input("Repository owner")

    repo = get_input("Repository name")
    while not repo:
        print_error("Repository is required")
        repo = get_input("Repository name")

    # Step 3: Token configuration
    print_header("Step 3: Authentication Token (PAT)")
    print("Create a PAT at: https://github.com/settings/tokens")
    print("Required scopes:")
    print("  - repo (for private repositories)")
    print("  - public_repo (for public repositories only)\n")

    # Check for existing token
    existing_token = None
    token_source = None

    # Check environment variable
    env_token = os.getenv('GITHUB_PAT')
    if env_token and len(env_token) >= 20:
        print_success("Found token in environment variable (GITHUB_PAT)")
        existing_token = env_token
        token_source = 'env'

    # Check keychain
    if not existing_token and KEYRING_AVAILABLE:
        keychain_token = get_github_token_from_keychain()
        if keychain_token:
            print_success("Found token in system keychain")
            existing_token = keychain_token
            token_source = 'keychain'

    if existing_token:
        if get_yes_no(f"Use existing token from {token_source}?"):
            token = existing_token
        else:
            token = get_secure_input("Enter new GitHub PAT token (input hidden)")
    else:
        token = get_secure_input("Enter your GitHub PAT token (input hidden)")

    while not token or len(token) < 10:
        print_error("Token is required and must be at least 10 characters")
        token = get_secure_input("Enter your GitHub PAT token (input hidden)")

    # Test token
    print("")
    print_info("Testing token...")
    if test_github_token(owner, token):
        print_success("Token is valid!")
    else:
        print_warning("Could not verify token. Continuing anyway...")

    # Save token to keychain if available
    if KEYRING_AVAILABLE and token_source != 'keychain':
        print("")
        if get_yes_no("Save token to system keychain for future use?"):
            if save_github_token_to_keychain(token):
                print_success("Token saved to system keychain")
            else:
                print_error("Failed to save token to keychain")

    # Step 4: Create config file
    print_header("Step 4: Configuration File")
    config_file, project_root = create_config_file(owner, repo)
    print_success(f"Configuration saved to: {config_file}")

    # Summary
    print_header("Setup Complete!")
    print("Your configuration:")
    print(f"  Platform: GitHub")
    print(f"  Owner: {owner}")
    print(f"  Repository: {repo}")
    print(f"  Project root: {project_root}")
    print(f"  Config file: {config_file}")
    print("")

    if token_source == 'env':
        print_info("Token: Using environment variable (GITHUB_PAT)")
    elif KEYRING_AVAILABLE:
        print_info("Token: Stored in system keychain")
    else:
        print_warning("Token: Not stored (set GITHUB_PAT or install keyring)")
        print_info("  pip install keyring")
        print_info("  python scripts/token_manager.py --save --platform github")

    print("")
    print("Next steps:")
    print(f"  1. Start Claude Code: {Colors.BLUE}claude{Colors.END}")
    print(f"  2. Run the command: {Colors.BLUE}/pr-review 123{Colors.END}")
    print("")
    print_warning("Note: GitHub comment fetching is not yet implemented.")
    print_info("PR information will be displayed, but comments are coming soon.")
    print("")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub Setup Wizard for PR Review Plugin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This wizard helps you configure the PR Review Plugin for GitHub.

It will:
  1. Check required dependencies
  2. Prompt for GitHub owner/repository
  3. Configure PAT token securely (keychain if available)
  4. Create the configuration file

Run without arguments for interactive mode.
        """
    )

    parser.add_argument('--check', action='store_true',
                        help='Check current configuration without making changes')
    parser.add_argument('--non-interactive', action='store_true',
                        help='Run without prompts (requires all options)')
    parser.add_argument('--owner', help='Repository owner (non-interactive)')
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
                platform = config.get('platform', 'unknown')
                print(f"  Platform: {platform}")
                if platform == 'github':
                    print(f"  Owner: {config.get('owner', 'Not set')}")
                    print(f"  Repository: {config.get('repository', 'Not set')}")
                else:
                    print_warning("This config is not for GitHub")
            except Exception as e:
                print_error(f"Failed to read config: {e}")
        else:
            print_error(f"Config file not found at {config_file}")

        # Check token
        print("")
        env_token = os.getenv('GITHUB_PAT')
        if env_token:
            print_success("Token: Found in environment variable (GITHUB_PAT)")
        elif KEYRING_AVAILABLE:
            keychain_token = get_github_token_from_keychain()
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
        if not all([args.owner, args.repo]):
            print_error("Non-interactive mode requires --owner and --repo")
            sys.exit(1)

        print_info(f"Creating config for {args.owner}/{args.repo}")
        config_file, project_root = create_config_file(args.owner, args.repo)
        print_success(f"Configuration saved to: {config_file}")

    else:
        # Interactive mode
        run_wizard()


if __name__ == '__main__':
    main()
