#!/data/data/com.termux/files/usr/bin/env python
"""Create a Termux-targeted Python 3.12 command-line utility script (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) named something like `piplist` that scans Python source files to discover third-party import dependencies and checks their availability/installation status, cross-referencing a local PyPI index file.

Purpose and behavior:ependency sc walk a directory (or single file) for `.py` files, skipping common irrelevant directories by default (`.git`, `.hg`, `.svn`, `.tox`, `.venv`, `venv`, `env`, `build`, `dist`, `__pycache__`, `node_modules`, `.mypy_cache`, `.pytest_cache`, `site-packages`, `.eggs`, `.idea`, `.vscode`), with an option to customize excluded directories via CLI args.

2. **Import extraction**: Use Python's `ast` module to parse each source file and extract all top-level import statements (`import x x.y` capturing the rootports that are wrapped in `try/except `try/except ModuleNotFoundError` blocks (treat these as "optional" dependencies, since the code already handles their absence gracefully), tracking line numbers and file paths for reporting.

3. **Module classification**: For each discovered root module name:
   - Check if it belongs to the Python standard library using a `STDLIB` set (imported from a local `dh` module).
   - Map import names to actual PyPI package names using a `PKG_MAPPING` dictionary (also from `dh`), building a reverse lookup table (`IMPORT_TO_PKG`) since `yaml` → `PyYAML`).
   - Normalize package names for comparison by lowercasing and collapsing `-`, `_`, `.` characters into a single `-` (PEP 503 style normalization).

4. **PyPI/local index lookup**: Check whether each non-stdlib package is already listed/installed by consulting a local JSON index file at `/sdcard/data/pip.json` (`PYPI_INDEX_PATH`). If a package is not found locally and needs remote verification, query PyPI's JSON API using the `yarg` library (`json2package`, handling `HTTPError` exceptions) to confirm the package exists and f: Implement a dis `~/.cache/piplist` avoid repeated network/API lookups. Cache keys are derived from a SHA-256 hash (truncated to 16 hex chars) of the module name. Each cache entry is a JSON file containing a timestamp (`ts`) and a `value`; entries older than `CACHE_TTL` (86400 seconds / 1 day) are treated as expired/missing. Provide `read_cache`/`write_cache` a sentinel object) to distinguish "notached" from leg cached `None`sy values.

6. **ures` (e.g., `ThreadPoolExecutor`) to parallelize network lookups for multiple packages to speed up scanning of projects with many dependencies.

7. **CLI interface**: Use `argparse` to accept arguments such as the target path(s) to scan, options to show only missing/uninstalled packages, flags to ignore optional (try/except-guarded) imports, custom exclude directories, verbosity/logging level, and possibly output format (e.g., plain text or JSON).

8. **Output/logging**: Use the `logging` module (logger named `"piplist"`) to report progress and results — e.g., listing missing third-party packages, their mapped PyPI names, and locations (file:line) where they were imported, distinguishing required vs. optional imports. Exit with an appropriate status code (e.g., non-zero if required dependencies are missing).

9. **Dependencies**: Relies on `requests` for HTTP calls, `yarg` for PyPI API package objects, and a local helper module `dh` providing `STDLIB` (collection of standard library module names) and `PKG_MAPPING` (dict mapping PyPI package names to their primary import name).

The final script should be self-contained, runnable directly in Termux on Android, and help developers quickly audit a Python project's directory tree for missing or unmapped third-party dependencies before packaging or deployment.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/fbMa7rQ4bXXteY5eMd5KUf"""

from __future__ import annotations
import argparse
import ast
import concurrent.futures
import contextlib
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from dh import PKG_MAPPING, STDLIB
import requests
from yarg import json2package
from yarg.exceptions import HTTPError


PYPI_INDEX_PATH = "/sdcard/data/pip.json"
CACHE_DIR = Path.home() / ".cache" / "piplist"
CACHE_TTL = 86400
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "site-packages",
    ".eggs",
    ".idea",
    ".vscode",
}
OPTIONAL_EXC = ("ImportError", "ModuleNotFoundError")
log = logging.getLogger("piplist")
_MISSING = object()


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


IMPORT_TO_PKG = {}
for _pkg, _imp in PKG_MAPPING.items():
    IMPORT_TO_PKG.setdefault(_imp, _pkg)
STDLIB_SET = set(STDLIB) if not isinstance(STDLIB, set) else STDLIB


