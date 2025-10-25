#!/usr/bin/env python3
"""
Comprehensive Azure DevOps API Debugger

Shows detailed request/response information for debugging API calls.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found.")
    print("   Install with: pip install requests")
    print("   Or run: ./setup_venv.sh")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: 'python-dotenv' library not found.")
    print("   Install with: pip install python-dotenv")
    print("   Or run: pip install -r requirements.txt")
    sys.exit(1)

import base64
from urllib.parse import quote

# Load environment variables from .env file
load_dotenv()


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str, color=Colors.CYAN):
    """Print a formatted section header."""
    print()
    print(f"{color}{Colors.BOLD}{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}{Colors.ENDC}")
    print()


def print_step(step: str, status: str = "info"):
    """Print a step with status indicator."""
    if status == "success":
        icon = f"{Colors.GREEN}✓{Colors.ENDC}"
    elif status == "error":
        icon = f"{Colors.RED}✗{Colors.ENDC}"
    elif status == "warning":
        icon = f"{Colors.YELLOW}⚠{Colors.ENDC}"
    else:
        icon = f"{Colors.BLUE}→{Colors.ENDC}"

    print(f"{icon} {step}")


def encode_token(token: str) -> str:
    """Encode PAT token for basic auth."""
    credentials = f":{token}"
    return base64.b64encode(credentials.encode()).decode()


def debug_request(url: str, headers: Dict, params: Dict, method: str = "GET"):
    """Show detailed request information."""
    print_section("📤 REQUEST DETAILS", Colors.CYAN)

    print(f"{Colors.BOLD}Method:{Colors.ENDC} {method}")
    print(f"{Colors.BOLD}URL:{Colors.ENDC} {url}")

    print(f"\n{Colors.BOLD}Query Parameters:{Colors.ENDC}")
    for key, value in params.items():
        print(f"  • {key} = {value}")

    print(f"\n{Colors.BOLD}Headers:{Colors.ENDC}")
    for key, value in headers.items():
        # Mask the auth token for security
        if key.lower() == "authorization":
            print(f"  • {key}: Basic [MASKED]")
        else:
            print(f"  • {key}: {value}")


def debug_response(response: requests.Response):
    """Show detailed response information."""
    print_section("📥 RESPONSE DETAILS", Colors.CYAN)

    # Status
    status_color = Colors.GREEN if response.status_code == 200 else Colors.RED
    print(f"{Colors.BOLD}Status Code:{Colors.ENDC} {status_color}{response.status_code}{Colors.ENDC}")
    print(f"{Colors.BOLD}Reason:{Colors.ENDC} {response.reason}")

    # Response headers
    print(f"\n{Colors.BOLD}Response Headers:{Colors.ENDC}")
    for key, value in response.headers.items():
        print(f"  • {key}: {value}")

    # Response body
    print(f"\n{Colors.BOLD}Response Body:{Colors.ENDC}")

    try:
        data = response.json()
        pretty_json = json.dumps(data, indent=2)

        # Truncate if too long
        if len(pretty_json) > 3000:
            print(pretty_json[:3000])
            print(f"\n{Colors.YELLOW}... (truncated, showing first 3000 characters){Colors.ENDC}")
        else:
            print(pretty_json)

    except json.JSONDecodeError:
        print(response.text[:1000])
        if len(response.text) > 1000:
            print(f"\n{Colors.YELLOW}... (truncated){Colors.ENDC}")


def test_pr_endpoint(org: str, project: str, repo: str, pr_id: int, token: str, save_log: bool = False):
    """Test PR threads endpoint with full debugging."""

    log_lines = []

    def log(msg: str):
        """Log to both console and optional file."""
        print(msg)
        if save_log:
            # Strip ANSI codes for file
            log_lines.append(msg.replace(Colors.HEADER, '').replace(Colors.BLUE, '')
                           .replace(Colors.CYAN, '').replace(Colors.GREEN, '')
                           .replace(Colors.YELLOW, '').replace(Colors.RED, '')
                           .replace(Colors.ENDC, '').replace(Colors.BOLD, '')
                           .replace(Colors.UNDERLINE, ''))

    print_section(f"🔍 DEBUGGING PR #{pr_id}", Colors.HEADER)

    log(f"Organization: {org}")
    log(f"Project: {project}")
    log(f"Repository: {repo}")
    log(f"Pull Request: {pr_id}")
    log(f"Timestamp: {datetime.now().isoformat()}")

    # Step 1: Get PR info
    print_section("Step 1: Fetching PR Information")

    pr_url = f"https://dev.azure.com/{quote(org)}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests/{pr_id}"
    params = {"api-version": "7.1"}
    headers = {
        "Authorization": f"Basic {encode_token(token)}",
        "Content-Type": "application/json"
    }

    debug_request(pr_url, headers, params)

    try:
        pr_response = requests.get(pr_url, headers=headers, params=params, timeout=10)
        debug_response(pr_response)

        if pr_response.status_code == 200:
            pr_data = pr_response.json()
            print_step(f"PR Title: {pr_data.get('title', 'N/A')}", "success")
            print_step(f"PR Status: {pr_data.get('status', 'N/A')}", "success")
            print_step(f"Created By: {pr_data.get('createdBy', {}).get('displayName', 'N/A')}", "success")
        elif pr_response.status_code == 401:
            print_step("Authentication failed", "error")
            log("\n❌ Authentication Error:")
            log("  • Check your PAT token is valid and not expired")
            log("  • Verify token has 'Code (Read)' scope")
            log("  • Try creating a new token at:")
            log(f"    https://dev.azure.com/{org}/_usersSettings/tokens")
            return False
        elif pr_response.status_code == 404:
            print_step("PR or repository not found", "error")
            log("\n❌ Not Found Error:")
            log(f"  • Verify PR #{pr_id} exists in repository '{repo}'")
            log(f"  • Check repository name/ID is correct")
            log(f"  • Confirm project name '{project}' is correct")
            log(f"  • Try accessing: https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{pr_id}")
            return False
        else:
            print_step(f"Unexpected status: {pr_response.status_code}", "error")
            return False

    except requests.exceptions.RequestException as e:
        print_step(f"Request failed: {e}", "error")
        return False

    # Step 2: Get PR threads (comments)
    print_section("Step 2: Fetching PR Comment Threads")

    threads_url = f"https://dev.azure.com/{quote(org)}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullRequests/{pr_id}/threads"

    debug_request(threads_url, headers, params)

    try:
        threads_response = requests.get(threads_url, headers=headers, params=params, timeout=10)
        debug_response(threads_response)

        if threads_response.status_code == 200:
            threads_data = threads_response.json()
            thread_count = threads_data.get('count', 0)

            print_step(f"Found {thread_count} comment threads", "success")

            if thread_count > 0:
                print("\n📊 Thread Summary:")

                threads = threads_data.get('value', [])
                active_count = len([t for t in threads if t.get('status') == 'active'])
                file_count = len([t for t in threads if t.get('threadContext', {}).get('filePath')])

                log(f"  • Total threads: {thread_count}")
                log(f"  • Active threads: {active_count}")
                log(f"  • File comments: {file_count}")
                log(f"  • General comments: {thread_count - file_count}")

                # Show first few threads
                log("\n💬 Sample Threads:")
                for i, thread in enumerate(threads[:3], 1):
                    log(f"\n  Thread {i}:")
                    log(f"    Status: {thread.get('status', 'unknown')}")

                    context = thread.get('threadContext', {})
                    if context.get('filePath'):
                        line = context.get('rightFileStart', {}).get('line', 0)
                        log(f"    Location: {context['filePath']}:{line}")

                    comments = thread.get('comments', [])
                    if comments:
                        first_comment = comments[0]
                        author = first_comment.get('author', {}).get('displayName', 'Unknown')
                        content = first_comment.get('content', '')[:100]
                        log(f"    Author: {author}")
                        log(f"    Preview: {content}...")

            return True

        else:
            print_step(f"Failed with status: {threads_response.status_code}", "error")
            return False

    except requests.exceptions.RequestException as e:
        print_step(f"Request failed: {e}", "error")
        return False

    finally:
        # Save log if requested
        if save_log and log_lines:
            log_filename = f"debug-pr-{pr_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
            with open(log_filename, 'w') as f:
                f.write('\n'.join(log_lines))
            print()
            print(f"{Colors.GREEN}✓ Debug log saved to: {log_filename}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(
        description="Debug Azure DevOps API calls with detailed output",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--org", required=True, help="Azure DevOps organization")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--pr", type=int, required=True, help="Pull request ID")
    parser.add_argument("--token", help="PAT token (or use AZURE_DEVOPS_PAT env var)")
    parser.add_argument("--save-log", action="store_true", help="Save debug output to file")

    args = parser.parse_args()

    # Get token
    token = args.token or os.getenv("AZURE_DEVOPS_PAT")
    if not token:
        print(f"{Colors.RED}Error: No token provided{Colors.ENDC}")
        print("Use --token or set AZURE_DEVOPS_PAT environment variable")
        sys.exit(1)

    # Run debug
    success = test_pr_endpoint(args.org, args.project, args.repo, args.pr, token, args.save_log)

    print()
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ API debugging completed successfully{Colors.ENDC}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ API debugging found issues{Colors.ENDC}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
