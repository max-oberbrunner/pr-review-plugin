#!/usr/bin/env bash

# PR Review Plugin - Installation Script
# Automatically installs the PR review command to Claude Code

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default commands directory
DEFAULT_COMMANDS_DIR="$HOME/.claude/commands"
COMMANDS_DIR="$DEFAULT_COMMANDS_DIR"

# Script directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
COMMAND_FILE="$PLUGIN_DIR/commands/pr-review.md"

# Print functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  PR Review Plugin - Installation${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --commands-dir=*)
                COMMANDS_DIR="${1#*=}"
                shift
                ;;
            --commands-dir)
                COMMANDS_DIR="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Usage: ./install.sh [OPTIONS]

Install the PR Review plugin for Claude Code.

OPTIONS:
    --commands-dir=PATH    Custom Claude Code commands directory
                          (default: ~/.claude/commands)
    --help, -h            Show this help message

EXAMPLES:
    ./install.sh
    ./install.sh --commands-dir=/custom/path/commands

EOF
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if command file exists
    if [[ ! -f "$COMMAND_FILE" ]]; then
        print_error "Command file not found: $COMMAND_FILE"
        print_error "Make sure you're running this script from the pr-review-plugin directory"
        exit 1
    fi

    print_success "Command file found"

    # Check if git is installed (helpful but not required)
    if command -v git &> /dev/null; then
        print_success "Git is installed"
    else
        print_warning "Git not found (optional, but recommended)"
    fi

    # Check if gh CLI is installed (helpful but not required)
    if command -v gh &> /dev/null; then
        print_success "GitHub CLI is installed"

        # Check if authenticated
        if gh auth status &> /dev/null; then
            print_success "GitHub CLI is authenticated"
        else
            print_warning "GitHub CLI not authenticated (run: gh auth login)"
        fi
    else
        print_warning "GitHub CLI not found (optional, but recommended for PR features)"
    fi
}

# Create commands directory if it doesn't exist
setup_commands_dir() {
    print_info "Setting up commands directory..."

    if [[ ! -d "$COMMANDS_DIR" ]]; then
        print_warning "Commands directory doesn't exist: $COMMANDS_DIR"
        read -p "Create it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$COMMANDS_DIR"
            print_success "Created directory: $COMMANDS_DIR"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    else
        print_success "Commands directory exists: $COMMANDS_DIR"
    fi
}

# Check if command already installed
check_existing_installation() {
    local target_file="$COMMANDS_DIR/pr-review.md"

    if [[ -e "$target_file" ]]; then
        print_warning "pr-review.md already exists in $COMMANDS_DIR"

        # Check if it's a symlink
        if [[ -L "$target_file" ]]; then
            local link_target=$(readlink "$target_file")
            print_info "Current installation is a symlink to: $link_target"
        else
            print_info "Current installation is a regular file"
        fi

        read -p "Replace existing installation? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Installation cancelled"
            exit 1
        fi

        # Remove existing file/symlink
        rm "$target_file"
        print_success "Removed existing installation"
    fi
}

# Install command
install_command() {
    local target_file="$COMMANDS_DIR/pr-review.md"

    print_info "Installing command..."

    # Ask user for installation method
    echo ""
    echo "Choose installation method:"
    echo "  1) Symlink (recommended - allows automatic updates)"
    echo "  2) Copy (static - requires manual updates)"
    echo ""
    read -p "Enter choice (1 or 2): " -n 1 -r
    echo ""

    case $REPLY in
        1)
            # Create symlink
            ln -s "$COMMAND_FILE" "$target_file"
            print_success "Created symlink: $target_file -> $COMMAND_FILE"
            print_info "Updates to the plugin will be automatically available"
            ;;
        2)
            # Copy file
            cp "$COMMAND_FILE" "$target_file"
            print_success "Copied command to: $target_file"
            print_warning "You'll need to manually update when the plugin is updated"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Set file permissions
    chmod 644 "$target_file"
    print_success "Set file permissions"
}

# Verify installation
verify_installation() {
    local target_file="$COMMANDS_DIR/pr-review.md"

    print_info "Verifying installation..."

    if [[ -e "$target_file" ]]; then
        print_success "Command file exists: $target_file"

        # Check if file is readable
        if [[ -r "$target_file" ]]; then
            print_success "Command file is readable"
        else
            print_error "Command file is not readable"
            return 1
        fi

        return 0
    else
        print_error "Command file not found after installation"
        return 1
    fi
}

# Run setup wizard
run_setup_wizard() {
    local github_wizard="$SCRIPT_DIR/setup_github.py"
    local ado_wizard="$SCRIPT_DIR/setup_ado.py"

    # Detect Python
    local python_cmd=""
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
    fi

    if [[ -z "$python_cmd" ]]; then
        print_warning "Python not found - cannot run setup wizard"
        return 1
    fi

    echo ""
    print_info "Would you like to run a setup wizard now?"
    echo ""
    echo "  1) GitHub"
    echo "  2) Azure DevOps"
    echo "  3) Skip (configure later)"
    echo ""
    read -p "Select platform (1/2/3): " -n 1 -r
    echo

    case $REPLY in
        1)
            if [[ ! -f "$github_wizard" ]]; then
                print_warning "GitHub setup wizard not found: $github_wizard"
                return 1
            fi
            print_info "Starting GitHub setup wizard..."
            echo ""
            "$python_cmd" "$github_wizard"
            return $?
            ;;
        2)
            if [[ ! -f "$ado_wizard" ]]; then
                print_warning "Azure DevOps setup wizard not found: $ado_wizard"
                return 1
            fi
            print_info "Starting Azure DevOps setup wizard..."
            echo ""
            "$python_cmd" "$ado_wizard"
            return $?
            ;;
        *)
            print_info "Skipping setup wizard. You can run it later with:"
            echo -e "   ${BLUE}# For GitHub:${NC}"
            echo -e "   ${BLUE}python $github_wizard${NC}"
            echo -e "   ${BLUE}# For Azure DevOps:${NC}"
            echo -e "   ${BLUE}python $ado_wizard${NC}"
            return 0
            ;;
    esac
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation Complete! 🎉${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Start or restart Claude Code:"
    echo -e "   ${BLUE}claude${NC}"
    echo ""
    echo "2. Verify the command is available:"
    echo -e "   ${BLUE}/pr-review --help${NC}"
    echo ""
    echo "3. Try it on a test PR:"
    echo -e "   ${BLUE}/pr-review 12345${NC}"
    echo ""
    echo "4. Read the documentation:"
    echo "   - Usage examples: docs/EXAMPLES.md"
    echo "   - Customization: docs/CUSTOMIZATION.md"
    echo ""
    echo "Need help? Check out:"
    echo "  📖 Documentation: https://github.com/YOUR-USERNAME/pr-review-plugin"
    echo "  🐛 Issues: https://github.com/YOUR-USERNAME/pr-review-plugin/issues"
    echo ""
}

# Main installation flow
main() {
    print_header

    parse_args "$@"

    check_prerequisites
    setup_commands_dir
    check_existing_installation
    install_command

    if verify_installation; then
        # Offer to run setup wizard
        run_setup_wizard

        print_next_steps
        exit 0
    else
        print_error "Installation verification failed"
        exit 1
    fi
}

# Run main function
main "$@"
