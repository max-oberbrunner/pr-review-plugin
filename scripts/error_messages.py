#!/usr/bin/env python3
"""
Centralized Error Messages for PR Review Plugin

Provides actionable, user-friendly error messages with troubleshooting
guidance and relevant URLs.
"""

from typing import Optional


class ErrorCode:
    """Error code constants."""
    AUTH_FAILED = "AUTH_FAILED"
    PR_NOT_FOUND = "PR_NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    CONFIG_MISSING = "CONFIG_MISSING"
    NOT_A_GIT_REPO = "NOT_A_GIT_REPO"
    TOKEN_INVALID = "TOKEN_INVALID"
    PATH_NOT_FOUND = "PATH_NOT_FOUND"


def get_token_creation_url(org: Optional[str] = None) -> str:
    """Get Azure DevOps PAT creation URL."""
    if org:
        return f"https://dev.azure.com/{org}/_usersSettings/tokens"
    return "https://dev.azure.com/{your-org}/_usersSettings/tokens"


def get_pr_url(org: str, project: str, repo: str, pr_id: int) -> str:
    """Get Azure DevOps PR URL."""
    return f"https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{pr_id}"


def get_azure_status_url() -> str:
    """Get Azure DevOps status page URL."""
    return "https://status.dev.azure.com/"


