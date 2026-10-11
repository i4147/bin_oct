#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script that uses the pyppeteer library to open a web page given as a command-line argument. The script should be runnable under Termux (Android) using a shebang pointing to the Termux Python path, and should use `from __future__ import annotations` at the top.

Requirements:

1. **Purpose**: Launch a headless Chromium browser via pyppeteer, navigate to a URL supplied as the first command-line argument, capture a screenshot, extract the page's text content, save that text to a file, and print the viewport dimensions and device pixel ratio.

2. **Imports**: Use `asyncio`, `sys`, `pathlib.Path`, and `pyppeteer.launch`. Include `from __future__ import annotations`.

3. **Input**: The URL is read from `sys.argv[1]`. No other arguments are expected. No argument validation or usage message is required beyond what naturally occurs (a missing argument will raise an IndexError).

4. **Browser flow** (inside an async `main()` function):
   - Launch a browser with default `launch()` options (no custom arguments).
   - Create a new page.
   - Navigate to the URL with `goto`.
   - Take a full-page-default screenshot (viewport only, using default options) and save it to a fixed filename `example.png` in the current working directory. The path is passed as a dictionary argument containing the key `"path"`.
   - Evaluate the JavaScript expression `document.body.textContent` with the `force_expr=True` keyword so pyppeteer treats the string as an expression rather than a function, storing the result in `content`.
   - Derive the output text filename by taking the URL string itself, converting it to a Path object, and calling `with_suffix(".txt")`. Note this behavior: because the full URL is used as the path, `with_suffix` operates on the last path component of the URL string, which may produce unexpected filenames (for example, URLs containing slashes will create nested path components, and URLs without a dot in the final segment will have `.txt` appended). Write the content to that path using UTF-8 encoding via `write_text`.
   - Evaluate a multi-line arrow-function JavaScript snippet that returns an object with three fields: `width` from `document.documentElement.clientWidth`, `height` from `document.documentElement.clientHeight`, and `deviceScaleFactor` from `window.devicePixelRatio`. Store the result in `dimensions`.
   - Print the `dimensions` dictionary to standard output.
   - Close the browser.

5. **Execution**: At module level, obtain the default event loop with `asyncio.get_event_loop()` and run `main()` to completion with `run_until_complete`.

6. **Error handling**: The script contains no explicit try/except blocks; exceptions from network failures, navigation timeouts, missing arguments, file write errors, or browser launch failures propagate and terminate the script. The browser is not closed if an exception occurs before the final close call. Reproduce this behavior faithfully unless otherwise noted.

7. **Edge cases and notes**:
   - The screenshot filename is always `example.png` regardless of the URL, so repeated runs overwrite it.
   - If `document.body` is null (e.g., on some non-HTML pages), `textContent` evaluation will fail.
   - The script depends on Chromium being available to pyppeteer (it downloads one on first launch if missing), which may be slow or unsupported on Termux.
   - Dimensions are reported from the page's documentElement, not from the browser window size.

8. **Usage**: Intended to be run from a shell as `python script.py <url>` or directly as an executable with the Termux shebang. Output includes the printed dimensions dictionary; the screenshot and text file are side effects written to the working directory.

Reproduce the behavior and structure described above, using simple, direct code without additional features, logging, or argument parsing libraries.
---"""

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
