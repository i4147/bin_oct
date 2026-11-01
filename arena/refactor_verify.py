#!/usr/bin/env python3
"""Verify a batch of refactored scripts against the refactor.md checklist.

Usage
    python3 arena/refactor_verify.py PATH [PATH ...]

Paths are relative to ``refactored/``. Each file is checked for: forbidden APIs,
loguru-only logging, pool rules, the ``main()`` guard, atomic-write delegation,
compile + ruff under Python 3.12, a successful ``--help`` run from outside
``refactored/``, and a ``--help``/``--version`` snapshot.

Environment overrides
    ARENA_PY      Python 3.12+ interpreter  (default: /tmp/py312/bin/python3.12)
    ARENA_RUFF    ruff executable           (default: /tmp/uvenv/bin/ruff)
    ARENA_EXTRAS  extra sys.path entries for runs (default: /tmp/py312-libs,
                  which is where loguru lives in this sandbox)

Results are written back into ``refactored/.progress.json``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "refactored"
SNAP = OUT / "_snapshots"
PROGRESS = OUT / ".progress.json"

PY = Path(os.environ.get("ARENA_PY", "/tmp/py312/bin/python3.12"))
RUFF = Path(os.environ.get("ARENA_RUFF", "/tmp/uvenv/bin/ruff"))
EXTRAS = [p for p in os.environ.get("ARENA_EXTRAS", "/tmp/py312-libs").split(os.pathsep) if p]

FORBIDDEN = re.compile(
    r"os\.path\b|concurrent\.futures|import logging|logging\.getLogger"
    r"|from dh|import dh|max_workers|--workers|--jobs|--processes|-j\b"
)
SECURITY = re.compile(r"os\.system|\beval\(|\bexec\(|shell\s*=\s*True")
BARE_EXCEPT = re.compile(r"except\s*:\s*$")
ATOMIC_INLINE = re.compile(r"os\.replace|\.fsync\(|\.tmp['\"]")
OPEN_CALL = re.compile(r"open\([^)]*\)")
BINARY_MODE = re.compile(r"""open\([^)]*['"](?:rb|wb|ab|rb\+|wb\+)['"]""")


def python_exe() -> Path:
    """Return the configured interpreter, falling back to ``python3``."""
    return PY if PY.exists() else Path("python3")


def run(
    cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its text output."""
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)


def check_file(name: str) -> list[str]:
    """Return a list of human-readable problems for one refactored script."""
    problems: list[str] = []
    path = OUT / name
    if not path.exists():
        return [f"missing output file {path}"]

    text = path.read_text(encoding="utf-8", errors="replace")

    for match in FORBIDDEN.finditer(text):
        line = text[: match.start()].count("\n") + 1
        problems.append(f"forbidden pattern {match.group(0)!r} at line {line}")

    original_path = ROOT / name
    original = (
        original_path.read_text(encoding="utf-8", errors="replace")
        if original_path.exists()
        else ""
    )
    if "loguru" not in text and ("logging" in original or "print(" in original):
        problems.append("no loguru usage")

    if "Pool(" in text and "imap_unordered" not in text:
        problems.append("multiprocessing.Pool without imap_unordered")
    if "Pool(" in text and "processes=4" not in text:
        problems.append("multiprocessing.Pool without processes=4")

    if "def main(" not in text:
        problems.append("no main()")
    if 'if __name__ == "__main__":' not in text:
        problems.append("no __main__ guard")

    if re.search(r"\bwrite_text\(|write_bytes\(|\.write\(|atomic_write\(", text):
        if "reqs.atomicio" not in text:
            problems.append("writes files without importing reqs.atomicio")
    if "reqs.atomicio" in text:
        consumer = text.split("reqs.atomicio", 1)[-1]
        if ATOMIC_INLINE.search(consumer):
            problems.append("inline atomic-write logic (os.replace/.fsync/.tmp)")

    for match in SECURITY.finditer(text):
        line = text[: match.start()].count("\n") + 1
        problems.append(f"review grep hit {match.group(0)!r} at line {line}")

    for number, line in enumerate(text.splitlines(), 1):
        if BARE_EXCEPT.search(line):
            problems.append(f"bare except at line {number}")
        if (
            OPEN_CALL.search(line)
            and "encoding=" not in line
            and not BINARY_MODE.search(line)
            and not line.strip().startswith("#")
        ):
            problems.append(f"open() without encoding at line {number}: {line.strip()[:70]}")

    py = python_exe()
    compiled = run([str(py), "-m", "py_compile", str(path)])
    if compiled.returncode != 0:
        problems.append("compile failed: " + compiled.stderr.strip().splitlines()[-1][:200])

    if RUFF.exists():
        lint = run(
            [
                str(RUFF),
                "check",
                "--target-version",
                "py312",
                "--select",
                "F,I,UP,B,SIM,RUF",
                "--isolated",
                str(path),
            ]
        )
        if lint.returncode != 0:
            codes = sorted(set(re.findall(r"\b([A-Z]+[0-9]{3})\b", lint.stdout)))
            problems.append("ruff: " + ",".join(codes[:8]))

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(OUT), *EXTRAS])

    help_run = run([str(py), str(path), "--help"], cwd=Path("/tmp"), env=env)
    if help_run.returncode != 0:
        tail = (help_run.stderr.strip().splitlines() or [""])[-1]
        problems.append("--help failed: " + tail[:200])
    else:
        SNAP.mkdir(parents=True, exist_ok=True)
        (SNAP / f"{name}.help.txt").write_text(help_run.stdout, encoding="utf-8")
        version_run = run([str(py), str(path), "--version"], cwd=Path("/tmp"), env=env)
        if version_run.returncode == 0 and version_run.stdout.strip():
            (SNAP / f"{name}.version.txt").write_text(version_run.stdout, encoding="utf-8")

    return problems


def main(argv: list[str]) -> int:
    """Verify each named script, update the progress file, and print a summary."""
    names = argv[1:]
    if not names:
        print(__doc__)
        return 2
    failed = 0
    state = json.loads(PROGRESS.read_text(encoding="utf-8")) if PROGRESS.exists() else {"items": {}}
    state.setdefault("items", {})
    for name in names:
        problems = check_file(name)
        entry = state["items"].setdefault(name, {})
        if problems:
            failed += 1
            entry["status"] = "failed"
            entry["reason"] = "; ".join(problems)[:400]
            print(f"FAIL {name}")
            for problem in problems[:8]:
                print(f"     - {problem}")
        else:
            entry["status"] = "verified"
            entry.pop("reason", None)
            entry["out"] = f"refactored/{name}"
    if PROGRESS.exists():
        PROGRESS.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
    print(f"{len(names) - failed}/{len(names)} verified, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
