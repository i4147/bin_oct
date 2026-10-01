#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that converts a text file's encoding from ISO-8859-1 to UTF-8 in place.
The function should take a filename, first create a backup copy with a ".bak" extension using shutil.copy2, then read the backup's content using ISO-8859-1 decoding, and finally write that content back to the original filename encoded as UTF-8.
After conversion, it should print a confirmation message stating the file was converted and where the backup was saved.
Include a main block that runs this conversion on a file named "script.sh"."""

import codecs
import shutil


def convert_in_place(filename):
    backup = f"{filename}.bak"
    shutil.copy2(filename, backup)
    with codecs.open(backup, "r", encoding="iso-8859-1") as f:
        content = f.read()
    with codecs.open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Converted {filename} (backup saved as {backup})")


if __name__ == "__main__":
    convert_in_place("script.sh")
