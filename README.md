# Claude Code PR Review Plugin

An Azure DevOps pull request review plugin for Claude Code that fetches PR comments and guides you through addressing them interactively.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ installed
- Azure DevOps account with access to your organization
- Personal Access Token (PAT) with Code (Read) scope

### Installation

**Windows (PowerShell):**
```powershell
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin
.\scripts\install.ps1
```

The installer will:
1. Prompt you for your Azure DevOps configuration (organization, project, repository)
2. Auto-detect your Python installation
3. Ask for your Azure DevOps Personal Access Token
4. Create the configuration file at `~/.claude/ado-config.json`
5. Install the `/pr-review` command to Claude Code

### Creating Your Azure DevOps Personal Access Token

1. Go to https://dev.azure.com/{your-org}/_usersSettings/tokens
2. Click "New Token"
3. Give it a name (e.g., "Claude Code PR Review")
4. Set expiration (recommend 90 days or custom)
5. Under "Scopes", select "Code" → "Read"
6. Click "Create"
7. Copy the token immediately (you won't be able to see it again!)

### Usage

```bash
# In Claude Code, review a PR by number
/pr-review 87663
```

Claude will:
1. Fetch all comments from the PR
2. Create a task list of active comments
3. Guide you through addressing each one interactively
4. Offer to commit the changes when done

## 📖 What It Does

This plugin integrates with Azure DevOps to:

- **Fetch PR Comments**: Retrieves all review comments from your PR
- **Filter Active Comments**: Shows only comments that need to be addressed
- **Interactive Workflow**: Guides you through each comment one by one
- **Code Context**: Shows the relevant code and explains what needs to change
- **Educational**: Explains WHY changes are needed, not just WHAT
- **Track Progress**: Uses TodoWrite to track which comments you've addressed
- **Git Integration**: Offers to create a commit with all your fixes

## 🔧 Configuration

The plugin uses `~/.claude/ado-config.json`:

```json
{
  "organization": "cudirect",
  "project": "Origence",
  "repository": "arcOS.Web",
  "scriptPath": "C:\\path\\to\\pr-review-plugin\\scripts\\fetch_pr_comments.py",
  "pythonPath": "C:\\path\\to\\python.exe",
  "token": "your-azure-devops-pat",
  "debugMode": false
}
```

You can manually edit this file if you need to update your token or switch repositories.

## 🔧 For Your Coworkers

To share this plugin with your team:

1. **Share the repo**: Push your pr-review-plugin to a shared location or Git repo
2. **Installation**: Have them clone and run `.\scripts\install.ps1`
3. **Configuration**: They'll be prompted for:
   - Your organization name (e.g., "cudirect")
   - Project name (e.g., "Origence")
   - Repository name (e.g., "arcOS.Web")
   - Their own Azure DevOps PAT token

Each person needs their own PAT token, but everything else can be the same.

## 🐛 Troubleshooting

**"Error: No token provided"**
- Check that `~/.claude/ado-config.json` has a valid `token` field
- Ensure your PAT hasn't expired

**"Authentication failed"**
- Verify your PAT has Code (Read) scope
- Create a new token if needed

**"Python not found"**
- Install Python 3.8+ from https://www.python.org/downloads/
- Update `pythonPath` in the config file

**"Script not found"**
- Ensure `scriptPath` in config points to `fetch_pr_comments.py`
- Use absolute paths, not relative

## 📄 Files

- `commands/pr-review.md` - The slash command that Claude reads
- `scripts/fetch_pr_comments.py` - Python script that fetches PR comments from Azure DevOps
- `scripts/install.ps1` - Windows installation script
- `.claude/example-ado-config.json` - Example configuration file

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

Built for efficient PR reviews with Claude Code
