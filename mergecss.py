#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that uses the `runcmd` function from the `dh` module to run the `cleancss` command-line tool, minifying and merging all CSS files in the current directory into a single output file named "merged.css".
The command should apply optimization level O2 with the "removeDuplicateRules" option enabled, and the script should display the command's output to the console.
The script's entry point should execute this command only when run directly as the main module."""

from __future__ import annotations

from dh import runcmd

if __name__ == "__main__":
    cmd = ["cleancss", "-O2", "removeDuplicateRules:on", "*.css", "-o", "merged.css"]
    runcmd(cmd, show_output=True)
