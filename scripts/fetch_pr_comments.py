#!/usr/bin/env python3
"""
Azure DevOps PR Comment Fetcher

Fetches pull request comments from Azure DevOps and formats them
for easy consumption by Claude Code or other tools.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: 'python-dotenv' library not found. Install with: pip install python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()


class ADOCommentFetcher:
    """Handles fetching and formatting Azure DevOps PR comments."""

    def __init__(self, org: str, project: str, repo: str, token: str, debug: bool = False):
        self.org = org
        self.project = project
        self.repo = repo
        self.token = token
        self.debug = debug
        self.base_url = f"https://dev.azure.com/{quote(org)}/{quote(project)}/_apis/git"
        self.headers = {
            "Authorization": f"Basic {self._encode_token(token)}",
            "Content-Type": "application/json"
        }

    def _debug_log(self, message: str):
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)

    @staticmethod
    def _encode_token(token: str) -> str:
        """Encode PAT token for basic auth."""
        import base64
        credentials = f":{token}"
        return base64.b64encode(credentials.encode()).decode()

    def fetch_pr_threads(self, pr_id: int) -> List[Dict]:
        """Fetch all comment threads for a PR."""
        url = f"{self.base_url}/repositories/{quote(self.repo)}/pullRequests/{pr_id}/threads"
        params = {"api-version": "7.1"}

        self._debug_log(f"Fetching threads from: {url}")
        self._debug_log(f"Parameters: {params}")

        try:
            response = requests.get(url, headers=self.headers, params=params)
            self._debug_log(f"Response status: {response.status_code}")

            response.raise_for_status()
            data = response.json()

            thread_count = data.get("count", len(data.get("value", [])))
            self._debug_log(f"Retrieved {thread_count} threads")

            return data.get("value", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"Error: Authentication failed. Check your PAT token.", file=sys.stderr)
            elif e.response.status_code == 404:
                print(f"Error: PR #{pr_id} not found in repo '{self.repo}'", file=sys.stderr)
            else:
                print(f"Error: HTTP {e.response.status_code} - {e.response.text}", file=sys.stderr)
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to connect to Azure DevOps: {e}", file=sys.stderr)
            sys.exit(1)

    def fetch_pr_info(self, pr_id: int) -> Dict:
        """Fetch basic PR information."""
        url = f"{self.base_url}/repositories/{quote(self.repo)}/pullRequests/{pr_id}"
        params = {"api-version": "7.1"}

        self._debug_log(f"Fetching PR info from: {url}")

        try:
            response = requests.get(url, headers=self.headers, params=params)
            self._debug_log(f"PR info response status: {response.status_code}")

            response.raise_for_status()
            pr_data = response.json()

            self._debug_log(f"PR Title: {pr_data.get('title', 'N/A')}")
            self._debug_log(f"PR Status: {pr_data.get('status', 'N/A')}")

            return pr_data
        except requests.exceptions.RequestException as e:
            self._debug_log(f"Failed to fetch PR info: {e}")
            return {}

    def format_markdown(self, pr_id: int, threads: List[Dict], pr_info: Optional[Dict] = None) -> str:
        """Format threads as Markdown report."""
        lines = []

        # Header
        lines.append(f"# PR Comments for PR #{pr_id}")
        lines.append("")

        if pr_info:
            lines.append(f"**Title:** {pr_info.get('title', 'N/A')}")
            lines.append(f"**Status:** {pr_info.get('status', 'N/A')}")
            created_by = pr_info.get('createdBy', {}).get('displayName', 'Unknown')
            lines.append(f"**Author:** {created_by}")
            lines.append("")

        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        if not threads:
            lines.append("*No comments found on this PR.*")
            return "\n".join(lines)

        # Group comments by file
        file_threads = {}
        general_threads = []

        for thread in threads:
            comments = thread.get("comments", [])
            if not comments:
                continue

            thread_context = thread.get("threadContext")
            if thread_context and thread_context.get("filePath"):
                file_path = thread_context["filePath"]
                line_info = thread_context.get("rightFileStart", {})
                line_num = line_info.get("line", 0)

                key = f"{file_path}:{line_num}" if line_num > 0 else file_path

                if key not in file_threads:
                    file_threads[key] = []
                file_threads[key].append(thread)
            else:
                general_threads.append(thread)

        # Output file-specific comments
        if file_threads:
            lines.append("## 📁 File Comments")
            lines.append("")

            for location in sorted(file_threads.keys()):
                lines.append(f"### {location}")
                lines.append("")

                for thread in file_threads[location]:
                    status = thread.get("status", "unknown")
                    status_emoji = {
                        "active": "🔴",
                        "fixed": "✅",
                        "closed": "✔️",
                        "pending": "⏳",
                        "wontFix": "🚫",
                        "byDesign": "📐"
                    }.get(status, "❓")

                    lines.append(f"**Thread #{thread.get('id', 'N/A')}** {status_emoji} *{status}*")
                    lines.append("")

                    for comment in thread.get("comments", []):
                        author = comment.get("author", {}).get("displayName", "Unknown")
                        content = comment.get("content", "").strip()
                        comment_type = comment.get("commentType", "text")

                        lines.append(f"**{author}:**")
                        if content:
                            # Indent comment content
                            for line in content.split("\n"):
                                lines.append(f"> {line}")
                        lines.append("")

                    lines.append("---")
                    lines.append("")

        # Output general comments
        if general_threads:
            lines.append("## 💬 General Comments")
            lines.append("")

            for thread in general_threads:
                status = thread.get("status", "unknown")
                status_emoji = {
                    "active": "🔴",
                    "fixed": "✅",
                    "closed": "✔️",
                    "pending": "⏳",
                    "wontFix": "🚫",
                    "byDesign": "📐"
                }.get(status, "❓")

                lines.append(f"**Thread #{thread.get('id', 'N/A')}** {status_emoji} *{status}*")
                lines.append("")

                for comment in thread.get("comments", []):
                    author = comment.get("author", {}).get("displayName", "Unknown")
                    content = comment.get("content", "").strip()

                    lines.append(f"**{author}:**")
                    if content:
                        for line in content.split("\n"):
                            lines.append(f"> {line}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Summary
        total_threads = len(threads)
        active_threads = len([t for t in threads if t.get("status") == "active"])

        lines.append(f"## 📊 Summary")
        lines.append("")
        lines.append(f"- **Total threads:** {total_threads}")
        lines.append(f"- **Active threads:** {active_threads}")
        lines.append(f"- **File comments:** {len(file_threads)}")
        lines.append(f"- **General comments:** {len(general_threads)}")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Azure DevOps PR comments and format them for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables
  export AZURE_DEVOPS_PAT=your-token-here
  python fetch_pr_comments.py --org myorg --project myproject --repo myrepo --pr 123

  # Using command-line token
  python fetch_pr_comments.py --org myorg --project myproject --repo myrepo --pr 123 --token your-token

  # Save to file
  python fetch_pr_comments.py --org myorg --project myproject --repo myrepo --pr 123 --output pr-comments.md
        """
    )

    parser.add_argument("--org", required=True, help="Azure DevOps organization name")
    parser.add_argument("--project", required=True, help="Project name or ID")
    parser.add_argument("--repo", required=True, help="Repository ID or name")
    parser.add_argument("--pr", type=int, required=True, help="Pull request ID")
    parser.add_argument("--token", help="Personal Access Token (or use AZURE_DEVOPS_PAT env var)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output (shows API requests/responses)")

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.getenv("AZURE_DEVOPS_PAT")
    if not token:
        print("Error: No token provided. Use --token or set AZURE_DEVOPS_PAT environment variable", file=sys.stderr)
        sys.exit(1)

    # Fetch comments
    fetcher = ADOCommentFetcher(args.org, args.project, args.repo, token, debug=args.debug)

    if not args.debug:
        print(f"Fetching comments for PR #{args.pr}...", file=sys.stderr)
    threads = fetcher.fetch_pr_threads(args.pr)

    if args.json:
        output = json.dumps(threads, indent=2)
    else:
        pr_info = fetcher.fetch_pr_info(args.pr)
        output = fetcher.format_markdown(args.pr, threads, pr_info)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✓ Comments saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
