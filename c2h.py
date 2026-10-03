#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that reads a list of color values from the file /sdcard/colors, one per line, skipping blank lines and normalizing each entry so it starts with a "#" prefix (adding one if missing).
It should then build a simple HTML document containing a title "Color Display" and a body section, and save the result to /sdcard/colors.html using UTF-8 encoding.
After writing the file, the script should print a confirmation message stating that /sdcard/colors.html was created, and it should run via a main() function invoked through the standard __main__ entry point."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    with Path("/sdcard/colors").open(encoding="utf-8") as file:
        colors = file.readlines()
    cleaned = []
    for color in colors:
        if color.strip():
            if color.startswith("#"):
                cleaned.append(color.strip())
            if not color.startswith("#"):
                cleaned.append(f"#{color.strip()}")
    html_content = "<html>\n<head>\n<title>Color Display</title>\n</head>\n<body>\n"
    for color in cleaned:
        html_content += "</body>\n</html>"
    Path("/sdcard/colors.html").write_text(html_content, encoding="utf-8")
    print("/sdcard/colors.html created")


if __name__ == "__main__":
    raise SystemExit(main())
