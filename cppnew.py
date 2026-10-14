#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line helper for quickly creating a new C++ source file from a standard competitive-programming style template and then opening it in the user's preferred text editor.
The tool should accept a single file path argument (supporting a leading "~" for the home directory). If no argument is provided, it should print a brief usage message and exit with a non-zero status. If the target file already exists, it must refuse to overwrite it, report an error to the standard error stream, and exit with a non-zero status.
When the file does not exist, the tool should create it pre-filled with a minimal C++ program skeleton that includes a comprehensive standard header, uses the standard namespace, disables C-style I/O synchronization and unties the input stream for fast input/output, contains a clearly marked placeholder comment where the solution code goes, and returns zero from the main function. After creation, it should print a confirmation message stating the file was created with a basic C++ template.
Next, the tool should determine which editor to launch by reading the user's configured editor from the environment, falling back to a common default terminal editor if none is set. It should then open the newly created file in that editor and wait for the editor to close. If the editor executable cannot be found, the tool should report a clear error naming the missing editor and exit with a non-zero status. If the user interrupts the process (e.g., with Ctrl+C), the tool should exit gracefully with the conventional interrupt exit code. Otherwise, the tool should exit with the same status code returned by the editor.
The script should be runnable directly as a standalone program and should propagate its result as the process exit code.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys

TEMPLATE = """\
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // Your code here
    return 0;
}
"""


def cppnew(*args):
    if not args:
        print("Usage: cppnew <filename.cpp>")
        return 1
    file = Path(args[0]).expanduser()
    if file.exists():
        print(f"Error: {file} already exists", file=sys.stderr)
        return 1
    file.write_text(TEMPLATE)
    print(f"Created {file} with basic C++ template")
    editor = (
        subprocess.run(["sh", "-c", 'printf %s "$EDITOR"'], capture_output=True, text=True).stdout.strip() or "nano"
    )
    try:
        return subprocess.run([editor, str(file)]).returncode
    except FileNotFoundError:
        print(f"Error: editor '{editor}' not found", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(cppnew(*sys.argv[1:]))
