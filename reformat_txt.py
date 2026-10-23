#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations

import argparse
import codecs
import os
import re
import shutil
import sys
from collections.abc import Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Final, Literal, NamedTuple

DEFAULT_WIDTH: Final[int] = 100
MIN_PIECE: Final[int] = 20
MIN_TAIL: Final[int] = 12

SKIP_DIRS: Final[frozenset[str]] = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
})

ABBREVIATIONS: Final[frozenset[str]] = frozenset({
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "sr.",
    "jr.",
    "st.",
    "vs.",
    "cf.",
    "fig.",
    "figs.",
    "vol.",
    "inc.",
    "ltd.",
    "co.",
    "corp.",
    "dept.",
    "approx.",
    "al.",
    "pp.",
    "eq.",
    "ref.",
})

SMALL_WORDS: Final[frozenset[str]] = frozenset({
    "a",
    "an",
    "the",
    "of",
    "and",
    "or",
    "for",
    "to",
    "in",
    "on",
    "at",
    "by",
    "with",
    "vs",
    "as",
})

CLOSERS: Final[str] = "\"'”’)\\]"
OPENERS: Final[str] = "\"'“‘(\\["

SENTENCE_END: Final[re.Pattern[str]] = re.compile(rf"([.!?…]+[{CLOSERS}]*)\s+(?=[{OPENERS}]*[A-Z0-9À-ÖØ-Þ])")

LIST_MARKER: Final[re.Pattern[str]] = re.compile(
    r"^(?P<indent>\s*)"
    r"(?P<marker>"
    r"[-*+•·‣◦▪●○■□–—]"
    r"|(?:\d{1,3}|#)[.)]"
    r"|[a-z][.)]"
    r"|[A-Z]\)"
    r"|(?:[ivx]{2,4}|[IVX]{2,4})[.)]"
    r"|\(\d{1,3}\)"
    r"|\([a-zA-Z]\)"
    r"|\[[ xX]\]"
    r")\s+(?P<text>\S.*)$"
)

FENCE: Final[re.Pattern[str]] = re.compile(r"^\s*(?:```|~~~)")
VERBATIM: Final[re.Pattern[str]] = re.compile(r"^\s*(?:\||>)|^\s*([-*_=])(?:\s*\1){2,}\s*$")
SETEXT_UNDERLINE: Final[re.Pattern[str]] = re.compile(r"^\s*(?:={2,}|-{2,})\s*$")
MD_HEADING: Final[re.Pattern[str]] = re.compile(r"^\s{0,3}(?P<hashes>#{1,6})\s+(?P<text>\S.*)$")
NUMBER_PREFIX: Final[re.Pattern[str]] = re.compile(r"^\s*(\d+(?:\.\d+)+)")
EMPH_DOUBLE: Final[re.Pattern[str]] = re.compile(r"^\s*(\*\*|__)\s*(?P<t>[^*_\s].*?)\s*\1\s*[:.]?\s*$")
EMPH_SINGLE: Final[re.Pattern[str]] = re.compile(r"^\s*(\*|_)(?=\S)(?P<t>[^*_].*?)(?<=\S)\1\s*[:.]?\s*$")
CHAPTER: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?i:chapter|section|part|appendix|article|book|lesson|unit)\s+(?:\d+[\d.]*|[IVXLC]+)\b.*$"
)
NUMBERED_HEADING: Final[re.Pattern[str]] = re.compile(r"^\s*\d+(?:\.\d+)+\.?\s+[A-Z].*$")
TERMINAL: Final[re.Pattern[str]] = re.compile(rf"[.!?:;…][{CLOSERS}]*$")

BREAK_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r";\s"),
    re.compile(r":\s"),
    re.compile(r",\s"),
    re.compile(r"\s(?=(?:—|–|--)\s)"),
    re.compile(
        r"\s(?=(?:and|but|or|which|who|whom|whose|whereas|while|because|although|though"
        r"|unless|until|however|therefore|when|where)\b)",
        re.IGNORECASE,
    ),
    re.compile(r"\s"),
)
PUNCTUATION_BREAKS: Final[int] = 3

CHAPTER_LEVELS: Final[dict[str, int]] = {"part": 1, "book": 1, "chapter": 2, "appendix": 2}
BULLETS: Final[frozenset[str]] = frozenset("-*+•·‣◦▪●○■□–—")

GREEN: Final[str] = "\033[32m"
DIM: Final[str] = "\033[2m"
YELLOW: Final[str] = "\033[33m"
RED: Final[str] = "\033[31m"
RESET: Final[str] = "\033[0m"

