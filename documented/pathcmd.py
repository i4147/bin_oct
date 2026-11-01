#!/data/data/com.termux/files/usr/bin/env python
"""pathcmd.py -- print the directories on ``PATH``.

Every entry is listed so it can be inspected for missing or duplicated directories.
"""

import os

if __name__ == "__main__":
    p_env = os.environ.get("PATH")
    pdirs = p_env.split(":")
    for p in pdirs:
        print(p)
