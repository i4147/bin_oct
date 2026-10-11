#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python terminal text editor with live Persian-formatted preview, without including any code.

---

Create a Python 3 command-line script (intended for Termux on Android, so use a `#!/data/data/com.termux/files/usr/bin/env python` shebang) that acts as a terminal text editor with a live, reshaped Persian-text preview pane.

**Purpose:** The user edits a text file in a full-screen terminal interface. Below or beside the editor, a small preview pane shows only the lines surrounding the current cursor position, rendered through a Persian text formatter so that right-to-left and Arabic-script text displays correctly in a terminal.

**Inputs:**
- An optional positional file path argument. If provided and the file exists, load its contents as the initial editor text. If it does not exist, start with empty text and save to that path on save. If no path is given, start with empty text and provide a default save behavior (e.g., prompt or a fixed default filename).
- A command-line option to select the UI backend (for example `urwid` as default, with an alternative such as a curses-based or plain fallback backend).

**Persian formatting dependency:**
- Import a function `format_persian` from a module named `faprint`. If that import fails with `ImportError`, insert the script's own directory (resolved from `__file__`) at the front of `sys.path` and import `format_persian` from a sibling module named `core`. If that also fails, let the error surface clearly.
- Every preview string must pass through `format_persian` before display; the raw editor buffer is never altered by it.

**Constants:**
- A module-level context size of 2 (number of lines shown above and below the cursor line in the preview).

**Core helper `around(s, pos, n=CTX)`:**
- Given full text `s` and a character offset `pos`, return the formatted slice consisting of the cursor's line plus up to `n` lines before it and up to `n` lines after it.
- Compute the start index by scanning backward from `pos` for newlines, moving up `n` line boundaries, stopping early at the start of the string.
- Compute the end index by scanning forward from `pos` for newlines, moving down `n+1` boundaries, stopping at the end of the string if fewer lines remain.
- Only the slice is passed to `format_persian`, keeping work and memory small for large files.

**Urwid backend `run_urwid(text)`:**
- Import `urwid` inside the function so the module loads even when urwid is absent.
- Create a preview `urwid.Text` initialized with `around(text, 0)`.
- Define a subclass of `urwid.Edit` (multiline, tab allowed, starting cursor at position 0, initial content `text`) whose `keypress` method:
  - Raises `urwid.ExitMainLoop` when the key is `ctrl q` (quit).
  - Otherwise delegates to the superclass `keypress`, then updates the preview text with `around(self.edit_text, self.edit_pos)`, and returns any unhandled key.
- Build the layout as a vertical `urwid.Pile`: the editor in a `Filler` anchored to top with weight 2, a horizontal divider line (`─`) packed to its natural height, and the preview `Text` in a `Filler` anchored to top with weight 1.
- Run the main loop and handle the quit path cleanly.

**Behavior and edge cases to handle:**
- Empty input text: preview should render without errors.
- Cursor at the very start or very end of the buffer: the boundary logic must not index out of range.
- Files with no trailing newline, or with only one line.
- Non-existent file path: start empty rather than crashing.
- Files that cannot be decoded as UTF-8: report a clear error and exit with nonzero status.
- Missing `urwid` package: print an actionable message telling the user to install it (e.g., via `pip install urwid`) and exit nonzero, rather than a raw traceback.
- Ensure the terminal is restored properly on exit, including on Ctrl+C.
- Saving: provide a save key (e.g., `ctrl s`) that writes the buffer as UTF-8 to the target path, and report success or failure in the UI or on exit.

