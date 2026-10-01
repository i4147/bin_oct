#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that packages the current working directory into a Python wheel file using the external "wheel pack" command-line tool.
The script should resolve the current directory as the target, change the working directory to its parent before running the command, and output the resulting wheel file to "/sdcard/whl".
It should invoke the subprocess without raising an exception on failure (using check=False), so any errors from the packing process are silently ignored rather than propagated."""

import os
import subprocess
from pathlib import Path

if __name__ == "__main__":
    target_dir = Path.cwd().resolve()
    os.chdir(target_dir.parent)
    subprocess.run(["wheel", "pack", str(target_dir), "-d", "/sdcard/whl"], check=False)
