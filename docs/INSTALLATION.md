# Installation Guide

Complete guide to installing the PR Review plugin for Claude Code.

## Prerequisites

Before installing, ensure you have:

- **Claude Code** installed and configured (version 1.0.0 or higher)
- **Git** installed on your system
- **GitHub CLI** (`gh`) installed and authenticated (optional, but recommended for PR features)
- A **GitHub account** with access to repositories you want to review

### Verify Prerequisites

```bash
# Check Claude Code
claude --version

# Check Git
git --version

# Check GitHub CLI (optional)
gh --version
gh auth status
```

## Installation Methods

### Method 1: Automated Installation (Recommended)

This is the quickest way to get started:

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin

# Run the install script
./scripts/install.sh
```

The script will:
1. Detect your Claude Code commands directory
2. Create a symbolic link to the command file
3. Verify the installation
4. Print next steps

### Method 2: Manual Installation with Symlink

Using a symlink allows automatic updates when you pull changes:

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin

# Create symlink (macOS/Linux)
ln -s "$(pwd)/commands/pr-review.md" ~/.claude/commands/pr-review.md

# Windows (run as Administrator in PowerShell)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\commands\pr-review.md" -Target "$(Get-Location)\commands\pr-review.md"
```

### Method 3: Manual Copy Installation

If you prefer not to use symlinks:

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin

# Copy the command file
cp commands/pr-review.md ~/.claude/commands/

# Windows (PowerShell)
Copy-Item commands\pr-review.md $env:USERPROFILE\.claude\commands\
```

**Note**: With this method, you'll need to manually copy updates when the plugin is updated.

## Verify Installation

After installation, verify the plugin is working:

```bash
# Start Claude Code
claude

# Try listing commands (should show pr-review)
/help

# Test the command
/pr-review --help
```

You should see the `/pr-review` command listed and be able to access its help information.

## Platform-Specific Notes

### macOS
- Default commands directory: `~/.claude/commands/`
- May need to grant Terminal full disk access in System Preferences > Security & Privacy

### Linux
- Default commands directory: `~/.claude/commands/`
- Ensure execute permissions: `chmod +x scripts/install.sh`

### Windows
- Default commands directory: `%USERPROFILE%\.claude\commands\`
- Symbolic links require Administrator privileges
- Use PowerShell or Git Bash for installation

## Configuration

### GitHub CLI Setup (Recommended)

For full PR review capabilities, authenticate GitHub CLI:

```bash
# Authenticate with GitHub
gh auth login

# Verify authentication
gh auth status

# Test PR access
gh pr list
```

### Custom Commands Directory

If you use a custom commands directory:

```bash
# Set CLAUDE_COMMANDS_DIR environment variable
export CLAUDE_COMMANDS_DIR=/path/to/your/commands

# Or use the install script with custom path
./scripts/install.sh --commands-dir=/path/to/your/commands
```

## Updating the Plugin

### With Symlink Installation

```bash
cd pr-review-plugin
git pull origin main
# Changes are automatically available (symlink)
```

### With Copy Installation

```bash
cd pr-review-plugin
git pull origin main
cp commands/pr-review.md ~/.claude/commands/
```

## Troubleshooting

### Command Not Found

**Problem**: `/pr-review` command not recognized in Claude Code

**Solutions**:
1. Verify file is in commands directory:
   ```bash
   ls -la ~/.claude/commands/pr-review.md
   ```
2. Restart Claude Code
3. Check file permissions:
   ```bash
   chmod 644 ~/.claude/commands/pr-review.md
   ```

### Symlink Issues

**Problem**: Symlink broken or not working

**Solutions**:
1. Verify symlink target:
   ```bash
   ls -l ~/.claude/commands/pr-review.md
   ```
2. Recreate symlink with absolute path:
   ```bash
   ln -sf /full/path/to/pr-review-plugin/commands/pr-review.md ~/.claude/commands/pr-review.md
   ```

### GitHub Authentication Errors

**Problem**: Can't access PRs or repository information

**Solutions**:
1. Authenticate GitHub CLI:
   ```bash
   gh auth login
   ```
2. Verify repository access:
   ```bash
   gh repo view OWNER/REPO
   ```
3. Check token scopes include `repo` access

### Permission Denied

**Problem**: Cannot create symlink or copy files

**Solutions**:
1. **macOS**: Grant Terminal full disk access in System Preferences
2. **Linux**: Ensure you have write permissions to `~/.claude/commands/`
3. **Windows**: Run PowerShell as Administrator for symlinks

### Wrong Commands Directory

**Problem**: Commands directory is not `~/.claude/commands/`

**Solutions**:
1. Find your Claude Code config:
   ```bash
   claude config show
   ```
2. Install to correct directory:
   ```bash
   ./scripts/install.sh --commands-dir=/path/to/commands
   ```

## Uninstallation

To remove the plugin:

```bash
# Remove symlink or file
rm ~/.claude/commands/pr-review.md

# Optionally remove the cloned repository
rm -rf pr-review-plugin
```

## Need Help?

- [Report Installation Issues](https://github.com/YOUR-USERNAME/pr-review-plugin/issues)
- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

## Next Steps

✅ Installation complete! Now you can:
1. Read [EXAMPLES.md](EXAMPLES.md) for usage examples
2. Try `/pr-review` on a test PR
3. Explore [CUSTOMIZATION.md](CUSTOMIZATION.md) to tailor the command to your needs
