#!/data/data/com.termux/files/usr/bin/python
"""
tpv - a terminal PDF viewer, powered by PyMuPDF.

Rasterises pages with PyMuPDF (imported as `fitz`) and paints them into the
terminal with 24-bit-colour half-block characters (U+2580).

Requirements:
    pip install PyMuPDF

Usage:
    python tpv.py document.pdf [-p PAGE] [-z ZOOM]

Keys:
    q / Esc / Ctrl-C    quit
    j / Down            scroll down one line
    k / Up              scroll up one line
    h / Left            scroll left
    l / Right           scroll right
    Space / PgDn / f    next screen (next page when already at the bottom)
    b / PgUp            prev screen (prev page when already at the top)
    n / N / p           next / previous page
    g / Home            top of page
    G / End             bottom of page
    + / -               zoom in / out
    0                   reset zoom and scroll
"""

from __future__ import annotations

import argparse
import os
import select
import shutil
import sys
import termios
import tty

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("tpv: PyMuPDF is required.  Install it with:  pip install PyMuPDF")


# ---------------------------------------------------------------------------
# ANSI escape sequences
# ---------------------------------------------------------------------------
RESET = "\x1b[0m"
HOME = "\x1b[H"
CLEAR = "\x1b[2J"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
ENTER_ALT = "\x1b[?1049h"
LEAVE_ALT = "\x1b[?1049l"
REVERSE = "\x1b[7m"

HALF_BLOCK = "\u2580"  # fg paints the top pixel, bg paints the bottom pixel


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
class RenderError(RuntimeError):
    pass


