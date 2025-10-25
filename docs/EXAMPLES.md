# Usage Examples

Real-world examples of using the PR Review plugin in different scenarios.

## Table of Contents

- [Basic Usage](#basic-usage)
- [GitHub PR Integration](#github-pr-integration)
- [Focused Reviews](#focused-reviews)
- [Team Workflows](#team-workflows)
- [CI/CD Integration](#cicd-integration)
- [Advanced Scenarios](#advanced-scenarios)

---

## Basic Usage

### Example 1: Review Current Branch

Review all changes in your current working branch compared to the base branch:

```bash
# Make sure you're on your feature branch
git checkout feature/user-authentication

# Start Claude Code
claude

# Run the review
/pr-review
```

**Output**:
```
🔍 Reviewing changes in feature/user-authentication...

📊 Review Summary:
- Files changed: 8
- Lines added: 342
- Lines removed: 56

🔴 Critical Issues (2):
1. auth.js:45 - Password stored in plain text (Security)
2. login.js:89 - SQL injection vulnerability in query

🟡 Warnings (5):
1. user-model.js:23 - Missing input validation
2. auth.js:67 - Error handling could be improved
...

✅ Good Practices Found:
- Comprehensive test coverage (87%)
- Well-documented functions
- Clear commit messages
```

### Example 2: Quick Surface-Level Review

When you want a fast review without deep analysis:

```bash
/pr-review --quick
```

**Use Case**: Quick sanity check before requesting formal team review.

---

## GitHub PR Integration

### Example 3: Review Open Pull Request

Review a specific PR by number:

```bash
# Review PR #123 in current repository
/pr-review #123
```

**What it does**:
- Fetches PR details from GitHub
- Reviews all changed files
- Considers PR description and comments
- Checks CI/CD status

### Example 4: Review PR from Different Repository

```bash
# Review PR from specific repository
/pr-review owner/repo#456
```

**Use Case**: Reviewing PRs in dependent repositories or across a monorepo.

### Example 5: Review PR with Context

```bash
# Review considering PR discussion
/pr-review #123 --include-comments
```

**What it does**:
- Incorporates existing review comments
- Considers discussion context
- Avoids duplicate feedback

---

## Focused Reviews

### Example 6: Security-Focused Review

Focus exclusively on security vulnerabilities:

```bash
/pr-review --focus=security
```

**Checks**:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication/authorization issues
- Sensitive data exposure
- Dependency vulnerabilities
- Cryptographic weaknesses

### Example 7: Performance Review

Focus on performance optimization:

```bash
/pr-review --focus=performance
```

**Checks**:
- Algorithmic complexity (O(n²) loops, etc.)
- Database query efficiency (N+1 queries)
- Memory usage patterns
- Resource leaks
- Caching opportunities
- Bundle size impact

### Example 8: Multi-Focus Review

Combine multiple focus areas:

```bash
/pr-review --focus=security,performance,testing
```

**Use Case**: Pre-production reviews where multiple aspects are critical.

---

## Team Workflows

### Example 9: Pre-Commit Review (Developer)

Developer self-reviews before pushing:

```bash
# Stage your changes
git add .

# Review before committing
/pr-review --quick

# If looks good, commit
git commit -m "Add user authentication"
```

**Benefit**: Catch issues before they reach code review.

### Example 10: Pre-Review Checklist (Developer)

Before requesting team review:

```bash
# Complete review with checklist
/pr-review --checklist

# Output includes actionable items:
# ✅ Tests added
# ✅ Documentation updated
# ❌ Performance benchmarks missing
# ❌ Security scan needed
```

### Example 11: Team Lead Review

Team lead reviewing multiple PRs:

```bash
# Review all open PRs in repository
/pr-review --all-prs --summary

# Or review PRs from specific author
/pr-review --author=junior-dev
```

### Example 12: Mentor Reviewing Junior Developer

Mentoring focus with educational feedback:

```bash
/pr-review #234 --educational --focus=best-practices
```

**Output includes**:
- Explanations of why issues matter
- Links to documentation
- Positive reinforcement of good patterns
- Learning resources

---

## CI/CD Integration

### Example 13: Automated PR Review in CI

Add to `.github/workflows/pr-review.yml`:

```yaml
name: AI PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Claude Code
        run: |
          npm install -g @anthropic/claude-code

      - name: Install PR Review Plugin
        run: |
          git clone https://github.com/YOUR-ORG/pr-review-plugin.git
          cd pr-review-plugin
          ./scripts/install.sh

      - name: Run Review
        run: |
          claude /pr-review ${{ github.event.pull_request.number }} --format=github-comment
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Example 14: Blocking CI on Critical Issues

Configure review to fail CI on critical issues:

```bash
/pr-review --fail-on=critical
```

**Exit codes**:
- `0`: No critical issues found
- `1`: Critical issues found (fails CI)
- `2`: Review could not complete

---

## Advanced Scenarios

### Example 15: Large PR Review

For PRs with many files:

```bash
# Review with diff chunks to manage context
/pr-review --chunked --chunk-size=500
```

**Benefit**: Better handling of large changesets.

### Example 16: Comparative Review

Compare two branches:

```bash
/pr-review --compare feature/new-api:main
```

**Use Case**: Understanding changes before merging feature branch.

### Example 17: Historical Review

Review a merged PR to learn from it:

```bash
/pr-review #789 --merged --retrospective
```

**Output focus**:
- What could have been caught earlier
- Patterns to watch for in future
- Impact assessment of changes

### Example 18: Language-Specific Review

Force specific language rules:

```bash
/pr-review --language=python --strict
```

**Applies**:
- Python-specific best practices
- PEP 8 style guide
- Type hinting requirements
- Python security patterns

### Example 19: Custom Review Criteria

Use a custom configuration:

```bash
/pr-review --config=.pr-review-config.json
```

**`.pr-review-config.json`**:
```json
{
  "severity_threshold": "warning",
  "focus_areas": ["security", "performance"],
  "exclude_files": ["*.test.js", "*.stories.js"],
  "custom_rules": [
    {
      "pattern": "TODO",
      "message": "Remove TODO comments before merging",
      "severity": "warning"
    }
  ]
}
```

### Example 20: Review with External Context

Include external documentation or specs:

```bash
/pr-review --context="See API spec: https://api.example.com/docs"
```

**Use Case**: Ensuring implementation matches specification.

---

## Real-World Workflow Examples

### Workflow A: Solo Developer Startup

```bash
# 1. Daily: Review yesterday's work
git checkout main
git pull
/pr-review --since="1 day ago"

# 2. Before lunch: Review morning's work
/pr-review --quick

# 3. Before pushing: Final check
/pr-review --focus=security,testing
```

### Workflow B: Mid-Size Team

```bash
# Developer workflow
git checkout -b feature/add-export
# ... make changes ...
/pr-review --quick
git commit -am "Add export functionality"
git push origin feature/add-export

# Create PR, then wait for automated review
gh pr create --fill

# After addressing feedback
/pr-review #PR_NUMBER --changes-only
```

### Workflow C: Enterprise with Compliance

```bash
# Required pre-merge review
/pr-review #PR_NUMBER \
  --focus=security,compliance,accessibility \
  --fail-on=critical \
  --generate-report=./review-report.pdf \
  --sign
```

---

## Tips & Tricks

### Tip 1: Create Aliases

Add to your shell config:

```bash
# Quick review
alias prq="/pr-review --quick"

# Security focus
alias prs="/pr-review --focus=security"

# Full pre-merge review
alias prm="/pr-review --focus=security,performance,testing --fail-on=critical"
```

### Tip 2: Combine with Git Hooks

In `.git/hooks/pre-push`:

```bash
#!/bin/bash
echo "Running PR review before push..."
claude /pr-review --quick --fail-on=critical

if [ $? -ne 0 ]; then
  echo "❌ Critical issues found. Fix before pushing."
  exit 1
fi
```

### Tip 3: Team Review Checklist

Create a team script `scripts/team-review.sh`:

```bash
#!/bin/bash
PR_NUMBER=$1

echo "📋 Running team review checklist..."

echo "1/4: Security scan..."
claude /pr-review $PR_NUMBER --focus=security

echo "2/4: Performance check..."
claude /pr-review $PR_NUMBER --focus=performance

echo "3/4: Test coverage..."
npm run test:coverage

echo "4/4: Build verification..."
npm run build

echo "✅ Team review checklist complete!"
```

---

## Scenario-Based Examples

### Scenario 1: Hotfix Review

```bash
# Quick security-focused review for production hotfix
git checkout hotfix/critical-security-patch
/pr-review --focus=security --fail-on=high --quick
```

### Scenario 2: Refactoring Review

```bash
# Ensure refactoring doesn't break functionality
/pr-review --focus=testing,compatibility --compare-behavior
```

### Scenario 3: Dependency Update Review

```bash
# Review impact of dependency updates
/pr-review --focus=security,breaking-changes --dependency-update
```

### Scenario 4: Documentation Review

```bash
# Focus on documentation quality
/pr-review --focus=documentation --check-examples
```

---

## Need More Examples?

- Check [CUSTOMIZATION.md](CUSTOMIZATION.md) for team-specific examples
- Visit [Issues](https://github.com/YOUR-USERNAME/pr-review-plugin/issues) to see community use cases
- Share your workflow! Submit a PR to add your example

---

**Pro Tip**: Start simple with basic reviews, then gradually incorporate more advanced features as your team gets comfortable with the tool!
