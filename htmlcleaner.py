#!/data/data/com.termux/files/usr/bin/python3.12
"""HTML Asset Extractor - Extract inline CSS and JavaScript to separate files.
This script processes HTML files to extract inline <style> and <script> tags, saves them as separate files in an assets directory, and updates the HTML to reference these external files.
Usage: python extract_assets.py [files/dirs...] If no arguments provided, processes all HTML files in current directory recursively."""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import multiprocessing as mp
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Configuration
NUM_WORKERS = 8
ASSETS_DIR_NAME = "assets"
CSS_SUBDIR = "css"
JS_SUBDIR = "js"
HTML_EXTENSIONS = {".html", ".htm"}
MIN_INLINE_SIZE = 0


@dataclass
class ExtractionResult:
    path: Path
    success: bool
    css_count: int = 0
    js_count: int = 0
    error: str | None = None


class HTMLExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.reset_state()
        self.extractions: list[tuple[str, str, dict]] = []  # (type, content, attrs)

    def reset_state(self):
        self.current_tag = None
        self.current_attrs = {}
        self.current_content = []
        self.in_style = False
        self.in_script = False
        self.script_has_src = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag_lower = tag.lower()

        if tag_lower == "style":
            self.in_style = True
            self.current_attrs = dict(attrs)
            self.current_content = []

        elif tag_lower == "script":
            attrs_dict = dict(attrs)

            if "src" not in attrs_dict:
                self.in_script = True
                self.script_has_src = False
                self.current_attrs = attrs_dict
                self.current_content = []
            else:
                self.script_has_src = True

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()

        if tag_lower == "style" and self.in_style:
            content = "".join(self.current_content).strip()
            if content and len(content) >= MIN_INLINE_SIZE:
                self.extractions.append(("css", content, self.current_attrs))
            self.in_style = False
            self.current_content = []

        elif tag_lower == "script" and self.in_script:
            content = "".join(self.current_content).strip()
            if content and len(content) >= MIN_INLINE_SIZE:
                self.extractions.append(("js", content, self.current_attrs))
            self.in_script = False
            self.current_content = []

    def handle_data(self, data: str):
        if self.in_style or self.in_script:
            self.current_content.append(data)

    def handle_entityref(self, name: str):
        if self.in_script:
            self.current_content.append(f"&{name};")

    def handle_charref(self, name: str):
        if self.in_script:
            self.current_content.append(f"&#{name};")

    def error(self, message: str):
        pass


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def get_unique_filename(base_name: str, extension: str, assets_dir: Path) -> str:
    filename = f"{base_name}{extension}"
    counter = 1

    while (assets_dir / filename).exists():
        filename = f"{base_name}_{counter}{extension}"
        counter += 1

    return filename


def extract_assets_from_html(html_content: str, html_path: Path, assets_base_dir: Path) -> tuple[str, int, int]:
    parser = HTMLExtractor()

    try:
        parser.feed(html_content)
        parser.close()
    except Exception:
        return html_content, 0, 0

    if not parser.extractions:
        return html_content, 0, 0

    css_dir = assets_base_dir / CSS_SUBDIR
    js_dir = assets_base_dir / JS_SUBDIR
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)

    try:
        rel_assets_path = assets_base_dir.relative_to(html_path.parent)
    except ValueError:
        rel_assets_path = Path(*[".."] * len(html_path.parent.parts)) / assets_base_dir

    replacements: list[tuple[str, str]] = []
    css_count = 0
    js_count = 0

    html_stem = html_path.stem

    for asset_type, content, attrs in parser.extractions:
        content_hash = compute_content_hash(content)

        if asset_type == "css":
            target_dir = css_dir
            extension = ".css"
            base_name = f"{html_stem}_{content_hash}"
            rel_path = rel_assets_path / CSS_SUBDIR
            css_count += 1

        else:  # js
            target_dir = js_dir
            extension = ".js"
            base_name = f"{html_stem}_{content_hash}"
            rel_path = rel_assets_path / JS_SUBDIR
            js_count += 1

        filename = get_unique_filename(base_name, extension, target_dir)
        asset_file = target_dir / filename

        try:
            asset_file.write_text(content, encoding="utf-8")
        except Exception:
            if asset_type == "css":
                css_count -= 1
            else:
                js_count -= 1
            continue

        rel_path = rel_path / filename

        href = str(rel_path).replace("\\", "/")

        if asset_type == "css":
            other_attrs = " ".join(f'{k}="{v}"' if v else k for k, v in attrs.items() if k not in ("href", "rel"))
            if other_attrs:
                replacement = f'<link rel="stylesheet" href="{href}" {other_attrs}>'
            else:
                replacement = f'<link rel="stylesheet" href="{href}">'
        else:
            other_attrs = " ".join(f'{k}="{v}"' if v else k for k, v in attrs.items() if k != "src")
            if other_attrs:
                replacement = f'<script src="{href}" {other_attrs}></script>'
            else:
                replacement = f'<script src="{href}"></script>'

        replacements.append((content, replacement))

    modified_html = html_content

    for original_content, replacement in replacements:
        escaped_content = re.escape(original_content)

        patterns = [
            rf"(<style[^>]*>)\s*{escaped_content}\s*(</style>)",
            rf"(<script[^>]*>)\s*{escaped_content}\s*(</script>)",
        ]

        for pattern in patterns:
            try:
                match = re.search(pattern, modified_html, re.DOTALL | re.IGNORECASE)
                if match:
                    if "<style" in match.group(1).lower():
                        modified_html = modified_html[: match.start()] + replacement + modified_html[match.end() :]
                    else:
                        modified_html = modified_html[: match.start()] + replacement + modified_html[match.end() :]
                    break
            except re.error:
                continue

    return modified_html, css_count, js_count


