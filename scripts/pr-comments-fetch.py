#!/usr/bin/env python3
"""
Minimal PR Comment Fetcher for Claude Code Skills

Fetches Azure DevOps PR comments and outputs Claude Code-optimized format.
Designed to be called by Claude Code skills with minimal dependencies.
"""

import argparse
import json
import os
import sys
from typing import Dict, List

try:
    import requests
except ImportError:
    print(json.dumps({"error": "requests library not found", "install": "pip install requests"}))
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def encode_token(token: str) -> str:
    """Encode PAT token for Azure DevOps basic auth."""
    import base64
    return base64.b64encode(f":{token}".encode()).decode()


def fetch_pr_data(org: str, project: str, repo: str, pr_id: int, token: str) -> Dict:
    """Fetch PR info and comment threads."""
    base_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"
    headers = {"Authorization": f"Basic {encode_token(token)}", "Content-Type": "application/json"}
    params = {"api-version": "7.1"}

    result = {"pr_info": None, "threads": [], "error": None}

    # Fetch PR info
    try:
        pr_response = requests.get(f"{base_url}/pullRequests/{pr_id}", headers=headers, params=params, timeout=10)
        if pr_response.status_code == 200:
            result["pr_info"] = pr_response.json()
        else:
            result["error"] = f"PR fetch failed: {pr_response.status_code}"
            return result
    except Exception as e:
        result["error"] = f"PR fetch error: {str(e)}"
        return result

    # Fetch threads
    try:
        threads_response = requests.get(f"{base_url}/pullRequests/{pr_id}/threads", headers=headers, params=params, timeout=10)
        if threads_response.status_code == 200:
            result["threads"] = threads_response.json().get("value", [])
        else:
            result["error"] = f"Threads fetch failed: {threads_response.status_code}"
    except Exception as e:
        result["error"] = f"Threads fetch error: {str(e)}"

    return result


def categorize_comments(threads: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize comments by priority based on content patterns."""
    categories = {"critical": [], "important": [], "style": [], "general": []}

    # Patterns for critical issues
    critical_patterns = [
        "pattern", "architecture", "service", "dependency", "inject",
        "avoid", "don't use", "bad pattern", "refactor"
    ]

    # Patterns for important issues
    important_patterns = [
        "required", "validation", "error", "check", "verify",
        "null", "undefined", "handle", "test"
    ]

    # Patterns for style
    style_patterns = [
        "variable", "color", "style", "format", "indent",
        "comment", "documentation", "naming"
    ]

    for thread in threads:
        if thread.get("status") != "active":
            continue

        comments = thread.get("comments", [])
        if not comments:
            continue

        content = comments[0].get("content", "").lower()
        thread_context = thread.get("threadContext", {})

        # Create comment entry
        entry = {
            "thread_id": thread.get("id"),
            "status": thread.get("status"),
            "file_path": thread_context.get("filePath", ""),
            "line": thread_context.get("rightFileStart", {}).get("line", 0),
            "author": comments[0].get("author", {}).get("displayName", "Unknown"),
            "content": comments[0].get("content", ""),
            "date": comments[0].get("publishedDate", "")
        }

        # Categorize
        if any(pattern in content for pattern in critical_patterns):
            categories["critical"].append(entry)
        elif any(pattern in content for pattern in important_patterns):
            categories["important"].append(entry)
        elif any(pattern in content for pattern in style_patterns):
            categories["style"].append(entry)
        elif entry["file_path"]:
            categories["important"].append(entry)
        else:
            categories["general"].append(entry)

    return categories


def format_for_claude(pr_info: Dict, categories: Dict[str, List[Dict]]) -> str:
    """Format output optimized for Claude Code consumption."""
    lines = []

    # Header
    title = pr_info.get("title", "Unknown")
    author = pr_info.get("createdBy", {}).get("displayName", "Unknown")
    pr_id = pr_info.get("pullRequestId", 0)

    lines.append(f"# PR #{pr_id}: {title}")
    lines.append(f"**Author:** {author}")
    lines.append("")

    # Calculate totals
    total_active = sum(len(comments) for comments in categories.values())

    if total_active == 0:
        lines.append("✅ No active comments to address!")
        return "\n".join(lines)

    lines.append(f"**Active Comments:** {total_active}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Critical issues
    if categories["critical"]:
        lines.append("## 🔴 Critical Issues (Architecture & Patterns)")
        lines.append("")
        for comment in categories["critical"]:
            location = f"{comment['file_path']}:{comment['line']}" if comment['file_path'] else "General"
            lines.append(f"### {location}")
            lines.append(f"**{comment['author']}:**")
            lines.append(f"> {comment['content']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Important issues
    if categories["important"]:
        lines.append("## 🟡 Important Issues (Code Quality)")
        lines.append("")
        for comment in categories["important"]:
            location = f"{comment['file_path']}:{comment['line']}" if comment['file_path'] else "General"
            lines.append(f"### {location}")
            lines.append(f"**{comment['author']}:**")
            lines.append(f"> {comment['content']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Style issues
    if categories["style"]:
        lines.append("## 🟢 Style & Best Practices")
        lines.append("")
        for comment in categories["style"]:
            location = f"{comment['file_path']}:{comment['line']}" if comment['file_path'] else "General"
            lines.append(f"### {location}")
            lines.append(f"**{comment['author']}:**")
            lines.append(f"> {comment['content']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # General comments
    if categories["general"]:
        lines.append("## 💬 General Discussion")
        lines.append("")
        for comment in categories["general"]:
            lines.append(f"**{comment['author']}:**")
            lines.append(f"> {comment['content']}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch Azure DevOps PR comments for Claude Code")
    parser.add_argument("--org", required=True, help="Organization")
    parser.add_argument("--project", required=True, help="Project")
    parser.add_argument("--repo", required=True, help="Repository")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--token", help="PAT token (or use AZURE_DEVOPS_PAT env var)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--format", choices=["claude", "json"], default="claude", help="Output format")

    args = parser.parse_args()

    # Get token
    token = args.token or os.getenv("AZURE_DEVOPS_PAT")
    if not token:
        error = {"error": "No token provided", "help": "Set AZURE_DEVOPS_PAT or use --token"}
        print(json.dumps(error) if args.json or args.format == "json" else json.dumps(error, indent=2))
        sys.exit(1)

    # Fetch data
    data = fetch_pr_data(args.org, args.project, args.repo, args.pr, token)

    if data["error"]:
        error = {"error": data["error"], "org": args.org, "project": args.project, "repo": args.repo, "pr": args.pr}
        print(json.dumps(error) if args.json or args.format == "json" else json.dumps(error, indent=2))
        sys.exit(1)

    # Output
    if args.json or args.format == "json":
        output = {
            "pr_info": data["pr_info"],
            "threads": data["threads"],
            "categories": categorize_comments(data["threads"])
        }
        print(json.dumps(output, indent=2))
    else:
        categories = categorize_comments(data["threads"])
        output = format_for_claude(data["pr_info"], categories)
        print(output)


if __name__ == "__main__":
    main()
