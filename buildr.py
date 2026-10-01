#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans the current working directory for all "setup.py" files, then for each one changes into its parent directory and runs "python setup.py bdist_wheel" to build a wheel package, printing an error message if the build command fails for a given file.
The execution should use helper functions "get_files", "mpf" (for parallel/multi-processing execution across the found setup.py files), and "runcmd" imported from a local module named "dh".
After processing all setup.py files, the script should again scan the current directory for any resulting ".whl" files and print out the path of each one found."""

from os import chdir as os_chdir
from pathlib import Path
from dh import get_files, mpf, runcmd


def process_file(path_str: str) -> None:
    path = Path(path_str)
    os_chdir(path.parent)
    cmd = ["python", "setup.py", "bdist_wheel"]
    ret, _, _ = runcmd(cmd)
    if ret != 0:
        print(f"Error building wheel for {path}")


if __name__ == "__main__":
    cwd = Path.cwd()
    files = get_files(cwd)
    targets = [str(path) for path in files if path.name == "setup.py"]
    mpf(process_file, targets)
    whl_files = get_files(cwd, ext=[".whl"])
    if whl_files:
        for k in whl_files:
            print(k)
