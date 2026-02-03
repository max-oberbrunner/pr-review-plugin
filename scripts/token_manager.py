#!/usr/bin/env python3
"""
Token Manager for PR Review Plugin

Provides secure, layered token resolution for multiple platforms:

Azure DevOps:
1. Environment variable (AZURE_DEVOPS_PAT)
2. System keychain (macOS Keychain / Windows Credential Manager)
3. Config file (with deprecation warning)
4. Interactive prompt (offer to save to keychain)

GitHub:
1. Environment variable (GITHUB_PAT)
2. System keychain (macOS Keychain / Windows Credential Manager)
3. Interactive prompt (offer to save to keychain)
"""

import os
import sys
import getpass
from typing import Optional, Tuple

# Service name for keychain storage
KEYCHAIN_SERVICE = "pr-review-plugin"

# Azure DevOps constants
KEYCHAIN_ACCOUNT_ADO = "azure-devops-pat"
ENV_VAR_NAME_ADO = "AZURE_DEVOPS_PAT"

# GitHub constants
KEYCHAIN_ACCOUNT_GITHUB = "github-pat"
ENV_VAR_NAME_GITHUB = "GITHUB_PAT"

# Legacy aliases for backward compatibility
KEYCHAIN_ACCOUNT = KEYCHAIN_ACCOUNT_ADO
ENV_VAR_NAME = ENV_VAR_NAME_ADO

# Try to import keyring (optional dependency)
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


def get_token_from_env() -> Optional[str]:
    """Get token from environment variable."""
    token = os.getenv(ENV_VAR_NAME)
    if token and len(token) >= 20:
        return token
    return None


def get_token_from_keychain() -> Optional[str]:
    """Get token from system keychain."""
    if not KEYRING_AVAILABLE:
        return None

    try:
        token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
        if token and len(token) >= 20:
            return token
    except Exception:
        # Keychain access failed (permissions, not available, etc.)
        pass
    return None


def save_token_to_keychain(token: str) -> bool:
    """
    Save token to system keychain.

    Returns:
        True if saved successfully, False otherwise
    """
    if not KEYRING_AVAILABLE:
        print("Warning: keyring library not installed. Cannot save to keychain.", file=sys.stderr)
        print("Install with: pip install keyring", file=sys.stderr)
        return False

    try:
        keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, token)
        return True
    except Exception as e:
        print(f"Warning: Failed to save token to keychain: {e}", file=sys.stderr)
        return False


def delete_token_from_keychain() -> bool:
    """
    Delete token from system keychain.

    Returns:
        True if deleted successfully, False otherwise
    """
    if not KEYRING_AVAILABLE:
        print("Warning: keyring library not installed.", file=sys.stderr)
        return False

    try:
        keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
        return True
    except keyring.errors.PasswordDeleteError:
        # Token doesn't exist
        return False
    except Exception as e:
        print(f"Warning: Failed to delete token from keychain: {e}", file=sys.stderr)
        return False


def get_token_from_config(config: dict) -> Optional[str]:
    """
    Get token from config file with deprecation warning.

    Args:
        config: Configuration dictionary

    Returns:
        Token if valid, None otherwise
    """
    token = config.get('token')
    if not token:
        return None

    # Check for placeholder values
    placeholder_values = [
        'YOUR_AZURE_DEVOPS_PAT_HERE',
        'PLACEHOLDER_TOKEN_NEEDS_TO_BE_SET',
        'your-token-here'
    ]
    if token in placeholder_values:
        return None

    # Validate token length
    if len(token) < 20:
        return None

    # Show deprecation warning
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("DEPRECATION WARNING: Token stored in config file", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("Storing tokens in plaintext config files is insecure.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Recommended alternatives:", file=sys.stderr)
    print(f"  1. Environment variable: export {ENV_VAR_NAME}='your-token'", file=sys.stderr)
    if KEYRING_AVAILABLE:
        print("  2. System keychain: python scripts/token_manager.py --save", file=sys.stderr)
    else:
        print("  2. System keychain: pip install keyring && python scripts/token_manager.py --save", file=sys.stderr)
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)

    return token


