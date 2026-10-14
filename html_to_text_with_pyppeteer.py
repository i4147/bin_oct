#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single web page URL from the command line, opens it in a headless browser, and captures both a visual and textual snapshot of the page. The script should save a full-page screenshot image named "example.png" in the current working directory, extract all visible text from the page body, and save that text to a plain-text file that uses the same base name as the URL-derived path with a ".txt" extension and UTF-8 encoding. It should also query the rendered page for its viewport width, viewport height, and device pixel ratio, then print these values in a readable form to the console. The tool must wait for the page to finish loading before capturing anything, and it should release the browser resources cleanly once all work is complete. Handle a missing URL argument gracefully by showing a brief usage message and exiting. Keep the script concise, self-contained, and runnable from the terminal with a single command.
---"""

from __future__ import annotations
import asyncio
from pathlib import Path
import sys
from pyppeteer import launch


async def main():
    url = sys.argv[1]
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    await page.screenshot({"path": "example.png"})
    content = await page.evaluate("document.body.textContent", force_expr=True)
    outfile = Path(url).with_suffix(".txt")
    Path(outfile).write_text(content, encoding="utf-8")
    dimensions = await page.evaluate("""() => {
        return {
            width: document.documentElement.clientWidth,
            height: document.documentElement.clientHeight,
            deviceScaleFactor: window.devicePixelRatio,
        }
    }""")
    print(dimensions)
    await browser.close()


asyncio.get_event_loop().run_until_complete(main())
