# PR Review Plugin - Windows Installation Script
# Automatically installs the PR review command to Claude Code

#Requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter(HelpMessage="Custom Claude Code commands directory")]
    [string]$CommandsDir = "$env:USERPROFILE\.claude\commands",

    [Parameter(HelpMessage="Show help message")]
    [switch]$Help
)

# Script configuration
$ErrorActionPreference = "Stop"
$InformationPreference = "Continue"

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginDir = Split-Path -Parent $ScriptDir
$CommandFile = Join-Path $PluginDir "commands\pr-review.md"

# Color helper functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "✗ " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Header {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host "  PR Review Plugin - Windows Installation" -ForegroundColor Blue
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host ""
}

function Show-Help {
    @"

Usage: .\install.ps1 [OPTIONS]

Install the PR Review plugin for Claude Code on Windows.

OPTIONS:
    -CommandsDir <PATH>    Custom Claude Code commands directory
                          (default: %USERPROFILE%\.claude\commands)
    -Help                 Show this help message

EXAMPLES:
    .\install.ps1
    .\install.ps1 -CommandsDir C:\custom\path\commands

REQUIREMENTS:
    - PowerShell 5.1 or higher
    - Python 3.8+ (for PR fetching functionality)
    - Azure DevOps Personal Access Token (PAT)

"@
}

function Test-Administrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-DeveloperMode {
    try {
        $devMode = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Name "AllowDevelopmentWithoutDevLicense" -ErrorAction SilentlyContinue
        return $devMode.AllowDevelopmentWithoutDevLicense -eq 1
    }
    catch {
        return $false
    }
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check if command file exists
    if (-not (Test-Path $CommandFile)) {
        Write-ErrorMessage "Command file not found: $CommandFile"
        Write-ErrorMessage "Make sure you're running this script from the pr-review-plugin directory"
        exit 1
    }
    Write-Success "Command file found"

    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    if ($psVersion.Major -ge 5) {
        Write-Success "PowerShell $($psVersion.Major).$($psVersion.Minor) is installed"
    }
    else {
        Write-Warning "PowerShell version is below 5.1 (current: $($psVersion.Major).$($psVersion.Minor))"
    }

    # Check if Git is installed (helpful but not required)
    try {
        $null = Get-Command git -ErrorAction Stop
        Write-Success "Git is installed"
    }
    catch {
        Write-Warning "Git not found (optional, but recommended)"
    }

    # Check if Python is installed (helpful but not required)
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python is installed: $pythonVersion"
    }
    catch {
        Write-Warning "Python not found (required for PR fetching functionality)"
        Write-Info "Install Python from: https://www.python.org/downloads/"
    }

    # Check if GitHub CLI is installed (helpful but not required)
    try {
        $null = Get-Command gh -ErrorAction Stop
        Write-Success "GitHub CLI is installed"

        # Check if authenticated
        try {
            $null = gh auth status 2>&1
            Write-Success "GitHub CLI is authenticated"
        }
        catch {
            Write-Warning "GitHub CLI not authenticated (run: gh auth login)"
        }
    }
    catch {
        Write-Warning "GitHub CLI not found (optional, but recommended)"
    }

    # Check symlink capability
    $isAdmin = Test-Administrator
    $isDeveloperMode = Test-DeveloperMode

    if ($isAdmin) {
        Write-Success "Running with Administrator privileges (symlinks supported)"
    }
    elseif ($isDeveloperMode) {
        Write-Success "Developer Mode is enabled (symlinks supported)"
    }
    else {
        Write-Warning "Not running as Administrator and Developer Mode not enabled"
        Write-Info "Symlinks may not work. Copy installation will be recommended."
    }
}

function New-CommandsDirectory {
    Write-Info "Setting up commands directory..."

    if (-not (Test-Path $CommandsDir)) {
        Write-Warning "Commands directory doesn't exist: $CommandsDir"
        $response = Read-Host "Create it? (Y/N)"

        if ($response -eq 'Y' -or $response -eq 'y') {
            New-Item -ItemType Directory -Path $CommandsDir -Force | Out-Null
            Write-Success "Created directory: $CommandsDir"
        }
        else {
            Write-ErrorMessage "Installation cancelled"
            exit 1
        }
    }
    else {
        Write-Success "Commands directory exists: $CommandsDir"
    }
}

