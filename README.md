# Claude Code PR Review Plugin

An Azure DevOps pull request review automation tool for Claude Code that fetches PR comments, presents them interactively, and guides developers through addressing each review comment systematically with persistent status tracking.

## Prerequisites

- **Python 3.8+** installed
- **Azure DevOps** account with access to your organization
- **Personal Access Token (PAT)** with Code (Read) scope
- **Claude Code** CLI installed

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/max-oberbrunner/pr-review-plugin.git
cd pr-review-plugin
```

### Step 2: Install Python Dependencies

```bash
pip install -r scripts/requirements.txt
```

Or with a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r scripts/requirements.txt
```

### Step 3: Run the Installer

**macOS/Linux:**
```bash
./scripts/install.sh
```

**Windows:**
```powershell
.\scripts\install.ps1
```

The installer will prompt you for your Azure DevOps organization, project, repository, and PAT token.

## Creating Your Azure DevOps PAT

1. Navigate to `https://dev.azure.com/{your-org}/_usersSettings/tokens`
2. Click **"New Token"**
3. Name it (e.g., "Claude Code PR Review")
4. Set expiration (recommended: 90 days)
5. Under **"Scopes"**, select **"Code"** → **"Read"**
6. Click **"Create"** and copy the token immediately

## Usage

```bash
# In Claude Code, review a PR by number
/pr-review 87663
```

The plugin will:
1. Fetch all comments from the PR with status tracking
2. Categorize by priority (Critical, Important, Style)
3. Guide you through each comment with code context
4. Track progress across sessions
5. Offer to create a git commit when complete

## Project Structure

```
pr-review-plugin/
├── .claude/
│   ├── example-ado-config.json
│   └── settings.local.json
├── commands/
│   └── pr-review.md
├── scripts/
│   ├── fetch_pr_comments.py
│   ├── status_tracker.py
│   ├── update_status.py
│   ├── run_pr_review.py
│   ├── setup_wizard.py
│   ├── token_manager.py
│   ├── error_messages.py
│   ├── install.ps1
│   ├── install.sh
│   └── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Configuration

Configuration is stored at `~/.claude/ado-config.json`:

```json
{
  "organization": "your-org",
  "project": "your-project",
  "repository": "your-repo",
  "scriptPath": "/path/to/fetch_pr_comments.py",
  "pythonPath": "/path/to/python",
  "token": "your-azure-devops-pat",
  "debugMode": false
}
```

**Status tracking** is stored in `.pr-status/pr-{NUMBER}-status.json` with values: `ACTIVE`, `COMPLETED`, `IN_PROGRESS`, `SKIPPED`, `BLOCKED`.

## Troubleshooting

### Authentication Issues

**"No token provided"** - Verify `~/.claude/ado-config.json` has a valid `token` field.

**"Authentication failed (401)"** - Your PAT may have expired or lacks **Code (Read)** scope. Create a new token at `https://dev.azure.com/{org}/_usersSettings/tokens`.

### Python Issues

**"Python not found"** - Install Python 3.8+ and update `pythonPath` in the config file.

**"ModuleNotFoundError: requests"** - Run `pip install -r scripts/requirements.txt`.

### Configuration Issues

**"Script not found"** - Ensure `scriptPath` in config uses an absolute path to `fetch_pr_comments.py`.

**"PR not found (404)"** - Verify the PR number and that you have access to the repository.

## License

MIT License - See [LICENSE](LICENSE) for details.
