#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from collections import defaultdict
import os
from pathlib import Path
import re
import sys


# Base prefix path for Termux environment
PREFIX = "/data/data/com.termux/files"


def get_path_dirs() -> list[str]:
    """
    Extracts, deduplicates, and normalizes directories listed in $PATH,
    preserving original precedence order and ignoring non-existent paths.
    """
    path_env = os.environ.get("PATH", "")
    if not path_env:
        return []

    unique_dirs: list[str] = []
    seen: set[str] = set()

    for raw_dir in path_env.split(":"):
        if not raw_dir:
            continue
        # Normalize directory path (strips duplicate slashes, relative specifiers)
        norm_dir = os.path.normpath(raw_dir)
        if norm_dir not in seen:
            seen.add(norm_dir)
            if os.path.isdir(norm_dir):
                unique_dirs.append(norm_dir)

    return unique_dirs


def get_commands_from_path(
    path_dirs: list[str],
) -> tuple[dict[str, tuple[str, str]], dict[str, list[str]]]:
    """
    Scans PATH directories for executable binaries. Uses os.scandir for high
    performance, avoiding redundant stat calls over Path.iterdir().

    Returns:
        - commands: Dict mapping command_name -> (full_file_path, parent_dir)
                    (Preserves the FIRST location per PATH precedence)
        - duplicates: Dict mapping command_name -> list of dirs containing duplicates
    """
    commands: dict[str, tuple[str, str]] = {}
    duplicate_commands: dict[str, list[str]] = defaultdict(list)

    for dir_path in path_dirs:
        try:
            # os.scandir yields DirEntry objects with cached stat attributes
            with os.scandir(dir_path) as entries:
                for entry in entries:
                    try:
                        # Check file status and execute permission
                        if entry.is_file(follow_symlinks=True) and os.access(entry.path, os.X_OK):
                            cmd_name = entry.name

                            # Respect shell lookup order: retain the FIRST executable found
                            if cmd_name not in commands:
                                commands[cmd_name] = (entry.path, dir_path)

                            duplicate_commands[cmd_name].append(dir_path)
                    except OSError:
                        continue
        except (PermissionError, OSError):
            continue

    path_duplicates = {cmd: paths for cmd, paths in duplicate_commands.items() if len(paths) > 1}
    return commands, path_duplicates


def extract_aliases(aliases_file: Path) -> dict[str, str]:
    """
    Parses alias definitions from the given configuration file.
    Returns a dict mapping alias_name -> raw target string.
    """
    aliases: dict[str, str] = {}
    if not aliases_file.exists():
        return aliases

    # Matches bash alias syntax: alias name=value
    alias_pattern = re.compile(r"^\s*alias\s+([a-zA-Z0-9_.-]+)\s*=\s*(.*)$")

    try:
        content = aliases_file.read_text(encoding="utf-8")
        # Join multiline backslash continuations
        content = re.sub(r"\\\n", "", content)

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = alias_pattern.match(stripped)
            if match:
                name = match.group(1)
                target = match.group(2).strip()
                aliases[name] = target
    except Exception as e:
        print(f"Warning: Could not read aliases file: {e}")

    return aliases


def is_wrapper_alias(alias_name: str, alias_target: str) -> bool:
    r"""
    Determines if an alias is an intentional wrapper for a binary of the same name.
    Examples ignored:
      - alias rg="rg 2>/dev/null"
      - alias ls='ls --color=auto'
      - alias grep='command grep -i'
      - alias cat='\cat -v'
    """
    if not alias_target:
        return False

    # Strip surrounding quotes
    target = alias_target.strip("'\"").strip()

    # Strip leading backslash escape (e.g., \rg)
    if target.startswith("\\"):
        target = target[1:].strip()

    # Strip common shell command invocation bypasses
    for prefix in ("command ", "builtin "):
        if target.startswith(prefix):
            target = target[len(prefix) :].strip()

    # Extract the base command invoked (first token)
    first_word = target.split()[0] if target.split() else ""

    # Normalize target in case full path was supplied (e.g., /usr/bin/rg -> rg)
    first_word = Path(first_word).name

    return first_word == alias_name


def extract_functions(functions_file: Path) -> dict[str, bool]:
    """
    Extracts shell function names using a unified single-pass regex pattern.
    """
    functions: dict[str, bool] = {}
    if not functions_file.exists():
        return functions

    # Combined regex covering standard bash function definitions:
    # 1. func_name() { ... }
    # 2. function func_name { ... }
    # 3. function func_name() { ... }
    func_pattern = re.compile(r"^\s*(?:function\s+([a-zA-Z0-9_.-]+)(?:\s*\(\s*\))?|([a-zA-Z0-9_.-]+)\s*\(\s*\))\s*\{")

    try:
        content = functions_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = func_pattern.match(stripped)
            if match:
                func_name = match.group(1) or match.group(2)
                functions[func_name] = True
    except Exception as e:
        print(f"Warning: Could not read functions file: {e}")

    return functions


def check_alias_conflicts(
    aliases: dict[str, str], path_commands: dict[str, tuple[str, str]]
) -> dict[str, tuple[str, str]]:
    """
    Identifies aliases that override PATH binaries, ignoring intentional wrapper aliases.
    """
    conflicts: dict[str, tuple[str, str]] = {}
    for alias_name, target in aliases.items():
        if alias_name in path_commands:
            # Ignore intentional wrappers like `alias rg="rg 2>/dev/null"`
            if is_wrapper_alias(alias_name, target):
                continue
            conflicts[alias_name] = path_commands[alias_name]
    return conflicts


