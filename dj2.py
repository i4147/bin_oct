#!/data/data/com.termux/files/usr/bin/env python
import shutil
from pathlib import Path


def is_git_repo_simple(folder_path: str | Path) -> bool:
    """
    Checks if a folder contains a '.git' directory using pathlib.
    """
    try:
        target_dir = Path(folder_path).expanduser().resolve()
        return target_dir.is_dir() and (target_dir / ".git").is_dir()
    except (PermissionError, OSError) as e:
        print(f"Error accessing path: {e}")
        return False


def clean_non_git_dir():
    """
    Recursively removes .github folders and .gitignore files in the current working
    directory ONLY if the current directory is not a Git repository.
    """
    # 1. Get the current working directory
    current_dir = Path.cwd().resolve()

    # 2. Safety check: Abort if this directory is a Git repository
    if is_git_repo_simple(current_dir):
        print(f"Abort: '{current_dir}' is a Git repository. No files were deleted.")
        return

    print(f"Cleaning non-git directory: {current_dir}\n")

    # 3. Recursively search the directory tree
    # rglob('*') finds all files and directories inside current_dir
    try:
        # We convert to a list to prevent issues while mutating the directory structure during iteration
        for path in list(current_dir.rglob("*")):
            # Remove .github directories and everything inside them
            if path.is_dir() and path.name == ".github":
                try:
                    shutil.rmtree(path)
                    print(f"Removed directory: {path.relative_to(current_dir)}")
                except Exception as e:
                    print(f"Failed to remove directory {path}: {e}")

            # Remove .gitignore files
            elif path.is_file() and path.name == ".gitignore":
                try:
                    path.unlink()
                    print(f"Removed file:      {path.relative_to(current_dir)}")
                except Exception as e:
                    print(f"Failed to remove file {path}: {e}")

    except PermissionError as e:
        print(f"Permission error scanning directory: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during cleanup: {e}")


if __name__ == "__main__":
    clean_non_git_dir()