def prompt_for_token(offer_keychain_save: bool = True) -> Optional[str]:
    """
    Interactively prompt user for token.

    Args:
        offer_keychain_save: Whether to offer to save token to keychain

    Returns:
        Token if provided, None if cancelled
    """
    print("", file=sys.stderr)
    print("Azure DevOps Personal Access Token (PAT) required", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    print("Create a PAT at: https://dev.azure.com/{org}/_usersSettings/tokens", file=sys.stderr)
    print("Required scope: Code (Read)", file=sys.stderr)
    print("", file=sys.stderr)

    try:
        token = getpass.getpass("Enter your PAT token (input hidden): ")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return None

    if not token or len(token) < 20:
        print("Error: Invalid token (too short or empty)", file=sys.stderr)
        return None

    # Offer to save to keychain
    if offer_keychain_save and KEYRING_AVAILABLE:
        print("", file=sys.stderr)
        try:
            save_response = input("Save token to system keychain for future use? (y/n): ")
            if save_response.lower() in ['y', 'yes']:
                if save_token_to_keychain(token):
                    print("Token saved to keychain successfully.", file=sys.stderr)
                else:
                    print("Failed to save token to keychain.", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            pass

    return token


def resolve_token(config: Optional[dict] = None, prompt_if_missing: bool = True) -> Tuple[Optional[str], str]:
    """
    Resolve token using layered approach.

    Resolution order:
    1. Environment variable (AZURE_DEVOPS_PAT)
    2. System keychain
    3. Config file (with deprecation warning)
    4. Interactive prompt (if prompt_if_missing=True)

    Args:
        config: Configuration dictionary (optional)
        prompt_if_missing: Whether to prompt user if no token found

    Returns:
        Tuple of (token, source) where source is one of:
        'env', 'keychain', 'config', 'prompt', or 'none'
    """
    # 1. Try environment variable
    token = get_token_from_env()
    if token:
        return (token, 'env')

    # 2. Try system keychain
    token = get_token_from_keychain()
    if token:
        return (token, 'keychain')

    # 3. Try config file
    if config:
        token = get_token_from_config(config)
        if token:
            return (token, 'config')

    # 4. Prompt user
    if prompt_if_missing:
        token = prompt_for_token()
        if token:
            return (token, 'prompt')

    return (None, 'none')


# =============================================================================
# GitHub-specific functions
# =============================================================================

def get_github_token_from_env() -> Optional[str]:
    """Get GitHub token from environment variable."""
    token = os.getenv(ENV_VAR_NAME_GITHUB)
    if token and len(token) >= 20:
        return token
    return None


def get_github_token_from_keychain() -> Optional[str]:
    """Get GitHub token from system keychain."""
    if not KEYRING_AVAILABLE:
        return None

    try:
        token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT_GITHUB)
        if token and len(token) >= 20:
            return token
    except Exception:
        # Keychain access failed (permissions, not available, etc.)
        pass
    return None


def save_github_token_to_keychain(token: str) -> bool:
    """
    Save GitHub token to system keychain.

    Returns:
        True if saved successfully, False otherwise
    """
    if not KEYRING_AVAILABLE:
        print("Warning: keyring library not installed. Cannot save to keychain.", file=sys.stderr)
        print("Install with: pip install keyring", file=sys.stderr)
        return False

    try:
        keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT_GITHUB, token)
        return True
    except Exception as e:
        print(f"Warning: Failed to save token to keychain: {e}", file=sys.stderr)
        return False


def delete_github_token_from_keychain() -> bool:
    """
    Delete GitHub token from system keychain.

    Returns:
        True if deleted successfully, False otherwise
    """
    if not KEYRING_AVAILABLE:
        print("Warning: keyring library not installed.", file=sys.stderr)
        return False

    try:
        keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT_GITHUB)
        return True
    except keyring.errors.PasswordDeleteError:
        # Token doesn't exist
        return False
    except Exception as e:
        print(f"Warning: Failed to delete token from keychain: {e}", file=sys.stderr)
        return False


