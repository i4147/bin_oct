#!/data/data/com.termux/files/usr/bin/env python

import os
import subprocess
from pathlib import Path

if __name__ == "__main__":
    target_dir = Path.cwd().resolve()
    os.chdir(target_dir.parent)
    subprocess.run(["wheel", "pack", str(target_dir), "-d", "/sdcard/whl"], check=False)
