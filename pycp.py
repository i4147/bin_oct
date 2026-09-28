#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that copies a single file to the Termux usr directory on Android (/data/data/com.termux/files/usr).
The script should accept the source file path as a command-line argument, strip any surrounding whitespace from it, and use shutil.copy2 to copy the file while preserving its metadata to the fixed destination directory.
After the copy completesfully, it should print "done" to indicate the operation finished."""

import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1].strip())
dest = Path("/data/data/com.termux/files/usr")
shutil.copy2(str(src), dest)
print("done")
