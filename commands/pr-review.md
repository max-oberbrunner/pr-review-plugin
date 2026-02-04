---
name: pr-review
description: Interactive PR review workflow for Azure DevOps and GitHub - fetches comments and guides through fixes
---

# PR Review Skill

Interactive workflow for addressing pull request comments from Azure DevOps or GitHub.

## Usage

```
/pr-review <PR-NUMBER>
```

Example: `/pr-review 87663`

## Configuration

Reads from `.claude/pr-review.json` in the project root (auto-detected via .git folder).

### GitHub Configuration
```json
{
  "platform": "github",
  "owner": "your-username-or-org",
  "repository": "your-repo"
}
```

### Azure DevOps Configuration
```json
{
  "platform": "azure-devops",
  "organization": "your-org",
  "project": "your-project",
  "repository": "your-repo"
}
```

Paths (scriptPath, pythonPath) are auto-detected.

### Token Resolution

The script resolves tokens automatically based on platform:

**Azure DevOps:**
1. Environment variable (`AZURE_DEVOPS_PAT`)
2. System keychain (macOS Keychain / Windows Credential Manager)
3. Config file (deprecated, shows warning)
4. Interactive prompt

**GitHub:**
1. Environment variable (`GITHUB_PAT`)
2. System keychain
3. Interactive prompt

If the user is prompted for a token, they enter it directly in the terminal. This is handled by the Python script, not by Claude.

> **Note:** GitHub comment fetching is not yet implemented. PR information will be displayed, but comments are coming soon.

## Workflow

### Step 0: Fetch PR Data (Single Command)

Run the orchestrator script to get everything in one call:

```bash
python {plugin_path}/scripts/run_pr_review.py {PR_NUMBER} --json
```

This returns a JSON object with:
- `success`: boolean
- `pr`: PR number
- `platform`: "azure-devops" or "github"
- `projectRoot`: absolute path
- `changedFiles`: list of changed files with paths and change types
- `commands`: execution plan with **command content included**
- `summary`: file counts (added, modified, deleted)
- `commandsSummary`: command names and file counts

**If `success` is false**, check the `error` field:
- `[CONFIG_MISSING]`: Project not configured - guide user to run setup wizard
- `[AUTH_MISSING]`: No token - guide user to save PAT to keychain
- `[PR_NOT_FOUND]`: Invalid PR number or wrong repository config

### Step 1: Run Code Analysis Commands (if enabled)

Check if `commands.enabled` is `true` in the JSON response. If so:

**1.1 Launch Analysis Subagents in Parallel**

For each command in `commands.commands[]`, launch a **Task** subagent:

```
Task: Run {command.name} analysis
Subagent type: general-purpose
Prompt: |
  You are analyzing code for PR #{PR_NUMBER} review.

  **Project root:** {projectRoot}

  **Command instructions:**
  {command.content}

  **Files to analyze ({command.fileCount} files):**
  {command.files joined by newlines}

  Read each file and check for violations. Return findings as structured markdown:
  - File path and line number for each issue
  - Brief description of the issue
  - Severity (critical/important/style)
```

Launch up to `commands.maxConcurrent` (default: 3) in parallel.

**1.2 Aggregate and Present Results**

After subagents complete, show summary:

```
## Code Analysis Results

**Commands Run:** {count}
**Files Analyzed:** {total}
**Issues Found:** {total_issues}

### {command_name} ({issue_count} issues)
| Severity | File | Issue |
|----------|------|-------|
| Important | path/file.ts:42 | Description |
...
```

**1.3 Ask User How to Proceed**

```
Found {X} code analysis issues across {Y} files.

Would you like to:
  A) Address these issues first, then PR comments
  B) Skip to PR comments
  C) See detailed breakdown
```

### Step 2: Fetch PR Comments

Run the comment fetcher:
```bash
python {plugin_path}/scripts/fetch_pr_comments.py \
  --org {organization} --project {project} --repo {repository} --pr {PR_NUMBER}
```

The script outputs comments in markdown format with:
- File comments grouped by location
- Thread status (active/fixed/closed)
- Reviewer names and comment content

### Step 3: Create Task List

Use **TaskCreate** to create a checklist of all active comments:

```
1. Fix [issue] in [file:line]
2. Fix [issue] in [file:line]
...
```

### Step 4: Interactive Review

Present the categorized comments to the user:

```
📋 PR #{PR_NUMBER}: {PR_TITLE}

Found {X} active comments:

🔴 Critical Issues:
  • {file}:{line} - {brief description}

🟡 Important Issues:
  • {file}:{line} - {brief description}

🟢 Style & Best Practices:
  • {file}:{line} - {brief description}

Which should we tackle first?
  A) Start with critical issues (recommended)
  B) Go in order
  C) Let me choose
```

