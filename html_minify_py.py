#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as an HTML minifier tool. It should accept raw HTML markup as input (from a string, a file, or a batch of files in a directory) and produce a smaller, functionally equivalent HTML output. The tool should be configurable with options that control which optimizations are applied: removing HTML comments, collapsing redundant whitespace while leaving whitespace-sensitive content untouched, stripping empty attributes, optionally removing optional closing or implied tags, and optionally minifying embedded CSS and JavaScript blocks. Whitespace-sensitive elements such as preformatted text, code samples, text areas, and script or style contents must be preserved exactly. The tool should gracefully handle malformed or fragmentary HTML by parsing it leniently and still producing valid output. It should be usable both as an importable class with a simple minify method and as a command-line utility that reads one or more input files, writes minified results to an output location (or alongside the originals with a suffix), and reports basic statistics such as original size, minified size, and percentage saved. Include clear error handling for missing files, unreadable input, and parsing failures, and print a concise summary when processing multiple files.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys
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