Status = Literal["changed", "unchanged", "converted", "skipped", "error"]


class Result(NamedTuple):
    path: Path
    status: Status
    before: int = 0
    after: int = 0
    detail: str = ""
    target: Path | None = None
    removed: bool = False


@dataclass(frozen=True)
class Options:
    width: int
    dry_run: bool
    markdown: bool
    remove: bool


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    raw: str
    underline: str | None = None


@dataclass
class ListItem:
    indent: str
    marker: str
    parts: list[str] = field(default_factory=list)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_abbreviation(chunk: str) -> bool:
    words = chunk.split()
    if not words:
        return False
    token = words[-1].lstrip(OPENERS)
    lowered = token.lower()
    if lowered in ABBREVIATIONS:
        return True
    if re.fullmatch(r"[A-Z]\.", token):
        return True
    if re.fullmatch(r"(?:[a-z]\.){2,}", token):
        return True
    return len(words) == 1 and re.fullmatch(r"(?:\d+|[a-zA-Z])[.)]", token) is not None


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    start = 0
    for match in SENTENCE_END.finditer(text):
        chunk = text[start : match.end(1)]
        if is_abbreviation(chunk):
            continue
        sentences.append(chunk.strip())
        start = match.end()
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def protected_mask(text: str) -> list[bool]:
    mask: list[bool] = []
    depth = 0
    in_code = False
    for char in text:
        if char == "`":
            in_code = not in_code
        elif not in_code:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth = max(0, depth - 1)
        mask.append(depth > 0 or in_code)
    return mask


def find_break(text: str, room: int) -> int | None:
    mask = protected_mask(text)
    for respect_protection in (True, False):
        for index, pattern in enumerate(BREAK_PATTERNS):
            best: int | None = None
            for match in pattern.finditer(text):
                position = match.start() + 1 if index < PUNCTUATION_BREAKS else match.start()
                if position > room:
                    break
                if position < MIN_PIECE or len(text) - position < MIN_TAIL:
                    continue
                if respect_protection and mask[match.start()]:
                    continue
                best = position
            if best is not None:
                return best
    space = text.find(" ", room)
    return space if space != -1 else None


