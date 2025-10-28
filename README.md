# Claude Code PR Review Plugin

An Azure DevOps pull request review automation tool for Claude Code that fetches PR comments, presents them interactively, and guides developers through addressing each review comment systematically with persistent status tracking.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **Azure DevOps** account with access to your organization
- **Personal Access Token (PAT)** with Code (Read) scope
- **Claude Code** CLI installed

### Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/max-oberbrunner/pr-review-plugin.git
cd pr-review-plugin
```

#### Step 2: Set Up Python Dependencies

Choose one of the following options:

**Option A: Direct Installation (Recommended)**

Install dependencies directly to your Python environment:

```bash
# Navigate to the scripts directory
cd scripts

# Install dependencies
pip install -r requirements.txt

# Return to repo root
cd ..
```

**Option B: Using Virtual Environment**

Create an isolated Python environment:

**Windows (PowerShell 5.1+):**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r scripts/requirements.txt
```

**macOS/Linux (Bash):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r scripts/requirements.txt
```

#### Step 3: Configure Azure DevOps Integration

**Windows (PowerShell 5.1+):**
```powershell
.\scripts\install.ps1
```

**macOS/Linux (Bash):**
```bash
./scripts/install.sh
```

The installer will:
1. Validate Python installation and prerequisites
2. Prompt you for Azure DevOps configuration (organization, project, repository)
3. Auto-detect your Python installation path
4. Request your Azure DevOps Personal Access Token
5. Create the configuration file at `~/.claude/ado-config.json`
6. Register the `/pr-review` command in Claude Code

### Creating Your Azure DevOps Personal Access Token

1. Navigate to https://dev.azure.com/{your-org}/_usersSettings/tokens
2. Click **"New Token"**
3. Name it (e.g., "Claude Code PR Review")
4. Set expiration (recommended: 90 days or custom)
5. Under **"Scopes"**, select **"Code"** → **"Read"**
6. Click **"Create"**
7. **Copy the token immediately** (you won't be able to see it again!)

### Usage

```bash
# In Claude Code, review a PR by number
/pr-review 87663
```

**Interactive Workflow:**
1. Fetches all comments from the PR (with status tracking)
2. Categorizes comments by priority:
   - 🔴 **Critical** - Must fix issues
   - 🟡 **Important** - Should address
   - 🟢 **Style** - Optional improvements
3. Creates an interactive task list with TodoWrite
4. Guides you through each comment with:
   - Relevant code context and line numbers
   - Explanation of WHY changes are needed
   - Implementation assistance or learning guidance
5. Tracks progress with persistent statuses across sessions
6. Offers to create a git commit when complete

## 📖 What It Does

This plugin provides comprehensive Azure DevOps PR review integration:

### Core Features
- **Fetch PR Comments**: Retrieves all review threads from Azure DevOps API (v7.1)
- **Priority Categorization**: Automatically sorts comments by severity (critical, important, style)
- **Interactive Workflow**: Step-by-step guided review process
- **Code Context**: Shows file locations, line numbers, and relevant code snippets
- **Educational Approach**: Explains the reasoning behind requested changes
- **Status Tracking**: Persistent tracking of comment progress across sessions
- **Multi-session Continuity**: Resume work on PRs across multiple Claude Code sessions
- **Git Integration**: Automatic commit message generation with detailed change descriptions

### Advanced Features
- **Custom Status System**: Track comments as ACTIVE, COMPLETED, IN_PROGRESS, SKIPPED, or BLOCKED
- **Status Persistence**: Progress saved in `.pr-status/pr-{NUMBER}-status.json` files
- **Manual Status Updates**: CLI tool for updating comment statuses outside Claude
- **Debug Mode**: Detailed API request/response logging for troubleshooting
- **Connection Testing**: Built-in validation tool (`test_connection.py`)
- **API Debugging**: Specialized diagnostic tool (`debug_api.py`)
- **Configuration Wrapper**: Simplified execution with automatic config handling

## 🗂️ Project Structure

```
pr-review-plugin/
├── .claude/                          # Claude Code integration
│   ├── example-ado-config.json      # Configuration template
│   └── settings.local.json          # Local settings
├── commands/
│   └── pr-review.md                 # Main slash command (244 lines)
├── docs/
│   ├── INSTALLATION.md              # Detailed setup guide
│   ├── CUSTOMIZATION.md             # Forking and customization
│   └── EXAMPLES.md                  # 20+ usage examples
├── scripts/
│   ├── fetch_pr_comments.py         # Core API client (385 lines)
│   ├── status_tracker.py            # Status persistence module (210 lines)
│   ├── update_status.py             # Manual status CLI (99 lines)
│   ├── run_pr_review.py             # Configuration wrapper (176 lines)
│   ├── test_connection.py           # Connection validator (176 lines)
│   ├── debug_api.py                 # API debugging tool
│   ├── install.ps1                  # Windows installer
│   ├── install.sh                   # Unix/Linux installer
│   ├── requirements.txt             # Python dependencies
│   └── .env.example                 # Environment template
├── README.md                         # This file
├── QUICKSTART.md                     # 5-minute setup guide
├── PROJECT_STRUCTURE.md              # Architecture documentation
├── STATUS_TRACKING.md                # Status tracking feature docs
├── CHANGELOG.md                      # Version history
├── CONTRIBUTING.md                   # Contribution guidelines
└── LICENSE                           # MIT License
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture documentation.

