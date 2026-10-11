#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that tells another AI coding agent how to build a Python terminal UI application (Textual-based) for finding and managing duplicate files on Android/Termux. Describe purpose, inputs/outputs, dependencies, logic, error handling, edge cases, and usage. Do not include code.

Build a terminal user interface (TUI) application in Python for finding and managing duplicate files on a filesystem. The script is intended to run under Termux on Android, so its shebang should point to the Termux Python interpreter path (/data/data/com.termux/files/usr/bin/env python). Write it as a single self-contained module.

**Dependencies and imports**
- Use the standard library only, plus the Textual framework (the `textual` package) for the UI.
- Use `from __future__ import annotations` for modern type hint syntax.
- Standard library modules needed: hashlib (for file hashing), sys, collections.defaultdict, dataclasses (dataclass, field), difflib.SequenceMatcher (for fuzzy filename similarity), pathlib.Path, and typing.ClassVar.
- From Textual, import: `on` decorator, `App`, `ComposeResult`, `Binding`, containers `Container`, `Horizontal`, `Vertical`, `ModalScreen`, `Widget`, and widgets `Button`, `DataTable`, `DirectoryTree`, `Footer`, `Header`, `Input`, `Label`, `OptionList`, `ProgressBar`, `RadioSet`, `Static`, `Switch`.

**Data model**
- A `FileEntry` dataclass holding: a `Path`, an integer `size` in bytes, an optional `hash` string (default none), and a `filename_normalized` string. In post-initialization, set `filename_normalized` to the lowercase version of the file's name.
- A `DuplicateGroup` dataclass holding a list of `FileEntry` objects (default empty list), a `match_score` float (default 100.0), and a `reason` string (default "exact"). Provide:
  - `total_size` property: returns 0 if there are no files; otherwise the size of the first file multiplied by (number of files minus one) — i.e., the reclaimable space if all but one copy are removed.
  - `size_str` property: the total size formatted with a human-readable helper.
- A helper `format_size(size_bytes)` that converts a byte count into a human-readable string by iterating units B, KB, MB, GB, TB, dividing by 1024 until the value is below 1024 (use one decimal place for non-byte units, and integer display for bytes), with a sensible fallback to TB for very large values.

**Application behavior**
- The main class is a Textual `App` with a header, footer, and a main layout built from containers, showing a directory selection area (a `DirectoryTree` so the user can browse and pick a folder to scan), controls for scan options, a `ProgressBar` for scan progress, a `DataTable` listing duplicate groups (with columns such as group index, file count, reclaimable size, match score/reason, and file paths), and a detail/action panel for the currently selected group.
- Keybindings are declared via a `ClassVar` list of `Binding` objects (e.g., quit, start scan, select/deselect files, delete selected, toggle options, and similar). Keep key choices sensible and document them in the footer.
- Scan options exposed in the UI:
  - Exact duplicate detection via content hashing (MD5 or SHA-256 via hashlib, reading files in chunks so large files are not loaded whole into memory).
  - Optional fuzzy filename matching using `SequenceMatcher` on normalized (lowercase) filenames, with a similarity threshold (e.g., a percentage) configurable by the user through an input field; fuzzy groups get a `match_score` equal to the similarity percentage and `reason` set to something like "similar name".
  - Toggle switches for options such as including hidden files/directories, following symbolic links (default off), and minimum file size to consider (configurable via an input).
  - A `RadioSet` to choose the hash algorithm or the grouping strategy (e.g., size-first prefilter then hash).
- Scanning algorithm:
  1. Walk the chosen directory recursively, skipping unreadable paths and handling `PermissionError` and `OSError` gracefully (log/skip, do not crash).
  2. Group files by size first; only files sharing a size with at least one other file are hashed (this is the key optimization).
  3. Within each size group, compute hashes of the files (in chunks) and group by hash; groups with 2+ members become exact `DuplicateGroup`s with match_score 100.
  4. If fuzzy mode is enabled, compare normalized filenames among files not already in exact groups (or among all candidates, avoiding duplicating entries) using `SequenceMatcher` ratio against the threshold; form groups accordingly.
  5. Sort results, e.g., by reclaimable size descending.
  - Run scanning in a way that keeps the UI responsive (use a Textual worker or thread, and update the `ProgressBar` periodically via messages or `call_from_thread`).
  - Support cancelling a running scan.