def cache_key(module):
    return hashlib.sha256(module.encode("utf-8")).hexdigest()[:16]


def read_cache(module):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / (cache_key(module) + ".json")
    if not p.exists():
        return _MISSING
    try:
        data = json.loads(p.read_text())
    except Exception:
        return _MISSING
    if time.time() - data.get("ts", 0) > CACHE_TTL:
        return _MISSING
    return data.get("value", _MISSING)


def write_cache(module, value):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / (cache_key(module) + ".json")
    with contextlib.suppress(Exception):
        p.write_text(json.dumps({"ts": time.time(), "value": value}))


def load_pypi_index(path=PYPI_INDEX_PATH):
    try:
        data = json.loads(Path(path).read_text())
    except Exception as e:
        log.warning("could not load PyPI index %s: %s", path, e)
        return set()
    keys = data.keys() if isinstance(data, dict) else data
    return {normalize(k) for k in keys}


def get_installed_packages(python=None):
    python = python or sys.executable
    cmd = [python, "-m", "pip", "freeze"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = proc.communicate()
    result = {}
    for line in stdout.splitlines():
        line = line.decode("utf-8", errors="ignore").strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, version = line.split("==", 1)
        else:
            name, version = line, None
        result[normalize(name)] = (name, version)
    return result


def get_imports_info(module, pypi_server="https://pypi.python.org/pypi/", proxy=None):
    try:
        response = requests.get("{0}{1}/json".format(pypi_server, module), proxies=proxy, timeout=15)
        if response.status_code == 200:
            if hasattr(response.content, "decode"):
                data = json2package(response.content.decode())
            else:
                data = json2package(response.content)
        elif response.status_code >= 300:
            raise HTTPError(status_code=response.status_code, reason=response.reason)
    except HTTPError:
        return None
    except requests.RequestException as e:
        log.debug("network error for %s: %s", module, e)
        return None
    return str(module) + "==" + str(data.latest_release_id)


def get_imports_info_cached(module, proxy=None):
    cached = read_cache(module)
    if cached is not _MISSING:
        return cached
    result = get_imports_info(module, proxy=proxy)
    write_cache(module, result)
    return result


def extract_imports_from_source(source, include_optional=False):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    found = []
    stack = [(tree, False)]
    while stack:
        node, optional = stack.pop()
        in_optional = optional
        if isinstance(node, ast.Try):
            for h in node.handlers:
                t = h.type
                if t is None:
                    in_optional = True
                elif isinstance(t, ast.Name) and t.id in OPTIONAL_EXC:
                    in_optional = True
                elif isinstance(t, ast.Tuple):
                    for e in t.elts:
                        if isinstance(e, ast.Name) and e.id in OPTIONAL_EXC:
                            in_optional = True
        if isinstance(node, ast.Import):
            for alias in node.names:
                n = alias.name.split(".")[0]
                if include_optional or not in_optional:
                    found.append(n)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            n = node.module.split(".")[0]
            if include_optional or not in_optional:
                found.append(n)
        for child in ast.iter_child_nodes(node):
            stack.append((child, in_optional))
    return found


def extract_imports_from_notebook(path, include_optional=False):
    try:
        nb = json.loads(Path(path).read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []
    found = []
    for cell in nb.get("cells", []):
        src = cell.get("source", [])
        if isinstance(src, list):
            src = "".join(src)
        if not src:
            continue
        found.extend(extract_imports_from_source(src, include_optional))
    return found


def get_project_imports(directory, ignore_dirs, include_optional=False):
    results = []
    ignore = set(ignore_dirs)
    for path, subdirs, files in os.walk(directory):
        subdirs[:] = [d for d in subdirs if d not in ignore and not d.startswith(".")]
        for name in files:
            full = os.path.join(path, name)
            if name.endswith(".py"):
                try:
                    source = Path(full).read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for m in extract_imports_from_source(source, include_optional):
                    results.append((m, full))
            elif name.endswith(".ipynb"):
                for m in extract_imports_from_notebook(full, include_optional):
                    results.append((m, full))
    return results


def is_local_module(name, source_file):
    d = os.path.dirname(os.path.abspath(source_file))
    if os.path.exists(os.path.join(d, name + ".py")):
        return True
    if os.path.exists(os.path.join(d, name, "__init__.py")):
        return True
    cur = d
    while True:
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        if os.path.exists(os.path.join(parent, name, "__init__.py")):
            return True
        cur = parent
    return False


def apply_pin(name, version, style):
    if style == "none" or not version:
        return name
    if style == "exact":
        return name + "==" + version
    if style == "compatible":
        return name + "~=" + version
    if style == "minimal":
        return name + ">=" + version
    return name


def resolve_online(pkg, index, proxy):
    if index and normalize(pkg) not in index:
        return None
    return get_imports_info_cached(pkg, proxy=proxy)


def read_ignores(path):
    out = set()
    try:
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                out.add(line)
    except Exception as e:
        log.warning("could not read ignore file %s: %s", path, e)
    return out


def init(args):
    level = logging.WARNING if args["quiet"] else (logging.DEBUG if args["verbose"] else logging.INFO)
    logging.basicConfig(level=level, format="%(message)s")
    root = args["path"] or os.curdir
    if not os.path.isdir(root):
        log.error("path does not exist: %s", root)
        return 2
    ignore_dirs = DEFAULT_EXCLUDE_DIRS | set(args["ignore_dir"] or [])
    exclude = {normalize(e) for e in (args["exclude"] or [])}
    if args["ignore_file"]:
        exclude |= {normalize(x) for x in read_ignores(args["ignore_file"])}
    include_only = {normalize(i) for i in (args["include"] or [])}
    raw = get_project_imports(root, ignore_dirs, include_optional=args["include_optional"])
    seen = {}
    for name, src in raw:
        if name in STDLIB_SET:
            continue
        if is_local_module(name, src):
            continue
        seen.setdefault(name, src)
    pkgs = []
    for name in sorted(seen):
        pkg = IMPORT_TO_PKG.get(name, name)
        if pkg not in pkgs:
            pkgs.append(pkg)
    if exclude:
        pkgs = [p for p in pkgs if normalize(p) not in exclude]
    if include_only:
        pkgs = [p for p in pkgs if normalize(p) in include_only]
    index = load_pypi_index()
    installed = get_installed_packages(args["python"])
    results = {}
    online = []
    for pkg in pkgs:
        norm = normalize(pkg)
        if norm in installed:
            results[pkg] = installed[norm]
        else:
            online.append(pkg)
    if online:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(resolve_online, p, index, args["proxy"]): p for p in online}
            for fut in concurrent.futures.as_completed(futures):
                pkg = futures[fut]
                try:
                    info = fut.result()
                except Exception as e:
                    log.debug("lookup error %s: %s", pkg, e)
                    info = None
                if info and "==" in info:
                    n, v = info.split("==", 1)
                    results[pkg] = (n, v)
                elif index and normalize(pkg) not in index:
                    log.warning("%s not on PyPI, skipping", pkg)
                else:
                    log.warning("could not resolve version for %s", pkg)
                    results[pkg] = (pkg, None)
    lines = []
    for pkg in results:
        if args["strip_installed"] and normalize(pkg) in installed:
            continue
        name, version = results[pkg]
        lines.append(apply_pin(name, version, args["pin"]))
    lines = sorted(set(lines), key=str.lower)
    if args["stdout"] or args["dry_run"]:
        sys.stdout.write("\n".join(lines) + ("\n" if lines else ""))
        return 0
    target = os.path.join(args["path"], "requirements.txt") if args["path"] else "requirements.txt"
    if os.path.exists(target) and not args["overwrite"]:
        try:
            existing = [l.strip() for l in Path(target).read_text().splitlines() if l.strip() and not l.startswith("#")]
        except Exception:
            existing = []
        merged = set(lines) | set(existing)
        lines = sorted(merged, key=str.lower)
    Path(target).write_text("\n".join(lines) + ("\n" if lines else ""))
    log.info("wrote %d entries to %s", len(lines), target)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--path", type=str, help="Path to target directory")
    ap.add_argument("--python", type=str, help="Python interpreter to query pip from")
    ap.add_argument("--proxy", type=str, help="HTTP(S) proxy for PyPI")
    ap.add_argument(
        "--pin",
        choices=["exact", "compatible", "minimal", "none"],
        default="exact",
    )
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--include", nargs="*", default=[])
    ap.add_argument("--ignore-dir", nargs="*", default=[])
    ap.add_argument("--ignore-file", type=str)
    ap.add_argument("--include-optional", action="store_true")
    ap.add_argument("--keep-installed", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = vars(ap.parse_args())
    args["strip_installed"] = not args["keep_installed"]
    try:
        sys.exit(init(args))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