## 🔧 Configuration

### Main Configuration File: `~/.claude/ado-config.json`

```json
{
  "organization": "your-org",           // Azure DevOps organization
  "project": "your-project",            // Project name
  "repository": "your-repo",            // Repository name
  "scriptPath": "/path/to/fetch_pr_comments.py",
  "pythonPath": "/path/to/python",      // Python executable path
  "token": "your-azure-devops-pat",     // Personal Access Token
  "debugMode": false                    // Enable detailed logging
}
```

**Configuration Notes:**
- Paths must be absolute (not relative)
- Windows paths use double backslashes: `C:\\path\\to\\file`
- Token is stored locally and never shared
- `debugMode: true` enables detailed API logging for troubleshooting

### Status Tracking Files: `.pr-status/pr-{NUMBER}-status.json`

```json
{
  "pr_number": 87663,
  "last_updated": "2025-10-27T13:00:02.349730",
  "threads": {
    "782180": {
      "status": "COMPLETED",
      "updated_at": "2025-10-27T12:59:49.840965",
      "note": "Implemented lenderIdentityDataService"
    }
  }
}
```

**Status Values:**
- `ACTIVE` - Needs to be addressed (default)
- `COMPLETED` - Fix has been implemented
- `IN_PROGRESS` - Currently working on it
- `SKIPPED` - Intentionally deferred
- `BLOCKED` - Cannot address (waiting for dependencies)

See [STATUS_TRACKING.md](STATUS_TRACKING.md) for detailed status management documentation.

## 🛠️ Advanced Usage

### Manual Status Updates

Update comment status without running the full workflow:

```bash
# Mark a comment as completed
python scripts/update_status.py 87663 782180 COMPLETED --note "Fixed validation logic"

# Mark as in progress
python scripts/update_status.py 87663 782181 IN_PROGRESS

# Clear custom status (revert to Azure DevOps status)
python scripts/update_status.py 87663 782180 --clear
```

### Test Connection

Validate your Azure DevOps configuration:

```bash
python scripts/test_connection.py
```

This will:
- Verify authentication with your PAT token
- Test API connectivity
- List available projects in your organization
- Provide troubleshooting suggestions if issues are found

### Debug Mode

Enable detailed API logging in `~/.claude/ado-config.json`:

```json
{
  "debugMode": true
}
```

Or run scripts directly with debug flag:

```bash
python scripts/fetch_pr_comments.py 87663 --debug
```

### Using the Configuration Wrapper

Run the PR review script with automatic configuration:

```bash
python scripts/run_pr_review.py 87663
```

This automatically:
- Loads configuration from `~/.claude/ado-config.json`
- Validates all paths and tokens
- Executes the comment fetcher with proper parameters

## 👥 Team Deployment

### Sharing with Your Team

1. **Share the Repository**:
   ```bash
   git push origin main
   # Share repo URL with team
   ```

2. **Team Installation**:
   ```bash
   git clone https://your-repo-url/pr-review-plugin.git
   cd pr-review-plugin
   .\scripts\install.ps1  # Windows
   ./scripts/install.sh   # macOS/Linux
   ```

3. **Configuration**: Each team member provides:
   - Same organization, project, and repository names
   - Their own Azure DevOps PAT token (required per user)
   - Their local Python installation path (auto-detected)

### Customization for Your Organization