- Actions on duplicates:
  - Within each group, the user can mark files to delete; by default, keep the first/oldest or first-listed file and mark the rest as candidates for deletion.
  - A confirmation `ModalScreen` must be shown before any deletion, displaying the number of files and total size to be freed, with Confirm and Cancel buttons.
  - Deletion uses `Path.unlink()` wrapped in error handling; report per-file failures (permission denied, file missing) without aborting the whole batch, and show a summary afterward.
  - Never delete the last remaining copy in a group; refuse if the selection would remove all files.
  - Optionally support a dry-run mode toggled by a switch that only reports what would be deleted.
- Edge cases to handle:
  - Empty directory or no duplicates found: show a clear message in the UI.
  - Zero-byte files: either exclude them by default or treat them with the minimum-size option.
  - Symbolic links: skip by default to avoid loops; resolve paths carefully if following is enabled, guarding against cycles.
  - Files that disappear or change during scanning: catch errors and skip.
  - Very large files: chunked hashing.
  - Invalid numeric input in input fields (threshold, min size): validate and fall back to defaults with a notice.
  - Non-UTF-8 or unusual filenames: avoid crashing when rendering paths in the table (use safe string conversion).
  - Hidden files: skipped unless the option is enabled.
  - Permission errors on directories: skip and continue.
- Error handling: wrap filesystem operations in try/except for `OSError`, `PermissionError`, and `FileNotFoundError`; surface non-fatal problems in a status line or notification area rather than raising.

**Entry point**
- Define a `main()` function that creates the app instance and runs it, and guard execution with `if __name__ == "__main__":`. Optionally accept a starting directory as a command-line argument from `sys.argv` (default to the current working directory or the Termux home directory if none is given; validate that the path exists and is a directory, otherwise print an error message to stderr and exit with a nonzero status).
- Make the script executable and runnable as `python <scriptname>.py [directory]` in Termux.

