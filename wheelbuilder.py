#!/data/data/com.termux/files/usr/bin/python
"""
Build wheels from extracted package source directories or .tar.gz files.
- Skips packages with Rust backend
- Uses multiprocessing for parallel builds
- Cleans up any temporary/build files
- Uses pathlib for path operations

Usage:
    python build_wheels.py          # Build from extracted subdirectories
    python build_wheels.py -g       # Build from .tar.gz files
"""

import subprocess
import shutil
import tarfile
import tempfile
import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def has_rust_backend(pkg_dir: Path) -> bool:
    """
    Check if package has Rust backend by looking for Cargo.toml.

    Args:
        pkg_dir: Path to package source directory

    Returns:
        True if Rust backend detected, False otherwise
    """
    cargo_toml = pkg_dir / "Cargo.toml"
    if cargo_toml.exists():
        logger.info(f"  → Rust backend detected in {pkg_dir.name}")
        return True
    return False


def cleanup_build_artifacts(pkg_dir: Path) -> None:
    """
    Remove temporary build directories and cache files.

    Args:
        pkg_dir: Path to package directory to clean
    """
    # Directories to remove
    dirs_to_remove = [
        pkg_dir / "build",
        pkg_dir / "dist",
        pkg_dir / "*.egg-info",
        pkg_dir / "__pycache__",
        pkg_dir / ".eggs",
    ]

    for pattern in dirs_to_remove:
        if "*" in pattern.name:
            # Handle glob patterns
            for item in pkg_dir.glob(pattern.name):
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        logger.debug(f"  → Removed {item.name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Failed to remove {item.name}: {e}")
        else:
            # Handle direct paths
            if pattern.exists():
                try:
                    shutil.rmtree(pattern)
                    logger.debug(f"  → Removed {pattern.name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Failed to remove {pattern.name}: {e}")


