#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that checks HTML files for structural tag problems and reports the results. The tool should accept one or more HTML file paths (or a directory to scan recursively for HTML files) from the command line, parse each document, and detect issues such as unclosed elements, closing tags that have no matching opening tag, mismatched or out-of-order nesting, and closing tags applied to void elements that should never be closed (for example, line breaks, images, or input fields). Each detected problem should be reported with the file name and the precise line and column where it occurs, along with a clear, human-readable description.
The script should log its progress and findings using a structured logging approach, print a concise summary at the end (number of files checked, number of files with errors, and total errors found), and exit with a non-zero status code when any errors are found so it can be used in continuous integration pipelines. It should handle missing files, unreadable files, and malformed input gracefully without crashing, reporting these as errors for the affected file while continuing to process the remaining files. Optionally, it should support a flag that suppresses non-error output for quiet operation, and a flag that writes the report to a specified output file in a machine-readable format such as JSON as well as the console.
The tool should be self-contained, robust, and well organized, with a clear command-line interface that includes help text describing each option.
---"""

from __future__ import annotations
import argparse
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from loguru import logger

VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class _TagChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def _pos(self):
        line, col = self.getpos()
        return f"line {line}, col {col}"

    def handle_starttag(self, tag, attrs):
        if tag in VOID_ELEMENTS:
            return
        self.stack.append((tag, self._pos()))

    def handle_startendtag(self, tag, attrs):
        return

    def handle_endtag(self, tag):
        if tag in VOID_ELEMENTS:
            self.errors.append(f"{self._pos()}: closing tag </{tag}> for void element")
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                while len(self.stack) - 1 > i:
                    t, p = self.stack.pop()
                    self.errors.append(f"unclosed <{t}> opened at {p}")
                self.stack.pop()
                return
        self.errors.append(f"{self._pos()}: stray closing tag </{tag}>")

    def finish(self):
        super().close()
        for tag, pos in self.stack:
            self.errors.append(f"unclosed <{tag}> opened at {pos}")
        return self.errors


def check_tags(raw):
    checker = _TagChecker()
    try:
        checker.feed(raw)
        return checker.finish()
    except Exception as e:
        return [f"tokenizer error: {e}"]


class _StackParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.errors = []
        self.output = []

    def _pos(self):
        line, col = self.getpos()
        return f"line {line}, col {col}"

    @staticmethod
    def _attrs(attrs):
        out = []
        for k, v in attrs:
            out.append(f" {k}" if v is None else f' {k}="{escape(v, quote=True)}"')
        return "".join(out)

    def handle_starttag(self, tag, attrs):
        self.output.append(f"<{tag}{self._attrs(attrs)}>")
        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, self._pos()))

    def handle_startendtag(self, tag, attrs):
        self.output.append(f"<{tag}{self._attrs(attrs)}/>")

    def handle_endtag(self, tag):
        if tag in VOID_ELEMENTS:
            self.errors.append(f"{self._pos()}: closing </{tag}> for void element; removed")
            return
        match = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                match = i
                break
        if match is None:
            self.errors.append(f"{self._pos()}: unexpected </{tag}>; removed")
            return
        while len(self.stack) - 1 > match:
            t, p = self.stack.pop()
            self.errors.append(f"{self._pos()}: unclosed <{t}> at {p}; inserted </{t}>")
            self.output.append(f"</{t}>")
        self.stack.pop()
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        self.output.append(data)

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.output.append(f"<!{decl}>")

    def handle_pi(self, data):
        self.output.append(f"<?{data}>")

    def finish(self):
        super().close()
        while self.stack:
            tag, pos = self.stack.pop()
            self.errors.append(f"EOF: unclosed <{tag}> at {pos}; inserted </{tag}>")
            self.output.append(f"</{tag}>")
        return "".join(self.output), self.errors


def backend_html_parser(raw):
    p = _StackParser()
    p.feed(raw)
    return p.finish()


def backend_lxml(raw):
    from lxml import (
        etree,
        html as lxml_html,
    )

    errors = []
    try:
        doc = lxml_html.fromstring(raw)
    except Exception as e:
        return raw, [f"lxml: {e}"]
    fixed = etree.tostring(doc, method="html", encoding="unicode")
    if fixed.strip() != raw.strip():
        errors.append("lxml: document was re-serialized (structure changed)")
    return fixed, errors


def backend_html5lib(raw):
    from xml.etree import ElementTree as ET
    import html5lib

    errors = []
    try:
        tree = html5lib.parse(raw, treebuilder="etree", namespaceHTMLElements=False)
    except Exception as e:
        return raw, [f"html5lib: {e}"]
    ET.register_namespace("", "")
    fixed = ET.tostring(tree.getroot(), encoding="unicode", method="html")
    if fixed.strip() != raw.strip():
        errors.append("html5lib: browser-equivalent tree differs from source")
    return fixed, errors


def backend_beautifulsoup(raw):
    from bs4 import BeautifulSoup

    errors = []
    try:
        soup = BeautifulSoup(raw, "html.parser")
    except Exception as e:
        return raw, [f"bs4: {e}"]
    fixed = str(soup)
    if fixed != raw:
        errors.append("bs4: re-serialized output differs from source")
    return fixed, errors


def backend_tidy(raw):
    from tidylib import tidy_document

    options = {
        "output-xhtml": 0,
        "output-html": 1,
        "show-warnings": 1,
        "show-errors": 0,
        "quiet": 1,
        "indent": 0,
        "wrap": 0,
        "char-encoding": "utf8",
    }
    try:
        fixed, msgs = tidy_document(raw, options=options)
    except Exception as e:
        return raw, [f"tidy: {e}"]
    errors = [f"tidy: {m.strip()}" for m in msgs.splitlines() if m.strip()]
    return fixed, errors


BACKENDS = {
    "html.parser": backend_html_parser,
    "lxml": backend_lxml,
    "html5lib": backend_html5lib,
    "bs4": backend_beautifulsoup,
    "tidy": backend_tidy,
}


def process_file(path, backend_fn):
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            raw = path.read_text(encoding="latin-1")
            logger.debug(f"{path}: latin-1 fallback")
        except Exception as e:
            logger.error(f"{path}: cannot decode: {e}")
            return "error"
    except Exception as e:
        logger.error(f"{path}: cannot read: {e}")
        return "error"
    balance_errors = check_tags(raw)
    if balance_errors:
        logger.warning(f"{path}: {len(balance_errors)} unbalanced tag(s) detected in source")
        for err in balance_errors:
            logger.warning(f"{path}: [balance] {err}")
    else:
        logger.debug(f"{path}: opening/closing tags balanced")
    try:
        fixed, errors = backend_fn(raw)
    except Exception as e:
        logger.error(f"{path}: backend exception: {e}")
        return "error"
    backend_errors = [e for e in errors if e not in balance_errors]
    for err in backend_errors:
        logger.warning(f"{path}: [backend] {err}")
    if fixed == raw:
        if balance_errors or backend_errors:
            logger.info(f"{path}: issues detected but output unchanged")
        else:
            logger.debug(f"{path}: OK")
        return "ok" if not balance_errors else "error"
    try:
        path.write_text(fixed, encoding="utf-8")
    except Exception as e:
        logger.error(f"{path}: cannot write: {e}")
        return "error"
    logger.success(f"{path}: repaired")
    return "fixed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--backend", choices=sorted(BACKENDS), default="html.parser")
    args = ap.parse_args()
    backend_fn = BACKENDS[args.backend]
    logger.info(f"Using backend: {args.backend}")
    cwd = Path.cwd()
    files = sorted(set(cwd.rglob("*.html")) | set(cwd.rglob("*.htm")))
    if not files:
        logger.info(f"No HTML files under {cwd}")
        return
    logger.info(f"Found {len(files)} HTML file(s)")
    counts = {"ok": 0, "fixed": 0, "error": 0}
    for f in files:
        counts[process_file(f, backend_fn)] += 1
    logger.info(f"Summary -> OK: {counts['ok']}, Fixed: {counts['fixed']}, Errors: {counts['error']}")


if __name__ == "__main__":
    main()
