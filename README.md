# Claude Code PR Review Plugin

A powerful, customizable pull request review command for Claude Code that helps teams maintain code quality through AI-assisted code reviews.

## 🚀 Quick Start

### Installation

**Option 1: Quick Install (Recommended)**

Linux/macOS:
```bash
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin
./scripts/install.sh
```

Windows (PowerShell):
```powershell
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin
.\scripts\install.ps1
```

**Option 2: Manual Install**

Linux/macOS:
```bash
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin

# Copy command to your Claude Code commands directory
cp commands/pr-review.md ~/.claude/commands/

# Or create a symlink (allows automatic updates when you pull)
ln -s "$(pwd)/commands/pr-review.md" ~/.claude/commands/pr-review.md
```

Windows (PowerShell):
```powershell
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin

# Copy command to your Claude Code commands directory
Copy-Item commands\pr-review.md $env:USERPROFILE\.claude\commands\

# Or create a symlink (requires Admin or Developer Mode)
New-Item -ItemType SymbolicLink -Path $env:USERPROFILE\.claude\commands\pr-review.md -Target "$PWD\commands\pr-review.md"
```

### Verify Installation
```bash
# In Claude Code, check if the command is available
/pr-review --help
```

## 📖 What It Does

This plugin provides intelligent PR review capabilities including:

- **Code Quality Analysis**: Identifies potential bugs, anti-patterns, and code smells
- **Security Scanning**: Detects common security vulnerabilities
- **Performance Review**: Suggests optimization opportunities
- **Style Consistency**: Checks adherence to coding standards
- **Documentation Check**: Ensures adequate code documentation
- **Test Coverage**: Validates test completeness

## 🎯 Usage

```bash
# Review current branch changes
/pr-review

# Review specific PR number
/pr-review #123

# Review with specific focus areas
/pr-review --focus=security,performance

# Quick review (surface-level only)
/pr-review --quick
```

See [EXAMPLES.md](docs/EXAMPLES.md) for more usage scenarios.

## 🔧 Customization

This plugin is designed to be fork-friendly! You can easily customize it for your team's specific needs:

1. Fork this repository
2. Modify the command file to match your standards
3. Share your fork with your team

See [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for detailed customization guide.

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [Customization Guide](docs/CUSTOMIZATION.md) - How to fork and modify
- [Examples](docs/EXAMPLES.md) - Usage examples and scenarios

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Share your customizations

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🔗 Links

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [Report Issues](https://github.com/YOUR-USERNAME/pr-review-plugin/issues)
- [Changelog](CHANGELOG.md)

## 💡 Tips

- **First time?** Start with the quick install and try `/pr-review` on a small PR
- **Want to customize?** Check the CUSTOMIZATION.md guide for common modifications
- **Having issues?** See INSTALLATION.md troubleshooting section

---

Made with ❤️ for better code reviews
