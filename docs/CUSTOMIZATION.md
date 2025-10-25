# Customization Guide

This guide will help you fork and customize the PR Review plugin to match your team's specific needs.

## 🍴 Fork-First Philosophy

The PR Review plugin is designed to be forked and customized. We encourage teams to:

1. **Fork** the repository to your organization or personal account
2. **Customize** the review criteria to match your standards
3. **Share** your fork with your team
4. **Contribute back** improvements to the main project (optional)

## Quick Start: Forking

### 1. Fork the Repository

```bash
# On GitHub, click "Fork" button or use CLI
gh repo fork YOUR-USERNAME/pr-review-plugin --clone

cd pr-review-plugin
```

### 2. Make Your Customizations

Edit `commands/pr-review.md` to customize the command behavior.

### 3. Share With Your Team

```bash
# Push your changes
git add .
git commit -m "Customize for [TEAM_NAME]"
git push origin main

# Team members can then install your fork
git clone https://github.com/YOUR-ORG/pr-review-plugin.git
cd pr-review-plugin
./scripts/install.sh
```

## 🎨 Common Customizations

### 1. Review Focus Areas

**Location**: `commands/pr-review.md` - Review Criteria section

**Default focuses**:
- Code Quality
- Security
- Performance
- Testing
- Documentation

**Example Customization**:
```markdown
## Review Focus Areas

### Your Team's Priorities
1. **Type Safety** - Ensure proper TypeScript usage
2. **Accessibility** - WCAG 2.1 AA compliance
3. **API Design** - RESTful standards adherence
4. **Error Handling** - Comprehensive error cases
5. **Performance** - Sub-200ms response times
```

### 2. Coding Standards

**Location**: `commands/pr-review.md` - Style Guide section

**Example Customization**:
```markdown
## Team Coding Standards

- **Language**: TypeScript strict mode required
- **Framework**: React 18+ with hooks only (no class components)
- **State Management**: Zustand preferred over Redux
- **Styling**: Tailwind CSS with custom design system
- **Testing**: Vitest with 80%+ coverage requirement
- **Documentation**: JSDoc for all public APIs
```

### 3. Severity Levels

**Location**: `commands/pr-review.md` - Issue Classification

**Example Customization**:
```markdown
## Issue Classification

### 🔴 Blocking (Must Fix)
- Security vulnerabilities (any CVSS score)
- Data loss risks
- Breaking API changes without migration
- Failed CI/CD checks

### 🟡 Warning (Should Fix)
- Performance degradation >10%
- Missing tests for new features
- Accessibility issues
- Inconsistent code style

### 🔵 Suggestion (Nice to Have)
- Optimization opportunities
- Refactoring suggestions
- Documentation improvements
```

### 4. Language-Specific Rules

**Location**: `commands/pr-review.md` - Language Rules section

**Example Customization**:
```markdown
## Python-Specific Review Checklist

- [ ] Type hints on all function signatures
- [ ] Docstrings follow Google style guide
- [ ] Black formatting applied
- [ ] Pylint score above 9.0
- [ ] No `type: ignore` comments without justification
- [ ] Async/await used for I/O operations
- [ ] Pydantic models for data validation
```

### 5. Team-Specific Checks

Add checks unique to your codebase:

```markdown
## Custom Checks for [YOUR_TEAM]

### Database Changes
- [ ] Migration files included
- [ ] Rollback strategy documented
- [ ] Index performance analyzed

### Feature Flags
- [ ] New features behind feature flags
- [ ] Flag cleanup ticket created
- [ ] A/B test metrics defined

### Monitoring
- [ ] Error tracking added
- [ ] Performance metrics instrumented
- [ ] Alert thresholds configured
```

## 🔧 Advanced Customizations

### 1. Multi-Repository Support

Create specialized versions for different repositories:

```bash
# Fork structure
pr-review-plugin/
├── commands/
│   ├── pr-review.md           # Base command
│   ├── pr-review-backend.md   # Backend-specific
│   ├── pr-review-frontend.md  # Frontend-specific
│   └── pr-review-mobile.md    # Mobile-specific
```

### 2. Integration with Custom Tools

Add team-specific tool checks:

```markdown
## Pre-Review Automation

Before manual review, ensure:

```bash
# Run your custom checks
npm run lint:custom
npm run security:scan
npm run bundle:analyze

# Run team-specific validators
./scripts/validate-api-contracts.sh
./scripts/check-feature-flags.sh
```
```

### 3. PR Template Integration

Align review criteria with your PR template:

```markdown
## Review Checklist (Match PR Template)

From your `.github/pull_request_template.md`:

- [ ] **Type of Change**: Correctly labeled
- [ ] **Breaking Changes**: Migration guide included
- [ ] **Screenshots**: Provided for UI changes
- [ ] **Dependencies**: Lock file updated
- [ ] **Rollback Plan**: Documented in PR description
```

