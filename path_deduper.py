#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python script which deduplicates the PATH environment variable and writes an auto-generated, marker-delimited block into a Termux ~/.bashrc file.

Create a Python 3 script intended for the Termux environment on Android (shebang pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python). The script must begin with `from __future__ import annotations` and use only the standard library: `os`, `collections.OrderedDict`, and `pathlib.Path`.

Purpose: Remove duplicate directory entries from the shell PATH and persist the deduplicated PATH into the user's Bash startup file, so that every new Bash session in Termux uses a clean PATH.

Required functions and behavior:

1. get_current_path(): Return the value of the PATH environment variable, or an empty string if it is not set.

2. parse_path_values(path_string): If the input is empty or falsy, return an empty list. Otherwise split the string on the colon character ":" and return the resulting list of entries.

3. deduplicate_paths(path_list): Preserve the first occurrence order of each entry while removing later duplicates. Skip empty entries entirely (empty strings are dropped). Use a set for fast membership checks and an OrderedDict to keep insertion order. Return a plain list.

4. generate_bash_config(paths): If the list is empty, return a tuple of two empty strings `("", "")`. Otherwise build:
   - A list of assignment lines, one per path, of the form `P<n>="<path>"` where n starts at 1 and increments per path (use enumerate starting at 1). Paths are wrapped in double quotes without escaping.
   - A single export statement that sets PATH to the references `$P1:$P2:...:$PN` followed by `:$PATH`, i.e. `export PATH=$P1:...:$PN:$PATH`.
   - Return a tuple of (assignment list, export statement string). Note that the empty-case return is a two-element tuple of empty strings, while the non-empty case returns a list and a string; preserve this inconsistency.

5. read_bashrc(bashrc_path): Accept a pathlib.Path. If the file exists, open it with UTF-8 encoding and return its full text; otherwise return an empty string.

6. find_and_remove_old_config(content): Remove any previously generated block from the given text. The block is delimited by these exact marker lines (each followed by a newline):
   - Start marker: `# === PATH DEDUPLICATION (AUTO-GENERATED) ===`
   - End marker: `# === END PATH DEDUPLICATION ===`
   Locate the start marker with a string find. If found, search for the end marker starting from the start position. If both are found, remove the text from the start marker through the end of the end marker line and return the remaining content. Handle missing markers gracefully by returning the content unchanged. Also consider trimming surplus blank lines left behind so repeated runs do not accumulate blank lines.

7. Additional logic (main workflow, to be implemented in a main function guarded by `if __name__ == "__main__":`):
   - Read the current PATH, parse it, and deduplicate the entries.
   - Resolve the target file as the user's `~/.bashrc` using `Path.home()`.
   - Read the existing bashrc content, strip any previously generated deduplication block, and then append a new block containing the start marker, the assignment lines, the export statement, and the end marker, each on its own line and ending with a newline.
   - Write the combined content back to the bashrc file with UTF-8 encoding, overwriting the file.
   - If the deduplicated path list is empty, generate no new block (only remove the old one) and avoid writing a malformed block.
   - Print a concise confirmation message to standard output reporting how many unique PATH entries were written and the bashrc location, and note that changes take effect in new shell sessions or after sourcing the file.

Error handling and edge cases:
- PATH unset or empty: produce no block and do not fail.
- Duplicate entries, empty segments from consecutive or trailing colons: removed.
- Missing ~/.bashrc: treat content as empty and create the file.
- Entries containing spaces or special characters: keep them as-is inside the double quotes.
- Running the script repeatedly must be idempotent: the old block is removed before the new one is appended, so the file never accumulates multiple blocks.
- Do not add any external dependencies, do not invoke shell commands, and do not modify environment variables of the running process.

