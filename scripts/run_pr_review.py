#!/usr/bin/env python3
"""
PR Review Wrapper Script

Simplifies running the PR comment fetcher by automatically reading
configuration and handling all the complexity.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def find_config_file():
    """Locate the ado-config.json file."""
    # Try home directory first
    home = Path.home()
    config_path = home / ".claude" / "ado-config.json"

    if config_path.exists():
        return config_path

    return None


def load_config(config_path):
    """Load and validate configuration."""
    try:
        # Try utf-8-sig first to handle BOM, fallback to utf-8
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
        except:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Validate required fields
        required = ['organization', 'project', 'repository', 'scriptPath', 'pythonPath', 'token']
        missing = [field for field in required if field not in config or not config[field]]

        if missing:
            print(f"ERROR: Missing required fields in config: {', '.join(missing)}", file=sys.stderr)
            return None

        # Validate token
        token = config['token']
        if len(token) < 20:
            print("ERROR: Token appears invalid (too short)", file=sys.stderr)
            return None

        if token in ['YOUR_AZURE_DEVOPS_PAT_HERE', 'PLACEHOLDER_TOKEN_NEEDS_TO_BE_SET']:
            print("ERROR: Please set a valid PAT token in ~/.claude/ado-config.json", file=sys.stderr)
            return None

        # Validate paths exist
        if not Path(config['pythonPath']).exists():
            print(f"ERROR: Python not found at: {config['pythonPath']}", file=sys.stderr)
            return None

        if not Path(config['scriptPath']).exists():
            print(f"ERROR: Script not found at: {config['scriptPath']}", file=sys.stderr)
            return None

        return config

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Failed to read config: {e}", file=sys.stderr)
        return None


def run_fetch_script(config, pr_number, output_file):
    """Execute the fetch_pr_comments.py script."""
    cmd = [
        config['pythonPath'],
        config['scriptPath'],
        '--org', config['organization'],
        '--project', config['project'],
        '--repo', config['repository'],
        '--pr', str(pr_number),
        '--token', config['token'],
        '--output', str(output_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"ERROR: Script failed with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False

        # Print any output from the script
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return True

    except subprocess.TimeoutExpired:
        print("ERROR: Script timed out after 60 seconds", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Failed to execute script: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='PR Review Wrapper - Fetches Azure DevOps PR comments'
    )
    parser.add_argument('pr_number', type=int, help='Pull request number')
    parser.add_argument('--output', '-o', help='Output file path (default: pr-{NUMBER}-comments.md in current directory)')
    parser.add_argument('--config', help='Path to config file (default: ~/.claude/ado-config.json)')

    args = parser.parse_args()

    # Find config file
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = find_config_file()

    if not config_path or not config_path.exists():
        print("ERROR: Configuration file not found at ~/.claude/ado-config.json", file=sys.stderr)
        print("\nPlease create the file with:", file=sys.stderr)
        print('{', file=sys.stderr)
        print('  "organization": "your-org",', file=sys.stderr)
        print('  "project": "your-project",', file=sys.stderr)
        print('  "repository": "your-repo",', file=sys.stderr)
        print('  "scriptPath": "path/to/fetch_pr_comments.py",', file=sys.stderr)
        print('  "pythonPath": "path/to/python",', file=sys.stderr)
        print('  "token": "your-azure-devops-pat"', file=sys.stderr)
        print('}', file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Loading configuration from {config_path}", file=sys.stderr)
    config = load_config(config_path)

    if not config:
        sys.exit(1)

    print("[SUCCESS] Configuration validated", file=sys.stderr)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path.cwd() / f"pr-{args.pr_number}-comments.md"

    print(f"[INFO] Fetching comments for PR #{args.pr_number}...", file=sys.stderr)

    # Run the fetch script
    success = run_fetch_script(config, args.pr_number, output_file)

    if success:
        print(f"[SUCCESS] Comments saved to: {output_file}", file=sys.stderr)
        print(str(output_file))  # Output the file path to stdout for parsing
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