### Step 5: Address Each Comment

For each issue:

**5.1 Show Context**
- Use **Read** tool to show current code at file:line
- Display the reviewer's comment
- Explain what needs to change and why

**5.2 Provide Insight**
```
★ Insight ─────────────────────────────────────
{Educational context about the issue}
{Why this pattern/approach is better}
{How it fits into the larger architecture}
─────────────────────────────────────────────────
```

**5.3 Implement Fix**

**If straightforward (<5 lines, clear pattern):**
- Implement using **Edit** tool
- Explain changes
- Mark todo as completed

**If complex (design decision, >5 lines, key logic):**
```
● **Learn by Doing**

**Context:** {What we're building and why this matters}

**Your Task:** In {file}, implement {specific task}. Look for TODO(human).

**Guidance:** {Trade-offs, constraints, approach suggestions}
```
- Use **Edit** tool to add TODO(human) marker
- Wait for user implementation
- Mark todo as completed after user finishes

**5.4 Update Progress**
- Mark current todo as completed
- Move to next in_progress item
- One todo in_progress at a time

### Step 6: Completion

After all issues addressed:

**6.1 Summary**
```
✅ All {X} comments addressed!

Changes made:
  • {file}: {what was fixed}
  • {file}: {what was fixed}
  ...
```

**6.2 Next Steps**
```
Would you like me to:
  A) Create a commit with these changes
  B) Show summary of all edits
  C) Nothing, I'll handle it
```

If user chooses A, create commit:
```
fix: address PR review comments

- {change 1}
- {change 2}
- {change 3}

Addresses comments from: {REVIEWER_NAME}
PR: #{PR_NUMBER}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Error Handling

When the script fails, parse the error output and respond appropriately:

### `[CONFIG_MISSING]` or `[PLATFORM_MISSING]`
Project not configured. Guide user to run the appropriate setup wizard:
```bash
# For GitHub:
python /path/to/pr-review-plugin/scripts/setup_github.py

# For Azure DevOps:
python /path/to/pr-review-plugin/scripts/setup_ado.py
```

### `[AUTH_FAILED]` or HTTP 401
Token invalid or expired. Tell user:
- Create new PAT at: `https://dev.azure.com/{org}/_usersSettings/tokens`
- Required scope: **Code (Read)**
- Save with: `python scripts/token_manager.py --save`

### `[PR_NOT_FOUND]` or HTTP 404
PR doesn't exist or config is wrong. Ask user to verify:
- PR number is correct
- Organization/project/repository in `.claude/pr-review.json` match the PR's location

### `[FORBIDDEN]` or HTTP 403
Token lacks permissions. User needs to create a new token with **Code (Read)** scope.

### `[TIMEOUT]` or `[CONNECTION_ERROR]`
Network issue. Ask user if they want to:
- Retry the request
- Check Azure DevOps status: https://status.dev.azure.com/

### General Troubleshooting

If the error is unclear, suggest these diagnostic commands:
```bash
# Check config
cat .claude/pr-review.json

# Check token status
python scripts/token_manager.py --status

# Test script directly
python scripts/fetch_pr_comments.py \
  --org your-org --project your-project --repo your-repo --pr 12345
```

## Key Principles

- **Interactive**: Pause for user input, don't batch fixes
- **Educational**: Explain WHY, not just WHAT
- **Learning Mode**: Request user input for design decisions
- **Track Progress**: Use TodoWrite throughout
- **One at a time**: Only one in_progress todo
- **File references**: Always use `file:line` format

## Example Session

```
User: /pr-review 87663

Claude: Fetching comments for PR #87663...

[Executes script, parses output]

Claude:
📋 PR #87663: CUNA Protection Advisor Settings

Found 5 active comments from Jason Wismer:

🔴 Critical Issues:
  • cuna-protection-advisor-data.service.ts:23 - Use lenderIdentityDataService
  • cuna-protection-advisor-settings.component.ts:130 - Avoid effects pattern

🟡 Important Issues:
  • GetCunaProtectionAdvisorSettingsRequest.cs:7 - Check Required message
  • SetCunaProtectionAdvisorSettingsRequest.cs:11 - Verify Required defaults

🟢 Style & Best Practices:
  • cuna-protection-advisor-settings.component.scss:3 - Use CSS variables

[Creates TodoWrite checklist]

Which should we tackle first?
  A) Start with critical issues ← Recommended
  B) Go in order
  C) Let me choose

User: A

Claude: Great! Let's start with the critical issue in
cuna-protection-advisor-data.service.ts:23

**Jason's Comment:**
> Please use the lenderIdentityDataService

Let me show you the current code...

[Continues interactively through each issue]
```
