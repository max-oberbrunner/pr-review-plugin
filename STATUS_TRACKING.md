# PR Comment Status Tracking

This feature allows you to track your progress on PR review comments across multiple fetches. When you re-run the PR review workflow, your progress is preserved.

## How It Works

### Status File
When you mark a comment with a custom status, it's saved to `pr-{NUMBER}-status.json` in your working directory. This file persists across PR comment fetches.

### Available Statuses

- **COMPLETED** - You've fully addressed this comment
- **IN_PROGRESS** - Currently working on this comment
- **SKIPPED** - Intentionally skipping (e.g., "Will address in separate PR")
- **BLOCKED** - Cannot address due to blocker (e.g., "Waiting for backend changes")

### Status Display Format

Comments in `pr-{NUMBER}-comments.md` will show combined status:

```markdown
**Thread #782180** [COMPLETED - Implemented lenderIdentityDataService] (Azure: [ACTIVE])
```

This means:
- You marked it as COMPLETED with a note
- Azure DevOps still shows it as ACTIVE (waiting for reviewer approval)

When reviewer marks it as fixed:
```markdown
**Thread #782180** [COMPLETED→FIXED] *verified by reviewer*
```

## Usage

### During PR Review Workflow

When using `/pr-review`, the workflow will automatically:

1. **Filter comments** - Only show `[ACTIVE]` and `[IN_PROGRESS]` comments in todo list
2. **Skip completed work** - `[COMPLETED]`, `[FIXED]`, `[SKIPPED]`, `[BLOCKED]` comments are excluded
3. **Update status** - After fixing each comment, status is saved automatically

### Manual Status Updates

Update status for a specific thread:

```bash
python "C:\Users\Max.Oberbrunner\pr-review-plugin\scripts\update_status.py" <PR_NUMBER> <THREAD_ID> <STATUS> [--note "reason"]
```

**Examples:**

```bash
# Mark as completed
python update_status.py 87663 782180 COMPLETED --note "Implemented lenderIdentityDataService"

# Mark as in progress
python update_status.py 87663 782177 IN_PROGRESS

# Mark as skipped with reason
python update_status.py 87663 782167 SKIPPED --note "Will address in separate CSS refactor PR"

# Mark as blocked
python update_status.py 87663 782191 BLOCKED --note "Waiting for backend validation changes"

# Remove custom status (revert to Azure status only)
python update_status.py 87663 782180 --clear
```

### View Current Status

Check the status file directly:

```bash
cat pr-87663-status.json
```

Example output:
```json
{
  "pr_number": 87663,
  "last_updated": "2025-10-27T13:00:02.349730",
  "threads": {
    "782180": {
      "status": "COMPLETED",
      "updated_at": "2025-10-27T12:59:49.840965",
      "note": "Implemented lenderIdentityDataService"
    },
    "782177": {
      "status": "IN_PROGRESS",
      "updated_at": "2025-10-27T13:00:02.349674",
      "note": null
    }
  }
}
```

## Workflow Example

### Initial Fetch
```bash
/pr-review 87663
```

Result: 5 active comments to address

### Work on Comments
1. Address comment in thread 782180
2. Run: `python update_status.py 87663 782180 COMPLETED`
3. Continue with other comments...

### Re-fetch After Lunch
```bash
/pr-review 87663
```

Result: Only 4 active comments (782180 is now `[COMPLETED]` and excluded from todo list)

### After Reviewer Marks as Fixed
Re-fetch again:
```bash
/pr-review 87663
```

Thread 782180 now shows: `[COMPLETED→FIXED] *verified by reviewer*`

## Benefits

✅ **Resume work** - Pick up where you left off across sessions
✅ **Track blockers** - Document why you can't address certain comments
✅ **Skip strategically** - Defer comments to future PRs with clear notes
✅ **Verify completion** - See when reviewers confirm your fixes
✅ **Stay organized** - Focus only on actionable comments

## File Locations

- **Status file**: `pr-{NUMBER}-status.json` (in working directory)
- **Comments file**: `pr-{NUMBER}-comments.md` (in working directory)
- **Scripts**: `C:\Users\Max.Oberbrunner\pr-review-plugin\scripts\`
  - `status_tracker.py` - Core status tracking module
  - `update_status.py` - CLI tool for manual updates
  - `fetch_pr_comments.py` - Fetches comments with status merging

## Cleanup

To start fresh and clear all tracked statuses for a PR:

```bash
rm pr-87663-status.json
```

Next fetch will show all comments as their original Azure DevOps status.
