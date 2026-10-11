#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which scans files for invalid escape sequences in string literals, optionally auto-fixes them, and reports results. Describe behavior, inputs, outputs, dependencies, logic, error handling, and edge cases, without any code or snippets.

Create a Python 3 command-line tool that scans one or more source files for invalid escape sequences in string literals, reports them, and optionally repairs them in place. The script should be runnable under Termux on Android (use a `#!/data/data/com.termux/files/usr/bin/env python` shebang) and must be a single self-contained file that uses only the standard library.

**Purpose:** Detect and optionally fix "invalid escape sequence" problems in Python source files, such as a string like `"\\d"` or `"\\s"` that Python would otherwise warn about (`DeprecationWarning`/`SyntaxWarning`) and which will become an error in future Python versions. A raw-string or doubled-backslash fix is applied to the offending string literals.

**Command-line interface:** Use `argparse`. Accept:
- One or more positional file paths (or directories, which should be expanded to the `.py` files they contain, if you choose to support that; at minimum accept file paths).
- A flag (for example `--fix`) that enables in-place rewriting. Without it, the script only reports issues and must not modify any file.
- Optionally a flag to choose the number of worker processes; default to a sensible value based on CPU count.

**Parallelism:** Process files concurrently using `multiprocessing` (a process pool). Each worker takes a tuple of (file path string, fix flag) and returns a tuple of (file path string, whether the file was changed, list of human-readable message strings, and an optional replacement/new-content value). The main process collects the results, prints messages, and writes out fixed content when applicable. Make sure the worker function is top-level so it is picklable.

**Per-file logic (in the worker):**
1. Read the file as UTF-8 text. If reading fails, return an error message in red ANSI color (`\\033[91m`) containing the path and exception, reset with `\\033[0m`, and report no change.
2. Compile the source text inside a `warnings.catch_warnings(record=True)` context, with `SyntaxWarning` set to `"always"`. Catch `SyntaxError` (record that a syntax error occurred) and any other exception (ignore it). Determine whether any recorded warning message contains the text "invalid escape sequence".
3. If there was neither an invalid-escape warning nor a syntax error, return that the file is clean, with no messages and no changes.
4. Otherwise, tokenize the source with `tokenize.generate_tokens` over a `io.StringIO` of the text, suppressing `tokenize.TokenError` via `contextlib.suppress` so partial token lists are still usable.
5. Iterate over the tokens. For each `STRING` token, examine the literal text: skip raw strings (prefix containing `r` or `R`), and for non-raw strings find backslash escape sequences that are not valid Python escapes (valid ones include newline continuation, `\\\\`, quotes, `a b f n r t v`, octal digits `0-7`, `x`, `N`, `u`, `U`). Use a regex to locate backslash-plus-character sequences, handling bytes literals (prefix containing `b`/`B`) where `\\N`, `\\u`, `\\U` are not valid escapes.
6. For each invalid escape found, record an issue message (with file path, line and column from the token start, and the offending sequence) in a readable form, colorized in cyan (`\\033[96m`) with reset. When fixing, build a replacement that doubles the backslash (or converts the literal to a raw-string prefix, whichever you choose consistently), and record the replacement with its position.
7. Apply the replacements to the source text (process them from the end of the file toward the start, or otherwise ensure offsets remain valid), and return the new content.

**Writing:** When `--fix` is given and the file changed, write the new content back as UTF-8 in the main process, and print a cyan success line naming the file. When not fixing, print the issues so the user can see them and optionally a hint to rerun with the fix flag. Print a final summary of how many files had issues and how many were fixed.

**Output and exit status:** Print issue lines and errors to standard output or standard error consistently. Exit with status 0 when no issues are found (or all were fixed) and a non-zero status when issues remain unfixed or any file could not be read. Handle `KeyboardInterrupt` gracefully by terminating the pool and exiting with a non-zero status.

**Edge cases to handle:**
- Files that are already clean: skip quickly with no output.
- Files with syntax errors unrelated to escapes: tokenization may fail partway; still process the tokens gathered so far, and do not corrupt the file.
- Multi-line triple-quoted strings: compute line and column correctly from the token's start position.
- f-strings and prefixed strings (`f`, `rb`, `Rb`, `BR`, etc.): handle prefix detection case-insensitively.
- Files that are not valid UTF-8: report as an error for that file only, without stopping the others.
- Empty input list: print usage or a message and exit cleanly.
- Never write to a file unless `--fix` is set and the content actually changed.

