#!/data/data/com.termux/files/usr/bin/env python
"""(No content in stream)

---"""

from __future__ import annotations

import subprocess


if __name__ == "__main__":
    cmd = ["apt", "list", "--upgradable"]
    _ = subprocess.run(cmd)
