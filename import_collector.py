#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given Python source file and determines which third-party packages it depends on, then reports which of those packages are missing from the current environment. The tool should accept a file path as input, parse the file's source code without executing it, and collect every top-level module that the file imports, while ignoring relative imports and gracefully handling files that cannot be read, decoded, or parsed due to syntax errors.
The tool should separate standard library modules from third-party dependencies, so that only external packages are considered. For each third-party module name, it should translate common import names into their installable distribution names where they differ (for example, modules that are commonly installed under a different package name), and then check whether each required distribution is currently installed in the active Python environment and report its version when present.
The output should be a clear, human-readable summary listing the required packages, their installation status, and any missing packages with a ready-to-run pip install command for them. The script should return a non-zero exit status when dependencies are missing and zero when everything is satisfied, and it should also be usable as an importable utility that returns the set of required packages programmatically. Include a helpful usage message for incorrect or missing arguments, and ensure that invalid, non-Python, or nonexistent file paths produce clear error messages rather than crashes.
---"""

from __future__ import annotations
import ast
import importlib.metadata
import importlib.util
from pathlib import Path
import sys
from dh import is_python_file

PACKAGE_MAPPING = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "google": "google-cloud-storage",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "fitz": "pymupdf",
    "skimage": "scikit-image",
    "telegram": "python-telegram-bot",
    "dateutil": "python-dateutil",
    "git": "GitPython",
    "jwt": "PyJWT",
    "OpenGL": "PyOpenGL",
}


def get_imports_from_file(path: Path):
    imports = set()
    try:
        with Path(path).open(encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(n.name.split(".")[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module.split(".")[0])
    except (SyntaxError, UnicodeDecodeError):
        pass
    return imports


def check_status(module_name) -> bool:
    try:
        importlib.metadata.distribution(module_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        spec = importlib.util.find_spec(module_name)
        return spec is not None


def main() -> None:
    cwd = Path()
    output_file = cwd / "importz.txt"
    pip_script = cwd / "install_deps.sh"
    all_imports = set()
    local_names = {p.stem for p in cwd.glob("*.py")}
    local_names.update({p.name for p in cwd.iterdir() if p.is_dir() and (p / "__init__.py").exists()})
    std_libs = getattr(sys, "stdlib_module_names", set())
    for path in cwd.rglob("*"):
        if is_python_file(path) and path.name not in {"importz.txt", "install_deps.sh"}:
            all_imports.update(get_imports_from_file(path))
    third_party = [imp for imp in all_imports if imp not in std_libs and imp not in local_names and imp != "__future__"]
    missing_for_pip = []
    already_installed = []
    for imp in sorted(third_party):
        if check_status(imp):
            already_installed.append(imp)
        else:
            pip_name = PACKAGE_MAPPING.get(imp, imp)
            missing_for_pip.append(pip_name)
    if third_party:
        output_file.write_text("\n".join(sorted(third_party)), encoding="utf-8")
        print(f"✅ Found {len(third_party)} 3rd-party dependencies.")
        if already_installed:
            print(f"📦 Already installed: {', '.join(already_installed)}")
        if missing_for_pip:
            install_cmd = f"pip install {' '.join(missing_for_pip)}"
            pip_script.write_text(f"#!/bin/sh\n{install_cmd}\n", encoding="utf-8")
            pip_script.chmod(pip_script.stat().st_mode | 73)
            print(f"⚠️  Missing: {', '.join(missing_for_pip)}")
            print(f"🚀 Run this to install missing: ./{pip_script.name}")
        else:
            if pip_script.exists():
                pip_script.unlink()
            print("✨ Environment is fully satisfied!")
    else:
        print("ℹ️ No 3rd-party imports found.")


if __name__ == "__main__":
    raise SystemExit(main())
