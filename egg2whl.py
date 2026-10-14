#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a legacy Python egg distribution (an unpacked EGG-INFO metadata folder) into a modern, installable source project. The tool should read the distribution's package metadata and entry point definitions, then generate a standard packaging configuration file so the project can be built and installed with modern Python packaging tools.
Requirements:
- Accept a path to an egg root directory containing an EGG-INFO metadata folder as input, and an output location where the converted project should be written or staged (use a temporary working area where appropriate).
- Read the core package metadata (such as name, version, and other descriptive fields) from the metadata file, tolerating non-UTF-8 bytes and ignoring malformed lines.
- Read any declared console or GUI entry points and carry them over into the generated packaging configuration.
- Produce a packaging configuration that uses automatic package discovery, includes package data, and marks the package as not zip-safe, with the metadata values substituted in. Handle missing or empty fields gracefully with sensible defaults.
- Build the resulting project by invoking the appropriate build step in an isolated subprocess, capture its output, and report success or a clear error message if the build fails.
- Clean up temporary files and directories afterward, even when an error occurs.
- Print concise progress messages and a final summary indicating where the built artifacts were placed.
- Exit with a non-zero status code on failure and zero on success.
- Keep the script self-contained, robust against missing files, and easy to run from the command line with a small set of arguments.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import tempfile


def parse_pkg_info(egg_info_dir):
    pkg_info_path = egg_info_dir / "PKG-INFO"
    metadata = {}
    if pkg_info_path.exists():
        with Path(pkg_info_path).open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
    return metadata


def create_setup_py(egg_root: Path, temp_dir: Path):
    egg_info_dir = egg_root / "EGG-INFO"
    egg_root / "setupmeta"
    metadata = parse_pkg_info(egg_info_dir)
    setup_py_content = """from setuptools import setup, find_packages
setup(
    name="{name}",
    version="{version}",
    packages=find_packages(),
    package_data={{}},
    include_package_data=True,
    zip_safe=False,
"""
    entry_points_path = egg_info_dir / "entry_points.txt"
    entry_points = ""
    if entry_points_path.exists():
        entry_points = Path(entry_points_path).read_text(encoding="utf-8")
        setup_py_content += f"    entry_points={{\n{entry_points}}},\n"
    setup_py_content += ")"
    name = metadata.get("Name", "unknown")
    version = metadata.get("Version", "0.0.0")
    setup_py_content = setup_py_content.format(name=name, version=version)
    setup_py_path = temp_dir / "setup.py"
    Path(setup_py_path).write_text(setup_py_content, encoding="utf-8")
    return name, version


def convert_egg_to_wheel(egg_root_path: str) -> str | None:
    egg_root = Path(egg_root_path)
    if not egg_root.exists():
        msg = f"Egg directory not found: {egg_root}"
        raise FileNotFoundError(msg)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        standard_egg_info = temp_path / f"{egg_root.name}.egg-info"
        shutil.copytree(egg_root / "EGG-INFO", standard_egg_info)
        setupmeta_src = temp_path / "setupmeta"
        shutil.copytree(egg_root / "setupmeta", setupmeta_src)
        _name, _version = create_setup_py(egg_root, temp_path)
        cmd = [
            sys.executable,
            "setup.py",
            "bdist_wheel",
            "--dist-dir",
            str(temp_path / "dist"),
        ]
        result = subprocess.run(cmd, cwd=temp_path, capture_output=True, text=True)
        if result.returncode != 0:
            print("Build errors:", result.stderr)
            return None
        wheel_files = list((temp_path / "dist").glob("*.whl"))
        if wheel_files:
            wheel_path = wheel_files[0]
            print(f"Wheel created: {wheel_path}")
            return str(wheel_path)
    return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python convert_egg.py <egg_directory>")
        sys.exit(1)
    egg_dir = sys.argv[1]
    wheel_path = convert_egg_to_wheel(egg_dir)
    if wheel_path:
        print(f"✓ Successfully converted to wheel: {wheel_path}")
    else:
        print("✗ Conversion failed")
        sys.exit(1)
