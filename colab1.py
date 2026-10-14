#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that backs up the installed third-party packages from the active Python environment's site-packages directory into a persistent cloud storage location, designed to run inside a Google Colab notebook. The script should mount the user's Google Drive, create a destination folder if it does not exist, and then process every top-level entry in the site-packages directory. Standalone files should be copied as-is into the destination, while each package directory should be compressed into a single archive file named after the package. When archiving, the script should include all regular files within the package but skip compiled bytecode cache files, and store paths relative to the site-packages root so the archives can be restored later. Packages whose names begin with "setuptools" or "pip" must be excluded from the export. Upon completion, the script should print a success message along with a summary of how many files were copied and how many directories were archived.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import site
import zipfile
from google.colab import drive

drive.mount("/content/drive")
site_pkgs = Path(site.getsitepackages()[0])
out_dir = Path("/content/drive/MyDrive/wheels")
out_dir.mkdir(parents=True, exist_ok=True)
EXCLUDE_PREFIXES = "setuptools", "pip"


def excluded(name: str) -> bool:
    return name.startswith(EXCLUDE_PREFIXES)


copied_files = 0
zipped_dirs = 0
for entry in site_pkgs.iterdir():
    name = entry.name
    if excluded(name):
        continue
    if entry.is_file():
        shutil.copy2(entry, out_dir / name)
        copied_files += 1
    elif entry.is_dir():
        zip_path = out_dir / f"{name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in entry.rglob("*"):
                if path.is_file() and path.suffix != ".pyc":
                    zf.write(path, path.relative_to(site_pkgs))
        zipped_dirs += 1
print("Export completed successfully.")
print(f"Site-packages source : {site_pkgs}")
print(f"Output directory     : {out_dir}")
print(f"Top-level files copied : {copied_files}")
print(f"Top-level dirs zipped  : {zipped_dirs}")
print("Excluded packages     : torch, tensorflow")