def wrap(prefix: str, text: str, continuation: str, width: int) -> list[str]:
    lines: list[str] = []
    current = prefix
    remaining = text
    while True:
        room = max(width - len(current), MIN_PIECE)
        if len(remaining) <= room:
            lines.append(current + remaining)
            return lines
        cut = find_break(remaining, room)
        if cut is None or cut >= len(remaining):
            lines.append(current + remaining)
            return lines
        lines.append(current + remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
        current = continuation


def is_title_case(words: Sequence[str]) -> bool:
    significant = [w for w in words if w.lower() not in SMALL_WORDS]
    return bool(significant) and words[0][:1].isupper() and all(w[:1].isupper() or w[:1].isdigit() for w in significant)


def setext_heading(line: str, following: str) -> Heading | None:
    if not SETEXT_UNDERLINE.match(following) or LIST_MARKER.match(line):
        return None
    level = 1 if following.strip().startswith("=") else 2
    return Heading(level, line.strip(), line, following)


def strong_heading(line: str) -> Heading | None:
    stripped = line.strip()
    markdown = MD_HEADING.match(line)
    if markdown:
        text = re.sub(r"\s+#+\s*$", "", markdown["text"]).strip()
        return Heading(len(markdown["hashes"]), text, line)
    for pattern in (EMPH_DOUBLE, EMPH_SINGLE):
        emphasis = pattern.match(line)
        if emphasis and emphasis.group(1) not in emphasis["t"] and len(emphasis["t"].split()) <= 12:
            return Heading(2, emphasis["t"].strip().rstrip(":").rstrip(), line)
    if len(stripped) <= 80 and CHAPTER.match(stripped):
        return Heading(CHAPTER_LEVELS.get(stripped.split()[0].lower(), 3), stripped, line)
    number = NUMBER_PREFIX.match(stripped)
    if (
        number
        and NUMBERED_HEADING.match(stripped)
        and len(stripped) <= 100
        and not stripped.endswith((".", "!", "?", ",", ";"))
    ):
        return Heading(min(6, len(number.group(1).split("."))), stripped, line)
    return None


def weak_heading(line: str) -> Heading | None:
    stripped = line.strip()
    if len(stripped) > 80:
        return None
    words = stripped.split()
    letters = sum(1 for c in stripped if c.isalpha())
    if letters >= 3 and stripped.isupper() and len(words) <= 10 and not stripped.endswith((".", ",", ";")):
        return Heading(2, stripped.rstrip(":").rstrip(), line)
    if stripped.endswith(":") and 1 <= len(words) <= 6 and is_title_case([w.rstrip(":") for w in words]):
        return Heading(3, stripped.rstrip(":"), line)
    return None


def to_markdown_marker(marker: str) -> tuple[str, str]:
    if marker in BULLETS:
        return "-", ""
    if marker.startswith("["):
        return f"- {marker}", ""
    if marker.startswith("#"):
        return "1.", ""
    number = re.fullmatch(r"(\d+)[.)]|\((\d+)\)", marker)
    if number:
        return f"{number.group(1) or number.group(2)}.", ""
    return "-", f"{marker} "


class Formatter:
    def __init__(self, width: int, markdown: bool) -> None:
        self.width = width
        self.markdown = markdown
        self.after_text = False
        self.out: list[str] = []
        self.paragraph: list[str] = []
        self.paragraph_indent = ""
        self.item: ListItem | None = None
        self.after_list = False

    def blank(self) -> None:
        self.after_text = False
        if self.out and self.out[-1] != "":
            self.out.append("")

    def blank_line(self) -> None:
        self.flush()
        self.blank()
        self.after_list = False

    def verbatim(self, line: str) -> None:
        self.flush()
        self.after_text = False
        self.out.append(line)

    def heading(self, heading: Heading) -> None:
        self.flush()
        self.blank()
        if self.markdown:
            self.out.append(f"{'#' * heading.level} {heading.text}")
        else:
            self.out.append(heading.raw.rstrip())
            if heading.underline is not None:
                self.out.append(heading.underline.strip())
        self.after_list = False

    def start_item(self, indent: str, marker: str, text: str) -> None:
        self.flush()
        prefix = ""
        if self.markdown:
            marker, prefix = to_markdown_marker(marker.strip())
            if self.after_text:
                self.blank()
        self.item = ListItem(indent=indent, marker=marker.strip() + " ", parts=[prefix + text.strip()])

    def text_line(self, line: str) -> None:
        indent = line[: len(line) - len(line.lstrip())]
        stripped = line.strip()
        if self.item is not None:
            if len(indent) > len(self.item.indent) or not TERMINAL.search(self.item.parts[-1]):
                self.item.parts.append(stripped)
                return
            self.flush_item()
        if not self.paragraph:
            self.paragraph_indent = indent
        self.paragraph.append(stripped)

    def flush_paragraph(self) -> None:
        if not self.paragraph:
            return
        if self.after_list:
            self.blank()
        self.after_list = False
        text = normalize(" ".join(self.paragraph))
        for sentence in split_sentences(text):
            self.out.extend(wrap(self.paragraph_indent, sentence, self.paragraph_indent, self.width))
        self.paragraph = []
        self.after_text = True

    def flush_item(self) -> None:
        item = self.item
        if item is None:
            return
        lead = item.indent + item.marker
        pad = item.indent + " " * len(item.marker)
        text = normalize(" ".join(item.parts))
        for number, sentence in enumerate(split_sentences(text)):
            self.out.extend(wrap(lead if number == 0 else pad, sentence, pad, self.width))
        self.item = None
        self.after_list = True
        self.after_text = False

    def flush(self) -> None:
        self.flush_paragraph()
        self.flush_item()

    def result(self) -> list[str]:
        self.flush()
        while self.out and self.out[-1] == "":
            self.out.pop()
        return self.out


def format_text(text: str, width: int, markdown: bool) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    formatter = Formatter(width, markdown)
    in_fence = False
    index = 0
    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip()
        stripped = line.strip()
        following = lines[index + 1] if index + 1 < len(lines) else ""
        index += 1

        if FENCE.match(line):
            in_fence = not in_fence
            formatter.verbatim(raw)
            continue
        if in_fence:
            formatter.verbatim(raw)
            continue
        if not stripped:
            formatter.blank_line()
            continue
        if VERBATIM.match(line):
            formatter.verbatim(line)
            continue
        setext = setext_heading(line, following)
        if setext:
            formatter.heading(setext)
            index += 1
            continue
        strong = strong_heading(line)
        if strong:
            formatter.heading(strong)
            continue
        match = LIST_MARKER.match(line)
        if match:
            formatter.start_item(match["indent"], match["marker"], match["text"])
            continue
        weak = weak_heading(line)
        if weak:
            formatter.heading(weak)
            continue
        formatter.text_line(line)

    result = formatter.result()
    return "\n".join(result) + "\n" if result else ""


def write_atomic(destination: Path, payload: bytes, mode_source: Path) -> None:
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        temporary.write_bytes(payload)
        shutil.copymode(mode_source, temporary)
        os.replace(temporary, destination)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def process_file(path: Path, options: Options) -> Result:
    try:
        raw = path.read_bytes()
        has_bom = raw.startswith(codecs.BOM_UTF8)
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        return Result(path, "skipped", detail=f"not valid utf-8 ({error.reason})")
    except OSError as error:
        return Result(path, "error", detail=str(error))

    newline = "\r\n" if "\r\n" in text else "\n"
    formatted = format_text(text, options.width, options.markdown).replace("\n", newline)
    payload = (codecs.BOM_UTF8 if has_bom else b"") + formatted.encode("utf-8")
    before, after = len(raw), len(payload)

    if options.markdown:
        target = path.with_suffix(".md")
        if not options.dry_run:
            try:
                write_atomic(target, payload, path)
                if options.remove:
                    path.unlink()
            except OSError as error:
                return Result(path, "error", before, after, str(error))
        return Result(path, "converted", before, after, target=target, removed=options.remove)

    if payload == raw:
        return Result(path, "unchanged", before, after)
    if not options.dry_run:
        try:
            write_atomic(path, payload, path)
        except OSError as error:
            return Result(path, "error", before, after, str(error))
    return Result(path, "changed", before, after)


def walk_txt_files(root: Path) -> Iterator[Path]:
    try:
        entries = sorted(root.iterdir(), key=lambda entry: entry.name.lower())
    except OSError:
        return
    for entry in entries:
        if entry.is_symlink():
            continue
        if entry.is_dir():
            if entry.name not in SKIP_DIRS:
                yield from walk_txt_files(entry)
        elif entry.suffix.lower() == ".txt" and entry.is_file():
            yield entry


def paint(text: str, style: str, enabled: bool) -> str:
    return f"{style}{text}{RESET}" if enabled else text


def human_size(size: int) -> str:
    value = float(abs(size))
    unit = "B"
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            break
        value /= 1024
    return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"


def signed_size(size: int) -> str:
    return f"{'+' if size >= 0 else '-'}{human_size(size)}"


def render(result: Result, name_width: int, color: bool) -> str:
    name = result.path.name
    if result.status == "converted" and result.target is not None:
        return f"{name} -> {result.target.name}"
    label = name.ljust(name_width + 2)
    if result.status == "changed":
        return label + paint(f"{result.after - result.before:+d}", GREEN, color)
    if result.status == "unchanged":
        return label + paint("unchanged", DIM, color)
    if result.status == "skipped":
        return label + paint(f"skipped: {result.detail}", YELLOW, color)
    return label + paint(f"error: {result.detail}", RED, color)


def summarize(results: Sequence[Result], options: Options, color: bool) -> list[str]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    noun = "file" if len(results) == 1 else "files"
    lines = [f"{len(results)} {noun}: " + ", ".join(f"{n} {status}" for status, n in counts.items())]

    measured = [r for r in results if r.status in ("changed", "unchanged", "converted")]
    before = sum(r.before for r in measured)
    after = sum(r.after for r in measured)
    delta = after - before
    percent = f", {delta / before * 100:+.1f}%" if before else ""
    space = f"space: {human_size(before)} -> {human_size(after)} ({paint(signed_size(delta) + percent, GREEN, color)})"
    if options.markdown and not options.remove:
        space += " originals kept"
    lines.append(space)

    if options.markdown and options.remove:
        verb = "would remove" if options.dry_run else "removed"
        lines.append(f"{verb} {counts.get('converted', 0)} original files")
    if options.dry_run:
        lines.append("dry run: nothing was written")
    return lines


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reformat .txt files recursively, in place.")
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("-j", "--workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-m", "--markdown", action="store_true", help="write file.md beside file.txt")
    parser.add_argument("-r", "--remove", action="store_true", help="with -m, delete the original .txt")
    args = parser.parse_args(argv)
    if args.remove and not args.markdown:
        parser.error("-r/--remove requires -m/--markdown")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root: Path = args.root.resolve()
    files = list(walk_txt_files(root))
    if not files:
        print(f"No .txt files found under {root}")
        return 0

    options = Options(width=args.width, dry_run=args.dry_run, markdown=args.markdown, remove=args.remove)
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    name_width = max(len(path.name) for path in files)
    workers = max(1, min(args.workers, len(files)))
    worker = partial(process_file, options=options)

    results: list[Result] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(worker, files, chunksize=max(1, len(files) // (workers * 4))):
            results.append(result)
            print(render(result, name_width, color))

    print()
    print("\n".join(summarize(results, options, color)))
    return 1 if any(r.status == "error" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