**Execution details:**
- Make the script executable and runnable directly as `./script.py [file] [--backend ...]`.
- Use `argparse` for argument parsing with a `--help` description.
- Use the `main()` pattern with `if __name__ == "__main__":` guard.
- Return a process exit code from `main()` and pass it to `sys.exit`.
- Use `pathlib.Path` and `os` where appropriate for path handling.
- Keep the code idiomatic, with short docstrings and comments matching a compact, practical style.
---"""

import argparse
import os
import sys
from pathlib import Path

try:
    from faprint import format_persian
except ImportError:  # faprint's core.py sitting next to this script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from core import format_persian

CTX = 2  # preview lines above/below the cursor line


def around(s, pos, n=CTX):
    """Format only the lines near `pos` (keeps work/memory small)."""
    a = s.rfind("\n", 0, pos) + 1
    for _ in range(n):
        if a == 0:
            break
        a = s.rfind("\n", 0, a - 1) + 1
    b = pos
    for _ in range(n + 1):
        j = s.find("\n", b)
        if j < 0:
            b = len(s)
            break
        b = j + 1
    return format_persian(s[a:b])


# --------------------------------------------------------------- urwid
def run_urwid(text):
    import urwid

    pv = urwid.Text(around(text, 0))

    class Ed(urwid.Edit):
        def keypress(self, size, key):
            if key == "ctrl q":
                raise urwid.ExitMainLoop()
            key = super().keypress(size, key)
            pv.set_text(around(self.edit_text, self.edit_pos))
            return key

    ed = Ed("", text, multiline=True, allow_tab=True, edit_pos=0)
    root = urwid.Pile([
        ("weight", 2, urwid.Filler(ed, "top")),
        ("pack", urwid.Divider("─")),
        ("weight", 1, urwid.Filler(pv, "top")),
    ])
    scr = urwid.display.raw.Screen()
    scr.tty_signal_keys(start="undefined", stop="undefined")  # free Ctrl+Q
    urwid.MainLoop(root, screen=scr).run()
    return ed.edit_text


# ---------------------------------------------------------------- curses
def run_curses(text):
    os.environ.setdefault("ESCDELAY", "25")
    import curses

    lines = text.split("\n")
    st = {"y": 0, "x": 0, "top": 0}

    def main(scr):
        curses.raw()
        scr.keypad(True)
        while True:
            y, x, top = st["y"], st["x"], st["top"]
            h, w = scr.getmaxyx()
            eh = max(1, h * 2 // 3)
            top = min(max(top, y - eh + 1), y)
            st["top"] = top
            left = max(0, x - w + 2)
            scr.erase()
            for i in range(eh):
                if top + i < len(lines):
                    scr.addnstr(i, 0, lines[top + i][left:], w - 1)
            if eh < h:
                scr.hline(eh, 0, curses.ACS_HLINE, w)
            pv = format_persian(lines[y])
            for i in range(h - eh - 1):
                chunk = pv[i * (w - 1) : (i + 1) * (w - 1)]
                if not chunk:
                    break
                scr.addnstr(eh + 1 + i, 0, chunk, w - 1)
            scr.move(y - top, x - left)
            k = scr.get_wch()
            if k == "\x11":
                return
            if k in ("\n", "\r", curses.KEY_ENTER):
                lines[y : y + 1] = [lines[y][:x], lines[y][x:]]
                st["y"], st["x"] = y + 1, 0
            elif k in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                if x:
                    lines[y] = lines[y][: x - 1] + lines[y][x:]
                    st["x"] = x - 1
                elif y:
                    st["x"] = len(lines[y - 1])
                    lines[y - 1 : y + 1] = [lines[y - 1] + lines[y]]
                    st["y"] = y - 1
            elif k == curses.KEY_DC:
                if x < len(lines[y]):
                    lines[y] = lines[y][:x] + lines[y][x + 1 :]
                elif y + 1 < len(lines):
                    lines[y : y + 2] = [lines[y] + lines[y + 1]]
            elif k == curses.KEY_LEFT:
                if x:
                    st["x"] = x - 1
                elif y:
                    st["y"], st["x"] = y - 1, len(lines[y - 1])
            elif k == curses.KEY_RIGHT:
                if x < len(lines[y]):
                    st["x"] = x + 1
                elif y + 1 < len(lines):
                    st["y"], st["x"] = y + 1, 0
            elif k in (
                curses.KEY_UP,
                curses.KEY_DOWN,
                curses.KEY_PPAGE,
                curses.KEY_NPAGE,
            ):
                d = {
                    curses.KEY_UP: -1,
                    curses.KEY_DOWN: 1,
                    curses.KEY_PPAGE: -eh,
                    curses.KEY_NPAGE: eh,
                }[k]
                st["y"] = min(max(y + d, 0), len(lines) - 1)
                st["x"] = min(x, len(lines[st["y"]]))
            elif k == curses.KEY_HOME:
                st["x"] = 0
            elif k == curses.KEY_END:
                st["x"] = len(lines[y])
            elif k == "\t":
                lines[y] = lines[y][:x] + "    " + lines[y][x:]
                st["x"] = x + 4
            elif isinstance(k, str) and k.isprintable():
                lines[y] = lines[y][:x] + k + lines[y][x:]
                st["x"] = x + 1

    curses.wrapper(main)
    return "\n".join(lines)


# --------------------------------------------------------- prompt_toolkit
def run_prompt_toolkit(text):
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.document import Document
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Dimension, HSplit, Layout, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

    buf = Buffer(multiline=True, document=Document(text, 0))
    edit = Window(BufferControl(buf), wrap_lines=True, height=Dimension(weight=2))
    prev = Window(
        FormattedTextControl(lambda: around(buf.text, buf.cursor_position)),
        wrap_lines=True,
        height=Dimension(weight=1),
    )
    kb = KeyBindings()

    @kb.add("c-q")
    def _(event):
        event.app.exit()

    root = HSplit([edit, Window(height=1, char="─"), prev])
    Application(Layout(root, focused_element=edit), key_bindings=kb, full_screen=True).run()
    return buf.text


# --------------------------------------------------------------- textual
def run_textual(text):
    from rich.text import Text
    from textual.app import App
    from textual.binding import Binding
    from textual.widgets import Static, TextArea

    class FaEdit(App):
        CSS = "TextArea{height:2fr} #pv{height:1fr;border-top:solid gray}"
        BINDINGS = [Binding("ctrl+q", "save_quit", "", priority=True, show=False)]

        def compose(self):
            yield TextArea(text, id="ed")
            yield Static("", id="pv")

        def on_mount(self):
            self.query_one("#ed").focus()
            self.refresh_pv()

        def on_text_area_selection_changed(self, event):
            self.refresh_pv()

        def refresh_pv(self):
            ta = self.query_one("#ed", TextArea)
            r = ta.cursor_location[0]
            lo, hi = max(0, r - CTX), min(ta.document.line_count, r + CTX + 1)
            s = "\n".join(ta.document.get_line(i) for i in range(lo, hi))
            self.query_one("#pv", Static).update(Text(format_persian(s)))

        def action_save_quit(self):
            self.exit(self.query_one("#ed", TextArea).text)

    return FaEdit().run() or text


BACKENDS = {
    "urwid": run_urwid,
    "curses": run_curses,
    "prompt_toolkit": run_prompt_toolkit,
    "textual": run_textual,
}


def main():
    ap = argparse.ArgumentParser(description="Edit Persian text with live faprint preview (Ctrl+Q saves & quits)")
    ap.add_argument("file")
    ap.add_argument("-b", "--backend", choices=BACKENDS, default="urwid")
    args = ap.parse_args()

    path = Path(args.file)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    new = BACKENDS[args.backend](old or "")
    if new != (old or "") or old is None:
        path.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    main()
