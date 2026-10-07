#!/data/data/com.termux/files/usr/bin/python
import re
import sys
from pathlib import Path


def update_setup_files() -> None:

    target_cp = f"cp3{sys.version_info.minor}"

    pattern = re.compile(r'(python,\s*abi\s*=\s*")cp3\d+(")')

    current_dir = Path.cwd()
    updated_files = 0

    for setup_file in current_dir.rglob("setup.py"):
        try:
            content = setup_file.read_text(encoding="utf-8")

            if pattern.search(content):
                new_content = pattern.sub(rf"\g<1>{target_cp}\2", content)

                if new_content != content:
                    setup_file.write_text(new_content, encoding="utf-8")
                    print(f"✓ Updated: {setup_file.relative_to(current_dir)}")
                    updated_files += 1

        except Exception as e:
            print(f"❌ Error processing {setup_file}: {e}")

    print(f"\nFinished! Updated {updated_files} file(s) to match Python version '{target_cp}'.")


if __name__ == "__main__":
    update_setup_files()
