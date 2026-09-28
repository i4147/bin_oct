#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that batch-cleans HTML files by stripping out all img tags and any inline "background-image" declarations from style attributes, using BeautifulSoup for parsing.
It should accept file paths as command-line arguments, or if none are given, recursively scan the current directory for files with .html, .htm, .md, .rst, and .txt extensions via a helper get_files function.
Processing must run in parallel using a multiprocessing Pool (8 workers, spawn context) for speed, with each worker reporting per-file size changes (increase, decrease, or no change) using colored console output, and the overall before/after directory size should also be tracked.
The script should rely on helper functions (cprint, fsz, get_files, gsz) imported from a local "dh" module, and silently skip files that fail to process."""

import sys
from collections import deque
from multiprocessing import get_context
from pathlib import Path
from bs4 import BeautifulSoup
from dh import cprint, fsz, get_files, gsz


def process_file(path: Path) -> None:
    before = gsz(path)
    Path(path)
    try:
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img"):
            img.decompose()
        for tag in soup.find_all(style=True):
            style = tag["style"]
            new_style = "; ".join(
                s for s in style.split(";") if "background-image" not in s
            ).strip()
            if new_style:
                tag["style"] = new_style
            else:
                del tag["style"]
        clean_html = str(soup)
        path.write_text(clean_html, encoding="utf-8")
        after = gsz(path)
        print(f"{path.name}", end=" ")
        diffsize = before - after
        if diffsize == 0:
            cprint("NO CHANGE", "yellow")
        elif diffsize > 0:
            cprint(f" + {fsz(diffsize)}")
        elif diffsize < 0:
            cprint(f" - {fsz(diffsize)}")
    except:
        pass


def main() -> None:
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    if args:
        files = [Path(f) for f in args]
    else:
        files = get_files(cwd, ext=[".html", ".htm", ".md", ".rst", ".txt"])
    with get_context("spawn").Pool(8) as p:
        pending = deque()
        for f in files:
            pending.append(p.apply_async(process_file, (f,)))
            if len(pending) > 16:
                pending.popleft().get()
        while pending:
            pending.popleft().get()
    diff_size = before - gsz(cwd)
    print(f"space saved : {fsz(diff_size)}")


if __name__ == "__main__":
    raise SystemExit(main())
