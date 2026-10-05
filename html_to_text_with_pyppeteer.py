#!/data/data/com.termux/files/usr/bin/python3.12
"""Write an async Python script using pyppeteer that takes a URL as a command-line argument, launches a headless browser, navigates to that URL, and saves a full-page screenshot to "example.png".
It should also extract the page's body text content and write it to a text file whose name is derived from the input URL (with a .txt suffix), then evaluate and print the viewport's width, height, and device pixel ratio as a dictionary.
The script should run the entire flow within an asyncio event loop and close the browser when finished."""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path
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