See [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for:
- Forking guidelines
- Custom comment categorization rules
- Workflow modifications
- Brand-specific adjustments

## 🐛 Troubleshooting

### Authentication Issues

**"Error: No token provided"**
- Verify `~/.claude/ado-config.json` has a valid `token` field
- Ensure your PAT hasn't expired
- Check that the config file is in your home directory

**"Authentication failed (401)"**
- Verify your PAT has **Code (Read)** scope
- Create a new token at https://dev.azure.com/{org}/_usersSettings/tokens
- Update the token in `~/.claude/ado-config.json`

### Python Issues

**"Python not found"**
- Install Python 3.8+ from https://www.python.org/downloads/
- Update `pythonPath` in config file to absolute path
- Run `python --version` to verify installation

**"ModuleNotFoundError: requests"**
- Ensure you've completed Step 2 of the installation:
  - **Option A**: From repo root: `cd scripts && pip install -r requirements.txt && cd ..`
  - **Option B**: With venv activated: `pip install -r scripts/requirements.txt`
- Verify dependencies installed: `requests>=2.31.0`, `python-dotenv>=1.0.0`
- If using Option B, ensure venv is activated in your current terminal session

### Configuration Issues

**"Script not found"**
- Ensure `scriptPath` in config points to `fetch_pr_comments.py`
- Use absolute paths, not relative paths
- Check for typos in the path

**"PR not found (404)"**
- Verify the PR number is correct
- Ensure you have access to the repository
- Check that organization, project, and repository names are correct

### Connection Issues

**"Connection timeout"**
- Check internet connectivity
- Verify Azure DevOps is accessible
- Try running `python scripts/test_connection.py`

**"SSL Certificate Error"**
- Update Python's certificates: `pip install --upgrade certifi`
- Check corporate firewall/proxy settings

### Status Tracking Issues

**"Status file not found"**
- Status files are created on first use in `.pr-status/` directory
- Ensure the directory exists and is writable
- `.pr-status/` is gitignored by default (intentional)

**"Status not persisting"**
- Check file permissions on `.pr-status/` directory
- Verify JSON syntax in status files
- Use `update_status.py` for manual corrections

For more help, run the connection test:
```bash
python scripts/test_connection.py
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide for new users
- **[docs/INSTALLATION.md](docs/INSTALLATION.md)** - Detailed installation instructions
- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - 20+ real-world usage examples
- **[docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md)** - Forking and customization guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Architecture and directory layout
- **[STATUS_TRACKING.md](STATUS_TRACKING.md)** - Status tracking feature documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and releases
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## 🔌 API Integration

### Azure DevOps REST API

- **API Version**: 7.1
- **Endpoints Used**:
  - `GET /repositories/{repo}/pullRequests/{pr_id}/threads` - Fetch PR comments
  - `GET /repositories/{repo}/pullRequests/{pr_id}` - Fetch PR metadata
- **Authentication**: Basic auth with PAT token (base64 encoded)
- **Timeout**: 10 seconds default

### Dependencies

```
requests>=2.31.0       # HTTP library for API calls
python-dotenv>=1.0.0   # Environment variable management
```

These dependencies are installed during Step 2 of the installation process:
- **Option A (Direct)**: `cd scripts && pip install -r requirements.txt && cd ..`
- **Option B (Virtual Environment)**: With venv activated: `pip install -r scripts/requirements.txt`

## 🎯 Use Cases

### Individual Developers
- Review PR comments interactively during development
- Track progress across multiple work sessions
- Learn from review feedback with contextual explanations

### Development Teams
- Standardize PR review workflows across the team
- Reduce time spent context-switching between Azure DevOps and IDE
- Maintain consistent code quality standards

### Code Review Best Practices
- Educational approach explains the "why" behind changes
- Priority categorization helps focus on critical issues first
- Status tracking ensures no comments are overlooked

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Pull request guidelines
- Testing requirements

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🏗️ Technical Stack

- **Languages**: Python 3.8+, Markdown, PowerShell, Bash
- **APIs**: Azure DevOps REST API v7.1
- **Integration**: Claude Code CLI slash commands
- **Data Format**: JSON for configuration and status persistence

## 📞 Support

- **Issues**: Report bugs at [GitHub Issues](https://github.com/max-oberbrunner/pr-review-plugin/issues)
- **Documentation**: Check docs/ directory for detailed guides
- **Examples**: See [docs/EXAMPLES.md](docs/EXAMPLES.md) for usage patterns

---

**Built for efficient, educational PR reviews with Claude Code** 🚀

Made with ❤️ for developers who want to streamline their Azure DevOps workflow