def format_error(code: str, message: str, details: str, fix: str) -> str:
    """
    Format a complete error message with all components.

    Args:
        code: Error code identifier
        message: Short error message
        details: Detailed explanation
        fix: Actionable fix instructions

    Returns:
        Formatted error message string
    """
    lines = [
        "",
        "=" * 60,
        f"ERROR [{code}]: {message}",
        "=" * 60,
        "",
        "Details:",
        f"  {details}",
        "",
        "How to fix:",
    ]

    for line in fix.split('\n'):
        lines.append(f"  {line}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    return '\n'.join(lines)


def auth_error(org: Optional[str] = None, http_status: int = 401) -> str:
    """
    Generate authentication error message (401).

    Args:
        org: Azure DevOps organization name
        http_status: HTTP status code

    Returns:
        Formatted error message
    """
    token_url = get_token_creation_url(org)

    fix = f"""1. Verify your PAT token is correct and not expired

2. Check token resolution order:
   - Environment variable: export AZURE_DEVOPS_PAT='your-token'
   - System keychain: python scripts/token_manager.py --status
   - Config file: .claude/pr-review.json (in project root)

3. Create a new PAT token if needed:
   {token_url}

   Required permissions:
   - Code (Read)

4. Test your token:
   curl -u :{'{your-token}'} "https://dev.azure.com/{org or '{org}'}/_apis/projects?api-version=7.1"

5. If using keychain, update the stored token:
   python scripts/token_manager.py --save"""

    return format_error(
        ErrorCode.AUTH_FAILED,
        "Authentication failed",
        f"Azure DevOps returned HTTP {http_status}. Your PAT token may be invalid, expired, or missing required permissions.",
        fix
    )


def pr_not_found_error(org: str, project: str, repo: str, pr_id: int) -> str:
    """
    Generate PR not found error message (404).

    Args:
        org: Azure DevOps organization
        project: Project name
        repo: Repository name
        pr_id: Pull request ID

    Returns:
        Formatted error message
    """
    pr_url = get_pr_url(org, project, repo, pr_id)

    fix = f"""1. Verify the PR exists:
   {pr_url}

2. Check your configuration values in .claude/pr-review.json (in project root):
   - organization: "{org}"
   - project: "{project}"
   - repository: "{repo}"

3. Verify the PR number is correct: #{pr_id}

4. Note: Repository names are case-sensitive in some cases.
   Try the exact name from Azure DevOps.

5. If the PR is in a different project/repo, update your config."""

    return format_error(
        ErrorCode.PR_NOT_FOUND,
        f"PR #{pr_id} not found",
        f"The pull request was not found in repository '{repo}'. This could mean the PR doesn't exist, or the org/project/repo configuration is incorrect.",
        fix
    )


def forbidden_error(org: Optional[str] = None) -> str:
    """
    Generate forbidden error message (403).

    Args:
        org: Azure DevOps organization name

    Returns:
        Formatted error message
    """
    token_url = get_token_creation_url(org)

    fix = f"""1. Your PAT token lacks required permissions.

2. Create a new token with Code (Read) scope:
   {token_url}

3. If this is a private repository, ensure:
   - Your account has access to the repository
   - The PAT is scoped to the correct organization

4. For fine-grained access, the token needs:
   - Code: Read (minimum for fetching PR comments)

5. Update your token using one of:
   - Environment variable: export AZURE_DEVOPS_PAT='new-token'
   - System keychain: python scripts/token_manager.py --save"""

    return format_error(
        ErrorCode.FORBIDDEN,
        "Access denied",
        "Your PAT token is valid but lacks permission to access this resource. The token may not have the required 'Code (Read)' scope.",
        fix
    )


def timeout_error(timeout_seconds: int = 60) -> str:
    """
    Generate timeout error message.

    Args:
        timeout_seconds: Timeout value that was exceeded

    Returns:
        Formatted error message
    """
    status_url = get_azure_status_url()

    fix = f"""1. Check Azure DevOps service status:
   {status_url}

2. Check your network connection:
   - Try opening Azure DevOps in your browser
   - Check if you're behind a proxy or VPN

3. Try again - this may be a temporary issue.

4. If the problem persists:
   - Check your firewall settings
   - Try from a different network
   - Contact your network administrator

5. The request timed out after {timeout_seconds} seconds.
   Large PRs with many comments may take longer."""

    return format_error(
        ErrorCode.TIMEOUT,
        f"Request timed out after {timeout_seconds} seconds",
        "The connection to Azure DevOps took too long. This could be a network issue or Azure DevOps may be experiencing problems.",
        fix
    )


def connection_error(error_message: str = "") -> str:
    """
    Generate connection error message.

    Args:
        error_message: Original error message

    Returns:
        Formatted error message
    """
    status_url = get_azure_status_url()

    details = "Failed to establish a connection to Azure DevOps."
    if error_message:
        details += f" Error: {error_message}"

    fix = f"""1. Check your internet connection.

2. Check Azure DevOps service status:
   {status_url}

3. Verify Azure DevOps URL is accessible:
   ping dev.azure.com

4. If you're behind a corporate proxy:
   - Configure proxy settings
   - Check with your network administrator

5. DNS issues - try:
   nslookup dev.azure.com

6. Firewall may be blocking access to:
   - dev.azure.com
   - *.visualstudio.com"""

    return format_error(
        ErrorCode.CONNECTION_ERROR,
        "Connection failed",
        details,
        fix
    )


def config_missing_error(project_root=None) -> str:
    """Generate config file missing error message."""
    config_path = f"{project_root}/.claude/pr-review.json" if project_root else ".claude/pr-review.json"

    fix = f"""1. Create the configuration file in your project root:
   {config_path}

2. Minimal configuration (paths are auto-detected):
   {{
     "organization": "your-org",
     "project": "your-project",
     "repository": "your-repo"
   }}

3. Set your token using one of these methods:
   - Environment variable: export AZURE_DEVOPS_PAT='your-token'
   - System keychain: python scripts/token_manager.py --save

4. Or run the setup wizard from within your project:
   python scripts/setup_wizard.py"""

    return format_error(
        ErrorCode.CONFIG_MISSING,
        "Configuration file not found",
        f"The configuration file {config_path} does not exist.",
        fix
    )


def not_a_git_repo_error() -> str:
    """Generate not in a git repository error message."""
    fix = """1. Navigate to your project directory:
   cd /path/to/your/project

2. Ensure you're in a git repository:
   git status

3. If this is a new project, initialize git:
   git init

4. The PR Review plugin requires a git repository to store
   configuration files in the project's .claude folder."""

    return format_error(
        ErrorCode.NOT_A_GIT_REPO,
        "Not in a git repository",
        "This command must be run from within a git repository. The plugin looks for a .git folder to determine the project root.",
        fix
    )


def token_invalid_error(reason: str = "unknown") -> str:
    """
    Generate invalid token error message.

    Args:
        reason: Reason why token is invalid

    Returns:
        Formatted error message
    """
    fix = """1. Token validation failed. Check:
   - Token is not a placeholder value
   - Token is at least 20 characters long
   - Token has not been truncated/corrupted

2. Set your token using:
   - Environment variable: export AZURE_DEVOPS_PAT='your-token'
   - System keychain: python scripts/token_manager.py --save

3. Check current token status:
   python scripts/token_manager.py --status

4. Create a new token if needed at:
   https://dev.azure.com/{your-org}/_usersSettings/tokens"""

    return format_error(
        ErrorCode.TOKEN_INVALID,
        "Invalid token",
        f"Token validation failed: {reason}",
        fix
    )


def path_not_found_error(path_type: str, path: str) -> str:
    """
    Generate path not found error message.

    Args:
        path_type: Type of path (e.g., 'Python', 'Script')
        path: The path that was not found

    Returns:
        Formatted error message
    """
    fix = f"""1. The specified {path_type.lower()} path does not exist:
   {path}

2. Paths are now auto-detected. Remove these from your config:
   - scriptPath (auto-detected relative to run_pr_review.py)
   - pythonPath (auto-detected from current Python interpreter)

3. If you need to specify a custom path, ensure it's correct:
   - Use absolute paths
   - Check for typos
   - Verify the file/executable exists

4. Minimal config (recommended):
   {{
     "organization": "your-org",
     "project": "your-project",
     "repository": "your-repo"
   }}"""

    return format_error(
        ErrorCode.PATH_NOT_FOUND,
        f"{path_type} not found",
        f"The configured {path_type.lower()} path does not exist or is not accessible.",
        fix
    )


def http_error(status_code: int, response_text: str = "", org: Optional[str] = None,
               project: Optional[str] = None, repo: Optional[str] = None, pr_id: Optional[int] = None) -> str:
    """
    Generate error message for HTTP errors.

    Routes to specific error handlers based on status code.

    Args:
        status_code: HTTP status code
        response_text: Response body text
        org: Azure DevOps organization
        project: Project name
        repo: Repository name
        pr_id: Pull request ID

    Returns:
        Formatted error message
    """
    if status_code == 401:
        return auth_error(org)
    elif status_code == 403:
        return forbidden_error(org)
    elif status_code == 404 and org and project and repo and pr_id:
        return pr_not_found_error(org, project, repo, pr_id)
    elif status_code == 404:
        return format_error(
            ErrorCode.PR_NOT_FOUND,
            "Resource not found (404)",
            f"The requested resource was not found. Response: {response_text[:200] if response_text else 'No details'}",
            "Verify your organization, project, repository, and PR number are correct."
        )
    else:
        return format_error(
            f"HTTP_{status_code}",
            f"HTTP Error {status_code}",
            f"Azure DevOps returned an unexpected error. Response: {response_text[:200] if response_text else 'No details'}",
            f"Check Azure DevOps status at {get_azure_status_url()} and try again."
        )
