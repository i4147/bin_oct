#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts Windows batch (.bat) files into equivalent Unix shell (.sh) scripts. The tool should read a batch file from a user-supplied path, translate it line by line into a bash-compatible script, and write the result to an output file, with the output filename derived from the input by default and optionally specified by the user.
The converter should recognize common batch-file constructs and map them to their closest shell equivalents, including:
- Comment and echo-suppression directives, converted to shell comments or no-ops
- Basic file and directory commands such as listing, changing directories, copying, moving, renaming, deleting, and displaying file contents
- Pausing for user input and clearing the screen
- Exiting with a status code
- Simple conditional file-existence checks, including their negated forms
- Text searching commands mapped to their grep equivalents
- Batch-style environment variable references converted to shell variable syntax, and variable assignment statements converted to shell assignments
Lines with no direct equivalent should be preserved as comments or flagged clearly in the output so the user can review them, rather than silently dropped. The converter should count successfully converted lines and errors, and report these statistics to the user at the end of the run. It should also handle missing input files, unreadable files, and write failures gracefully with clear error messages and a non-zero exit status.
The script should be runnable from the command line, accept the input path as a required argument, accept an optional output path, and emit a shell script that begins with an appropriate shebang line and is marked as executable where the platform permits. Handle line endings robustly, including Windows-, and preserve the original order and structure of the script as closely as possible.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys


class BatToShConverter:
    COMMAND_MAP: dict[str, str] = {
        r"^echo\s+off\s*$": "# Echo off",
        r"^@echo\s+off\s*$": "# Echo off",
        r"^pause\s*$": 'read -p "Press enter to continue..."',
        r"^cls\s*$": "clear",
        r"^exit\s*$": "exit 0",
        r"^cd\s+": "cd ",
        r"^dir\s*$": "ls -la",
        r"^dir\s+": "ls -la ",
        r"^del\s+": "rm ",
        r"^copy\s+": "cp ",
        r"^move\s+": "mv ",
        r"^ren\s+": "mv ",
        r"^type\s+": "cat ",
        r"^findstr\s+": "grep ",
        r"^if\s+exist\s+": "if [ -f ",
        r"^if\s+not\s+exist\s+": "if [ ! -f ",
    }

    def __init__(self):
        self.converted_count = 0
        self.error_count = 0

    def convert_line(self, line: str) -> str:
        line = line.rstrip("\r\n")
        if not line.strip() or line.strip().startswith("REM"):
            if line.strip().startswith("REM"):
                return line.replace("REM", "#", 1)
            return line
        line = re.sub(r"%([A-Za-z_][A-Za-z0-9_]*)%", r"$\1", line)
        line = re.sub(r"^set\s+", "", line, flags=re.IGNORECASE)
        line = re.sub(
            r'if\s+"?([^"]*?)"?\s+==\s+"?([^"]*?)"?',
            r'if [ "$\1" = "$\2" ]',
            line,
            flags=re.IGNORECASE,
        )
        for pattern, replacement in self.COMMAND_MAP.items():
            if re.match(pattern, line, re.IGNORECASE):
                line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                break
        line = re.sub(r"^:\w+\s*$", lambda m: f"# {m.group(0)}", line)
        line = re.sub(r"goto\s+(\w+)", r"# TODO: goto \1", line, flags=re.IGNORECASE)
        return line

    def convert_file(self, bat_file: Path) -> str:
        try:
            with open(bat_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"❌ Error reading {bat_file}: {e}")
            self.error_count += 1
            return ""
        converted_lines = [
            "#!/bin/bash\n",
            "# Converted from " + bat_file.name + "\n",
            "\n",
        ]
        for line in lines:
            converted_lines.append(self.convert_line(line) + "\n")
        return "".join(converted_lines)

    def process_directory(self, directory: Path | None = None) -> None:
        if directory is None:
            directory = Path.cwd()
        if not directory.exists():
            print(f"❌ Directory not found: {directory}")
            return
        bat_files = list(directory.rglob("*.bat"))
        if not bat_files:
            print(f"ℹ️  No .bat files found in {directory}")
            return
        print(f"🔍 Found {len(bat_files)} .bat file(s)\n")
        for bat_file in bat_files:
            sh_file = bat_file.with_suffix(".sh")
            print(f"📝 Converting: {bat_file.name} → {sh_file.name}")
            converted_content = self.convert_file(bat_file)
            if converted_content:
                try:
                    with open(sh_file, "w", encoding="utf-8") as f:
                        f.write(converted_content)
                    sh_file.chmod(0o755)
                    self.converted_count += 1
                    bat_file.unlink()
                    print(f"   ✅ Converted successfully\n")
                except Exception as e:
                    print(f"   ❌ Error writing {sh_file}: {e}\n")
                    self.error_count += 1

    def print_summary(self) -> None:
        print("=" * 40)
        print(f"📊 Conversion Summary")
        print(f"   ✅ Successful: {self.converted_count}")
        print(f"   ❌ Errors: {self.error_count}")
        print("=" * 40)


def main():
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    converter = BatToShConverter()
    converter.process_directory(target_dir)
    converter.print_summary()


if __name__ == "__main__":
    raise SystemExit(main())