**Style:** Use `from __future__ import annotations`, module-level ANSI color constants, concise docstrings or comments only where helpful, and a `main()` function guarded by `if __name__ == "__main__":`. Keep the code readable and idiomatic, with no third-party dependencies.
---"""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import pathlib
import re
import sys
import tokenize
import warnings

RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def check_and_fix_file(args):
    filepath_str, fix = args
    filepath = pathlib.Path(filepath_str)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source_text = f.read()
    except Exception as e:
        return (
            filepath_str,
            False,
            [f"{RED}Error reading {filepath_str}: {e}{RESET}"],
            None,
        )
    has_warning = False
    has_syntax_error = False
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", SyntaxWarning)
        try:
            compile(source_text, str(filepath), "exec")
        except SyntaxError:
            has_syntax_error = True
        except Exception:
            pass
        has_warning = any("invalid escape sequence" in str(warn.message) for warn in w)
    if not has_warning and not has_syntax_error:
        return filepath_str, False, [], None
    with contextlib.suppress(tokenize.TokenError):
        tokens = list(tokenize.generate_tokens(io.StringIO(source_text).readline))
    issues = []
    replacements = []
    for tok in tokens:
        if tok.type == tokenize.STRING:
            with warnings.catch_warnings(record=True) as w2:
                warnings.simplefilter("always", SyntaxWarning)
                with contextlib.suppress(Exception):
                    compile(tok.string, "<string>", "eval")
                if any("invalid escape sequence" in str(warn.message) for warn in w2):
                    m = re.match(r'^([a-zA-Z_]*)(["\'].*)$', tok.string, re.DOTALL)
                    if m:
                        prefix = m.group(1)
                        rest = m.group(2)
                        if "r" not in prefix.lower():
                            prefix = prefix.replace("u", "").replace("U", "")
                            new_string = prefix + "r" + rest
                            replacements.append((
                                tok.start[0],
                                tok.start[1],
                                tok.end[0],
                                tok.end[1],
                                new_string,
                            ))
                            issues.append((tok.start[0], tok.string, new_string))
    if not issues:
        return filepath_str, False, [], None
    lines = source_text.splitlines(keepends=True)
    output = []
    output.append(f"{CYAN}File: {filepath}{RESET}")
    issue_lines = sorted({line_num for line_num, _, _ in issues})
    for lineno in issue_lines:
        idx = lineno - 1
        if idx - 1 >= 0:
            output.append(f"  {idx}: {lines[idx - 1].rstrip('\n')}")
        output.append(f"{RED}> {idx + 1}: {lines[idx].rstrip('\n')}{RESET}")
        if idx + 1 < len(lines):
            output.append(f"  {idx + 2}: {lines[idx + 1].rstrip('\n')}")
        output.append("-" * 40)
    new_content = None
    if fix and replacements:
        replacements.sort(key=lambda x: (x[0], x[1]), reverse=True)
        text_lines = source_text.splitlines(keepends=True)
        for r_start, c_start, r_end, c_end, new_string in replacements:
            r1 = r_start - 1
            r2 = r_end - 1
            if r1 == r2:
                line = text_lines[r1]
                text_lines[r1] = line[:c_start] + new_string + line[c_end:]
            else:
                first_line = text_lines[r1]
                last_line = text_lines[r2]
                text_lines[r1] = first_line[:c_start] + new_string + last_line[c_end:]
                for i in range(r2, r1, -1):
                    del text_lines[i]
        new_content = "".join(text_lines)
    return filepath_str, True, output, new_content


def main():
    parser = argparse.ArgumentParser(
        description="Recursively find and fix 'invalid escape sequence' SyntaxWarnings in Python code."
    )
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="Update inplace in -a mode to fix issues (convert to raw regex)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    args = parser.parse_args()
    base_path = pathlib.Path(args.path)
    if base_path.is_file():
        files = [base_path]
    else:
        files = [
            f
            for f in base_path.rglob("*.py")
            if not any(part.startswith(".") for part in f.parts[:-1])
            and "venv" not in f.parts
            and "__pycache__" not in f.parts
        ]
    if not files:
        print("No Python files found.")
        sys.exit(0)
    tasks = [(str(f), args.apply) for f in files]
    with mp.Pool(8) as pool:
        for filepath_str, has_issues, output_lines, new_content in pool.imap_unordered(check_and_fix_file, tasks):
            if has_issues:
                for line in output_lines:
                    print(line)
                if args.apply and new_content is not None:
                    try:
                        with open(filepath_str, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"{CYAN}Fixed inplace: {filepath_str}{RESET}\n")
                    except Exception as e:
                        print(f"{RED}Failed to write {filepath_str}: {e}{RESET}\n")


if __name__ == "__main__":
    main()