function Test-ExistingInstallation {
    $targetFile = Join-Path $CommandsDir "pr-review.md"

    if (Test-Path $targetFile) {
        Write-Warning "pr-review.md already exists in $CommandsDir"

        # Check if it's a symlink
        $item = Get-Item $targetFile
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            $linkTarget = $item.Target
            Write-Info "Current installation is a symlink to: $linkTarget"
        }
        else {
            Write-Info "Current installation is a regular file"
        }

        $response = Read-Host "Replace existing installation? (Y/N)"

        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-ErrorMessage "Installation cancelled"
            exit 1
        }

        # Remove existing file/symlink
        Remove-Item $targetFile -Force
        Write-Success "Removed existing installation"
    }
}

function Install-Command {
    $targetFile = Join-Path $CommandsDir "pr-review.md"

    Write-Info "Installing command..."

    # Check if symlinks are supported
    $isAdmin = Test-Administrator
    $isDeveloperMode = Test-DeveloperMode
    $canSymlink = $isAdmin -or $isDeveloperMode

    Write-Host ""
    Write-Host "Choose installation method:"

    if ($canSymlink) {
        Write-Host "  1) Symlink (recommended - allows automatic updates)"
        Write-Host "  2) Copy (static - requires manual updates)"
    }
    else {
        Write-Host "  1) Copy (recommended - symlinks not available)"
        Write-Host "  2) Try symlink anyway (may fail)"
    }
    Write-Host ""

    $choice = Read-Host "Enter choice (1 or 2)"

    switch ($choice) {
        "1" {
            if ($canSymlink) {
                # Create symlink
                try {
                    New-Item -ItemType SymbolicLink -Path $targetFile -Target $CommandFile -Force | Out-Null
                    Write-Success "Created symlink: $targetFile -> $CommandFile"
                    Write-Info "Updates to the plugin will be automatically available"
                }
                catch {
                    Write-ErrorMessage "Failed to create symlink: $_"
                    Write-Info "Falling back to copy method..."
                    Copy-Item $CommandFile $targetFile -Force
                    Write-Success "Copied command to: $targetFile"
                    Write-Warning "You'll need to manually update when the plugin is updated"
                }
            }
            else {
                # Copy file
                Copy-Item $CommandFile $targetFile -Force
                Write-Success "Copied command to: $targetFile"
                Write-Warning "You'll need to manually update when the plugin is updated"
            }
        }
        "2" {
            if ($canSymlink) {
                # Copy file
                Copy-Item $CommandFile $targetFile -Force
                Write-Success "Copied command to: $targetFile"
                Write-Warning "You'll need to manually update when the plugin is updated"
            }
            else {
                # Try symlink anyway
                try {
                    New-Item -ItemType SymbolicLink -Path $targetFile -Target $CommandFile -Force | Out-Null
                    Write-Success "Created symlink: $targetFile -> $CommandFile"
                    Write-Info "Updates to the plugin will be automatically available"
                }
                catch {
                    Write-ErrorMessage "Failed to create symlink: $_"
                    Write-Info "Falling back to copy method..."
                    Copy-Item $CommandFile $targetFile -Force
                    Write-Success "Copied command to: $targetFile"
                    Write-Warning "You'll need to manually update when the plugin is updated"
                }
            }
        }
        default {
            Write-ErrorMessage "Invalid choice"
            exit 1
        }
    }
}

function Invoke-SetupWizard {
    Write-Info "Setting up configuration..."

    $githubWizard = Join-Path $ScriptDir "setup_github.py"
    $adoWizard = Join-Path $ScriptDir "setup_ado.py"

    # Detect Python
    $pythonCmd = $null
    try {
        $pythonCmd = (Get-Command python -ErrorAction Stop).Source
    }
    catch {
        try {
            $pythonCmd = (Get-Command python3 -ErrorAction Stop).Source
        }
        catch {
            Write-Warning "Python not found - cannot run setup wizard"
            Write-Info "Falling back to manual configuration..."
            New-ConfigFileManual
            return
        }
    }

    Write-Host ""
    Write-Host "Would you like to run a setup wizard now?" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1) GitHub"
    Write-Host "  2) Azure DevOps"
    Write-Host "  3) Skip (configure later)"
    Write-Host ""
    $response = Read-Host "Select platform (1/2/3)"

    switch ($response) {
        '1' {
            if (-not (Test-Path $githubWizard)) {
                Write-Warning "GitHub setup wizard not found: $githubWizard"
                New-ConfigFileManual
                return
            }
            Write-Info "Starting GitHub setup wizard..."
            Write-Host ""
            & $pythonCmd $githubWizard
        }
        '2' {
            if (-not (Test-Path $adoWizard)) {
                Write-Warning "Azure DevOps setup wizard not found: $adoWizard"
                New-ConfigFileManual
                return
            }
            Write-Info "Starting Azure DevOps setup wizard..."
            Write-Host ""
            & $pythonCmd $adoWizard
        }
        default {
            Write-Info "Skipping setup wizard. You can run it later with:"
            Write-Host "   # For GitHub:" -ForegroundColor Blue
            Write-Host "   python $githubWizard" -ForegroundColor Blue
            Write-Host "   # For Azure DevOps:" -ForegroundColor Blue
            Write-Host "   python $adoWizard" -ForegroundColor Blue
        }
    }
}

