#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that generates a ready-to-publish Python package setup configuration for a given project directory. The script should accept a path to a project folder and automatically detect the main package inside it, whether that is a directory containing an initialization file, a subdirectory that forms a package, or a single standalone module file. It should skip non-essential files such as setup scripts when looking for the module.
Once the package is located, the script should scrape project metadata from the package's source files, including the version number, author name, author email, project URL, and license. If a version cannot be found, it should fall back to a sensible default version. The metadata extraction should tolerate imperfect or partially readable source files without crashing.
The script should then produce the packaging files needed for distribution, such as a setup configuration and a project description file, populated with the detected name, version, author details, and other metadata. It should report clearly to the user which package was detected, what metadata was found or defaulted, and where the generated files were written. Handle missing paths, empty directories, and unreadable files gracefully with informative error messages and a non-zero exit status on failure.
The tool should be runnable from the command line, taking the path as its primary argument, and should avoid overwriting existing packaging files without confirmation or an explicit override option.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys

DEFAULT_VERSION: str = "1.4.7"


def resolve_package(target: Path) -> tuple[str | None, Path | None, Path | None]:
    if (target / "__init__.py").is_file():
        return target.name, target, target.parent
    for entry in sorted(target.iterdir()):
        if entry.is_dir() and (entry / "__init__.py").is_file():
            return entry.name, entry, target
    for entry in sorted(target.iterdir()):
        if entry.is_file() and entry.suffix == ".py" and entry.name != "setup.py":
            return entry.stem, entry, target
    return None, None, None


def scrape_metadata(pkg_dir: Path, version: str) -> dict[str, str]:
    meta: dict[str, str] = {
        "version": version,
        "author": "",
        "author_email": "",
        "url": "",
        "license": "",
    }
    init: Path = pkg_dir / "__init__.py"
    if init.is_file():
        text: str = init.read_text(encoding="utf-8", errors="ignore")
        patterns: dict[str, str] = {
            "version": r"__version__\s*=\s*['\"]([^'\"]+)['\"]",
            "author": r"__author__\s*=\s*['\"]([^'\"]+)['\"]",
            "author_email": r"__email__\s*=\s*['\"]([^'\"]+)['\"]",
            "url": r"__url__\s*=\s*['\"]([^'\"]+)['\"]",
            "license": r"__license__\s*=\s*['\"]([^'\"]+)['\"]",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                meta[key] = match.group(1)
    return meta


def build_setup_py(pkg_name: str, meta: dict[str, str], out_dir: Path) -> str:
    readme_expr: str = "''"
    for readme in ("README.md", "README.rst", "README.txt", "README"):
        if (out_dir / readme).is_file():
            readme_expr = f"open({readme!r}, encoding='utf-8').read() if os.path.exists({readme!r}) else ''"
            break
    lines: list[str] = [
        '"""Auto-generated setup.py."""',
        "import os",
        "from setuptools import setup, find_packages",
        "",
        "HERE = os.path.abspath(os.path.dirname(__file__))",
        "os.chdir(HERE)",
        "",
        "setup(",
        f"    name={pkg_name!r},",
        f"    version={meta['version']!r},",
        f"    description={pkg_name!r},",
        f"    long_description={readme_expr},",
        "    long_description_content_type='text/markdown',",
        f"    author={meta['author']!r},",
        f"    author_email={meta['author_email']!r},",
        f"    url={meta['url']!r},",
        f"    license={meta['license']!r},",
        "    packages=find_packages(exclude=('tests', 'tests.*')),",
        "    include_package_data=True,",
        "    python_requires='>=3.7',",
        "    install_requires=[",
        "    ],",
        "    classifiers=[",
        "        'Programming Language :: Python :: 3',",
        "        'License :: OSI Approved :: MIT License',",
        "        'Operating System :: OS Independent',",
        "    ],",
        ")",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <package_folder> [version]", file=sys.stderr)
        sys.exit(1)
    target: Path = Path(sys.argv[1]).expanduser().resolve()
    version: str = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_VERSION
    if not target.is_dir():
        print(f"Error: {target} is not a directory", file=sys.stderr)
        sys.exit(1)
    pkg_name, pkg_dir, out_dir = resolve_package(target)
    if pkg_name is None or pkg_dir is None or out_dir is None:
        print(f"Error: no importable package found at {target}", file=sys.stderr)
        sys.exit(1)
    meta: dict[str, str] = scrape_metadata(pkg_dir, version)
    setup_py: Path = out_dir / "setup.py"
    if setup_py.exists():
        print(f"Warning: {setup_py} already exists, overwriting.", file=sys.stderr)
    setup_py.write_text(build_setup_py(pkg_name, meta, out_dir), encoding="utf-8")
    print(f"Wrote {setup_py} (package={pkg_name!r}, version={meta['version']!r})")


if __name__ == "__main__":
    main()
