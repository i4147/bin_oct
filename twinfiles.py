#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans the current working directory for pairs of files sharing the same base name but with two different user-specified extensions.
The script should prompt the user to enter two file extensions and choose which one (1 or 2) to delete when both files of a pair exist, automatically normalizing the extensions to include a leading dot if missing.
It should walk all files matching the first extension, check whether a matching file with the second extension exists in the same location, and if so, delete the file corresponding to the chosen extension while keeping the other, printing a message showing which file was deleted and which was kept.
The script should exit cleanly via SystemExit after processing all matches."""

from pathlib import Path


def main() -> None:
    cwd = Path.cwd()
    ext1 = input("ext 1 :").strip()
    ext2 = input("ext 2 :").strip()
    choice = input("remove which one: 1 or 2: ").strip()
    if not ext1.startswith("."):
        ext1 = "." + ext1
    if not ext2.startswith("."):
        ext2 = "." + ext2
    todel = ext1 if choice == "1" else ext2
    for path in cwd.rglob(f"*{ext1}"):
        if path.is_file() and path.suffix == ext1:
            twin = path.with_suffix(ext2)
            if twin.exists():
                if todel == ext1:
                    print(f"[✖] {path}  (keeping {twin})")
                    path.unlink()
                else:
                    print(f"[✖] {twin}  (keeping {path})")
                    twin.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