def check_conflicts(names: dict[str, bool], path_commands: dict[str, tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """
    Identifies shell functions that collide with existing PATH binaries.
    """
    return {name: path_commands[name] for name in names if name in path_commands}


def display_results(
    alias_conflicts: dict[str, tuple[str, str]],
    func_conflicts: dict[str, tuple[str, str]],
    path_duplicates: dict[str, list[str]],
    path_dirs: list[str],
) -> None:
    """Displays formatted CLI output analyzing PATH structure and identified conflicts."""
    print("-" * 40)
    print("🔍 PATH CONFLICT ANALYSIS")
    print("-" * 40)
    print(f"\n📁 PATH directories scanned ({len(path_dirs)}):")
    for i, dir_path in enumerate(path_dirs[:10], 1):
        print(f"    {i}. {dir_path}")
    if len(path_dirs) > 10:
        print(f"    ... and {len(path_dirs) - 10} more")

    if path_duplicates:
        print(f"\n⚠️  WARNING: Commands found in multiple PATH locations ({len(path_duplicates)}):")
        for cmd, paths in sorted(path_duplicates.items())[:10]:
            print(f"    • '\033[5;96m{cmd}\033[0m' found in:")
            for path in paths:
                print(f"      - {str(path).replace(PREFIX, '')}")
        if len(path_duplicates) > 10:
            print(f"    ... and {len(path_duplicates) - 10} more")
    else:
        print("\n✓ No duplicate commands across PATH directories")

    alias_total = len(alias_conflicts)
    func_total = len(func_conflicts)

    print(f"\n📋 ALIASES ({alias_total} conflict(s))")
    if alias_conflicts:
        print(f"    ❌ Conflicts with PATH commands ({alias_total}):")
        for alias, (full_path, dir_path) in sorted(alias_conflicts.items()):
            print(f"       • '\033[5;96m{alias}\033[0m' -> conflicts with: {str(full_path).replace(PREFIX, '')}")
        print("\n    💡 Suggestion: Rename these aliases or remove the conflicting binaries")
    else:
        print("    ✓ No conflicts with PATH commands")

    print(f"\n🔧 FUNCTIONS ({func_total} conflict(s))")
    if func_conflicts:
        print(f"    ❌ Conflicts with PATH commands ({func_total}):")
        for func, (full_path, dir_path) in sorted(func_conflicts.items()):
            print(f"       • '{func}' -> conflicts with: {full_path}")
        print("\n    💡 Suggestion: Rename these functions or use 'command' prefix")
    else:
        print("    ✓ No conflicts with PATH commands")

    total_conflicts = alias_total + func_total
    print("\n" + "=" * 40)
    print(f"📊 SUMMARY: {total_conflicts} total conflict(s) found")
    if total_conflicts > 0:
        print("\n⚠️  Conflicts can cause unexpected behavior!")
        print("    Bash will use aliases/functions over PATH binaries")
        print("    To use the binary instead, prefix with 'command' or '\\'")
        print("    Example: command ls  or  \\ls")
    print("-" * 40)


def suggest_fixes(
    alias_conflicts: dict[str, tuple[str, str]],
    func_conflicts: dict[str, tuple[str, str]],
) -> None:
    """Prints remediation suggestions when --verbose or -v flag is active."""
    if not alias_conflicts and not func_conflicts:
        return
    print("\n🔧 SUGGESTED FIXES:")
    print("-" * 40)
    if alias_conflicts:
        print("\nFor alias conflicts:")
        for conflict in sorted(alias_conflicts.keys())[:5]:
            print(f"    • Rename alias: alias {conflict}_alias='...'")
            print(f"    • Or use in scripts: \\{conflict} (escapes alias)")
    if func_conflicts:
        print("\nFor function conflicts:")
        for conflict in sorted(func_conflicts.keys())[:5]:
            print(f"    • Rename function: {conflict}_func() {{ ... }}")
            print(f"    • Or use in scripts: command {conflict}")
    print("\nTo see all conflicts in detail, run with --verbose flag")


def main() -> None:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    config_dir = Path.home() / ".config/bash.d"
    aliases_file = config_dir / "aliases.sh"
    functions_file = config_dir / "functions.sh"

    print("🔍 Scanning for conflicts between bash aliases/functions and PATH binaries...")

    path_dirs = get_path_dirs()
    path_commands, path_duplicates = get_commands_from_path(path_dirs)

    print(f"✓ Found {len(path_commands)} unique commands in PATH")
    print(f"✓ Found {len(path_duplicates)} commands with duplicates across PATH")

    aliases = extract_aliases(aliases_file)
    functions = extract_functions(functions_file)

    print(f"✓ Loaded {len(aliases)} aliases")
    print(f"✓ Loaded {len(functions)} functions")

    # Conflict analysis
    alias_conflicts = check_alias_conflicts(aliases, path_commands)
    func_conflicts = check_conflicts(functions, path_commands)

    display_results(alias_conflicts, func_conflicts, path_duplicates, path_dirs)

    if verbose:
        suggest_fixes(alias_conflicts, func_conflicts)

    if alias_conflicts or func_conflicts:
        sys.exit(1)

    print("\n✅ No conflicts detected! Your aliases and functions are safe.")
    sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
