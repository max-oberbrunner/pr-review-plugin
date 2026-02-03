#!/usr/bin/env python3
"""
GitHub PR Fetcher for PR Review Plugin

Fetches pull request information from GitHub and formats it
for easy consumption by Claude Code or other tools.

Note: Comment fetching is not yet implemented and will be added in a future update.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

# Import error messages
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from error_messages import (
        github_auth_error, github_pr_not_found_error, github_forbidden_error,
        github_rate_limited_error, github_http_error
    )
    ERROR_MESSAGES_AVAILABLE = True
except ImportError:
    ERROR_MESSAGES_AVAILABLE = False


class GitHubPRFetcher:
    """Handles fetching and formatting GitHub PR information."""

    def __init__(self, owner: str, repo: str, token: str, debug: bool = False):
        """
        Initialize the GitHub PR fetcher.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            token: GitHub Personal Access Token
            debug: Enable debug output
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.debug = debug
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def _debug_log(self, message: str):
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def _handle_error(self, response: requests.Response, pr_number: Optional[int] = None):
        """Handle HTTP errors from GitHub API."""
        if ERROR_MESSAGES_AVAILABLE:
            error_msg = github_http_error(
                response.status_code,
                response.text,
                owner=self.owner,
                repo=self.repo,
                pr_number=pr_number
            )
            print(error_msg, file=sys.stderr)
        else:
            # Fallback to simple error messages
            if response.status_code == 401:
                print("Error: GitHub authentication failed. Check your PAT token.", file=sys.stderr)
            elif response.status_code == 404:
                print(f"Error: PR #{pr_number} not found in repo '{self.owner}/{self.repo}'", file=sys.stderr)
            elif response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    print("Error: GitHub API rate limit exceeded.", file=sys.stderr)
                else:
                    print("Error: Access denied. Check your PAT token permissions.", file=sys.stderr)
            else:
                print(f"Error: HTTP {response.status_code} - {response.text}", file=sys.stderr)
        sys.exit(1)

    def fetch_pr_info(self, pr_number: int) -> Dict:
        """
        Fetch basic PR information.

        Args:
            pr_number: Pull request number

        Returns:
            Dictionary with PR information
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"

        self._debug_log(f"Fetching PR info from: {url}")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            self._debug_log(f"PR info response status: {response.status_code}")

            if response.status_code != 200:
                self._handle_error(response, pr_number)

            pr_data = response.json()

            self._debug_log(f"PR Title: {pr_data.get('title', 'N/A')}")
            self._debug_log(f"PR State: {pr_data.get('state', 'N/A')}")

            return pr_data
        except requests.exceptions.Timeout:
            print("Error: Request timed out after 30 seconds", file=sys.stderr)
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to connect to GitHub: {e}", file=sys.stderr)
            sys.exit(1)

    def fetch_pr_comments(self, pr_number: int) -> List[Dict]:
        """
        Fetch PR comments.

        NOTE: This is a placeholder. Comment fetching will be implemented in a future update.

        Args:
            pr_number: Pull request number

        Returns:
            Empty list (placeholder)
        """
        self._debug_log(f"Comment fetching not yet implemented for PR #{pr_number}")
        return []

    def format_markdown(self, pr_number: int, pr_info: Dict, comments: List[Dict]) -> str:
        """
        Format PR information as Markdown report.

        Args:
            pr_number: Pull request number
            pr_info: PR metadata dictionary
            comments: List of comments (currently empty)

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        title = pr_info.get('title', 'Unknown')
        lines.append(f"# Pull Request #{pr_number}: {title}")
        lines.append("")

        # PR metadata
        lines.append(f"**Repository:** {self.owner}/{self.repo}")
        author = pr_info.get('user', {}).get('login', 'Unknown')
        lines.append(f"**Author:** {author}")
        state = pr_info.get('state', 'unknown')
        lines.append(f"**Status:** {state.capitalize()}")
        lines.append(f"**URL:** {pr_info.get('html_url', 'N/A')}")
        lines.append("")

        # Branch info
        head = pr_info.get('head', {})
        base = pr_info.get('base', {})
        lines.append(f"**Branch:** {head.get('ref', 'unknown')} -> {base.get('ref', 'unknown')}")
        lines.append("")

        # Stats
        additions = pr_info.get('additions', 0)
        deletions = pr_info.get('deletions', 0)
        changed_files = pr_info.get('changed_files', 0)
        lines.append(f"**Changes:** +{additions} -{deletions} in {changed_files} files")
        lines.append("")

        # Description
        lines.append("## Description")
        lines.append("")
        body = pr_info.get('body', '')
        if body:
            lines.append(body)
        else:
            lines.append("*No description provided.*")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Comments section (placeholder)
        lines.append("## Comments")
        lines.append("")
        lines.append("> **Note:** GitHub comment fetching is not yet implemented.")
        lines.append("> This feature is coming soon.")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Generated timestamp
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub PR information and format for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variable
  export GITHUB_PAT=your-token-here
  python fetch_github_pr.py --owner octocat --repo hello-world --pr 123

  # Using command-line token
  python fetch_github_pr.py --owner octocat --repo hello-world --pr 123 --token your-token

  # Save to file
  python fetch_github_pr.py --owner octocat --repo hello-world --pr 123 --output pr-info.md
        """
    )

    parser.add_argument("--owner", required=True, help="Repository owner (user or organization)")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    parser.add_argument("--token", help="Personal Access Token (or use GITHUB_PAT env var)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.getenv("GITHUB_PAT")
    if not token:
        print("Error: No token provided. Use --token or set GITHUB_PAT environment variable", file=sys.stderr)
        sys.exit(1)

    # Fetch PR info
    fetcher = GitHubPRFetcher(args.owner, args.repo, token, debug=args.debug)

    if not args.debug:
        print(f"Fetching PR #{args.pr} from {args.owner}/{args.repo}...", file=sys.stderr)

    pr_info = fetcher.fetch_pr_info(args.pr)
    comments = fetcher.fetch_pr_comments(args.pr)

    if args.json:
        output = json.dumps({
            "pr_info": pr_info,
            "comments": comments
        }, indent=2)
    else:
        output = fetcher.format_markdown(args.pr, pr_info, comments)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[SUCCESS] PR info saved to {args.output}", file=sys.stderr)
    else:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
        print(output)


if __name__ == "__main__":
    main()
