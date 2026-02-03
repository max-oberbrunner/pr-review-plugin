#!/usr/bin/env python3
"""
PR Comment Status Tracker

Tracks the status of PR review comments across multiple fetches,
preserving user progress (COMPLETED, IN_PROGRESS, SKIPPED, BLOCKED).
"""

import json
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


def get_status_dir(project_root: Optional[Path] = None) -> Path:
    """
    Get status directory path in the project's .claude folder.

    Args:
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Path to status directory
    """
    if not project_root:
        project_root = find_project_root()

    if not project_root:
        # Fallback to current directory if not in a git repo
        project_root = Path.cwd()

    return project_root / ".claude" / "pr-status"


class StatusTracker:
    """Manages persistent status tracking for PR comments."""

    def __init__(self, pr_number: int, project_root: Optional[Path] = None):
        """
        Initialize status tracker.

        Args:
            pr_number: The pull request number
            project_root: Project root path (auto-detected if not provided)
        """
        self.pr_number = pr_number
        self.project_root = project_root or find_project_root() or Path.cwd()
        self.statuses = {}

        # Status files stored in project's .claude/pr-status/ folder
        self.status_dir = get_status_dir(self.project_root)

        # Ensure directory exists
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.status_dir / f"pr-{pr_number}-status.json"

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


def create_status_tracker(pr_number: int, project_root: Optional[Path] = None) -> StatusTracker:
    """
    Factory function to create and initialize a status tracker.

    Args:
        pr_number: The pull request number
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Initialized StatusTracker instance with data loaded if available

    Example:
        tracker = create_status_tracker(123)
        tracker = create_status_tracker(123, project_root=Path('/path/to/project'))
    """
    tracker = StatusTracker(pr_number, project_root)
    tracker.load()  # Load existing data if available
    return tracker


def get_status_file_info(pr_number: int, project_root: Optional[Path] = None) -> Dict[str, Path | bool]:
    """
    Get information about status file location.

    Args:
        pr_number: Pull request number
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Dict with 'path', 'exists', 'directory' keys
    """
    status_dir = get_status_dir(project_root)
    status_file = status_dir / f"pr-{pr_number}-status.json"

    return {
        'path': status_file,
        'exists': status_file.exists(),
        'directory': status_dir
    }
