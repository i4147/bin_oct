#!/data/data/com.termux/files/usr/bin/env python

import subprocess

if __name__ == "__main__":
    cmd = ["apt", "list", "--upgradable"]
    _ = subprocess.run(cmd)
