# Quick Start Guide

Get up and running with Azure DevOps PR Review Plugin in 5 minutes!

## ⚡ 5-Minute Setup

```powershell
# Clone and install (Windows PowerShell)
git clone <YOUR_REPO_URL>
cd pr-review-plugin
.\scripts\install.ps1
```

The installer will prompt you for:
- Azure DevOps Organization (e.g., "cudirect")
- Project name (e.g., "Origence")
- Repository name (e.g., "arcOS.Web")
- Your Personal Access Token (PAT)

That's it! 🎉

## 📋 Prerequisites Checklist

Before installing, make sure you have:

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] Azure DevOps account with access to your repos
- [ ] Personal Access Token with Code (Read) scope

**Don't have a PAT?** See section below on creating one.

## 🔑 Creating Your Azure DevOps PAT

1. Go to: https://dev.azure.com/YOUR-ORG/_usersSettings/tokens
2. Click "New Token"
3. Name: "Claude Code PR Review"
4. Expiration: 90 days (or custom)
5. Scope: Select "Code" → "Read"
6. Click "Create" and **copy the token immediately**

## 🎯 First Review

In Claude Code, run:
```
/pr-review 87663
```

Replace `87663` with your PR number from Azure DevOps.

Claude will:
1. Fetch all review comments
2. Create a task list of active comments
3. Guide you through fixing each one
4. Show code context and explain why changes are needed
5. Offer to commit the fixes

## 🚀 Example Session

```
You: /pr-review 87663

Claude: PR #87663: CUNA Protection Advisor Settings

Found 5 active comments from Jason Wismer:

cuna-protection-advisor-data.service.ts:23 - Use lenderIdentityDataService
cuna-protection-advisor-settings.component.ts:130 - Avoid effects pattern
GetCunaProtectionAdvisorSettingsRequest.cs:7 - Check Required message
...

Which should we tackle first?
  A) Go in order (recommended)
  B) Let me choose

You: A

Claude: [Shows code, explains the issue, makes the fix or asks you to]
```

## 💡 Pro Tips

### Keep Your Token Updated
PAT tokens expire! When yours expires, just edit `~/.claude/ado-config.json` and update the `token` field.

### Multiple Repos
Working on multiple repos? You can manually edit the config to switch between them, or keep multiple config files and swap them.

### Share With Your Team
Your teammates can use the same org/project/repo settings, but everyone needs their own PAT token.

## 🆘 Troubleshooting

**"Error: Config file not found"**
- Run `.\scripts\install.ps1` again

**"Authentication failed"**
- Check your PAT in `~/.claude/ado-config.json`
- Verify it has Code (Read) scope
- Check if it's expired

**"Python not found"**
- Install Python 3.8+ from python.org
- Update `pythonPath` in the config

**"No active comments"**
- Great! Your PR has been fully reviewed
- Or the reviewer hasn't left comments yet

## 📁 Files Created

- `~/.claude/ado-config.json` - Configuration (includes PAT)
- `~/.claude/commands/pr-review.md` - The slash command

## 🤝 Sharing With Teammates

1. Push this plugin repo to a shared location
2. Have teammates run:
   ```powershell
   git clone <YOUR_REPO_URL>
   cd pr-review-plugin
   .\scripts\install.ps1
   ```
3. They'll be prompted for the same info
4. Each person needs their own PAT token

## 🎉 You're Ready!

You're now ready to address PR comments efficiently with Claude!

---

**Need more help?** Check the full [README.md](README.md)
