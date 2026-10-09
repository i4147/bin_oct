#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt for an AI coding agent to generate a Python script with the following purpose and behavior:

Theility designed to runux (Android) environment, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`.

**Purpose**: Recursively scan a directory tree for Python (`.py`) files and automatically detect and fix invalid/unnecessary backslash escape sequences inside string literals, converting problematic strings into raw strings (or otherwise correcting them) where safe to order to eWarning` issape sequences.

**k the directory tree using something like `Path.rglob("*.py")` to find all Python files, skipping anything that isn't a regular file).
- The raw bytes of each Python source file read from disk.

**Main outputs**:
- Modified Python source files written back to disk (in place) when invalid escape sequences are found and can be safely fixed.
- Some indication (return value/flag) of whether a given file was changed, so the script can report or track which files were modified.

**Not` module to tokenize the source bvia on a `ioream) rather than relying on naive regex replacement across the whole file, so thatRING tokens are analokenError` gracefully by returning the original bytes unchanged and a "not changed" flag if tokenization fails.
3. For each STRING token, use a regular expression to parse out the string's prefix (e.g., combinations of `r`, `R`, `u`, `U`, `b`, `B`, `f`, `F`), the quote style (handling both single/double and triple quotes), and the inner content.
4. Skip any/`R` prefix (raw strings), since escpreted and Define a set of "valid" esc Python recognizes (e.g., `n`, `slash, single/double quotex`, `u`, `U`, `N`, octal digits ` continuation newline/carriage return).
6. Scan theslash-escape occattern like `\\\\.`) and classify each asid or invalid based on the character following the backslash.
7. If a string contains invalid escape sequences:
   - Mark the file as changed.
   - If the string contains no valid escape sequences at all and is not an f-string, convert it to a raw string by adding an `r`/`R` prefix (matching case convention with existing prefix, e.g., uppercase prefix if original prefix was uppercase).
   - Otherwise (mixed valid and invalid escapes, or f-strings where raw conversion isn't straightforward), apply an appropriate alternative fix (such as escaping the problematic backslashes properly) instead of blindly converting to a raw string, since f-strings and mixed-escape strings can't simply be prefixed with `r`.
8. Reconstruct the file from the (possibly modified) tokens, preserving formatting as much as possible, and only write the file back if actual changes were made.
9. Use `ast` for validating that the resulting modafter the fix (to avoid corrupting files runLI tool (using importing only standard library modules:`, `tokenize`, and `pathlib.ing this escing tic described above, including the `get_python_files` generator function and the `fix_source_code` function that returns a tuple of `(possibly_modified_bytes, changed_flag)`.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/Va4xBt5bbWsmKax2Lhkhzv"""

from __future__ import annotations
import ast
import io
from pathlib import Path
import re
import sys
import tokenize


def get_python_files(root_dir: Path):
    for path in root_dir.rglob("*.py"):
        if path.is_file():
            yield path


def fix_source_code(source_bytes: bytes) -> tuple[bytes, bool]:
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(source_bytes).readline))
    except tokenize.TokenError:
        return source_bytes, False

    out_tokens = []
    changed = False

    string_pattern = re.compile(r'^([rRuUbBfF]*)([\'"]{1,3})(.*)(\2)$', re.DOTALL)

    valid_escape_chars = set("nrtbfva\\'\"xuUN01234567\n\r")

    for tok in tokens:
        if tok.type == tokenize.STRING:
            m = string_pattern.match(tok.string)
            if m:
                prefix, quote, content, end_quote = m.groups()

                if "r" in prefix.lower():
                    out_tokens.append(tok)
                    continue

                has_valid_escape = False
                has_invalid_escape = False

                for escape_match in re.finditer(r"\\.", content):
                    char = escape_match.group()[1]
                    if char in valid_escape_chars:
                        has_valid_escape = True
                    else:
                        has_invalid_escape = True

                if has_invalid_escape:
                    changed = True

                    if not has_valid_escape and "f" not in prefix.lower():
                        new_prefix = prefix + ("R" if prefix.isupper() else "r")
                        new_string = new_prefix + quote + content + end_quote

                    else:

                        def replacer(match):
                            char = match.group(1)
                            if char in valid_escape_chars:
                                return match.group(0)
                            return "\\\\" + char

                        new_content = re.sub(r"\\(.)", replacer, content)
                        new_string = prefix + quote + new_content + end_quote

                    out_tokens.append(tokenize.TokenInfo(tok.type, new_string, tok.start, tok.end, tok.line))
                    continue

        out_tokens.append(tok)

    if changed:
        new_source = tokenize.untokenize(out_tokens)
        return new_source, True

    return source_bytes, False


def main():
    root = Path.cwd()
    print(f"Scanning for Python files in: {root}")

    changed_files = []
    error_files = []

    for py_file in get_python_files(root):
        try:
            original_bytes = py_file.read_bytes()
            new_bytes, changed = fix_source_code(original_bytes)

            if changed:
                try:
                    ast.parse(new_bytes)
                except SyntaxError as e:
                    rel_path = py_file.relative_to(root)
                    print(f"⚠️  Skipping {rel_path} - Syntax error introduced during fix: {e}")
                    error_files.append(rel_path)
                    continue

                py_file.write_bytes(new_bytes)

                rel_path = py_file.relative_to(root)
                print(f"✅ Fixed: {rel_path}")
                changed_files.append(rel_path)

        except Exception as e:
            rel_path = py_file.relative_to(root)
            print(f"❌ Error processing {rel_path}: {e}")
            error_files.append(rel_path)

    print("\n" + "=" * 40)
    print("Execution Summary")
    print("=" * 40)
    print(f"Successfully fixed: {len(changed_files)} files.")
    if error_files:
        print(f"Encountered errors: {len(error_files)} files.")
        sys.exit(1)


if __name__ == "__main__":
    main()
