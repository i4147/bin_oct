#!/data/data/com.termux/files/usr/bin/env python
from __future__ import annotations

from dh import runcmd

if __name__ == "__main__":
    from string import ascii_lowercase, ascii_uppercase

    for char in ascii_lowercase:
        cmd = ["srp", char]
        runcmd(cmd, show_output=True)
    for char in ascii_uppercase:
        cmd = ["srp", char]
        runcmd(cmd, show_output=True)
    print("done")
