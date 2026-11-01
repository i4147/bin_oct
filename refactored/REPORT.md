# Refactor report — bin_oct

State file: `refactored/.progress.json` (idempotent resume point).
Interpreter used for every check: **Python 3.12.16**.

## Environment

| Item | Value |
|---|---|
| `python3` (sandbox default) | 3.11.2 — below the 3.12 floor |
| Interpreter used | **3.12.16**, built from source (`codeload.github.com/python/cpython` tag `v3.12.16`) into `/tmp/py312` |
| Stdlib availability | `zlib`, `hashlib`, `multiprocessing`, `tarfile`, `zipfile`, `venv` available; `ssl`, `ctypes`, `bz2`, `lzma`, `sqlite3`, `readline`, `curses` **unavailable** (no dev headers in the image) |
| Linter | ruff 0.17.3 with `--target-version py312` |

Because the interpreter is built without `ssl`, `bz2`, `lzma`, `ctypes` and `sqlite3`, a
`--help` smoke run that imports one of those modules transitively fails **for
environmental reasons**. Such scripts are recorded with the reason in
`.progress.json` rather than being silently marked clean.

## `reqs/atomicio.py`

* Copied byte-for-byte to `refactored/reqs/atomicio.py`
  (`sha256 bcbaf37665c0719cf21db0d5dcef03e5ec38582fc165576d9e5ff52c5ec087a0`, identical to the original, never edited).
* Public API used by the scripts: `atomic_write(path, data, *, encoding="utf-8", dry_run-free, mkdir=True, skip_unchanged=False, backup=..., as_json=None, **kw)`.
  Every consumer imports `from reqs.atomicio import atomic_write` and passes text
  (`str`, written verbatim, no trailing newline added) or binary (`bytes`) payloads.
* Scripts that publish derived files always write through it; renames (`Path.rename`)
  and reads are not writes and bypass it deliberately.

## Scope and assumptions

* Manifest: **836** tracked `*.py` files at the repository root.
* `documented/` is **excluded**: it holds generated output from the earlier
  docstring task, not hand-written source. `refactored/` and `reqs/` are excluded per spec.
* `.gitignore`: the directory itself is not excluded, but the repository-wide `*.json`
  rule (line 86) excluded `refactored/.progress.json`, which is a required deliverable.
  The **only** permitted edit to an existing file was made — one negation appended to the
  repo-root `.gitignore`:

  ```diff
  +# refactor output must stay committable (refactor.md)
  +!refactored/.progress.json
  ```

  After the edit `git status --porcelain --ignored refactored/ | grep '^!!'` returns
  nothing, and `git check-ignore -v refactored/.progress.json` resolves to the negation
  rule. Generated `__pycache__/` trees are removed before each commit.
* Documented behavior deltas (all deliberate, none silent):
  * `cleanhistory.py` — dedupe now keeps first-occurrence order instead of `set()` order.
  * `upkl.py` — `pickle.load` is replaced by a restricted unpickler that refuses every
    global lookup (rule 14 forbids unpickling file data; behavior for data-only pickles
    is unchanged, code execution is no longer possible).
  * `compryst.py` — see the failed table.
* Cross-script convention adopted for consistency (rule 20 asks for a report; this is the
  rule applied here):
  * `main(argv: list[str] | None = None) -> int` in every script, `raise SystemExit(main())`.
  * argparse only, `--help` and `--version` everywhere, `--dry-run` on every mutating script.
  * Program output stays on **stdout** via `print` (byte-identical to the original);
    diagnostics and failures go through **loguru** to stderr. No `logging` module usage.
  * Exit codes: `0` success, `1` runtime error, `2` argparse usage error.

## Class-based structure

Every script is built around one cohesive class that owns the work, with
`main()` doing argument parsing, logging setup and error mapping:

