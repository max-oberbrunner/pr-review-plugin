#!/usr/bin/env python3
"""
Command Runner Script

Orchestrates command execution for PR review:
- Loads commands configuration from pr-review.json
- Discovers command files in target project's .claude/commands/
- Filters changed files by filePatterns for each command
- Returns structured list of commands to execute with their target files
"""

import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


def load_commands_config(config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load and validate the commands section from pr-review.json.

    Args:
        config_path: Path to pr-review.json

    Returns:
        Commands configuration dict or None if not configured/disabled
    """
    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[ERROR] Failed to load config: {e}", file=sys.stderr)
        return None

    commands_config = config.get("commands")
    if not commands_config:
        return None

    # Check if enabled
    if not commands_config.get("enabled", False):
        return None

    # Validate include list exists
    if not commands_config.get("include"):
        print("[WARNING] commands.include is empty, no commands to run", file=sys.stderr)
        return None

    # Set defaults
    commands_config.setdefault("filePatterns", {})
    commands_config.setdefault("maxConcurrent", 3)

    return commands_config


def discover_command_files(project_root: Path, include_list: List[str]) -> Dict[str, Path]:
    """
    Find command files in the target project's .claude/commands/ directory.

    Args:
        project_root: Root of the project being reviewed
        include_list: List of command filenames to look for

    Returns:
        Dict mapping command name to full path for found commands
    """
    commands_dir = project_root / ".claude" / "commands"

    if not commands_dir.exists():
        print(f"[WARNING] Commands directory not found: {commands_dir}", file=sys.stderr)
        return {}

    found_commands = {}

    for command_name in include_list:
        # Support both with and without .md extension
        if not command_name.endswith(".md"):
            command_name = f"{command_name}.md"

        command_path = commands_dir / command_name

        if command_path.exists():
            found_commands[command_name] = command_path
        else:
            print(f"[WARNING] Command file not found: {command_path}", file=sys.stderr)

    return found_commands


def match_glob_pattern(filepath: str, pattern: str) -> bool:
    """
    Check if a filepath matches a glob pattern.

    Supports:
    - * matches any single path component
    - ** matches zero or more path components
    - ? matches single character
    - [...] matches character class
    """
    # Normalize path separators
    filepath = filepath.replace("\\", "/")
    pattern = pattern.replace("\\", "/")

    # Handle ** (double star) for recursive matching
    if "**" in pattern:
        # Split pattern on **
        parts = pattern.split("**")

        if len(parts) == 2:
            prefix, suffix = parts
            prefix = prefix.rstrip("/")
            suffix = suffix.lstrip("/")

            # File must match prefix (if any) and suffix (if any)
            if prefix and not filepath.startswith(prefix.rstrip("*")):
                # Check if the prefix pattern matches start of path
                prefix_pattern = prefix.rstrip("/")
                if prefix_pattern and not fnmatch.fnmatch(filepath.split("/")[0] if "/" in filepath else filepath, prefix_pattern.split("/")[0] if "/" in prefix_pattern else prefix_pattern):
                    if not filepath.startswith(prefix_pattern.replace("*", "")):
                        pass  # May still match

            if suffix:
                # The suffix must match the end of the filepath
                return fnmatch.fnmatch(filepath, f"*{suffix}") or fnmatch.fnmatch(filepath.split("/")[-1], suffix.lstrip("/"))

            return True

    # Simple glob matching
    return fnmatch.fnmatch(filepath, pattern)


def filter_files_for_command(
    changed_files: List[Dict],
    patterns: Optional[List[str]]
) -> List[str]:
    """
    Filter changed files by glob patterns for a specific command.

    Args:
        changed_files: List of changed file dicts (with 'path' key)
        patterns: List of glob patterns (e.g., ["**/*.cs", "**/*.ts"])
                 If None or empty, returns all files

    Returns:
        List of file paths that match the patterns
    """
    # Extract paths from changed files, excluding deleted files
    file_paths = [
        f["path"] for f in changed_files
        if f.get("changeType") != "deleted"
    ]

    if not patterns:
        # No patterns means all files
        return file_paths

    matched_files = []

    for filepath in file_paths:
        for pattern in patterns:
            if match_glob_pattern(filepath, pattern):
                matched_files.append(filepath)
                break  # Don't add same file twice

    return matched_files


def prepare_command_executions(
    commands_config: Dict[str, Any],
    command_files: Dict[str, Path],
    changed_files: List[Dict]
) -> List[Dict[str, Any]]:
    """
    Build execution list for all commands.

    Args:
        commands_config: The commands configuration from pr-review.json
        command_files: Dict mapping command name to path
        changed_files: List of changed file dicts from fetch_changed_files

    Returns:
        List of execution dicts with:
        - name: command filename
        - path: full path to command file
        - files: list of files to analyze
        - patterns: patterns used (for logging)
    """
    executions = []
    file_patterns = commands_config.get("filePatterns", {})

    for command_name, command_path in command_files.items():
        # Get patterns for this command (if any)
        patterns = file_patterns.get(command_name)

        # Filter files
        matched_files = filter_files_for_command(changed_files, patterns)

        if not matched_files:
            print(f"[INFO] Skipping {command_name}: no matching files", file=sys.stderr)
            continue

        executions.append({
            "name": command_name,
            "path": str(command_path),
            "files": matched_files,
            "fileCount": len(matched_files),
            "patterns": patterns or ["*"]
        })

    return executions


def read_command_content(command_path: Path) -> Optional[str]:
    """Read the content of a command file."""
    try:
        with open(command_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        print(f"[ERROR] Failed to read command file {command_path}: {e}", file=sys.stderr)
        return None


def find_project_root() -> Optional[Path]:
    """Find the project root by searching upward for a .git folder."""
    current = Path.cwd()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    if (current / ".git").exists():
        return current

    return None


def main():
    """
    Main entry point for command runner.

    Usage:
        python command_runner.py --changed-files <json_file_or_json_string>
        python command_runner.py --pr 12345  # Will call fetch_changed_files

    Outputs JSON with commands to execute.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Prepare commands for PR review"
    )
    parser.add_argument("--config", help="Path to pr-review.json")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--changed-files", help="JSON file or string with changed files")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    # Find project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = find_project_root()

    if not project_root:
        print("[ERROR] Could not find project root (no .git directory)", file=sys.stderr)
        sys.exit(1)

    # Load config
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = project_root / ".claude" / "pr-review.json"

    commands_config = load_commands_config(config_path)

    if not commands_config:
        # Commands not enabled or configured
        output = {
            "enabled": False,
            "reason": "Commands not enabled or not configured",
            "commands": []
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Load changed files
    if not args.changed_files:
        print("[ERROR] --changed-files is required", file=sys.stderr)
        sys.exit(1)

    # Try to parse as JSON string first, then as file path
    changed_files_data = None
    if args.changed_files.startswith("{") or args.changed_files.startswith("["):
        try:
            changed_files_data = json.loads(args.changed_files)
        except json.JSONDecodeError:
            pass

    if changed_files_data is None:
        # Try as file path
        changed_files_path = Path(args.changed_files)
        if changed_files_path.exists():
            with open(changed_files_path, 'r', encoding='utf-8') as f:
                changed_files_data = json.load(f)
        else:
            print(f"[ERROR] Changed files not found: {args.changed_files}", file=sys.stderr)
            sys.exit(1)

    # Extract files list
    if isinstance(changed_files_data, dict):
        changed_files = changed_files_data.get("files", [])
    else:
        changed_files = changed_files_data

    if args.debug:
        print(f"[DEBUG] Loaded {len(changed_files)} changed files", file=sys.stderr)

    # Discover command files
    include_list = commands_config.get("include", [])
    command_files = discover_command_files(project_root, include_list)

    if not command_files:
        output = {
            "enabled": True,
            "reason": "No command files found",
            "commands": [],
            "searched": include_list
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Prepare executions
    executions = prepare_command_executions(commands_config, command_files, changed_files)

    # Build output
    output = {
        "enabled": True,
        "projectRoot": str(project_root),
        "maxConcurrent": commands_config.get("maxConcurrent", 3),
        "totalCommands": len(executions),
        "totalFiles": sum(e["fileCount"] for e in executions),
        "commands": executions
    }

    json_output = json.dumps(output, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"[SUCCESS] Command execution plan saved to {args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