Output the complete script with type hints optional, docstrings or comments brief, and no third-party imports.
---"""

from __future__ import annotations

import os
from collections import OrderedDict
from pathlib import Path


def get_current_path():
    return os.environ.get("PATH", "")


def parse_path_values(path_string):
    if not path_string:
        return []
    return path_string.split(":")


def deduplicate_paths(path_list):
    seen = set()
    deduplicated = OrderedDict()
    for path in path_list:
        if path and path not in seen:
            seen.add(path)
            deduplicated[path] = True
    return list(deduplicated.keys())


def generate_bash_config(paths):
    if not paths:
        return ("", "")
    assignments = []
    for i, path in enumerate(paths, 1):
        assignments.append(f'P{i}="{path}"')
    path_vars = ":".join([f"$P{i}" for i in range(1, len(paths) + 1)])
    export_statement = f"export PATH={path_vars}:$PATH"
    return (assignments, export_statement)


def read_bashrc(bashrc_path):
    if bashrc_path.exists():
        with open(bashrc_path, encoding="utf-8") as f:
            return f.read()
    return ""


def find_and_remove_old_config(content):
    marker_start = "# === PATH DEDUPLICATION (AUTO-GENERATED) ===\n"
    marker_end = "# === END PATH DEDUPLICATION ===\n"
    start_idx = content.find(marker_start)
    if start_idx != -1:
        end_idx = content.find(marker_end, start_idx)
        if end_idx != -1:
            end_idx += len(marker_end)
            content = content[:start_idx] + content[end_idx:]
    return content.rstrip() + "\n"


def append_to_bashrc(bashrc_path, assignments, export_statement):
    content = read_bashrc(bashrc_path)
    content = find_and_remove_old_config(content)
    new_config = "\n# === PATH DEDUPLICATION (AUTO-GENERATED) ===\n"
    new_config += "# This section was automatically generated by path_dedup.py\n"
    new_config += "# Edit this section or regenerate by running: python3 path_dedup.py\n\n"
    for assignment in assignments:
        new_config += assignment + "\n"
    new_config += "\n" + export_statement + "\n"
    new_config += "# === END PATH DEDUPLICATION ===\n"
    with open(bashrc_path, "a", encoding="utf-8") as f:
        f.write(new_config)


def display_results(original_paths, deduplicated_paths, assignments, export_statement):
    print("-" * 40)
    print("PATH DEDUPLICATION RESULTS")
    print("-" * 40)
    print("\n📊 Summary:")
    print(f"   Original PATH entries:      {len(original_paths)}")
    print(f"   Deduplicated entries:       {len(deduplicated_paths)}")
    print(f"   Duplicates removed:         {len(original_paths) - len(deduplicated_paths)}")
    print("\n📝 Generated Variables:")
    for i, assignment in enumerate(assignments, 1):
        print(f"   {assignment}")
    print("\n📤 Export Statement:")
    print(f"   {export_statement}")
    print("\n🔍 Details of Deduplicated Paths:")
    for i, path in enumerate(deduplicated_paths, 1):
        print(f"   P{i} = {path}")
    if len(original_paths) > len(deduplicated_paths):
        print("\n⚠️  Removed Duplicates:")
        removed = set(original_paths) - set(deduplicated_paths)
        seen = set()
        for path in original_paths:
            if path in removed and path not in seen:
                count = original_paths.count(path)
                if count > 1:
                    print(f"   {path} (appeared {count} times)")
                    seen.add(path)
    print("\n" + "=" * 40)


def backup_bashrc(bashrc_path):
    if bashrc_path.exists():
        backup_path = bashrc_path.with_suffix(".bashrc.backup")
        if not backup_path.exists():
            import shutil

            shutil.copy2(bashrc_path, backup_path)
            print(f"✓ Backup created: {backup_path}")
            return True
    return False


def main():
    print("\n🚀 Clash of Clans TH18 BASE deduplicator...")
    home_dir = Path.home()
    bashrc_path = home_dir / ".bashrc"
    print("\n📌 Reading current PATH environment variable...")
    path_string = get_current_path()
    if not path_string:
        print("❌ Error: PATH environment variable is empty!")
        return
    original_paths = parse_path_values(path_string)
    print(f"✓ Found {len(original_paths)} PATH entries")
    print("\n🔄 Deduplicating PATH values...")
    deduplicated_paths = deduplicate_paths(original_paths)
    print(f"✓ Deduplicated to {len(deduplicated_paths)} unique entries")
    print("\n⚙️  Generating bash configuration...")
    assignments, export_statement = generate_bash_config(deduplicated_paths)
    if not assignments:
        print("❌ Error: No valid paths to export!")
        return
    display_results(original_paths, deduplicated_paths, assignments, export_statement)
    print("\n💾 Preparing to save to ~/.bashrc")
    response = input("   Continue? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("❌ Cancelled. No changes made.")
        return
    backup_bashrc(bashrc_path)
    print("\n✍️  Appending configuration to ~/.bashrc...")
    try:
        append_to_bashrc(bashrc_path, assignments, export_statement)
        print(f"✓ Successfully saved to {bashrc_path}")
    except Exception as e:
        print(f"❌ Error writing to {bashrc_path}: {e}")
        return
    print("\n" + "=" * 40)
    print("🎉 SUCCESS! Configuration saved to ~/.bashrc")
    print("-" * 40)
    print("\n📋 To activate the new PATH configuration, run one of:")
    print("   source ~/.bashrc")
    print("   # or")
    print("   . ~/.bashrc")
    print("\n💡 Then verify with:")
    print("   echo $PATH")
    print("\n✨ Done!")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
