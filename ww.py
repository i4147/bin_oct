#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that packages the current working directory into a Python wheel file using the command-line wheel tool, and saves the resulting wheel into a fixed output folder on an Android-style storage path (/sdcard/whl). The script should be runnable directly as a standalone program. It should determine the project directory from where it is executed, temporarily move to the parent directory of that project before invoking the packaging step, and then pass the project's full path to the packaging tool so it can build the wheel. The packaging step should write its output into the designated destination folder. The script should not stop with an error if the packaging tool reports a failure; it should simply run the packaging attempt and finish. Keep the behavior simple and focused: no user prompts, no configuration files, and no extra output beyond what the packaging tool produces.
---"""

from __future__ import annotations
import os
from pathlib import Path
import subprocess

if __name__ == "__main__":
    target_dir = Path.cwd().resolve()
    os.chdir(target_dir.parent)
    subprocess.run(["wheel", "pack", str(target_dir), "-d", "/sdcard/whl"], check=False)
