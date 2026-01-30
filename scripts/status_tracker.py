#!/usr/bin/env python3
"""
PR Comment Status Tracker

Tracks the status of PR review comments across multiple fetches,
preserving user progress (COMPLETED, IN_PROGRESS, SKIPPED, BLOCKED).
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CommentStatus:
    """Valid custom status values for comments."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

    @classmethod
    def all_statuses(cls):
        return [cls.ACTIVE, cls.COMPLETED, cls.IN_PROGRESS, cls.SKIPPED, cls.BLOCKED]


def get_centralized_status_dir(org: str, project: str, repo: str) -> Path:
    """
    Get centralized status directory path.

    Args:
        org: Azure DevOps organization
        project: Project name
        repo: Repository name

    Returns:
        Path to centralized status directory
    """
    return Path.home() / ".claude" / "pr-review-status" / org / project / repo


def get_legacy_status_file(pr_number: int, working_dir: Optional[Path] = None) -> Path:
    """
    Get legacy status file path for migration purposes.

    Args:
        pr_number: Pull request number
        working_dir: Legacy working directory

    Returns:
        Path to legacy status file
    """
    base_dir = working_dir or Path.cwd()
    return base_dir / ".pr-status" / f"pr-{pr_number}-status.json"


class StatusTracker:
    """Manages persistent status tracking for PR comments."""

    def __init__(self, pr_number: int, working_dir: Optional[Path] = None,
                 org: Optional[str] = None, project: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize status tracker.

        Args:
            pr_number: The pull request number
            working_dir: Directory where status file should be stored (legacy fallback)
            org: Azure DevOps organization (for centralized storage)
            project: Project name (for centralized storage)
            repo: Repository name (for centralized storage)
        """
        self.pr_number = pr_number
        self.org = org
        self.project = project
        self.repo = repo
        self.working_dir = working_dir or Path.cwd()
        self.statuses = {}

        # Determine status file location
        if org and project and repo:
            # Centralized location: ~/.claude/pr-review-status/{org}/{project}/{repo}/
            self.status_dir = get_centralized_status_dir(org, project, repo)
            self.use_centralized = True
        else:
            # Legacy fallback: .pr-status/ in working directory
            self.status_dir = self.working_dir / ".pr-status"
            self.use_centralized = False

        # Ensure directory exists
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.status_dir / f"pr-{pr_number}-status.json"

        # Check for legacy file and migrate if needed
        if self.use_centralized:
            self._migrate_legacy_status()

    def _migrate_legacy_status(self) -> bool:
        """
        Migrate status from legacy location to centralized location.

        Returns:
            True if migration occurred, False otherwise
        """
        if not self.use_centralized:
            return False

        # Check multiple potential legacy locations
        legacy_locations = [
            get_legacy_status_file(self.pr_number, self.working_dir),
            get_legacy_status_file(self.pr_number, Path.cwd()),
        ]

        for legacy_file in legacy_locations:
            if legacy_file.exists() and not self.status_file.exists():
                try:
                    # Copy legacy file to new location
                    shutil.copy2(legacy_file, self.status_file)
                    print(f"[INFO] Migrated status file from {legacy_file} to {self.status_file}")

                    # Optionally delete the old file (keep for safety)
                    # legacy_file.unlink()

                    return True
                except Exception as e:
                    print(f"Warning: Failed to migrate legacy status file: {e}")

        return False

    def load(self) -> bool:
        """
        Load status data from file.

        Returns:
            True if file exists and was loaded successfully, False otherwise
        """
        if not self.status_file.exists():
            return False

        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.statuses = data.get('threads', {})
                return True
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to load status file: {e}")
            return False

    def save(self) -> bool:
        """
        Save status data to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            data = {
                'pr_number': self.pr_number,
                'last_updated': datetime.now().isoformat(),
                'threads': self.statuses
            }

            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except OSError as e:
            print(f"Warning: Failed to save status file: {e}")
            return False

    def get_status(self, thread_id: int) -> Optional[Dict]:
        """
        Get status for a specific thread.

        Args:
            thread_id: The thread ID

        Returns:
            Status dict with 'status', 'updated_at', and optional 'note', or None
        """
        return self.statuses.get(str(thread_id))

    def set_status(self, thread_id: int, status: str, note: Optional[str] = None) -> None:
        """
        Set status for a specific thread.

        Args:
            thread_id: The thread ID
            status: One of CommentStatus values (ACTIVE, COMPLETED, IN_PROGRESS, SKIPPED, BLOCKED)
            note: Optional note/reason for the status
        """
        if status not in CommentStatus.all_statuses():
            raise ValueError(f"Invalid status: {status}. Must be one of {CommentStatus.all_statuses()}")

        self.statuses[str(thread_id)] = {
            'status': status,
            'updated_at': datetime.now().isoformat(),
            'note': note
        }

    def remove_status(self, thread_id: int) -> bool:
        """
        Remove status for a specific thread.

        Args:
            thread_id: The thread ID

        Returns:
            True if status was removed, False if it didn't exist
        """
        thread_key = str(thread_id)
        if thread_key in self.statuses:
            del self.statuses[thread_key]
            return True
        return False

    def merge_with_threads(self, threads: List[Dict]) -> List[Dict]:
        """
        Merge tracked statuses with fresh thread data from Azure DevOps API.

        This enriches threads with custom status information while preserving
        Azure DevOps status information.

        Args:
            threads: List of thread dicts from Azure DevOps API

        Returns:
            Enriched thread list with custom_status field added where applicable
        """
        enriched_threads = []

        for thread in threads:
            thread_id = thread.get('id')
            if not thread_id:
                enriched_threads.append(thread)
                continue

            # Get custom status if it exists
            custom_status = self.get_status(thread_id)

            if custom_status:
                # Add custom status info to thread
                thread_copy = thread.copy()
                thread_copy['custom_status'] = custom_status
                enriched_threads.append(thread_copy)
            else:
                enriched_threads.append(thread)

        return enriched_threads

    def get_all_statuses(self) -> Dict[str, Dict]:
        """
        Get all tracked statuses.

        Returns:
            Dict mapping thread IDs to status information
        """
        return self.statuses.copy()

    def clear_all(self) -> None:
        """Clear all tracked statuses."""
        self.statuses = {}

    def delete_file(self) -> bool:
        """
        Delete the status file from disk.

        Returns:
            True if file was deleted, False if it didn't exist
        """
        if self.status_file.exists():
            try:
                self.status_file.unlink()
                return True
            except OSError:
                return False
        return False


def create_status_tracker(pr_number: int, working_dir: Optional[Path] = None,
                          org: Optional[str] = None, project: Optional[str] = None,
                          repo: Optional[str] = None) -> StatusTracker:
    """
    Factory function to create and initialize a status tracker.

    Args:
        pr_number: The pull request number
        working_dir: Directory where status file should be stored (legacy fallback)
        org: Azure DevOps organization (for centralized storage)
        project: Project name (for centralized storage)
        repo: Repository name (for centralized storage)

    Returns:
        Initialized StatusTracker instance with data loaded if available

    Example:
        # Centralized storage (recommended)
        tracker = create_status_tracker(123, org='myorg', project='myproject', repo='myrepo')

        # Legacy storage (backwards compatible)
        tracker = create_status_tracker(123, working_dir=Path('/some/dir'))
    """
    tracker = StatusTracker(pr_number, working_dir, org=org, project=project, repo=repo)
    tracker.load()  # Load existing data if available
    return tracker


def get_status_file_info(pr_number: int, org: Optional[str] = None,
                         project: Optional[str] = None, repo: Optional[str] = None,
                         working_dir: Optional[Path] = None) -> Dict[str, any]:
    """
    Get information about status file location.

    Args:
        pr_number: Pull request number
        org: Azure DevOps organization
        project: Project name
        repo: Repository name
        working_dir: Legacy working directory

    Returns:
        Dict with 'path', 'exists', 'is_centralized' keys
    """
    if org and project and repo:
        status_dir = get_centralized_status_dir(org, project, repo)
        is_centralized = True
    else:
        status_dir = (working_dir or Path.cwd()) / ".pr-status"
        is_centralized = False

    status_file = status_dir / f"pr-{pr_number}-status.json"

    return {
        'path': status_file,
        'exists': status_file.exists(),
        'is_centralized': is_centralized,
        'directory': status_dir
    }
