#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that merges multiple requirements files found in the imm a given root folder into a single consolidated requirements file placed in that root folder.
The script should accept a root directory path as input (defaulting to the current working directory if none is provided) and an optional flag that, when enabled, deletes the original per-subdirectory requirements files after a successful merge. It should scan only the first level of subdirectories under the root, and consider a subdirectory only if it contains a file named requirements.txt.
For each discovered requirements file, process its contents in a stable, sorted order by subdirectory name. Before the entries from each file, insert a clearly visible comment header identifying which subdirectory the entries came from. Preserve blank lines and comment lines exactly as they appear in the source files. Deduplicate package requirement lines across all files so that the first occurrence is kept as-is, and any later repeated requirement (compared after trimming surrounding whitespace) is retained in the output but marked as a duplicate by prefixing it with a comment that indicates it is a duplicate. Separate each source file's section with a blank line, and ensure the final output ends with a single trailing newline.
If no subdirectories containing a requirements file are found, the script should print a clear message to the user stating that no requirements file was found in the top-level subdirectories, and it should not create or modify any output file. Otherwise, write the merged result to the root directory's requirements.txt file, overwriting any existing file there, and report to the user the path of the generated file. Handle file read and write errors gracefully with informative messages rather than crashing with an unhandled traceback.
Provide a command-line interface with clear help text describing the root directory argument and the option to remove the original files, so the tool can be run directly from a terminal.
---"""

from __future__ import annotations
import argparse
from pathlib import Path


def merge_requirements(root: Path, remove_originals: bool = False) -> Path:
    output = root / "requirements.txt"
    sources = sorted(p for p in root.iterdir() if p.is_dir() and (p / "requirements.txt").is_file())
    if not sources:
        print("No requirements.txt found in top-level subdirectories.")
        return output
    lines: list[str] = []
    seen: set[str] = set()
    for subdir in sources:
        req_file = subdir / "requirements.txt"
        lines.append(f"# --- {subdir.name}/requirements.txt ---")
        for raw in req_file.read_text().splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                lines.append(raw)
                continue
            if stripped in seen:
                lines.append(f"# (duplicate) {raw}")
            else:
                seen.add(stripped)
                lines.append(raw)
        lines.append("")
    output.write_text("\n".join(lines).rstrip() + "\n")
    print(f"Wrote {output}")
    if remove_originals:
        for subdir in sources:
            (subdir / "requirements.txt").unlink()
            print(f"Removed {subdir / 'requirements.txt'}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge requirements.txt from top-level subdirs.")
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove original requirements.txt files after merging.",
    )
    args = parser.parse_args()
    merge_requirements(Path.cwd(), remove_originals=args.remove)


if __name__ == "__main__":
    main()
