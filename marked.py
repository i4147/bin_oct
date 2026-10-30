#!/data/data/com.termux/files/usr/bin/env python
# marked.py
"""A pure-Python port of the core of the npm package `marked`."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


@dataclass
class Token:
    type: str
    raw: str = ""
    text: str = ""
    tokens: Optional[List["Token"]] = None
    # Token‑specific fields (populated as needed)
    depth: int = 0
    lang: str = ""
    codeBlockStyle: str = ""
    ordered: bool = False
    start: int = 0
    loose: bool = False
    items: List["Token"] = field(default_factory=list)
    href: str = ""
    title: Optional[str] = None
    header: List[Token] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    align: List[Optional[str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class Renderer:
    """Default HTML renderer. Override methods to customise output."""

    def code(self, code: str, lang: str, escaped: bool) -> str:
        if not escaped:
            code = self._escape(code)
        lang_str = f' class="language-{lang}"' if lang else ""
        return f"<pre><code{lang_str}>{code}</code></pre>\n"

    def blockquote(self, quote: str) -> str:
        return f"<blockquote>\n{quote}</blockquote>\n"

    def html(self, html: str) -> str:
        return html

    def heading(self, text: str, level: int) -> str:
        return f"<h{level}>{text}</h{level}>\n"

    def hr(self) -> str:
        return "<hr>\n"

    def list(self, body: str, ordered: bool, start: int = 1) -> str:
        tag = "ol" if ordered else "ul"
        start_attr = f' start="{start}"' if ordered and start != 1 else ""
        return f"<{tag}{start_attr}>\n{body}</{tag}>\n"

    def listitem(self, text: str) -> str:
        return f"<li>{text}</li>\n"

    def paragraph(self, text: str) -> str:
        return f"<p>{text}</p>\n"

    def table(self, header: str, body: str) -> str:
        return f"<table>\n<thead>\n{header}</thead>\n<tbody>\n{body}</tbody>\n</table>\n"

    def tablerow(self, content: str) -> str:
        return f"<tr>\n{content}</tr>\n"

    def tablecell(self, content: str, align: Optional[str] = None) -> str:
        align_attr = f' align="{align}"' if align else ""
        return f"<td{align_attr}>{content}</td>\n"

    def strong(self, text: str) -> str:
        return f"<strong>{text}</strong>"

    def em(self, text: str) -> str:
        return f"<em>{text}</em>"

    def codespan(self, text: str) -> str:
        return f"<code>{self._escape(text)}</code>"

    def br(self) -> str:
        return "<br>"

    def del_(self, text: str) -> str:
        return f"<del>{text}</del>"

    def link(self, href: str, title: Optional[str], text: str) -> str:
        title_attr = f' title="{title}"' if title else ""
        return f'<a href="{href}"{title_attr}>{text}</a>'

    def image(self, href: str, title: Optional[str], text: str) -> str:
        title_attr = f' title="{title}"' if title else ""
        return f'<img src="{href}" alt="{text}"{title_attr}>'

    def text(self, text: str) -> str:
        return text

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


class Tokenizer:
    """Breaks raw Markdown into tokens. Regex‑based, like the original."""

    def __init__(self, options: Dict[str, Any]):
        self.options = options
        self.rules = self._build_rules()

    def _build_rules(self) -> List[tuple]:
        # Each rule is (name, compiled_regex, handler)
        return [
            ("code", re.compile(r"^( {4}[^\n]+\n*)+", re.M), self._code),
            ("fences", re.compile(r"^ *(`{3,}|~{3,})[ \.]*(\S+)? *\n([\s\S]*?)\s*\1 *(?:\n+|$)", re.M), self._fences),
            ("heading", re.compile(r"^ *(#{1,6}) +([^\n]+?) *#* *(?:\n+|$)", re.M), self._heading),
            (
                "nptable",
                re.compile(r"^ *(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n*", re.M),
                self._nptable,
            ),
            ("lheading", re.compile(r"^([^\n]+)\n *(=|-){2,} *(?:\n+|$)", re.M), self._lheading),
            ("blockquote", re.compile(r"^( *>[^\n]+(\n(?!def)[^\n]+)*\n*)+", re.M), self._blockquote),
            ("list", re.compile(r"^( *)(bull) [\s\S]+?(?:hr|def|\n{2,}(?! )(?!\1bull )\n*|\s*$)", re.M), self._list),
            (
                "html",
                re.compile(r"^ *(?:comment *(?:\n|\s*$)|closed *(?:\n{2,}|\s*$)|closing *(?:\n{2,}|\s*$))", re.M),
                self._html,
            ),
            (
                "def",
                re.compile(r"^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +[\"(]([^\n]+)[\")])? *(?:\n+|$)", re.M),
                self._def,
            ),
            ("table", re.compile(r"^ *\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n*", re.M), self._table),
            ("hr", re.compile(r"^ *(?:[*\-_] *){3,} *(?:\n+|$)", re.M), self._hr),
            ("newline", re.compile(r"^\n+", re.M), self._newline),
            (
                "paragraph",
                re.compile(r"^((?:[^\n]+\n?(?!hr|heading|lheading|blockquote|tag|def))+)\n*", re.M),
                self._paragraph,
            ),
            ("text", re.compile(r"^[^\n]+", re.M), self._text),
            ("escape", re.compile(r"^\\([\\`*{}\[\]()#+\-.!_>~|])", re.M), self._escape),
            ("autolink", re.compile(r"^<([^ >]+(@|:\/)[^ >]+)>", re.M), self._autolink),
            ("url", re.compile(r"^(https?:\/\/[^\s<]+[^<.,:;\"')\]\s])", re.M), self._url),
            #            ("tag", re.compile(r"^<!--[\s\S]*?-->|^<\/?\w+(?\:\"*\[^"]*"|'[^']*'|[^'">])*?>", re.M), self._tag),
            (
                "link",
                re.compile(
                    r"^!?\[((?:\[[^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*)\]\(\s*<?([\s\S]*?)>?(?:\s+['\"]([\s\S]*?)['\"])?\s*\)",
                    re.M,
                ),
                self._link,
            ),
            (
                "reflink",
                re.compile(r"^!?\[((?:\[[^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*)\]\s*\[([^\]]*)\]", re.M),
                self._reflink,
            ),
            ("nolink", re.compile(r"^!?\[((?:\[[^\]]*\]|[^\[\]])*)\]", re.M), self._nolink),
            ("strong", re.compile(r"^__([\s\S]+?)__(?!_)|^\*\*([\s\S]+?)\*\*(?!\*)", re.M), self._strong),
            ("em", re.compile(r"^\b_((?:[^_]|__)+?)_\b|^\*((?:\*\*|[\s\S])+?)\*(?!\*)", re.M), self._em),
            ("code", re.compile(r"^(`+)\s*([\s\S]*?[^`])\s*\1(?!`)", re.M), self._codespan),
            ("br", re.compile(r"^ {2,}\n(?!\s*$)", re.M), self._br),
            ("del", re.compile(r"^~~(?=\S)([\s\S]*?\S)~~", re.M), self._del),
            ("text", re.compile(r"^[\s\S]+?(?=[\\<!\[_*`~]|https?:\/\/| {2,}\n|$)", re.M), self._text),
        ]

    # --- Individual tokenizer handlers (simplified) ---

    def _code(self, cap: re.Match) -> Token:
        text = cap.group(0)
        return Token("code", raw=text, text=text.rstrip("\n"))

    def _fences(self, cap: re.Match) -> Token:
        lang = cap.group(2) or ""
        code = cap.group(3)
        return Token("code", raw=cap.group(0), text=code, lang=lang)

    def _heading(self, cap: re.Match) -> Token:
        level = len(cap.group(1))
        text = cap.group(2)
        return Token("heading", raw=cap.group(0), text=text, depth=level)

    def _nptable(self, cap: re.Match) -> Token:
        header = cap.group(1)
        align = cap.group(2)
        body = cap.group(3)
        return Token("table", raw=cap.group(0), header=header, align=align, text=body)

    def _lheading(self, cap: re.Match) -> Token:
        level = 1 if cap.group(2) == "=" else 2
        return Token("heading", raw=cap.group(0), text=cap.group(1), depth=level)

    def _blockquote(self, cap: re.Match) -> Token:
        text = re.sub(r"^ *> ?", "", cap.group(0), flags=re.M)
        return Token("blockquote", raw=cap.group(0), text=text)

    def _list(self, cap: re.Match) -> Token:
        # Simplified list handling (does not parse nested lists perfectly)
        raw = cap.group(0)
        ordered = bool(re.match(r"^ *\d+\. ", raw))
        return Token("list", raw=raw, ordered=ordered, text=raw)

    def _html(self, cap: re.Match) -> Token:
        return Token("html", raw=cap.group(0), text=cap.group(0))

    def _def(self, cap: re.Match) -> Token:
        # Definition – treated as no‑op in this simplified port
        return Token("def", raw=cap.group(0))

    def _table(self, cap: re.Match) -> Token:
        header = cap.group(1)
        align = cap.group(2)
        body = cap.group(3)
        return Token("table", raw=cap.group(0), header=header, align=align, text=body)

    def _hr(self, cap: re.Match) -> Token:
        return Token("hr", raw=cap.group(0))

    def _newline(self, cap: re.Match) -> Token:
        return Token("space", raw=cap.group(0))

    def _paragraph(self, cap: re.Match) -> Token:
        return Token("paragraph", raw=cap.group(0), text=cap.group(0).rstrip("\n"))

    def _text(self, cap: re.Match) -> Token:
        return Token("text", raw=cap.group(0), text=cap.group(0))

    # --- Inline tokenizers ---

    def _escape(self, cap: re.Match) -> Token:
        return Token("text", raw=cap.group(0), text=cap.group(1))

    def _autolink(self, cap: re.Match) -> Token:
        text = cap.group(1)
        href = text
        return Token("link", raw=cap.group(0), text=text, href=href)

    def _url(self, cap: re.Match) -> Token:
        text = cap.group(1)
        return Token("link", raw=cap.group(0), text=text, href=text)

    def _tag(self, cap: re.Match) -> Token:
        return Token("html", raw=cap.group(0), text=cap.group(0))

    def _link(self, cap: re.Match) -> Token:
        text = cap.group(1)
        href = cap.group(2)
        title = cap.group(3)
        return Token("link", raw=cap.group(0), text=text, href=href, title=title)

    def _reflink(self, cap: re.Match) -> Token:
        # Simplified: treat as plain text
        return Token("text", raw=cap.group(0), text=cap.group(0))

    def _nolink(self, cap: re.Match) -> Token:
        return Token("text", raw=cap.group(0), text=cap.group(0))

    def _strong(self, cap: re.Match) -> Token:
        text = cap.group(1) or cap.group(2)
        return Token("strong", raw=cap.group(0), text=text)

    def _em(self, cap: re.Match) -> Token:
        text = cap.group(1) or cap.group(2)
        return Token("em", raw=cap.group(0), text=text)

    def _codespan(self, cap: re.Match) -> Token:
        return Token("codespan", raw=cap.group(0), text=cap.group(2))

    def _br(self, cap: re.Match) -> Token:
        return Token("br", raw=cap.group(0))

    def _del(self, cap: re.Match) -> Token:
        return Token("del", raw=cap.group(0), text=cap.group(1))


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class Lexer:
    """Tokenises a Markdown string into a flat list of block tokens."""

    def __init__(self, options: Dict[str, Any]):
        self.options = options
        self.tokenizer = Tokenizer(options)

    def lex(self, src: str) -> List[Token]:
        src = src.replace("\r\n", "\n").replace("\r", "\n")
        src += "\n\n"
        tokens: List[Token] = []
        while src:
            for name, regex, handler in self.tokenizer.rules:
                cap = regex.match(src)
                if cap:
                    token = handler(cap)
                    src = src[cap.end() :]
                    if token.type == "space":
                        continue
                    tokens.append(token)
                    break
            else:
                # Fallback – consume one character to avoid infinite loop
                tokens.append(Token("text", raw=src[0], text=src[0]))
                src = src[1:]
        return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class Parser:
    """Turns tokens into HTML via a Renderer."""

    def __init__(self, options: Dict[str, Any]):
        self.options = options
        self.renderer = options.get("renderer") or Renderer()
        self.tokenizer = Tokenizer(options)

    def parse(self, tokens: List[Token]) -> str:
        out = []
        for token in tokens:
            out.append(self._render_token(token))
        return "".join(out)

    def _render_token(self, token: Token) -> str:
        if token.type == "heading":
            text = self._render_inline(token.text)
            return self.renderer.heading(text, token.depth)
        if token.type == "paragraph":
            text = self._render_inline(token.text)
            return self.renderer.paragraph(text)
        if token.type == "code":
            return self.renderer.code(token.text, token.lang, False)
        if token.type == "blockquote":
            inner = Lexer(self.options).lex(token.text)
            body = self.parse(inner)
            return self.renderer.blockquote(body)
        if token.type == "hr":
            return self.renderer.hr()
        if token.type == "list":
            return self._render_list(token)
        if token.type == "table":
            return self._render_table(token)
        if token.type == "html":
            return self.renderer.html(token.text)
        if token.type == "text":
            return self._render_inline(token.text)
        if token.type == "space":
            return "\n"
        # Unknown token – render raw
        return token.raw

    def _render_inline(self, text: str) -> str:
        """Very small inline parser: strong, em, codespan, link, del, br."""
        # Tokenise inline content
        tokens = self._inline_tokens(text)
        out = []
        for tok in tokens:
            if tok.type == "strong":
                out.append(self.renderer.strong(self._render_inline(tok.text)))
            elif tok.type == "em":
                out.append(self.renderer.em(self._render_inline(tok.text)))
            elif tok.type == "codespan":
                out.append(self.renderer.codespan(tok.text))
            elif tok.type == "link":
                out.append(self.renderer.link(tok.href, tok.title, self._render_inline(tok.text)))
            elif tok.type == "del":
                out.append(self.renderer.del_(self._render_inline(tok.text)))
            elif tok.type == "br":
                out.append(self.renderer.br())
            else:
                out.append(self.renderer.text(tok.text or tok.raw))
        return "".join(out)

    def _inline_tokens(self, text: str) -> List[Token]:
        """Rough inline tokeniser – sufficient for the supported syntax."""
        tokens: List[Token] = []
        # Simple regex‑based split for inline constructs
        pattern = re.compile(
            r"(\*\*.*?\*\*|__.*?__|"
            r"\*.*?\*|_.*?_|"
            r"`[^`]*`|"
            r"\[.*?\]\(.*?\)|"
            r"~~.*?~~|"
            r" {2,}\n)",
            re.S,
        )
        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                tokens.append(Token("text", raw=text[last : m.start()], text=text[last : m.start()]))
            s = m.group(0)
            if s.startswith(("**", "__")):
                tokens.append(Token("strong", raw=s, text=s[2:-2]))
            elif s.startswith(("*", "_")):
                tokens.append(Token("em", raw=s, text=s[1:-1]))
            elif s.startswith("`"):
                tokens.append(Token("codespan", raw=s, text=s[1:-1]))
            elif s.startswith("["):
                # link: [text](href)
                inner = re.match(r"\[(.*?)\]\((.*?)\)", s)
                if inner:
                    tokens.append(Token("link", raw=s, text=inner.group(1), href=inner.group(2)))
                else:
                    tokens.append(Token("text", raw=s, text=s))
            elif s.startswith("~~"):
                tokens.append(Token("del", raw=s, text=s[2:-2]))
            elif s.strip() == "" and "\n" in s:
                tokens.append(Token("br", raw=s))
            else:
                tokens.append(Token("text", raw=s, text=s))
            last = m.end()
        if last < len(text):
            tokens.append(Token("text", raw=text[last:], text=text[last:]))
        return tokens

    def _render_list(self, token: Token) -> str:
        # Simplified list rendering (split on newlines)
        lines = token.text.split("\n")
        items = [line for line in lines if line.strip()]
        body = ""
        for item in items:
            item_text = re.sub(r"^ *[*+-] |^ *\d+\. ", "", item)
            body += self.renderer.listitem(self._render_inline(item_text))
        return self.renderer.list(body, token.ordered)

    def _render_table(self, token: Token) -> str:
        # Very simplified table handling
        header_cells = [c.strip() for c in token.header.split("|")]
        aligns = [a.strip() for a in token.align.split("|")] if token.align else []
        header_html = ""
        for i, cell in enumerate(header_cells):
            align = aligns[i] if i < len(aligns) else None
            header_html += self.renderer.tablecell(self._render_inline(cell), align)
        body_html = ""
        for row in token.text.split("\n"):
            if not row.strip():
                continue
            cells = [c.strip() for c in row.split("|")]
            row_html = ""
            for i, cell in enumerate(cells):
                align = aligns[i] if i < len(aligns) else None
                row_html += self.renderer.tablecell(self._render_inline(cell), align)
            body_html += self.renderer.tablerow(row_html)
        return self.renderer.table(self.renderer.tablerow(header_html), body_html)


# ---------------------------------------------------------------------------
# Public API – the `marked` object
# ---------------------------------------------------------------------------


class Marked:
    """A locally scoped `marked` instance (mirrors `new Marked()`)."""

    def __init__(self, *args: Union[Dict[str, Any], Callable[[Any], None]]):
        self.defaults: Dict[str, Any] = {
            "async": False,
            "breaks": False,
            "gfm": True,
            "pedantic": False,
            "renderer": None,
            "silent": False,
            "tokenizer": None,
            "walkTokens": None,
        }
        for arg in args:
            if callable(arg):
                # Extension function (not fully supported here)
                pass
            elif isinstance(arg, dict):
                self.defaults.update(arg)

    def use(self, options: Dict[str, Any]) -> "Marked":
        self.defaults.update(options)
        return self

    def parse(self, src: str, options: Optional[Dict[str, Any]] = None) -> str:
        opts = {**self.defaults, **(options or {})}
        lexer = Lexer(opts)
        tokens = lexer.lex(src)
        if opts.get("walkTokens"):
            for tok in tokens:
                opts["walkTokens"](tok)
        parser = Parser(opts)
        return parser.parse(tokens)

    def parseInline(self, src: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Parse inline Markdown only (no block‑level tokens)."""
        opts = {**self.defaults, **(options or {})}
        parser = Parser(opts)
        return parser._render_inline(src)


# Global instance, like the npm package's default export
marked = Marked()

__all__ = ["marked", "Marked", "Renderer", "Tokenizer", "Lexer", "Parser", "Token"]