```python
class FileLowercaser:
    def __init__(self, path: Path, *, dry_run: bool = False) -> None: ...
    def run(self) -> int: ...

def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logger.remove(); logger.add(sys.stderr, level="INFO")
    try:
        return FileLowercaser(args.path, dry_run=args.dry_run).run()
    except OSError as exc:
        logger.error("cannot process {}: {}", args.path, exc)
        return 1
```

Small pure helpers live on the class (`@staticmethod`) so Phase 2 can lift a
whole method into `_shared/` without rewriting call sites.

## Phase 1 — batch log

### Batch 1 — 15 verified, 1 failed

| Script | Class | Notes |
|---|---|---|
| `empt.py` | `FileEmptier` | atomic truncate, `--dry-run` |
| `mergecss.py` | `CssMerger` | `dh.runcmd` inlined into `subprocess.run(cwd=...)`; `dh` dependency gone |
| `pathcmd.py` | `PathEntryLister` | env read inside `run()`, no import-time access |
| `c2f.py` | `TemperatureConverter` | output `212.00`, byte-identical |
| `f2c.py` | `FahrenheitReporter` | preserves the original `celecius:`/`kelvin:` spacing |
| `raster.py` | `AbiSuffixRenamer` | target-exists guard, `--dry-run` |
| `ww.py` | `WheelPacker` | `os.chdir` replaced by `subprocess(cwd=...)` |
| `alu.py` | `UpgradableLister` | propagates `apt` exit status |
| `decode_unicode.py` | `UnicodeAsciifier` | NFKD + ascii strip, atomic rewrite |
| `cleanhistory.py` | `HistoryCleaner` | ordered dedupe (delta above) |
| `fv.py` | `FilePager` | `-` reads stdin |
| `lowerer.py` | `FileLowercaser` | atomic rewrite |
| `pyhead.py` | `FileHeadPrinter` | bare `except` replaced by `OSError`/`UnicodeError` |
| `srpr.py` | `SrpRunner` | `dh.runcmd` inlined; `--dry-run` |
| `upkl.py` | `PickleUnpacker` + `_RestrictedUnpickler` | see safety delta above |

Behavior spot-checks run against the originals with 3.11 for comparison:
`c2f 100` → `212.00` (identical), `f2c 212` → `celecius: 100.00  kelvin:373.15` (identical),
`lowerer`/`decode_unicode`/`empt`/`pathcmd` produced byte-identical results,
`upkl` wrote identical payload bytes and **refused** a hostile pickle
(`refusing to load global posix.system`, exit 1).

### Failed

| Script | Reason |
|---|---|
| `comprust.py` | imports the local module `compression_prompt`, absent from the repo; behavior cannot be preserved or verified |

## Verification performed per script

* forbidden-API grep: `os.path`, `concurrent.futures`, `import logging`,
  `logging.getLogger`, `from dh`, `import dh`, `max_workers`, `--workers`, `--jobs`,
  `--processes`, `-j` → clean
* `multiprocessing.Pool` only with `imap_unordered(..., processes=4)` (no pool scripts yet)
* `main()` + `if __name__ == "__main__":` guard → present
* file writers import `reqs.atomicio`; no `os.replace` / `.fsync(` / `.tmp` in consumers
* `open()` always carries `encoding=`, except explicit binary modes
* review greps for `os.system`, `eval(`, `exec(`, `shell=True`, bare `except`,
  `except Exception: pass` → clean
* `python3.12 -m py_compile` → pass
* `ruff check --target-version py312 --select F,I,UP,B,SIM,RUF --isolated` → pass
* `python3.12 refactored/<script> --help` from `/tmp` (outside `refactored/`) → pass
* `refactored/_snapshots/<script>.help.txt` (+ `.version.txt`) written

## Status

```
PAUSED at 15/836 (phase 1) — state saved in refactored/.progress.json.
```

Resume by re-running the prompt: `verified` items are skipped, `failed` retried,
`pending` processed. Phase 2 (dedup into `refactored/_shared/`) starts only when the
manifest is exhausted.