function New-ConfigFileManual {
    # Manual config creation instructions (fallback if wizard unavailable)
    Write-Info "Manual configuration required..."
    Write-Host ""
    Write-Host "Configuration is stored per-project in .claude/pr-review.json" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To configure, navigate to your project and run:" -ForegroundColor Cyan
    Write-Host "   # For GitHub:" -ForegroundColor Blue
    Write-Host "   python $ScriptDir\setup_github.py" -ForegroundColor Blue
    Write-Host "   # For Azure DevOps:" -ForegroundColor Blue
    Write-Host "   python $ScriptDir\setup_ado.py" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Or manually create .claude/pr-review.json in your project root:" -ForegroundColor Cyan
    Write-Host @"
   {
     "organization": "your-org",
     "project": "your-project",
     "repository": "your-repo"
   }
"@ -ForegroundColor Gray
    Write-Host ""
    Write-Info "Token configuration:"
    Write-Host "  Set environment variable: `$env:AZURE_DEVOPS_PAT = 'your-token'" -ForegroundColor Blue
    Write-Host "  Or run: python scripts/token_manager.py --save" -ForegroundColor Blue
    Write-Host ""
}

function Test-Installation {
    $targetFile = Join-Path $CommandsDir "pr-review.md"

    Write-Info "Verifying installation..."

    if (Test-Path $targetFile) {
        Write-Success "Command file exists: $targetFile"

        # Check if file is readable
        try {
            $null = Get-Content $targetFile -TotalCount 1
            Write-Success "Command file is readable"
        }
        catch {
            Write-ErrorMessage "Command file is not readable: $_"
            return $false
        }

        return $true
    }
    else {
        Write-ErrorMessage "Command file not found after installation"
        return $false
    }
}

function Write-NextSteps {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  Installation Complete! 🎉" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "1. Navigate to your project and run the appropriate setup wizard:" -ForegroundColor Yellow
    Write-Host "   cd your-project" -ForegroundColor Blue
    Write-Host "   # For GitHub:" -ForegroundColor Blue
    Write-Host "   python $ScriptDir\setup_github.py" -ForegroundColor Blue
    Write-Host "   # For Azure DevOps:" -ForegroundColor Blue
    Write-Host "   python $ScriptDir\setup_ado.py" -ForegroundColor Blue
    Write-Host "   (Creates .claude/pr-review.json in your project)"
    Write-Host ""
    Write-Host "2. Set up Python environment (if not already done):"
    Write-Host "   cd $PluginDir\scripts" -ForegroundColor Blue
    Write-Host "   python -m venv venv" -ForegroundColor Blue
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Blue
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Blue
    Write-Host ""
    Write-Host "3. Configure Azure DevOps PAT:"
    Write-Host "   Copy .env.example to .env and add your PAT token"
    Write-Host "   Create PAT at: https://dev.azure.com/`{org`}/_usersSettings/tokens"
    Write-Host ""
    Write-Host "4. Start or restart Claude Code:"
    Write-Host "   claude" -ForegroundColor Blue
    Write-Host ""
    Write-Host "5. Verify the command is available:"
    Write-Host "   /pr-review --help" -ForegroundColor Blue
    Write-Host ""
    Write-Host "6. Try it on a test PR:"
    Write-Host "   /pr-review 12345" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Documentation:"
    Write-Host "  📖 Usage examples: $PluginDir\docs\EXAMPLES.md"
    Write-Host "  🔧 Customization: $PluginDir\docs\CUSTOMIZATION.md"
    Write-Host "  📥 Installation: $PluginDir\docs\INSTALLATION.md"
    Write-Host ""
}

# Main installation flow
function Start-Installation {
    Write-Header

    if ($Help) {
        Show-Help
        exit 0
    }

    try {
        Test-Prerequisites
        New-CommandsDirectory
        Test-ExistingInstallation
        Install-Command

        # Run setup wizard instead of manual config
        Invoke-SetupWizard

        if (Test-Installation) {
            Write-NextSteps
            exit 0
        }
        else {
            Write-ErrorMessage "Installation verification failed"
            exit 1
        }
    }
    catch {
        Write-ErrorMessage "Installation failed: $_"
        Write-Host $_.ScriptStackTrace
        exit 1
    }
}

# Run installation
Start-Installation
