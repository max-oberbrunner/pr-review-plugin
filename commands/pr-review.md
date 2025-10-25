---
name: pr-review
description: Interactive Azure DevOps PR review workflow - fetches comments and guides through fixes
---

# PR Review Skill

Interactive workflow for addressing Azure DevOps pull request comments.

## Usage

```
/pr-review <PR-NUMBER>
```

Example: `/pr-review 87663`

## Configuration

Reads from `~/.claude/ado-config.json`:
```json
{
  "organization": "cudirect",
  "project": "Origence",
  "repository": "arcOS.Web",
  "scriptPath": "/Users/maxoberbrunner/ado-pr/pr-comments-fetch.py",
  "pythonPath": "/Users/maxoberbrunner/ado-pr/venv/bin/python"
}
```

## Workflow

### Step 1: Fetch Comments

Read config and execute:
```bash
{pythonPath} {scriptPath} \
  --org {organization} \
  --project {project} \
  --repo {repository} \
  --pr {PR_NUMBER} \
  --format claude
```

The script outputs comments categorized by priority:
- 🔴 Critical (architecture, patterns, dependencies)
- 🟡 Important (validation, error handling, code quality)
- 🟢 Style (formatting, naming, best practices)

### Step 2: Create Task List

Use **TodoWrite** to create a checklist of all active comments:

```
1. Fix [issue] in [file:line]
2. Fix [issue] in [file:line]
...
```

### Step 3: Interactive Review

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

### Step 4: Address Each Comment

For each issue:

**4.1 Show Context**
- Use **Read** tool to show current code at file:line
- Display the reviewer's comment
- Explain what needs to change and why

**4.2 Provide Insight**
```
★ Insight ─────────────────────────────────────
{Educational context about the issue}
{Why this pattern/approach is better}
{How it fits into the larger architecture}
─────────────────────────────────────────────────
```

**4.3 Implement Fix**

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

**4.4 Update Progress**
- Mark current todo as completed
- Move to next in_progress item
- One todo in_progress at a time

### Step 5: Completion

After all issues addressed:

**5.1 Summary**
```
✅ All {X} comments addressed!

Changes made:
  • {file}: {what was fixed}
  • {file}: {what was fixed}
  ...
```

**5.2 Next Steps**
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

If script fails, troubleshoot:

1. **Check config exists:**
   ```bash
   cat ~/.claude/ado-config.json
   ```

2. **Test script directly:**
   ```bash
   source /Users/maxoberbrunner/ado-pr/venv/bin/activate
   python /Users/maxoberbrunner/ado-pr/pr-comments-fetch.py \
     --org cudirect --project Origence --repo arcOS.Web --pr 87663
   ```

3. **Verify token:**
   ```bash
   python /Users/maxoberbrunner/ado-pr/test_connection.py
   ```

4. **Check venv:**
   ```bash
   ls /Users/maxoberbrunner/ado-pr/venv/bin/python
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
