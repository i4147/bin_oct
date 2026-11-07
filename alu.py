#!/data/data/com.termux/files/usr/bin/env python
"""Show the packages with pending upgrades on a Termux/apt system.

A one-liner wrapper around ``apt list --upgradable``, kept as a short command instead of remembering the apt
invocation.

Usage: alu

Examples:
    $ alu

Takes no arguments and runs ``apt`` with the inherited terminal.
"""

import subprocess


if __name__ == "__main__":
    cmd = ["apt", "list", "--upgradable"]
    _ = subprocess.run(cmd)
