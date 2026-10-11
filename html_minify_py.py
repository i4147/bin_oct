#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to write a Python HTML minifier script with the following specification:

Write a Python 3 script (intended to run under Termux on Android, with a `#!/data/data/com.termux/files/usr/bin/env python` shebang) that minifies HTML files. Use `from __future__ import annotations`, and import the standard `re`, `sys`, and `pathlib.Path`, plus `typing.TYPE_CHECKING`. Import `get_files` and `mpf` from a local helper module named `dh`, and use `lxml.html` for DOM parsing. Import `HtmlElement` from `lxml.html` only under `TYPE_CHECKING`.

Core design: implement a class `HTMLMinifier` whose constructor accepts these boolean keyword options with defaults: `remove_comments=True`, `collapse_whitespace=True`, `remove_empty_attributes=True`, `remove_optional_tags=False`, `minify_css=False`, `minify_js=False`. Store each as an attribute, and store a private set of tags to preserve whitespace in: `pre`, `textarea`, `code`, `script`, `style`.

The public method `minify(html_str: str) -> str` should parse the input with `lxml.html.fromstring`; if that raises `lxml.html.ParserError`, fall back to `lxml.html.fragment_fromstring` with `create_parent=True`. Then run a recursive node-processing pass (`_process_node`) that respects the preserve set and applies the enabled options (comment removal, whitespace collapsing outside preserved tags, removal of empty attributes, optional tag removal, and optional CSS/JS minification). Serialize with `lxml.html.tostring(..., encoding="unicode", method="html")` and pass the result through a `_post_process` step that performs final regex-based cleanup (e.g., trimming whitespace between tags and tidying leftover spacing).

Command-line behavior: the script should be runnable directly. It should use `get_files` from `dh` to resolve input files (accepting paths or patterns from `sys.argv`), read each file, minify it with an `HTMLMinifier` instance, and write the result. Use `pathlib.Path` for all file handling. Handle errors per file so one failing file does not stop processing of the rest; report failures to stderr and exit with a nonzero status if any file failed. Report successes or summary counts to stdout. If no arguments or no matching files are given, print a usage message to stderr and exit nonzero.

Use `mpf` from `dh` where the original design calls for it (multi-file processing or progress output); treat it as an external helper and do not reimplement it.

Edge cases to handle: empty input, input that is not valid HTML (fragment fallback), content inside preserved tags left untouched, unreadable or non-UTF-8 files (report and continue), and output paths that cannot be written.

Write the complete script as a single file, with a `main()` function guarded by `if __name__ == "__main__":`, and keep the code style clean with type hints throughout.
---"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from dh import get_files, mpf
from lxml import html as lxml_html

if TYPE_CHECKING:
    from lxml.html import HtmlElement


class HTMLMinifier:
    def __init__(
        self,
        remove_comments: bool = True,
        collapse_whitespace: bool = True,
        remove_empty_attributes: bool = True,
        remove_optional_tags: bool = False,
        minify_css: bool = False,
        minify_js: bool = False,
    ):
        self.remove_comments = remove_comments
        self.collapse_whitespace = collapse_whitespace
        self.remove_empty_attributes = remove_empty_attributes
        self.remove_optional_tags = remove_optional_tags
        self.minify_css = minify_css
        self.minify_js = minify_js
        self._preserve_tags = {"pre", "textarea", "code", "script", "style"}

    def minify(self, html_str: str) -> str:
        try:
            doc = lxml_html.fromstring(html_str)
        except lxml_html.ParserError:
            doc = lxml_html.fragment_fromstring(html_str, create_parent=True)
        self._process_node(doc)
        result = lxml_html.tostring(doc, encoding="unicode", method="html")
        return self._post_process(result)

    def _process_node(self, node: HtmlElement) -> None:
        if node.tag in self._preserve_tags:
            return
        if node.text and self.collapse_whitespace:
            node.text = self._collapse_whitespace(node.text)
        if self.remove_empty_attributes and node.attrib:
            attrs_to_remove = [k for k, v in node.attrib.items() if not v or v.isspace()]
            for attr in attrs_to_remove:
                del node.attrib[attr]
        for child in list(node):
            self._process_node(child)
            if child.tail and self.collapse_whitespace:
                child.tail = self._collapse_whitespace(child.tail)

    def _collapse_whitespace(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _post_process(self, html_str: str) -> str:
        if self.remove_comments:
            html_str = re.sub(r"<!--.*?-->", "", html_str, flags=re.DOTALL)
        if self.minify_css:
            html_str = self._minify_style_tags(html_str)
        if self.minify_js:
            html_str = self._minify_script_tags(html_str)
        html_str = re.sub(r">\s+<", "><", html_str)
        html_str = re.sub(r"\s+", " ", html_str).strip()
        return html_str

    def _minify_style_tags(self, html_str: str) -> str:
        def minify_css(match):
            css = match.group(1)
            css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
            css = re.sub(r"\s*([{};:,])\s*", r"\1", css)
            css = re.sub(r";\s*}", "}", css)
            return f"<style>{css.strip()}</style>"

        return re.sub(r"<style[^>]*>(.*?)</style>", minify_css, html_str, flags=re.DOTALL)

    def _minify_script_tags(self, html_str: str) -> str:
        def minify_js(match):
            js = match.group(1)
            js = re.sub(r"//.*?$", "", js, flags=re.MULTILINE)
            js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)
            js = re.sub(r"\s+", " ", js)
            return f"<script>{js.strip()}</script>"

        return re.sub(r"<script[^>]*>(.*?)</script>", minify_js, html_str, flags=re.DOTALL)


def minify(
    html_str: str,
    remove_comments: bool = True,
    collapse_whitespace: bool = True,
    **options,
) -> str:
    minifier = HTMLMinifier(
        remove_comments=remove_comments,
        collapse_whitespace=collapse_whitespace,
        **options,
    )
    return minifier.minify(html_str)


def process_file(
    path: str | Path,
    **options,
) -> str:
    path = Path(path)
    html_str = path.read_text(encoding="utf-8")
    minified = minify(html_str, **options)
    path.write_text(minified, encoding="utf-8")
    return minified


def main():
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".html"])
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