### 4. Custom Output Format

Modify the review output format:

```markdown
## Output Format

Provide review in this structure:

### Executive Summary
[2-3 sentence overview]

### Metrics
- Files Changed: X
- Lines Added/Removed: +X/-Y
- Complexity Score: Z
- Test Coverage Delta: ±X%

### Critical Issues (🔴)
[List with file:line references]

### Recommendations (🟡)
[Prioritized list]

### Praise (✅)
[Highlight good practices]

### Automated Checks
[Link to CI/CD results]
```

## 📋 Configuration Variables

For easier customization, use variables at the top of your command:

```markdown
# PR Review Configuration

<!-- TEAM CONFIGURATION -->
TEAM_NAME="Platform Engineering"
REPO_TYPE="backend" # backend | frontend | mobile | fullstack
LANGUAGE="python" # python | typescript | go | java
COVERAGE_THRESHOLD=80
PERFORMANCE_BUDGET="500ms"
SECURITY_LEVEL="strict" # strict | moderate | basic
<!-- END CONFIGURATION -->
```

## 🌳 Maintaining Your Fork

### Keeping Up with Upstream Changes

```bash
# Add upstream remote
git remote add upstream https://github.com/ORIGINAL-OWNER/pr-review-plugin.git

# Fetch upstream changes
git fetch upstream

# Merge upstream changes
git merge upstream/main

# Resolve conflicts, then push
git push origin main
```

### Versioning Your Fork

Tag your customizations for team consistency:

```bash
# Create a release for your team
git tag -a v1.0.0-yourteam -m "Team-specific PR review v1.0.0"
git push origin v1.0.0-yourteam

# Team members install specific version
git clone --branch v1.0.0-yourteam https://github.com/YOUR-ORG/pr-review-plugin.git
```

### Documentation for Your Fork

Update the README with team-specific information:

```markdown
# PR Review Plugin - [YOUR TEAM] Fork

This is [YOUR TEAM]'s customized version of the PR Review plugin.

## Team-Specific Features
- Python-focused reviews with type checking
- Integration with internal security scanner
- Automated performance regression detection

## Installation for [YOUR TEAM]
```bash
git clone https://github.com/YOUR-ORG/pr-review-plugin.git
./scripts/install.sh
```

## Team Contacts
- Maintainer: @your-username
- Questions: #team-channel on Slack
```

## 💡 Customization Ideas

### For Startups
- Focus on shipping speed and technical debt awareness
- Relaxed rules with clear "fix later" categorization
- Emphasis on documentation for knowledge sharing

### For Enterprise Teams
- Strict security and compliance checks
- Detailed audit trail requirements
- Integration with corporate governance tools

### For Open Source Projects
- Community guidelines and code of conduct checks
- Contribution recognition
- Backward compatibility validation
- Documentation for first-time contributors

### For Security-Critical Applications
- Mandatory security review checklist
- Threat modeling validation
- Dependency vulnerability scanning
- Security testing requirements

## 🤝 Contributing Back

If you create useful customizations, consider contributing them back:

1. Create a feature branch in your fork
2. Implement the customization as an optional feature
3. Submit a PR to the upstream repository
4. Share how your team uses it

## 📚 Examples of Team Forks

### Example 1: Django Backend Team

```markdown
## Django-Specific Checks

- [ ] Model changes include migrations
- [ ] Views use proper permissions (LoginRequired, etc.)
- [ ] ORM queries optimized (select_related, prefetch_related)
- [ ] Admin interface updated for new models
- [ ] Django REST Framework serializers follow conventions
- [ ] Settings changes documented in deployment guide
```

### Example 2: React Frontend Team

```markdown
## React Best Practices

- [ ] Components follow single responsibility principle
- [ ] Hooks follow rules of hooks
- [ ] No prop drilling (use Context or state management)
- [ ] Memoization used appropriately (useMemo, useCallback)
- [ ] Error boundaries wrap risky components
- [ ] Accessibility: ARIA labels, keyboard navigation
- [ ] Storybook stories created for UI components
```

### Example 3: Microservices Team

```markdown
## Microservices Standards

- [ ] API contract matches OpenAPI spec
- [ ] Circuit breakers configured
- [ ] Distributed tracing instrumented
- [ ] Service mesh configuration updated
- [ ] Load testing results included
- [ ] Rollout strategy defined (canary/blue-green)
```

## 🚀 Next Steps

1. **Fork** the repository
2. **Customize** one section at a time
3. **Test** with a small PR
4. **Iterate** based on team feedback
5. **Share** your fork with the team
6. **Document** team-specific usage

Need inspiration? Check out [EXAMPLES.md](EXAMPLES.md) for usage scenarios!

---

**Questions?** Open an issue or reach out to the community!
