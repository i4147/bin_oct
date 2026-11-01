#!/data/data/com.termux/files/usr/bin/env python

"""alu.py -- list the Termux/APT packages that have an upgrade available.

Thin wrapper around ``apt list --upgradable``; the package manager decides
what is printed.
"""

from __future__ import annotations

import subprocess


if __name__ == "__main__":
    cmd = ["apt", "list", "--upgradable"]
    _ = subprocess.run(cmd)
