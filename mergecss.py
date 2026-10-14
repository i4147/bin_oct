#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a simple command-line wrapper for a CSS minification and merging step. When executed directly, it should run the external CSS optimizer tool on all CSS files in the current working directory, applying a high level of optimization and removing duplicate CSS rules, then combine the results into a single output stylesheet named "merged.css". The script should display the tool's output in the console while it runs, so the user can see progress and any warnings or errors. It should rely on a small helper utility for executing shell commands rather than implementing the process handling itself. Keep the script minimal and focused: its only job is to launch this one optimization command with these settings and report what happens.
---"""

from __future__ import annotations
from dh import runcmd

if __name__ == "__main__":
    cmd = ["cleancss", "-O2", "removeDuplicateRules:on", "*.css", "-o", "merged.css"]
    runcmd(cmd, show_output=True)
