#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively searches the current working directory for all files with a .whl extension.
For each wheel file found, it should copy its contents to a fixed destination folder at /sdcard/whl using the same filename, overwriting any existing file with the same name at that location, and then delete the original source file.
As each file is moved, the script should print a line showing the source filename mapped to the destination filename, and after processing all files it should print "done" to indicate completion."""

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
