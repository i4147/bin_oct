#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that parses the metadata header of a Python package distribution file (such as the METADATA or PKG-INFO text found inside a wheel or source distribution), extracting the structured fields it contains and converting them into a cline-readable output. The script should accept a path to a metadata file (or a directory containing one) as its main input, and produce a structured representation of the package information, such as a JSON document or a formatted summary written to standard output or a specified output file.
Key behaviors to cover:
- Read the metadata file and separate the header section from the free-form long description that follows it, stopping at the first blank line or the first line that does not follow the "Key: Value" pattern.
- Recognize single-valued fields (such as name, version, summary, home page, license, author, and author email) and store each as a single string.
- Recognize multi-valued fields (such as requirements, extras, classifiers, keywords, dynamic fields, and project URLs) and collect every occurrence into a list, preserving their original order.
- Handle continuation lines that begin with whitespace by appending their content to the previous field's value, so that multi-line values are reconstructed correctly.
- Normalize values by trimming surrounding whitespace and ignoring empty entries.
- Gracefully handle missing fields, malformed lines, unknown keys, and files with unexpected encodings, reporting problems clearly instead of crashing where reasonable.
- Provide a command-line interface that accepts the input path, an optional output path, and an option to choose the output format, with helpful usage messages and meaningful exit codes on error.
- Include the long description text as a separate field in the output when present.
- Keep the code modular, readable, and well documented with docstrings and comments, and include basic error handling for missing files and invalid input.
---"""

from __future__ import annotations
import json
from pathlib import Path
import re
import sys


def parse_metadata_section(lines):
    metadata = {}
    current_key = None
    end_line = 0
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line.startswith((" ", "\t")):
            if (
                current_key
                and current_key
                not in [
                    "Requires-Dist",
                    "Provides-Extra",
                    "Dynamic",
                    "Classifier",
                    "Keywords",
                    "Project-URL",
                ]
                and current_key in metadata
            ):
                metadata[current_key] += " " + line_stripped
            continue
        if not line_stripped or ":" not in line_stripped:
            end_line = i
            break
        if ":" in line_stripped:
            key, value = line_stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key not in [
                "Author",
                "Author-Email",
                "Maintainer",
                "Maintainer-Email",
                "Home-Page",
                "Download-URL",
                "Project-URL",
                "Requires-Dist",
                "Provides-Extra",
                "Dynamic",
                "Classifier",
                "Keywords",
                "License",
                "License-Expression",
            ]:
                metadata[key] = value
                current_key = key
            else:
                current_key = None
        else:
            current_key = None
        end_line = i + 1
    return metadata, end_line


def find_section_boundaries(content, start_pos=0):
    sections = []
    pos = start_pos
    code_pattern = re.compile(r"```(python|shell|bash|sh|py)\s*\n(.*?)```", re.DOTALL)
    while pos < len(content):
        code_match = code_pattern.search(content, pos)
        if code_match:
            if code_match.start() > pos:
                md_text = content[pos : code_match.start()].strip()
                if md_text:
                    sections.append(("markdown", md_text))
            code_text = code_match.group(2).strip()
            sections.append(("code", code_text))
            pos = code_match.end()
        else:
            remaining = content[pos:].strip()
            if remaining:
                sections.append(("markdown", remaining))
            break
    return sections


def convert_metadata_to_notebook(metadata_path):
    with open(metadata_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    metadata, content_start = parse_metadata_section(lines)
    pkg_name = metadata.get("Name", "unknown_package")
    pkg_version = metadata.get("Version", "0.0.0")
    safe_pkg_name = re.sub(r"[^\w\-_]", "_", pkg_name)
    output_path = f"{safe_pkg_name}.ipynb"
    remaining_content = "\n".join(lines[content_start:])
    sections = find_section_boundaries(remaining_content)
    notebook = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    title_content = f"# {pkg_name} v{pkg_version}\n\nConverted from METADATA file"
    title_cell = {"cell_type": "markdown", "metadata": {}, "source": [title_content]}
    notebook["cells"].append(title_cell)
    for cell_type, content in sections:
        if cell_type == "markdown":
            cell = {"cell_type": "markdown", "metadata": {}, "source": [content]}
        else:
            cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [content],
            }
        notebook["cells"].append(cell)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    print(f"Package: {pkg_name} v{pkg_version}")
    print(f"Notebook created: {output_path}")
    print(f"Total cells: {len(notebook['cells'])}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python metadata_to_notebook.py <METADATA_file>")
        print("Output will be saved as <package_name>.ipynb")
        sys.exit(1)
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    convert_metadata_to_notebook(input_file)


if __name__ == "__main__":
    raise SystemExit(main())
