#!/data/data/com.termux/files/usr/bin/env python
"""mergecss.py -- merge every CSS file into ``merged.css``.

cleancss runs with level 2 optimisations and duplicate rule removal.
"""

from __future__ import annotations

from dh import runcmd

if __name__ == "__main__":
    cmd = ["cleancss", "-O2", "removeDuplicateRules:on", "*.css", "-o", "merged.css"]
    runcmd(cmd, show_output=True)