def build_wheel_from_dir(pkg_dir: Path) -> Tuple[Path, Optional[str]]:
    """
    Check for Rust backend and build wheel from extracted package directory.

    Args:
        pkg_dir: Path to extracted package directory

    Returns:
        Tuple of (pkg_dir, error_message or None if successful)
    """
    logger.info(f"Processing: {pkg_dir.name}")

    try:
        # Check if setup.py or setup.cfg or pyproject.toml exists
        has_setup = any([
            (pkg_dir / "setup.py").exists(),
            (pkg_dir / "setup.cfg").exists(),
            (pkg_dir / "pyproject.toml").exists(),
        ])

        if not has_setup:
            return pkg_dir, "No setup.py/setup.cfg/pyproject.toml found"

        # Check for Rust backend
        if has_rust_backend(pkg_dir):
            return pkg_dir, "Skipped (Rust backend detected)"

        # Clean up any previous build artifacts
        logger.info(f"  → Cleaning previous build artifacts...")
        cleanup_build_artifacts(pkg_dir)

        # Build wheel
        logger.info(f"  → Building wheel for {pkg_dir.name}...")
        result = subprocess.run(
            [
                "python",
                "-m",
                "pip",
                "wheel",
                "--no-cache-dir",
                "--no-deps",
                "--wheel-dir",
                str(Path.cwd() / "wheels"),
                str(pkg_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(pkg_dir),
        )

        if result.returncode == 0:
            logger.info(f"  ✓ Successfully built wheel for {pkg_dir.name}")
            # Clean up build artifacts after successful build
            cleanup_build_artifacts(pkg_dir)
            return pkg_dir, None
        else:
            error_msg = result.stderr or result.stdout
            return pkg_dir, f"Build failed: {error_msg[:150]}"

    except subprocess.TimeoutExpired:
        return pkg_dir, "Build timeout (>300s)"
    except Exception as e:
        return pkg_dir, f"Error: {str(e)}"


def build_wheel_from_tar_gz(tar_gz_file: Path) -> Tuple[Path, Optional[str]]:
    """
    Extract package from .tar.gz, check for Rust backend, and build wheel.

    Args:
        tar_gz_file: Path to .tar.gz package file

    Returns:
        Tuple of (tar_gz_file, error_message or None if successful)
    """
    logger.info(f"Processing: {tar_gz_file.name}")

    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Extract the tar.gz file
            logger.info(f"  → Extracting {tar_gz_file.name}...")
            with tarfile.open(tar_gz_file, "r:gz") as tar:
                tar.extractall(path=temp_path)

            # Find the package directory (usually first directory in tar)
            extracted_items = list(temp_path.iterdir())
            if not extracted_items:
                return tar_gz_file, f"No files extracted from {tar_gz_file.name}"

            pkg_dir = extracted_items[0]
            if pkg_dir.is_file():
                pkg_dir = temp_path

            # Check for Rust backend
            if has_rust_backend(pkg_dir):
                return tar_gz_file, "Skipped (Rust backend detected)"

            # Build wheel
            logger.info(f"  → Building wheel for {tar_gz_file.name}...")
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pip",
                    "wheel",
                    "--no-cache-dir",
                    "--no-deps",
                    "--wheel-dir",
                    str(Path.cwd() / "wheels"),
                    str(pkg_dir),
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                logger.info(f"  ✓ Successfully built wheel for {tar_gz_file.name}")
                return tar_gz_file, None
            else:
                error_msg = result.stderr or result.stdout
                return tar_gz_file, f"Build failed: {error_msg[:150]}"

        except tarfile.TarError as e:
            return tar_gz_file, f"Extraction failed: {str(e)}"
        except subprocess.TimeoutExpired:
            return tar_gz_file, "Build timeout (>300s)"
        except Exception as e:
            return tar_gz_file, f"Error: {str(e)}"


def is_valid_package_dir(path: Path) -> bool:
    """
    Check if directory appears to be a Python package source.

    Args:
        path: Path to check

    Returns:
        True if directory contains package metadata files
    """
    if not path.is_dir():
        return False

    # Check for common package metadata files
    has_metadata = any([
        (path / "setup.py").exists(),
        (path / "setup.cfg").exists(),
        (path / "pyproject.toml").exists(),
        (path / "PKG-INFO").exists(),
    ])

    return has_metadata


def build_from_directories() -> None:
    """Build wheels from extracted package subdirectories in current folder."""

    current_dir = Path.cwd()

    # Find all subdirectories that appear to be Python packages
    pkg_dirs = sorted([d for d in current_dir.iterdir() if is_valid_package_dir(d)])

    if not pkg_dirs:
        logger.warning("No valid Python package directories found in current directory")
        logger.info("Looking for directories with setup.py, setup.cfg, or pyproject.toml")
        return

    logger.info(f"Found {len(pkg_dirs)} package directory/directories to process")
    for pkg_dir in pkg_dirs:
        logger.info(f"  • {pkg_dir.name}")

    # Create wheels output directory
    wheels_dir = current_dir / "wheels"
    wheels_dir.mkdir(exist_ok=True)
    logger.info(f"\nWheels will be saved to: {wheels_dir}\n")

    # Use multiprocessing to build wheels in parallel
    num_workers = min(cpu_count() - 1, len(pkg_dirs)) or 1
    logger.info(f"Using {num_workers} worker(s) for parallel builds\n")

    try:
        with Pool(processes=num_workers) as pool:
            results = pool.map(build_wheel_from_dir, pkg_dirs)

        # Process and log results
        logger.info("\n" + "=" * 70)
        logger.info("BUILD SUMMARY")
        logger.info("=" * 70)

        successful = 0
        skipped = 0
        failed = 0

        for pkg_dir, error in results:
            if error is None:
                successful += 1
                logger.info(f"✓ {pkg_dir.name}: SUCCESS")
            elif "Skipped" in error:
                skipped += 1
                logger.info(f"⊘ {pkg_dir.name}: {error}")
            else:
                failed += 1
                logger.error(f"✗ {pkg_dir.name}: {error}")

        logger.info("=" * 70)
        logger.info(f"Results: {successful} successful, {skipped} skipped, {failed} failed")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Multiprocessing failed: {e}")
        return

    # List built wheels
    wheels = list(wheels_dir.glob("*.whl"))
    if wheels:
        logger.info(f"\nBuilt wheels ({len(wheels)}):")
        for wheel in sorted(wheels):
            size_mb = wheel.stat().st_size / (1024 * 1024)
            logger.info(f"  • {wheel.name} ({size_mb:.2f} MB)")
    else:
        logger.warning("No wheels were built")


def build_from_tar_gz() -> None:
    """Build wheels from .tar.gz files in current folder."""

    current_dir = Path.cwd()

    # Find all .tar.gz files in current directory
    tar_gz_files = sorted(current_dir.glob("*.tar.gz"))

    if not tar_gz_files:
        logger.warning("No .tar.gz files found in current directory")
        return

    logger.info(f"Found {len(tar_gz_files)} package(s) to process")
    for tar_file in tar_gz_files:
        logger.info(f"  • {tar_file.name}")

    # Create wheels output directory
    wheels_dir = current_dir / "wheels"
    wheels_dir.mkdir(exist_ok=True)
    logger.info(f"\nWheels will be saved to: {wheels_dir}\n")

    # Use multiprocessing to build wheels in parallel
    num_workers = min(cpu_count() - 1, len(tar_gz_files)) or 1
    logger.info(f"Using {num_workers} worker(s) for parallel builds\n")

    try:
        with Pool(processes=num_workers) as pool:
            results = pool.map(build_wheel_from_tar_gz, tar_gz_files)

        # Process and log results
        logger.info("\n" + "=" * 70)
        logger.info("BUILD SUMMARY")
        logger.info("=" * 70)

        successful = 0
        skipped = 0
        failed = 0

        for tar_file, error in results:
            if error is None:
                successful += 1
                logger.info(f"✓ {tar_file.name}: SUCCESS")
            elif "Skipped" in error:
                skipped += 1
                logger.info(f"⊘ {tar_file.name}: {error}")
            else:
                failed += 1
                logger.error(f"✗ {tar_file.name}: {error}")

        logger.info("=" * 70)
        logger.info(f"Results: {successful} successful, {skipped} skipped, {failed} failed")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Multiprocessing failed: {e}")
        return

    # List built wheels
    wheels = list(wheels_dir.glob("*.whl"))
    if wheels:
        logger.info(f"\nBuilt wheels ({len(wheels)}):")
        for wheel in sorted(wheels):
            size_mb = wheel.stat().st_size / (1024 * 1024)
            logger.info(f"  • {wheel.name} ({size_mb:.2f} MB)")
    else:
        logger.warning("No wheels were built")


def main() -> None:
    """Main function to handle CLI arguments and orchestrate wheel building."""

    parser = argparse.ArgumentParser(
        description="Build Python wheels from package sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_wheels.py          # Build from extracted subdirectories
  python build_wheels.py -g       # Build from .tar.gz files
        """,
    )

    parser.add_argument(
        "-g", "--gzip", action="store_true", help="Build from .tar.gz files instead of extracted subdirectories"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    if args.gzip:
        logger.info("Mode: Building from .tar.gz files")
        logger.info("=" * 70 + "\n")
        build_from_tar_gz()
    else:
        logger.info("Mode: Building from extracted subdirectories")
        logger.info("=" * 70 + "\n")
        build_from_directories()


if __name__ == "__main__":
    main()
