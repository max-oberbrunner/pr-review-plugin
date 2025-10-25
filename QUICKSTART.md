# Quick Start Guide

Get up and running with PR Review Plugin in 5 minutes!

## ⚡ 1-Minute Setup

```bash
# Clone and install
git clone https://github.com/YOUR-USERNAME/pr-review-plugin.git
cd pr-review-plugin
./scripts/install.sh

# Start using it
claude
/pr-review
```

That's it! 🎉

## 📋 Prerequisites Checklist

Before installing, make sure you have:

- [ ] Claude Code installed (`claude --version`)
- [ ] Git installed (`git --version`)
- [ ] (Optional) GitHub CLI installed and authenticated (`gh auth status`)

Missing something? See [INSTALLATION.md](docs/INSTALLATION.md) for setup help.

## 🎯 First Review

### Try It On Your Current Branch

```bash
# 1. Switch to a branch with changes
git checkout feature/your-branch

# 2. Start Claude Code
claude

# 3. Run the review
/pr-review
```

### Try It On a GitHub PR

```bash
# In Claude Code
/pr-review #123
```

## 🚀 Common Commands

| Command | What It Does |
|---------|--------------|
| `/pr-review` | Review current branch changes |
| `/pr-review #123` | Review PR #123 from GitHub |
| `/pr-review --quick` | Fast surface-level review |
| `/pr-review --focus=security` | Security-focused review |
| `/pr-review --help` | Show all options |

## 💡 Pro Tips

### Tip 1: Start Small
Try reviewing a small PR first to see what the tool does.

### Tip 2: Use Quick Mode
Use `--quick` for rapid feedback during development.

### Tip 3: Focus Reviews
Use `--focus=security` or `--focus=performance` to zero in on specific concerns.

### Tip 4: Create Aliases
Add to your `.bashrc` or `.zshrc`:
```bash
alias prq="claude /pr-review --quick"
alias prs="claude /pr-review --focus=security"
```

## 🎓 Learn More

- **Usage Examples**: See [EXAMPLES.md](docs/EXAMPLES.md) for 20+ scenarios
- **Customization**: Read [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) to tailor it
- **Troubleshooting**: Check [INSTALLATION.md](docs/INSTALLATION.md#troubleshooting)

## 🆘 Need Help?

**Command not found?**
- Restart Claude Code
- Check `~/.claude/commands/pr-review.md` exists

**Can't access PRs?**
- Run `gh auth login` to authenticate GitHub CLI

**Other issues?**
- See [INSTALLATION.md - Troubleshooting](docs/INSTALLATION.md#troubleshooting)
- [Report an issue](https://github.com/YOUR-USERNAME/pr-review-plugin/issues)

## 🎉 You're Ready!

Now you're ready to catch bugs, improve code quality, and ship with confidence!

Happy reviewing! 🚀

---

**Next Steps:**
1. ✅ Complete installation
2. ✅ Try your first review
3. 📖 Explore [EXAMPLES.md](docs/EXAMPLES.md)
4. 🔧 Customize for your team ([CUSTOMIZATION.md](docs/CUSTOMIZATION.md))
5. 🤝 Share with teammates
