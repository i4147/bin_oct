#!/data/data/com.termux/files/usr/bin/python3.12
import ast
import io
import re
import sys
import tokenize
from pathlib import Path


def get_python_files(root_dir: Path):
    """
    Generator style file system walker.
    Yields all .py files recursively in the given directory.
    """
    for path in root_dir.rglob("*.py"):
        if path.is_file():
            yield path


def fix_source_code(source_bytes: bytes) -> tuple[bytes, bool]:
    """
    Parses source code into tokens, targets string literals containing invalid
    escape sequences, and appropriately converts them to raw strings or escapes them.
    Returns a tuple of (modified_bytes, is_changed).
    """
    try:
        # We read bytes to let tokenize automatically detect the file's encoding (PEP 263)
        tokens = list(tokenize.tokenize(io.BytesIO(source_bytes).readline))
    except tokenize.TokenError:
        # File has unmatched brackets/quotes, return as unmodified
        return source_bytes, False

    out_tokens = []
    changed = False

    # Regex to split a standard string token into prefix, quotes, content, and closing quotes
    string_pattern = re.compile(r'^([rRuUbBfF]*)([\'"]{1,3})(.*)(\2)$', re.DOTALL)

    # Python valid escape characters in string literals
    valid_escape_chars = set("nrtbfva\\'\"xuUN01234567\n\r")

    for tok in tokens:
        if tok.type == tokenize.STRING:
            m = string_pattern.match(tok.string)
            if m:
                prefix, quote, content, end_quote = m.groups()

                # Skip if already a raw string
                if "r" in prefix.lower():
                    out_tokens.append(tok)
                    continue

                has_valid_escape = False
                has_invalid_escape = False

                # Find all backslash sequences in the string body
                for escape_match in re.finditer(r"\\.", content):
                    char = escape_match.group()[1]
                    if char in valid_escape_chars:
                        has_valid_escape = True
                    else:
                        has_invalid_escape = True

                if has_invalid_escape:
                    changed = True

                    # PREFERENCE: Convert to raw string if there are no valid escapes
                    # that depend on interpretation (like \n, \t). Also skip f-strings
                    # as 'fr' behavior with nested brackets can get messy.
                    if not has_valid_escape and "f" not in prefix.lower():
                        new_prefix = prefix + ("R" if prefix.isupper() else "r")
                        new_string = new_prefix + quote + content + end_quote

                    # FALLBACK: Double-escape only the invalid backslash sequences
                    else:

                        def replacer(match):
                            char = match.group(1)
                            if char in valid_escape_chars:
                                return match.group(0)  # Unchanged
                            return "\\\\" + char  # Double escape

                        new_content = re.sub(r"\\(.)", replacer, content)
                        new_string = prefix + quote + new_content + end_quote

                    # Replace the old token with the safely modified string
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
                # VALIDATION: Ensure we didn't introduce SyntaxErrors
                try:
                    ast.parse(new_bytes)
                except SyntaxError as e:
                    rel_path = py_file.relative_to(root)
                    print(f"⚠️  Skipping {rel_path} - Syntax error introduced during fix: {e}")
                    error_files.append(rel_path)
                    continue

                # Write to file in-place
                py_file.write_bytes(new_bytes)

                rel_path = py_file.relative_to(root)
                print(f"✅ Fixed: {rel_path}")
                changed_files.append(rel_path)

        except Exception as e:
            rel_path = py_file.relative_to(root)
            print(f"❌ Error processing {rel_path}: {e}")
            error_files.append(rel_path)

    # Summary report
    print("\n" + "=" * 40)
    print("Execution Summary")
    print("=" * 40)
    print(f"Successfully fixed: {len(changed_files)} files.")
    if error_files:
        print(f"Encountered errors: {len(error_files)} files.")
        sys.exit(1)


if __name__ == "__main__":
    main()