class Renderer:
    """Rasterises PDF pages with PyMuPDF."""

    CACHE_LIMIT = 6

    def __init__(self, path: str) -> None:
        self.path = path
        try:
            self.doc = fitz.open(path)
        except Exception as exc:  # noqa: BLE001
            raise RenderError(str(exc)) from exc

        if self.doc.page_count == 0:
            raise RenderError("document contains no pages")

        self._cache: dict[tuple[int, int], tuple[int, int, bytes]] = {}

    def close(self) -> None:
        try:
            self.doc.close()
        except Exception:  # noqa: BLE001
            pass

    # -- page count --------------------------------------------------------
    def page_count(self) -> int:
        return self.doc.page_count

    # -- rendering ---------------------------------------------------------
    def page(self, index: int, width: int) -> tuple[int, int, bytes]:
        """Return ``(width, height, rgb_bytes)`` for a page, with caching."""
        key = (index, width)
        hit = self._cache.get(key)
        if hit is not None:
            return hit

        try:
            pdf_page = self.doc.load_page(index)
        except Exception as exc:  # noqa: BLE001
            raise RenderError(f"cannot load page {index + 1}: {exc}") from exc

        # The page's natural size in points (1/72 inch).
        rect = pdf_page.rect
        if rect.width <= 0 or rect.height <= 0:
            raise RenderError(f"page {index + 1} has zero area")

        # Scale factor so that the rendered pixmap is `width` pixels wide.
        scale = width / rect.width
        matrix = fitz.Matrix(scale, scale)

        try:
            pix = pdf_page.get_pixmap(
                matrix=matrix,
                colorspace=fitz.csRGB,
                alpha=False,
                annots=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise RenderError(f"failed to render page {index + 1}: {exc}") from exc

        if pix.n != 3 or pix.alpha:
            # Normalise to tightly packed 3-channel RGB.
            pix = fitz.Pixmap(fitz.csRGB, pix)

        w, h = pix.width, pix.height
        samples = bytes(pix.samples)
        if len(samples) < w * h * 3:
            raise RenderError("renderer produced a truncated pixmap")
        # Guard against any row padding the backend might introduce.
        if len(samples) != w * h * 3:
            stride = len(samples) // h
            samples = b"".join(samples[r * stride : r * stride + w * 3] for r in range(h))

        result = (w, h, samples)
        if len(self._cache) >= self.CACHE_LIMIT:
            self._cache.clear()
        self._cache[key] = result
        return result


# ---------------------------------------------------------------------------
# Keyboard input
# ---------------------------------------------------------------------------
def read_key(fd: int, timeout: float | None = None) -> str | None:
    """Read one logical key.  ``None`` means the timeout elapsed."""
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return None

    first = os.read(fd, 1)
    if not first:  # EOF - terminal went away
        return "q"
    if first != b"\x1b":
        return first.decode("utf-8", "replace")

    seq = bytearray(first)
    while len(seq) < 8:
        ready, _, _ = select.select([fd], [], [], 0.03)
        if not ready:
            break
        seq += os.read(fd, 1)
        if seq[-1:].isalpha() or seq[-1:] == b"~":
            break
    return seq.decode("latin-1")


# ---------------------------------------------------------------------------
# Viewer
# ---------------------------------------------------------------------------
class Viewer:
    MIN_ZOOM = 0.25
    MAX_ZOOM = 8.0
    ZOOM_STEP = 1.25
    MAX_RENDER_WIDTH = 4000

    def __init__(self, path: str, page: int = 1, zoom: float = 1.0) -> None:
        self.path = path
        self.renderer = Renderer(path)
        self.page_count = self.renderer.page_count()
        if self.page_count == 0:
            raise RenderError("document contains no pages")

        self.page_index = max(0, min(page - 1, self.page_count - 1))
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self.x = 0
        self.y = 0
        self.running = True

    # -- geometry ----------------------------------------------------------
    def term_size(self) -> tuple[int, int]:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines

    def view_rows(self) -> int:
        _, lines = self.term_size()
        return max(1, lines - 1)

    def render_width(self) -> int:
        cols, _ = self.term_size()
        return max(1, min(self.MAX_RENDER_WIDTH, int(round(cols * self.zoom))))

    def page_px_size(self) -> tuple[int, int]:
        w, h, _ = self.renderer.page(self.page_index, self.render_width())
        return w, h

    # -- painting ----------------------------------------------------------
    @staticmethod
    def _paint_row(data: bytes, w: int, h: int, top: int, x0: int, cols: int) -> str:
        bottom = top + 1
        have_top = 0 <= top < h
        have_bot = 0 <= bottom < h
        base_t = top * w * 3
        base_b = bottom * w * 3

        out: list[str] = []
        last_fg: tuple[int, int, int] | None = None
        last_bg: tuple[int, int, int] | None = None
        blank = False

        for i in range(cols):
            x = x0 + i
            if x >= w:  # past the right edge of the page
                if not blank:
                    out.append(RESET)
                    last_fg = last_bg = None
                    blank = True
                out.append(" ")
                continue

            blank = False
            if have_top:
                p = base_t + x * 3
                fg = (data[p], data[p + 1], data[p + 2])
            else:
                fg = (0, 0, 0)

            if have_bot:
                p = base_b + x * 3
                bg = (data[p], data[p + 1], data[p + 2])
            else:
                bg = (0, 0, 0)

            if fg != last_fg:
                out.append(f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m")
                last_fg = fg
            if bg != last_bg:
                out.append(f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m")
                last_bg = bg
            out.append(HALF_BLOCK)

        out.append(RESET)
        return "".join(out)

    def _status(self, cols: int, note: str = "") -> str:
        name = os.path.basename(self.path)
        if note:
            line = f" {note} "
        else:
            try:
                _, h = self.page_px_size()
            except RenderError:
                h = 0
            rows = self.view_rows()
            max_y = max(0, h - rows * 2)
            pct = 100 if max_y == 0 else int(round(100 * self.y / max_y))
            line = f" {name}  {self.page_index + 1}/{self.page_count}  {pct:3d}%  {self.zoom:.2f}x "
        hint = " q quit  n/p page  j/k scroll  +/- zoom "
        if len(line) + len(hint) <= cols:
            line = line + " " * (cols - len(line) - len(hint)) + hint
        return REVERSE + line[:cols].ljust(cols) + RESET

    def draw(self) -> None:
        cols, _ = self.term_size()
        rows = self.view_rows()
        width = self.render_width()

        error: str | None = None
        try:
            w, h, data = self.renderer.page(self.page_index, width)
        except RenderError as exc:
            error = str(exc)
            w = h = 1
            data = b"\x00\x00\x00"
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            w = h = 1
            data = b"\x00\x00\x00"

        if error is None:
            max_y = max(0, h - rows * 2)
            self.y = max(0, min(self.y, max_y))
            max_x = max(0, w - cols)
            self.x = max(0, min(self.x, max_x))

        buf = [HOME]
        if error:
            buf.append(RESET)
            buf.append(f" {error} ".ljust(cols)[:cols])
            for _ in range(rows - 1):
                buf.append("\r\n")
        else:
            for row in range(rows):
                buf.append(self._paint_row(data, w, h, self.y + row * 2, self.x, cols))
                buf.append("\r\n")  # raw mode: need CR to return to col 0

        buf.append(RESET)
        buf.append(self._status(cols, error or ""))
        sys.stdout.write("".join(buf))
        sys.stdout.flush()

    # -- navigation --------------------------------------------------------
    def goto_page(self, index: int) -> None:
        if 0 <= index < self.page_count:
            self.page_index = index
            self.x = self.y = 0

    def screen_down(self) -> None:
        step = self.view_rows() * 2
        _, h = self.page_px_size()
        max_y = max(0, h - step)
        if self.y >= max_y:
            if self.page_index + 1 < self.page_count:
                self.page_index += 1
                self.x = self.y = 0
        else:
            self.y = min(self.y + step, max_y)

    def screen_up(self) -> None:
        step = self.view_rows() * 2
        if self.y <= 0:
            if self.page_index > 0:
                self.page_index -= 1
                self.x = 0
                _, h = self.page_px_size()
                self.y = max(0, h - step)
        else:
            self.y = max(0, self.y - step)

    def set_zoom(self, value: float) -> None:
        value = max(self.MIN_ZOOM, min(self.MAX_ZOOM, value))
        if value == self.zoom:
            return
        old_w = self.render_width()
        _, old_h = self.page_px_size()  # cached from the current frame
        frac = self.y / old_h if old_h else 0.0
        self.zoom = value
        new_w = self.render_width()
        new_h = max(1, round(old_h * new_w / old_w))
        self.y = int(frac * new_h)

    # -- key dispatch ------------------------------------------------------
    def handle(self, key: str) -> None:
        if key in ("q", "Q", "\x03") or key == "\x1b":
            self.running = False

        elif key in ("j", "\x1b[B", "\n", "\r"):
            self.y += 2
        elif key in ("k", "\x1b[A"):
            self.y -= 2
        elif key in ("h", "\x1b[D"):
            self.x -= 4
        elif key in ("l", "\x1b[C"):
            self.x += 4

        elif key in (" ", "\x1b[6~", "f", "J"):
            self.screen_down()
        elif key in ("b", "\x1b[5~", "K"):
            self.screen_up()

        elif key == "n":
            self.goto_page(self.page_index + 1)
        elif key in ("N", "p"):
            self.goto_page(self.page_index - 1)

        elif key in ("g", "\x1b[H", "\x1b[1~", "\x1b[7~", "\x1bOH"):
            self.x = self.y = 0
        elif key in ("G", "\x1b[F", "\x1b[4~", "\x1b[8~", "\x1bOF"):
            self.y = 1 << 30

        elif key in ("+", "="):
            self.set_zoom(self.zoom * self.ZOOM_STEP)
        elif key in ("-", "_"):
            self.set_zoom(self.zoom / self.ZOOM_STEP)
        elif key == "0":
            self.zoom = 1.0
            self.x = self.y = 0

    # -- main loop ---------------------------------------------------------
    def run(self, fd: int) -> None:
        dirty = True
        last_size = (0, 0)

        while self.running:
            size = self.term_size()
            if size != last_size:
                last_size = size
                self.renderer._cache.clear()  # render width changed
                dirty = True

            if dirty:
                self.draw()
                dirty = False

            key = read_key(fd, 0.25)
            if key is None:
                continue
            self.handle(key)
            dirty = True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tpv",
        description="View a PDF file in the terminal (PyMuPDF backend).",
    )
    parser.add_argument("file", help="path to the PDF file")
    parser.add_argument("-p", "--page", type=int, default=1, help="page to open first (1-based, default 1)")
    parser.add_argument("-z", "--zoom", type=float, default=1.0, help="initial zoom factor (default 1.0)")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.file):
        parser.error(f"no such file: {args.file}")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error("must be run from an interactive terminal")

    try:
        viewer = Viewer(args.file, args.page, args.zoom)
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"tpv: could not open {args.file!r}: {exc}")

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdout.write(ENTER_ALT + HIDE_CURSOR + CLEAR + HOME)
        sys.stdout.flush()
        viewer.run(fd)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        sys.stdout.write(RESET + SHOW_CURSOR + LEAVE_ALT)
        sys.stdout.flush()
        viewer.renderer.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
