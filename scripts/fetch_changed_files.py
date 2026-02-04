#!/usr/bin/env python3
"""
Fetch Changed Files Script

Fetches the list of files changed in a PR from Azure DevOps or GitHub.
Outputs JSON with file paths, change types, and line counts.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

# Import token manager from same directory
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from token_manager import resolve_token, resolve_github_token
except ImportError:
    def resolve_token(config=None, prompt_if_missing=True):
        token = os.getenv('AZURE_DEVOPS_PAT')
        if token:
            return (token, 'env')
        return (None, 'none')

    def resolve_github_token(prompt_if_missing=True):
        token = os.getenv('GITHUB_PAT')
        if token:
            return (token, 'env')
        return (None, 'none')


class ADOChangedFilesFetcher:
    """Fetches changed files from Azure DevOps PR."""

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
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)

    @staticmethod
    def _encode_token(token: str) -> str:
        import base64
        credentials = f":{token}"
        return base64.b64encode(credentials.encode()).decode()

    def fetch_iterations(self, pr_id: int) -> List[Dict]:
        """Fetch all iterations for a PR."""
        url = f"{self.base_url}/repositories/{quote(self.repo)}/pullRequests/{pr_id}/iterations"
        params = {"api-version": "7.1"}

        self._debug_log(f"Fetching iterations from: {url}")

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("value", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching iterations: {e}", file=sys.stderr)
            return []

    def fetch_iteration_changes(self, pr_id: int, iteration_id: int) -> List[Dict]:
        """Fetch changes for a specific iteration."""
        url = f"{self.base_url}/repositories/{quote(self.repo)}/pullRequests/{pr_id}/iterations/{iteration_id}/changes"
        params = {"api-version": "7.1"}

        self._debug_log(f"Fetching changes for iteration {iteration_id}")

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("changeEntries", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching iteration changes: {e}", file=sys.stderr)
            return []

    def fetch_changed_files(self, pr_id: int) -> List[Dict]:
        """
        Fetch all changed files in a PR.

        Returns list of dicts with:
        - path: file path
        - changeType: add/edit/delete/rename
        - originalPath: original path (for renames)
        """
        iterations = self.fetch_iterations(pr_id)
        if not iterations:
            self._debug_log("No iterations found")
            return []

        # Get the latest iteration
        latest_iteration = max(iterations, key=lambda x: x.get("id", 0))
        iteration_id = latest_iteration.get("id")

        self._debug_log(f"Using latest iteration: {iteration_id}")

        changes = self.fetch_iteration_changes(pr_id, iteration_id)
        changed_files = []
        seen_paths = set()

        for change in changes:
            item = change.get("item", {})
            path = item.get("path", "")

            # Skip directories and empty paths
            if not path or item.get("isFolder", False):
                continue

            # Skip duplicates
            if path in seen_paths:
                continue
            seen_paths.add(path)

            # Map ADO change types
            change_type_map = {
                "add": "added",
                "edit": "modified",
                "delete": "deleted",
                "rename": "renamed",
                "sourceRename": "renamed"
            }
            change_type = change.get("changeType", "edit")
            normalized_type = change_type_map.get(change_type.lower(), "modified")

            file_info = {
                "path": path.lstrip("/"),  # Remove leading slash
                "changeType": normalized_type,
            }

            # Include original path for renames
            if normalized_type == "renamed":
                original_path = change.get("sourceServerItem", "")
                if original_path:
                    file_info["originalPath"] = original_path.lstrip("/")

            changed_files.append(file_info)

        return changed_files


class GitHubChangedFilesFetcher:
    """Fetches changed files from GitHub PR."""

    def __init__(self, owner: str, repo: str, token: str, debug: bool = False):
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
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def fetch_changed_files(self, pr_number: int) -> List[Dict]:
        """
        Fetch all changed files in a PR.

        Uses pagination to get all files if more than 100.
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files"
        params = {"per_page": 100}
        all_files = []
        page = 1

        while True:
            params["page"] = page
            self._debug_log(f"Fetching files page {page} from: {url}")

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                files = response.json()

                if not files:
                    break

                for file in files:
                    # Map GitHub status to normalized change type
                    status_map = {
                        "added": "added",
                        "modified": "modified",
                        "removed": "deleted",
                        "renamed": "renamed",
                        "copied": "added",
                        "changed": "modified"
                    }
                    status = file.get("status", "modified")
                    change_type = status_map.get(status, "modified")

                    file_info = {
                        "path": file.get("filename", ""),
                        "changeType": change_type,
                        "additions": file.get("additions", 0),
                        "deletions": file.get("deletions", 0),
                        "changes": file.get("changes", 0)
                    }

                    # Include original path for renames
                    if change_type == "renamed" and file.get("previous_filename"):
                        file_info["originalPath"] = file.get("previous_filename")

                    all_files.append(file_info)

                # Check if there are more pages
                if len(files) < 100:
                    break
                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching changed files: {e}", file=sys.stderr)
                break

        return all_files


