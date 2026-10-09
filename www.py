#!/data/data/com.termux/files/usr/bin/env python

from __future__ import annotations
from pathlib import Path

if __name__ == "__main__":
    cwd = Path.cwd()
    for path in cwd.rglob("*.whl"):
        fname = path.name
        target_dir = Path("/sdcard/whl")
        if not target_dir.exists():
            target_dir.mkdir(exist_ok=True)
        target_path = target_dir / fname
        if target_path.exists():
            target_path.unlink()
        data = path.read_bytes()
        target_path.write_bytes(data)
        path.unlink()
        print(f"{path.name} -> {target_path.name}")
    print("done")