**Code quality expectations**
- Use type hints throughout, docstrings for public classes and functions, and clear separation between the data model, scanning logic, and UI classes.
- Keep the scanning logic independent of the UI so it can be tested alone.
- Use descriptive names and constants (for chunk size, default threshold, supported hash algorithms) defined at module level.
---"""

from __future__ import annotations

import hashlib
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    ProgressBar,
    RadioSet,
    Static,
    Switch,
)


@dataclass
class FileEntry:
    path: Path
    size: int
    hash: str | None = None
    filename_normalized: str = ""

    def __post_init__(self) -> None:
        self.filename_normalized = self.path.name.lower()


@dataclass
class DuplicateGroup:
    files: list[FileEntry] = field(default_factory=list)
    match_score: float = 100.0
    reason: str = "exact"

    @property
    def total_size(self) -> int:
        if not self.files:
            return 0
        return self.files[0].size * (len(self.files) - 1)

    @property
    def size_str(self) -> str:
        return format_size(self.total_size)


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def compute_file_hash(path: Path, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def normalize_filename(filename: str) -> list[str]:
    import re

    name = Path(filename).stem.lower()
    words = re.split(r"[\s\-_.]+", name)
    return [w for w in words if w]


def fuzzy_match_score(words1: list[str], words2: list[str], similarity_threshold: float = 0.8) -> float:
    if not words1 or not words2:
        return 0.0
    matches = 0
    for w1 in words1:
        for w2 in words2:
            if SequenceMatcher(None, w1, w2).ratio() >= similarity_threshold:
                matches += 1
                break
    total = len(words1) + len(words2)
    if total == 0:
        return 0.0
    return (2 * matches / total) * 100


class DuplicateFinder:
    def __init__(
        self,
        scan_mode: str = "contents",
        min_size: int = 0,
        fuzzy_threshold: float = 80.0,
    ) -> None:
        self.scan_mode = scan_mode
        self.min_size = min_size
        self.fuzzy_threshold = fuzzy_threshold
        self.files: list[FileEntry] = []
        self.duplicates: list[DuplicateGroup] = []
        self.progress_callback = None

    def scan_directory(self, root: Path, progress_callback=None) -> None:
        self.progress_callback = progress_callback
        self.files = []
        all_files = list(root.rglob("*"))
        total = len(all_files)
        for i, path in enumerate(all_files):
            if progress_callback:
                progress_callback(i, total, f"Scanning: {path}")
            if not path.is_file():
                continue
            try:
                stat = path.stat()
                if stat.st_size < self.min_size:
                    continue
                self.files.append(
                    FileEntry(
                        path=path,
                        size=stat.st_size,
                        filename_normalized=path.name.lower(),
                    )
                )
            except (OSError, PermissionError):
                continue

    def find_duplicates(self, progress_callback=None) -> list[DuplicateGroup]:
        self.duplicates = []
        if self.scan_mode == "filename":
            self._find_by_filename(progress_callback)
        else:
            self._find_by_contents(progress_callback)
        return self.duplicates

    def _find_by_filename(self, progress_callback=None) -> None:
        groups: dict[str, list[FileEntry]] = defaultdict(list)
        for file in self.files:
            key = file.filename_normalized
            groups[key].append(file)
        for key, files in groups.items():
            if len(files) > 1:
                self.duplicates.append(DuplicateGroup(files=files, match_score=100.0, reason="filename_exact"))
        if self.fuzzy_threshold > 0:
            keys = list(groups.keys())
            checked = set()
            for i, key1 in enumerate(keys):
                if progress_callback:
                    progress_callback(i, len(keys), f"Fuzzy matching: {key1}")
                words1 = normalize_filename(key1)
                if not words1:
                    continue
                for key2 in keys[i + 1 :]:
                    if (key1, key2) in checked or (key2, key1) in checked:
                        continue
                    checked.add((key1, key2))
                    words2 = normalize_filename(key2)
                    if not words2:
                        continue
                    score = fuzzy_match_score(words1, words2)
                    if score >= self.fuzzy_threshold and score < 100:
                        combined = groups[key1] + groups[key2]
                        self.duplicates.append(
                            DuplicateGroup(
                                files=combined,
                                match_score=score,
                                reason="filename_fuzzy",
                            )
                        )

    def _find_by_contents(self, progress_callback=None) -> None:
        by_size: dict[int, list[FileEntry]] = defaultdict(list)
        for file in self.files:
            by_size[file.size].append(file)
        candidates = [files for files in by_size.values() if len(files) > 1]
        total_candidates = sum(len(c) for c in candidates)
        processed = 0
        for group in candidates:
            hash_groups: dict[str, list[FileEntry]] = defaultdict(list)
            for file in group:
                if progress_callback:
                    processed += 1
                    progress_callback(processed, total_candidates, f"Hashing: {file.path}")
                try:
                    file.hash = compute_file_hash(file.path)
                    hash_groups[file.hash].append(file)
                except (OSError, PermissionError, IOError):
                    continue
            for files in hash_groups.values():
                if len(files) > 1:
                    self.duplicates.append(DuplicateGroup(files=files, match_score=100.0, reason="contents"))


class ScanSettings(Widget):
    DEFAULT_CSS = """
    ScanSettings {
        width: 100%;
        height: auto;
        padding: 1 2;
        background: $surface;
    }
    ScanSettings .setting-row {
        height: auto;
        margin: 1 0;
    }
    ScanSettings Label {
        width: 20;
        content-align: left middle;
    }
    ScanSettings RadioSet, ScanSettings Input, ScanSettings Switch {
        width: 1fr;
    }
    """
    scan_mode: str = "contents"
    fuzzy_threshold: float = 80.0
    min_size: int = 0

    def compose(self) -> ComposeResult:
        with Horizontal(classes="setting-row"):
            yield Label("Scan Mode:", id="mode-label")
            yield RadioSet(
                OptionList.Option("Contents", id="opt-contents"),
                OptionList.Option("Filename", id="opt-filename"),
                id="scan-mode",
            )
        with Horizontal(classes="setting-row"):
            yield Label("Fuzzy Threshold:", id="fuzzy-label")
            yield Input(value="80", id="fuzzy-input", type="integer")
        with Horizontal(classes="setting-row"):
            yield Label("Min File Size (bytes):", id="minsize-label")
            yield Input(value="0", id="minsize-input", type="integer")

    @on(RadioSet.Changed, "#scan-mode")
    def on_mode_changed(self, event: RadioSet.Changed) -> None:
        self.scan_mode = "contents" if event.value == 0 else "filename"

    @on(Input.Changed, "#fuzzy-input")
    def on_fuzzy_changed(self, event: Input.Changed) -> None:
        try:
            self.fuzzy_threshold = float(event.value)
        except ValueError:
            self.fuzzy_threshold = 80.0

    @on(Input.Changed, "#minsize-input")
    def on_minsize_changed(self, event: Input.Changed) -> None:
        try:
            self.min_size = int(event.value)
        except ValueError:
            self.min_size = 0


class ResultsTable(Widget):
    DEFAULT_CSS = """
    ResultsTable {
        width: 100%;
        height: 1fr;
    }
    ResultsTable DataTable {
        width: 100%;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        table = DataTable(id="results-table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_header = True
        yield table

    def update_results(self, duplicates: list[DuplicateGroup]) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear()
        if not table.columns:
            table.add_column("Group", width=8)
            table.add_column("Files", width=12)
            table.add_column("Size Each", width=12)
            table.add_column("Wasted Space", width=15)
            table.add_column("Match %", width=10)
            table.add_column("Reason", width=15)
            table.add_column("Sample Path", width=60)
        for i, group in enumerate(duplicates, 1):
            if not group.files:
                continue
            sample = group.files[0]
            table.add_row(
                str(i),
                str(len(group.files)),
                format_size(sample.size),
                group.size_str,
                f"{group.match_score:.1f}%",
                group.reason,
                (str(sample.path)[:58] + "…" if len(str(sample.path)) > 60 else str(sample.path)),
                key=f"group-{i}",
            )


class ScanProgress(ModalScreen):
    DEFAULT_CSS = """
    ScanProgress {
        align: center middle;
    }
    ScanProgress > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
    }
    ScanProgress #status {
        width: 100%;
        content-align: center middle;
        margin: 1 0;
    }
    ScanProgress #progress {
        width: 100%;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Scanning...", id="status")
            yield ProgressBar(id="progress", show_eta=False)
            yield Button("Cancel", id="cancel-btn", variant="error")

    def update_progress(self, current: int, total: int, message: str = "") -> None:
        progress = self.query_one("#progress", ProgressBar)
        status = self.query_one("#status", Label)
        if total > 0:
            progress.progress = (current / total) * 100
        else:
            progress.progress = 0
        if message:
            if len(message) > 50:
                message = "…" + message[-47:]
            status.update(f"[bold]{current}/{total}[/bold] {message}")

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self) -> None:
        self.app.pop_screen()


class DupeGuruApp(App):
    TITLE = "dupeguru-ng"
    SUB_TITLE = "Duplicate File Finder"
    CSS = """
    Screen {
        background: $background;
    }
    #main-container {
        width: 100%;
        height: 100%;
    }
    #sidebar {
        width: 30;
        height: 100%;
        background: $surface;
        border-right: solid $primary;
        padding: 1;
    }
    #content {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    #path-display {
        width: 100%;
        height: auto;
        margin: 1 0;
        background: $primary-background;
        padding: 1;
        text-align: center;
    }
    #controls {
        height: auto;
        margin: 1 0;
    }
    #controls Button {
        width: 100%;
        margin: 1 0;
    }
    #stats {
        height: auto;
        margin: 1 0;
        padding: 1;
        background: $surface;
    }
    #results-container {
        width: 100%;
        height: 1fr;
    }
    """
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "scan", "Scan", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("c", "clear", "Clear", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.finder = DuplicateFinder()
        self.selected_path: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield Label("[bold]Directory[/bold]", id="dir-label")
                yield DirectoryTree(".", id="dir-tree")
                with Vertical(id="controls"):
                    yield Button("Scan Selected", id="scan-btn", variant="primary")
                    yield Button("Clear Results", id="clear-btn", variant="warning")
                with Vertical(id="stats"):
                    yield Label("[bold]Statistics[/bold]")
                    yield Label("", id="stat-files")
                    yield Label("", id="stat-dupes")
                    yield Label("", id="stat-space")
            with Vertical(id="content"):
                yield Static("Select a directory to scan", id="path-display")
                yield ScanSettings(id="settings")
                with Container(id="results-container"):
                    yield ResultsTable(id="results")
        yield Footer()

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.selected_path = event.path.parent
        self._update_path_display()

    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.selected_path = event.path
        self._update_path_display()

    def _update_path_display(self) -> None:
        if self.selected_path:
            path_str = str(self.selected_path)
            if len(path_str) > 70:
                path_str = "…" + path_str[-67:]
            self.query_one("#path-display", Static).update(f"[bold]Path:[/bold] {path_str}")

    @on(Button.Pressed, "#scan-btn")
    def on_scan_pressed(self) -> None:
        if not self.selected_path:
            self.notify("Please select a directory first", severity="warning")
            return
        self.action_scan()

    @on(Button.Pressed, "#clear-btn")
    def on_clear_pressed(self) -> None:
        self.action_clear()

    def action_scan(self) -> None:
        if not self.selected_path:
            return
        settings = self.query_one("#settings", ScanSettings)
        self.finder = DuplicateFinder(
            scan_mode=settings.scan_mode,
            min_size=settings.min_size,
            fuzzy_threshold=settings.fuzzy_threshold,
        )
        progress_screen = ScanProgress()
        self.push_screen(progress_screen)

        def progress_cb(current: int, total: int, message: str = "") -> None:
            self.call_after_refresh(progress_screen.update_progress, current, total, message)

        try:
            self.finder.scan_directory(self.selected_path, progress_cb)
            self.finder.find_duplicates(progress_cb)
            self.call_after_refresh(self._display_results)
        finally:
            self.call_after_refresh(self.pop_screen)

    def _display_results(self) -> None:
        results = self.query_one("#results", ResultsTable)
        results.update_results(self.finder.duplicates)
        total_files = len(self.finder.files)
        total_dupes = len(self.finder.duplicates)
        wasted = sum(g.total_size for g in self.finder.duplicates)
        self.query_one("#stat-files", Label).update(f"Files scanned: {total_files}")
        self.query_one("#stat-dupes", Label).update(f"Duplicate groups: {total_dupes}")
        self.query_one("#stat-space", Label).update(f"Wasted space: {format_size(wasted)}")
        self.notify(f"Found {total_dupes} duplicate groups", severity="information")

    def action_clear(self) -> None:
        results = self.query_one("#results", ResultsTable)
        results.update_results([])
        self.query_one("#stat-files", Label).update("")
        self.query_one("#stat-dupes", Label).update("")
        self.query_one("#stat-space", Label).update("")
        self.notify("Results cleared", severity="information")

    def action_refresh(self) -> None:
        if self.finder.duplicates:
            self._display_results()
        else:
            self.notify("No results to refresh", severity="warning")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="dupeguru-ng: Find duplicate files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dupeguru-ng                     Launch TUI
  dupeguru-ng /path/to/scan       Launch TUI with pre-selected path
        """,
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Directory to scan (default: current directory)",
    )
    args = parser.parse_args()
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)
    if not args.path.is_dir():
        print(f"Error: Not a directory: {args.path}", file=sys.stderr)
        sys.exit(1)
    app = DupeGuruApp()
    app.run()


if __name__ == "__main__":
    main()
