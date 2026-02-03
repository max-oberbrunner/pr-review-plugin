# Claude Code PR Review Plugin

A pull request review automation tool for Claude Code that supports both **Azure DevOps** and **GitHub**. Fetches PR comments, presents them interactively, and guides developers through addressing each review comment systematically with persistent status tracking.

## Prerequisites

- **Python 3.8+** installed
- **Claude Code** CLI installed
- One of:
  - **Azure DevOps** account with PAT (Code Read scope)
  - **GitHub** account with PAT (repo or public_repo scope)

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

## Creating Your Personal Access Token (PAT)

### GitHub PAT

1. Navigate to https://github.com/settings/tokens
2. Click **"Generate new token"** (classic)
3. Name it (e.g., "Claude Code PR Review")
4. Set expiration (recommended: 90 days)
5. Select scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories only)
6. Click **"Generate token"** and copy immediately

### Azure DevOps PAT

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
│   └── settings.local.json
├── commands/
│   └── pr-review.md
├── scripts/
│   ├── fetch_pr_comments.py   # Azure DevOps fetcher
│   ├── fetch_github_pr.py     # GitHub fetcher
│   ├── status_tracker.py
│   ├── update_status.py
│   ├── run_pr_review.py       # Platform router
│   ├── setup_ado.py           # Azure DevOps setup wizard
│   ├── setup_github.py        # GitHub setup wizard
│   ├── token_manager.py       # Multi-platform token management
│   ├── error_messages.py
│   ├── install.ps1
│   ├── install.sh
│   └── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

When configured in your project, the plugin creates:
```
your-project/
├── .claude/
│   ├── pr-review.json      # Configuration (per-project)
│   └── pr-status/          # PR review status tracking
│       └── pr-{N}-status.json
└── ...
```

## Configuration

Configuration is stored per-project at `.claude/pr-review.json` (in the project root).

### GitHub Configuration

```json
{
  "platform": "github",
  "owner": "your-username-or-org",
  "repository": "your-repo"
}
```

Token resolved from: `GITHUB_PAT` env var > System keychain > Prompt

### Azure DevOps Configuration

```json
{
  "platform": "azure-devops",
  "organization": "your-org",
  "project": "your-project",
  "repository": "your-repo"
}
```

Token resolved from: `AZURE_DEVOPS_PAT` env var > System keychain > Config file (deprecated) > Prompt

Paths (scriptPath, pythonPath) are auto-detected for both platforms.

**Status tracking** is stored in `.claude/pr-status/pr-{NUMBER}-status.json` with values: `ACTIVE`, `COMPLETED`, `IN_PROGRESS`, `SKIPPED`, `BLOCKED`.

## Troubleshooting

### Authentication Issues

**"No token provided"**
- For GitHub: Set `GITHUB_PAT` or run `python scripts/token_manager.py --save --platform github`
- For Azure DevOps: Set `AZURE_DEVOPS_PAT` or run `python scripts/token_manager.py --save`

**"Authentication failed (401)"**
- GitHub: Your PAT may have expired. Create a new token at https://github.com/settings/tokens
- Azure DevOps: Create a new token at `https://dev.azure.com/{org}/_usersSettings/tokens`

### Python Issues

**"Python not found"** - Install Python 3.8+. Paths are auto-detected.

**"ModuleNotFoundError: requests"** - Run `pip install -r scripts/requirements.txt`.

### Configuration Issues

**"Not in a git repository"** - Run the command from within a git repository.

**"Missing platform field"** - Run the appropriate setup wizard:
- GitHub: `python scripts/setup_github.py`
- Azure DevOps: `python scripts/setup_ado.py`

**"Configuration file not found"** - Run the appropriate setup wizard from your project directory.

**"PR not found (404)"** - Verify the PR number and that you have access to the repository.

### GitHub Limitations

GitHub comment fetching is not yet fully implemented. The plugin will display PR information (title, description, author, branch info) but comment parsing is coming soon.

## License

MIT License - See [LICENSE](LICENSE) for details.
