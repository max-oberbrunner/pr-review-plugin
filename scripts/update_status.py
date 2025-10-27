#!/usr/bin/env python3
"""
Update PR Comment Status

Helper script to update the status of a specific PR comment thread.
Used by Claude Code during PR review workflow.
"""

import argparse
import sys
from pathlib import Path

# Import status tracker
try:
    from status_tracker import create_status_tracker, CommentStatus
except ImportError:
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    from status_tracker import create_status_tracker, CommentStatus


def main():
    parser = argparse.ArgumentParser(
        description='Update status of a PR comment thread',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mark thread as completed
  python update_status.py 87663 782167 COMPLETED

  # Mark thread as blocked with reason
  python update_status.py 87663 782191 BLOCKED --note "Waiting for backend changes"

  # Mark thread as skipped
  python update_status.py 87663 782180 SKIPPED --note "Will address in separate PR"

  # Remove custom status (revert to Azure status only)
  python update_status.py 87663 782167 --clear
        """
    )

    parser.add_argument('pr_number', type=int, help='Pull request number')
    parser.add_argument('thread_id', type=int, help='Thread ID to update')
    parser.add_argument('status', nargs='?', help=f'Status to set: {", ".join(CommentStatus.all_statuses())}')
    parser.add_argument('--note', '-n', help='Optional note/reason for the status')
    parser.add_argument('--clear', action='store_true', help='Remove custom status for this thread')
    parser.add_argument('--working-dir', '-d', help='Working directory (default: current directory)')

    args = parser.parse_args()

    # Determine working directory
    working_dir = Path(args.working_dir) if args.working_dir else Path.cwd()

    # Load status tracker
    tracker = create_status_tracker(args.pr_number, working_dir)

    # Handle clear action
    if args.clear:
        if tracker.remove_status(args.thread_id):
            tracker.save()
            print(f"[SUCCESS] Cleared custom status for thread #{args.thread_id}")
            sys.exit(0)
        else:
            print(f"[INFO] Thread #{args.thread_id} had no custom status")
            sys.exit(0)

    # Validate status argument
    if not args.status:
        print("ERROR: Status is required (or use --clear to remove status)", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Validate status value
    if args.status not in CommentStatus.all_statuses():
        print(f"ERROR: Invalid status '{args.status}'", file=sys.stderr)
        print(f"Valid statuses: {', '.join(CommentStatus.all_statuses())}", file=sys.stderr)
        sys.exit(1)

    # Update status
    try:
        tracker.set_status(args.thread_id, args.status, args.note)
        tracker.save()

        status_msg = f"[{args.status}"
        if args.note:
            status_msg += f" - {args.note}"
        status_msg += "]"

        print(f"[SUCCESS] Updated thread #{args.thread_id} to {status_msg}")
        print(f"[INFO] Status file: {tracker.status_file}")

    except Exception as e:
        print(f"ERROR: Failed to update status: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
