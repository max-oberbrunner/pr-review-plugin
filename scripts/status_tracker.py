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
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

    @classmethod
    def all_statuses(cls):
        return [cls.COMPLETED, cls.IN_PROGRESS, cls.SKIPPED, cls.BLOCKED]


class StatusTracker:
    """Manages persistent status tracking for PR comments."""

    def __init__(self, pr_number: int, working_dir: Optional[Path] = None):
        """
        Initialize status tracker.

        Args:
            pr_number: The pull request number
            working_dir: Directory where status file should be stored (default: current directory)
        """
        self.pr_number = pr_number
        self.working_dir = working_dir or Path.cwd()
        self.status_file = self.working_dir / f"pr-{pr_number}-status.json"
        self.statuses = {}

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
            status: One of CommentStatus values (COMPLETED, IN_PROGRESS, SKIPPED, BLOCKED)
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


def create_status_tracker(pr_number: int, working_dir: Optional[Path] = None) -> StatusTracker:
    """
    Factory function to create and initialize a status tracker.

    Args:
        pr_number: The pull request number
        working_dir: Directory where status file should be stored

    Returns:
        Initialized StatusTracker instance with data loaded if available
    """
    tracker = StatusTracker(pr_number, working_dir)
    tracker.load()  # Load existing data if available
    return tracker
