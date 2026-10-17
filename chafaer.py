#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
import shutil
import sys

from PIL import Image


def render(image_path: str) -> None:
    img = Image.open(image_path).convert("RGB")
    cols, rows = shutil.get_terminal_size()
    rows -= 1
    target_w = cols
    target_h = rows * 2
    img_ratio = img.width / img.height
    term_ratio = target_w / target_h
    if img_ratio > term_ratio:
        new_w = target_w
        new_h = max(1, int(target_w / img_ratio))
    else:
        new_h = target_h
        new_w = max(1, int(target_h * img_ratio))
    img = img.resize((new_w, new_h), Image.LANCZOS)
    px = img.load()
    h = img.height - (img.height % 2)
    out = []
    for y in range(0, h, 2):
        line = []
        for x in range(img.width):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, y + 1]
            line.append(f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m\u2580")
        line.append("\x1b[0m")
        out.append("".join(line))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: imgview.py IMAGE")
        sys.exit(1)
    render(sys.argv[1])