def prompt_for_github_token(offer_keychain_save: bool = True) -> Optional[str]:
    """
    Interactively prompt user for GitHub token.

    Args:
        offer_keychain_save: Whether to offer to save token to keychain

    Returns:
        Token if provided, None if cancelled
    """
    print("", file=sys.stderr)
    print("GitHub Personal Access Token (PAT) required", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    print("Create a PAT at: https://github.com/settings/tokens", file=sys.stderr)
    print("Required scope: repo (for private repos) or public_repo (for public repos)", file=sys.stderr)
    print("", file=sys.stderr)

    try:
        token = getpass.getpass("Enter your GitHub PAT token (input hidden): ")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return None

    if not token or len(token) < 10:
        print("Error: Invalid token (too short or empty)", file=sys.stderr)
        return None

    # Offer to save to keychain
    if offer_keychain_save and KEYRING_AVAILABLE:
        print("", file=sys.stderr)
        try:
            save_response = input("Save token to system keychain for future use? (y/n): ")
            if save_response.lower() in ['y', 'yes']:
                if save_github_token_to_keychain(token):
                    print("Token saved to keychain successfully.", file=sys.stderr)
                else:
                    print("Failed to save token to keychain.", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            pass

    return token


def resolve_github_token(prompt_if_missing: bool = True) -> Tuple[Optional[str], str]:
    """
    Resolve GitHub token using layered approach.

    Resolution order:
    1. Environment variable (GITHUB_PAT)
    2. System keychain
    3. Interactive prompt (if prompt_if_missing=True)

    Args:
        prompt_if_missing: Whether to prompt user if no token found

    Returns:
        Tuple of (token, source) where source is one of:
        'env', 'keychain', 'prompt', or 'none'
    """
    # 1. Try environment variable
    token = get_github_token_from_env()
    if token:
        return (token, 'env')

    # 2. Try system keychain
    token = get_github_token_from_keychain()
    if token:
        return (token, 'keychain')

    # 3. Prompt user
    if prompt_if_missing:
        token = prompt_for_github_token()
        if token:
            return (token, 'prompt')

    return (None, 'none')


def main():
    """CLI interface for token management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage PAT tokens securely for Azure DevOps and GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save Azure DevOps token to system keychain (default)
  python token_manager.py --save

  # Save GitHub token to system keychain
  python token_manager.py --save --platform github

  # Delete token from system keychain
  python token_manager.py --delete
  python token_manager.py --delete --platform github

  # Check current token status
  python token_manager.py --status

Environment Variables:
  AZURE_DEVOPS_PAT    Azure DevOps token
  GITHUB_PAT          GitHub token

Resolution Order:
  1. Environment variable
  2. System keychain (macOS Keychain / Windows Credential Manager)
  3. Config file (Azure DevOps only, DEPRECATED)
  4. Interactive prompt
        """
    )

    parser.add_argument('--save', action='store_true',
                        help='Save token to system keychain')
    parser.add_argument('--delete', action='store_true',
                        help='Delete token from system keychain')
    parser.add_argument('--status', action='store_true',
                        help='Show current token status (which source is active)')
    parser.add_argument('--platform', choices=['azure-devops', 'github'], default='azure-devops',
                        help='Platform to manage tokens for (default: azure-devops)')

    args = parser.parse_args()

    # Determine platform-specific settings
    is_github = args.platform == 'github'
    platform_name = "GitHub" if is_github else "Azure DevOps"
    env_var = ENV_VAR_NAME_GITHUB if is_github else ENV_VAR_NAME_ADO
    keychain_account = KEYCHAIN_ACCOUNT_GITHUB if is_github else KEYCHAIN_ACCOUNT_ADO
    save_func = save_github_token_to_keychain if is_github else save_token_to_keychain
    delete_func = delete_github_token_from_keychain if is_github else delete_token_from_keychain
    get_env_func = get_github_token_from_env if is_github else get_token_from_env
    get_keychain_func = get_github_token_from_keychain if is_github else get_token_from_keychain

    if args.save:
        if not KEYRING_AVAILABLE:
            print("Error: keyring library not installed.", file=sys.stderr)
            print("Install with: pip install keyring", file=sys.stderr)
            sys.exit(1)

        print(f"Save {platform_name} PAT to system keychain")
        print("-" * 40)
        try:
            token = getpass.getpass("Enter your PAT token (input hidden): ")
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(1)

        if not token or len(token) < 20:
            print("Error: Invalid token (too short or empty)")
            sys.exit(1)

        if save_func(token):
            print("Token saved to system keychain successfully!")
            print(f"Service: {KEYCHAIN_SERVICE}")
            print(f"Account: {keychain_account}")
        else:
            print("Failed to save token to keychain.")
            sys.exit(1)

    elif args.delete:
        if not KEYRING_AVAILABLE:
            print("Error: keyring library not installed.", file=sys.stderr)
            sys.exit(1)

        print(f"Delete {platform_name} PAT from system keychain")
        print("-" * 40)

        if delete_func():
            print("Token deleted from system keychain.")
        else:
            print("No token found in keychain or deletion failed.")

    elif args.status:
        print("PR Review Plugin - Token Status")
        print("=" * 50)

        # Azure DevOps section
        print("\n[Azure DevOps]")
        print("-" * 30)

        # Check environment
        ado_env_token = get_token_from_env()
        if ado_env_token:
            print(f"[ACTIVE] Environment variable ({ENV_VAR_NAME_ADO})")
            print(f"         Token: {ado_env_token[:4]}...{ado_env_token[-4:]}")
        else:
            print(f"[  --  ] Environment variable ({ENV_VAR_NAME_ADO})")

        # Check keychain
        ado_keychain_token = None
        if KEYRING_AVAILABLE:
            ado_keychain_token = get_token_from_keychain()
            if ado_keychain_token:
                status = "[ACTIVE]" if not ado_env_token else "[BACKUP]"
                print(f"{status} System keychain ({KEYCHAIN_ACCOUNT_ADO})")
                print(f"         Token: {ado_keychain_token[:4]}...{ado_keychain_token[-4:]}")
            else:
                print(f"[  --  ] System keychain ({KEYCHAIN_ACCOUNT_ADO})")
        else:
            print("[  --  ] System keychain (keyring not installed)")

        # Check config file (in project root) - ADO only
        from pathlib import Path

        def find_project_root():
            current = Path.cwd()
            while current != current.parent:
                if (current / ".git").exists():
                    return current
                current = current.parent
            if (current / ".git").exists():
                return current
            return None

        project_root = find_project_root()
        if project_root:
            config_path = project_root / ".claude" / "pr-review.json"
            if config_path.exists():
                try:
                    import json
                    with open(config_path, 'r', encoding='utf-8-sig') as f:
                        config = json.load(f)
                    config_token = config.get('token')
                    if config_token and len(config_token) >= 20 and config_token not in [
                        'YOUR_AZURE_DEVOPS_PAT_HERE', 'PLACEHOLDER_TOKEN_NEEDS_TO_BE_SET'
                    ]:
                        status = "[ACTIVE]" if not ado_env_token and not ado_keychain_token else "[BACKUP]"
                        print(f"{status} Config file (DEPRECATED)")
                        print(f"         Path: {config_path}")
                        print(f"         Token: {config_token[:4]}...{config_token[-4:]}")
                    else:
                        print(f"[  --  ] Config file (placeholder or invalid)")
                except Exception:
                    print(f"[ERROR ] Config file (failed to read)")
            else:
                print(f"[  --  ] Config file (not found)")
        else:
            print(f"[  --  ] Config file (not in a git repository)")

        # GitHub section
        print("\n[GitHub]")
        print("-" * 30)

        # Check environment
        gh_env_token = get_github_token_from_env()
        if gh_env_token:
            print(f"[ACTIVE] Environment variable ({ENV_VAR_NAME_GITHUB})")
            print(f"         Token: {gh_env_token[:4]}...{gh_env_token[-4:]}")
        else:
            print(f"[  --  ] Environment variable ({ENV_VAR_NAME_GITHUB})")

        # Check keychain
        if KEYRING_AVAILABLE:
            gh_keychain_token = get_github_token_from_keychain()
            if gh_keychain_token:
                status = "[ACTIVE]" if not gh_env_token else "[BACKUP]"
                print(f"{status} System keychain ({KEYCHAIN_ACCOUNT_GITHUB})")
                print(f"         Token: {gh_keychain_token[:4]}...{gh_keychain_token[-4:]}")
            else:
                print(f"[  --  ] System keychain ({KEYCHAIN_ACCOUNT_GITHUB})")
        else:
            print("[  --  ] System keychain (keyring not installed)")

        print("")
        print("Resolution order: env > keychain > config (ADO only) > prompt")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