def find_project_root():
    """Find the project root by searching upward for a .git folder."""
    current = Path.cwd()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    if (current / ".git").exists():
        return current

    return None


def load_config(config_path: Optional[Path] = None) -> Optional[Dict]:
    """Load configuration from pr-review.json."""
    if config_path is None:
        project_root = find_project_root()
        if not project_root:
            return None
        config_path = project_root / ".claude" / "pr-review.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch changed files from a PR (Azure DevOps or GitHub)"
    )
    parser.add_argument("--pr", type=int, required=True, help="Pull request number/ID")
    parser.add_argument("--config", help="Path to pr-review.json config file")
    parser.add_argument("--token", help="Override PAT token")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")

    # Platform-specific overrides
    parser.add_argument("--platform", choices=["azure-devops", "github"], help="Platform override")
    parser.add_argument("--org", help="Azure DevOps organization")
    parser.add_argument("--project", help="Azure DevOps project")
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--owner", help="GitHub owner (user or org)")

    args = parser.parse_args()

    # Load config
    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    # Determine platform and settings
    platform = args.platform or (config.get("platform") if config else None)
    if not platform:
        print("Error: Platform not specified. Use --platform or configure in pr-review.json", file=sys.stderr)
        sys.exit(1)

    # Get token
    if args.token:
        token = args.token
    elif platform == "github":
        token, _ = resolve_github_token(prompt_if_missing=False)
    else:
        token, _ = resolve_token(config, prompt_if_missing=False)

    if not token:
        env_var = "GITHUB_PAT" if platform == "github" else "AZURE_DEVOPS_PAT"
        print(f"Error: No token found. Set {env_var} or use --token", file=sys.stderr)
        sys.exit(1)

    # Fetch changed files based on platform
    if platform == "github":
        owner = args.owner or (config.get("owner") if config else None)
        repo = args.repo or (config.get("repository") if config else None)

        if not owner or not repo:
            print("Error: GitHub requires --owner and --repo (or config)", file=sys.stderr)
            sys.exit(1)

        if not args.debug:
            print(f"[INFO] Fetching changed files for PR #{args.pr} from {owner}/{repo}...", file=sys.stderr)

        fetcher = GitHubChangedFilesFetcher(owner, repo, token, debug=args.debug)
        changed_files = fetcher.fetch_changed_files(args.pr)
    else:
        # Azure DevOps
        org = args.org or (config.get("organization") if config else None)
        project = args.project or (config.get("project") if config else None)
        repo = args.repo or (config.get("repository") if config else None)

        if not org or not project or not repo:
            print("Error: Azure DevOps requires --org, --project, and --repo (or config)", file=sys.stderr)
            sys.exit(1)

        if not args.debug:
            print(f"[INFO] Fetching changed files for PR #{args.pr} from {org}/{project}/{repo}...", file=sys.stderr)

        fetcher = ADOChangedFilesFetcher(org, project, repo, token, debug=args.debug)
        changed_files = fetcher.fetch_changed_files(args.pr)

    # Build output
    output = {
        "pr": args.pr,
        "platform": platform,
        "totalFiles": len(changed_files),
        "files": changed_files,
        "summary": {
            "added": len([f for f in changed_files if f["changeType"] == "added"]),
            "modified": len([f for f in changed_files if f["changeType"] == "modified"]),
            "deleted": len([f for f in changed_files if f["changeType"] == "deleted"]),
            "renamed": len([f for f in changed_files if f["changeType"] == "renamed"])
        }
    }

    json_output = json.dumps(output, indent=2)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"[SUCCESS] Changed files saved to {args.output}", file=sys.stderr)
    else:
        print(json_output)

    print(f"[INFO] Found {len(changed_files)} changed files", file=sys.stderr)


if __name__ == "__main__":
    main()