def process_html_file(path: Path) -> ExtractionResult:
    try:
        if not path.is_file():
            return ExtractionResult(path=path, success=False, error="Not a file")

        MAX_FILE_SIZE = 50 * 1024 * 1024
        file_size = path.stat().st_size

        if file_size > MAX_FILE_SIZE:
            return ExtractionResult(
                path=path,
                success=False,
                error=f"File too large ({file_size / 1024 / 1024:.1f} MB)",
            )

        if file_size == 0:
            return ExtractionResult(path=path, success=True, error="Empty file")

        html_content = path.read_text(encoding="utf-8", errors="replace")

        assets_dir = path.parent / ASSETS_DIR_NAME

        modified_html, css_count, js_count = extract_assets_from_html(html_content, path, assets_dir)

        if css_count > 0 or js_count > 0:
            temp_path = path.with_suffix(path.suffix + ".tmp")
            try:
                temp_path.write_text(modified_html, encoding="utf-8")
                temp_path.replace(path)
            except Exception:
                if temp_path.exists():
                    temp_path.unlink()
                raise

        return ExtractionResult(path=path, success=True, css_count=css_count, js_count=js_count)

    except UnicodeDecodeError as e:
        return ExtractionResult(path=path, success=False, error=f"Encoding error: {e}")
    except PermissionError as e:
        return ExtractionResult(path=path, success=False, error=f"Permission denied: {e}")
    except Exception as e:
        return ExtractionResult(path=path, success=False, error=f"{type(e).__name__}: {e}")


def find_html_files(paths: list[Path]) -> Iterator[Path]:
    seen = set()

    for path in paths:
        path = path.resolve()

        if path.is_file():
            if path.suffix.lower() in HTML_EXTENSIONS and path not in seen:
                seen.add(path)
                yield path

        elif path.is_dir():
            for html_file in path.rglob("*"):
                if html_file.is_file() and html_file.suffix.lower() in HTML_EXTENSIONS:
                    resolved = html_file.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield resolved

        else:
            print(f"Warning: Path does not exist: {path}", file=sys.stderr)


def get_default_paths() -> list[Path]:
    return [Path.cwd()]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract inline CSS and JavaScript from HTML files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s                          # Process current directory recursively
    %(prog)s index.html               # Process single file
    %(prog)s src/ dist/               # Process multiple directories
    %(prog)s *.html                   # Process multiple files (shell glob)
        """,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to process (default: current directory)",
    )

    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=NUM_WORKERS,
        help=f"Number of worker processes (default: {NUM_WORKERS})",
    )

    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")

    parser.add_argument(
        "--min-size",
        type=int,
        default=MIN_INLINE_SIZE,
        help=f"Minimum inline content size to extract (default: {MIN_INLINE_SIZE})",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    global MIN_INLINE_SIZE
    MIN_INLINE_SIZE = args.min_size

    paths = args.paths or get_default_paths()

    if not args.quiet:
        print("Scanning for HTML files...", file=sys.stderr)

    html_files = list(find_html_files(paths))

    if not html_files:
        print("No HTML files found.", file=sys.stderr)
        return 0

    if not args.quiet:
        print(f"Found {len(html_files)} HTML file(s) to process.", file=sys.stderr)

    num_workers = min(args.workers, len(html_files), mp.cpu_count() * 2)
    num_workers = max(1, num_workers)

    if not args.quiet:
        print(f"Using {num_workers} worker(s)...", file=sys.stderr)

    total_css = 0
    total_js = 0
    total_processed = 0
    total_errors = 0

    with mp.Pool(processes=num_workers) as pool:
        try:
            for result in pool.imap_unordered(process_html_file, html_files, chunksize=4):
                total_processed += 1

                if result.success:
                    total_css += result.css_count
                    total_js += result.js_count

                    if not args.quiet:
                        if result.css_count > 0 or result.js_count > 0:
                            print(
                                f"✓ {result.path}: {result.css_count} CSS, {result.js_count} JS extracted",
                                file=sys.stderr,
                            )
                        elif result.error:
                            print(f"○ {result.path}: {result.error}", file=sys.stderr)
                else:
                    total_errors += 1
                    print(f"✗ {result.path}: {result.error}", file=sys.stderr)

        except KeyboardInterrupt:
            print("\nInterrupted by user.", file=sys.stderr)
            pool.terminate()
            return 130

    print(
        f"\nSummary: {total_processed} file(s) processed, "
        f"{total_css} CSS and {total_js} JS extracted, "
        f"{total_errors} error(s).",
        file=sys.stderr,
    )

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
