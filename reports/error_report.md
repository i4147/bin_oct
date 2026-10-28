# Error report — scripts that cannot run

Generated 2026-10-27T23:04:53+00:00 · Python 3.11.2 · **821 scripts** checked.

Static analysis only: no script was executed. Import failures caused by modules that are not installed are **excluded** by request.

## Headline numbers

| Metric | Count |
|---|---:|
| Scripts analysed | 821 |
| Scripts with blocking errors | 69 |
| Scripts that cannot start | 11 |
| Distinct blocking issues | 138 |
| Runtime risks (may crash) | 1519 |
| Python-3.12-only syntax files | 7 |
| Ignored import issues | 1600 |
| Other non-blocking diagnostics | 1139 |
| Raw diagnostics from all 4 tools | 5304 |

## Tools (reports saved separately)

| Tool | Version | Diagnostics | Blocking | Report |
|---|---|---:|---:|---|
| ruff | ruff 0.17.3 | 582 | 71 | `ruff_report.json` |
| pylint | pylint 4.1.3 | 823 | 129 | `pylint_report.json` |
| mypy | mypy 2.4.0 (compiled: yes) | 1360 | 106 | `mypy_report.json` |
| ty | ty 0.0.92 | 2539 | 116 | `ty_report.json` |

Commands and flags are recorded in each JSON report and in `reports/README.md`.

## Blocking errors by category

| Category | Issues | What it does |
|---|---:|---|
| `undefined_name` | 110 | NameError at the reported line |
| `call_signature` | 14 | TypeError from a broken call |
| `syntax_error` | 7 | script cannot be parsed/started |
| `invalid_flow` | 6 | SyntaxError / illegal control flow |
| `attribute_error` | 1 | AttributeError risk |

## Python 3.12-only syntax (blocked only on Python 3.11)

7 files use PEP 695 (`type X = ...`, `def f[T]`) or PEP 701 (multiline / backslash f-string expressions). They are valid on CPython >= 3.12 but this environment runs 3.11, so they fail at startup. `ty --python-version 3.12` reports **zero** syntax diagnostics for them.

| File | Line | CPython 3.11 error |
|---|---:|---|
| `codepener.py` | 9 | unterminated string literal (detected at line 9) |
| `fixescape.py` | 80 | f-string expression part cannot include a backslash |
| `minhtml.py` | 47 | invalid syntax |
| `rmc3.py` | 130 | invalid syntax |
| `rmh.py` | 210 | unterminated string literal (detected at line 210) |
| `srmc2.py` | 169 | expected '(' |
| `zip_crack.py` | 129 | unterminated string literal (detected at line 129) |

Options: run these scripts with CPython >= 3.12, or rewrite the `type` statements as `TypeAlias` assignments and move multiline f-string expressions into local variables.

## Scripts that cannot start

Files with a `startup` blocking issue (parse error or a module-level undefined name).

| File | Status | Issues | Details |
|---|---|---:|---|
| `codepener.py` | cannot start | 1 | L9 syntax_error |
| `fixescape.py` | cannot start | 1 | L80 syntax_error |
| `h2md.py` | cannot start | 2 | L31 undefined_name; L16 undefined_name |
| `hunspeller.py` | cannot start | 1 | L200 undefined_name |
| `minhtml.py` | cannot start | 2 | L47 syntax_error; L264 undefined_name |
| `pydevtools.py` | cannot start | 7 | L831 undefined_name; L1206 undefined_name; L30 undefined_name; L560 undefined_name |
| `rmc3.py` | cannot start | 1 | L130 syntax_error |
| `rmh.py` | cannot start | 1 | L210 syntax_error |
| `srmc2.py` | cannot start | 1 | L169 syntax_error |
| `summar.py` | cannot start | 1 | L14 undefined_name |
| `zip_crack.py` | cannot start | 1 | L129 syntax_error |

## Blocking issues (full list)

| File | Line | Category | When | Tools | Message |
|---|---:|---|---|---|---|
| `codepener.py` | 9 | `syntax_error` | startup | cpython-compile, pylint, ruff, ty | CPython 3.11.2: SyntaxError: unterminated string literal (detected at line 9) at line 9 |
| `fixescape.py` | 80 | `syntax_error` | startup | cpython-compile, pylint, ruff, ty | CPython 3.11.2: SyntaxError: f-string expression part cannot include a backslash at line 80 |
| `h2md.py` | 31 | `undefined_name` | startup | mypy, ty | Name "p" is used before definition |
| `hunspeller.py` | 200 | `undefined_name` | startup | mypy, pylint, ruff, ty | Undefined name `os` |
| `minhtml.py` | 47 | `syntax_error` | startup | cpython-compile, mypy, pylint, ruff, ty | CPython 3.11.2: SyntaxError: invalid syntax at line 47 |
| `minhtml.py` | 264 | `undefined_name` | startup | mypy, ruff, ty | Undefined name `contextlib` |
| `pydevtools.py` | 831 | `undefined_name` | startup | mypy, pylint, ruff, ty | Undefined name `textwrap` |
| `pydevtools.py` | 1206 | `undefined_name` | startup | mypy, pylint, ruff, ty | Undefined name `textwrap` |
| `rmc3.py` | 130 | `syntax_error` | startup | cpython-compile, mypy, pylint, ruff, ty | CPython 3.11.2: SyntaxError: invalid syntax at line 130 |
| `rmh.py` | 210 | `syntax_error` | startup | cpython-compile, pylint, ruff, ty | CPython 3.11.2: SyntaxError: unterminated string literal (detected at line 210) at line 210 |
| `srmc2.py` | 169 | `syntax_error` | startup | cpython-compile, mypy, pylint, ruff, ty | CPython 3.11.2: SyntaxError: expected '(' at line 169 |
| `summar.py` | 14 | `undefined_name` | startup | mypy, pylint, ruff, ty | Undefined name `syd` |
| `zip_crack.py` | 129 | `syntax_error` | startup | cpython-compile, pylint, ruff, ty | CPython 3.11.2: SyntaxError: unterminated string literal (detected at line 129) at line 129 |
| `addel.py` | 462 | `call_signature` | on execution | mypy, ty | Too many arguments |
| `addel.py` | 479 | `call_signature` | on execution | mypy, ty | Too many arguments |
| `addel.py` | 511 | `call_signature` | on execution | mypy, ty | Too many arguments |
| `artools.py` | 129 | `invalid_flow` | on execution | ty | Yield type `GzipFile` does not match annotated yield type `BinaryIO` |
| `artools.py` | 132 | `invalid_flow` | on execution | ty | Yield type `BZ2File` does not match annotated yield type `BinaryIO` |
| `artools.py` | 135 | `invalid_flow` | on execution | ty | Yield type `LZMAFile` does not match annotated yield type `BinaryIO` |
| `artools.py` | 156 | `invalid_flow` | on execution | ty | Yield type `GzipFile` does not match annotated yield type `BinaryIO` |
| `artools.py` | 159 | `invalid_flow` | on execution | ty | Yield type `BZ2File` does not match annotated yield type `BinaryIO` |
| `artools.py` | 162 | `invalid_flow` | on execution | ty | Yield type `LZMAFile` does not match annotated yield type `BinaryIO` |
| `autofix_typo.py` | 242 | `call_signature` | on execution | mypy, pylint, ty | Too many positional arguments for method call |
| `autofix_typo.py` | 246 | `call_signature` | on execution | mypy, pylint, ty | Too many positional arguments for method call |
| `bestwhois.py` | 46 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `bestwhois.py` | 49 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `bestwhois.py` | 51 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `bestwhois.py` | 53 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `bestwhois.py` | 56 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `bestwhois.py` | 296 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `bestwhois.py` | 298 | `undefined_name` | on execution | mypy | Name "raw_str" is not defined |
| `clean_version.py` | 43 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `msg` |
| `cleaner.py` | 24 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `ANSI_RE` |
| `cleaner.py` | 38 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `FENCE_RE` |
| `cleaner.py` | 39 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `SHELL_PROMPT_RE` |
| `cleaner.py` | 40 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `PREAMBLE_RE` |
| `cleaner.py` | 56 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Path` |
| `cleaner.py` | 57 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Path` |
| `copilot_noneng.py` | 162 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `as_completed` |
| `copilot_noneng.py` | 188 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `as_completed` |
| `copilot_noneng.py` | 211 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `as_completed` |
| `cppu.py` | 34 | `undefined_name` | on execution | ruff | Undefined name `before` |
| `cppu.py` | 34 | `undefined_name` | on execution | ruff | Undefined name `after` |
| `crmc.py` | 277 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `contextlib` |
| `crun.py` | 39 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `run_command` |
| `crun.py` | 39 | `undefined_name` | on execution | pylint | Possibly using variable 'cmd' before assignment |
| `csshtmlpret.py` | 73 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 214 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `minidom` |
| `csshtmlpret.py` | 242 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 266 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 273 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 274 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 284 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 332 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 333 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 339 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 340 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 341 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 343 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 344 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 345 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 347 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 348 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 349 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 352 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 360 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `csshtmlpret.py` | 361 | `undefined_name` | on execution | mypy | Name "args" is not defined |
| `decryptor.py` | 16 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `LiteralString` |
| `deduper.py` | 109 | `call_signature` | on execution | mypy, pylint, ty | Unexpected keyword argument 'filter' in method call |
| `deduplicate_python.py` | 81 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Language` |
| `dj.py` | 214 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `rel_path` |
| `dll.py` | 18 | `undefined_name` | on execution | pylint | Possibly using variable 'fromline' before assignment |
| `dll.py` | 18 | `undefined_name` | on execution | pylint | Possibly using variable 'toline' before assignment |
| `drmc.py` | 129 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `fil88enames` |
| `dt1.py` | 121 | `undefined_name` | on execution | ruff, ty | Undefined name `source` |
| `dupfx.py` | 83 | `undefined_name` | on execution | pylint | Using variable 'Iterator' before assignment |
| `egg2whl.py` | 63 | `undefined_name` | on execution | pylint | Possibly using variable 'sys' before assignment |
| `ensurebracket.py` | 15 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `path` |
| `ex_const.py` | 26 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `CHUNK_SIZE` |
| `ex_const.py` | 71 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `get_pyfiles` |
| `excss.py` | 24 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `unique_path` |
| `find_big_files.py` | 21 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `should_skip` |
| `find_big_files.py` | 26 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `should_skip` |
| `furls.py` | 273 | `call_signature` | on execution | mypy, pylint, ty | Unexpected keyword argument 'found' in function call |
| `fztrans.py` | 37 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Iterable` |
| `gitrepos.py` | 14 | `undefined_name` | on execution | pylint | Using variable 'url' before assignment |
| `gittools.py` | 234 | `undefined_name` | on execution | pylint | Possibly using variable 'sys' before assignment |
| `h2md.py` | 16 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `md_content` |
| `htmltomarkdown.py` | 605 | `call_signature` | on execution | mypy, ty | Missing positional argument "attrs" in call to "Tag" |
| `htmltomd.py` | 147 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Pool` |
| `htmltools.py` | 903 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `BytesParser` |
| `htmltools.py` | 903 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `policy` |
| `img2asci.py` | 13 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `path` |
| `img2asci.py` | 25 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Pool` |
| `imports4.py` | 128 | `undefined_name` | on execution | pylint | Possibly using variable 'data' before assignment |
| `importtools.py` | 627 | `call_signature` | on execution | mypy, pylint, ty | Too many positional arguments for function call |
| `java_serialization_data_converter.py` | 19 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Any` |
| `main_guard_checker.py` | 214 | `call_signature` | on execution | mypy, ty | Too many arguments |
| `man_doc.py` | 67 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `err` |
| `micro2py.py` | 21 | `undefined_name` | on execution | mypy, pylint | Possibly using variable 'importlib' before assignment |
| `mkpik.py` | 54 | `call_signature` | on execution | mypy, pylint, ty | Unexpected keyword argument 'legacy' in function call |
| `mkpyc.py` | 44 | `undefined_name` | on execution | pylint | Possibly using variable 'sign' before assignment |
| `movebin.py` | 14 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `is_binary` |
| `nb2py.py` | 125 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `AsyncResult` |
| `ncdu.py` | 478 | `undefined_name` | on execution | mypy | Name "curses._CursesWindow" is not defined |
| `pfzf.py` | 211 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Local variable `selected_idx` referenced before assignment |
| `pfzf.py` | 212 | `undefined_name` | on execution | mypy, ty | Name "selected_idx" is used before definition |
| `pfzf.py` | 213 | `undefined_name` | on execution | mypy, ty | Name "selected_idx" is used before definition |
| `pfzf.py` | 214 | `undefined_name` | on execution | mypy, ty | Name "selected_idx" is used before definition |
| `pfzf.py` | 216 | `undefined_name` | on execution | ty | Name `selected_idx` used when not defined |
| `pycppcheck.py` | 21 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `run_command` |
| `pydevtools.py` | 30 | `undefined_name` | on execution | mypy, ruff, ty | Undefined name `NoReturn` |
| `pydevtools.py` | 560 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `textwrap` |
| `pydevtools.py` | 598 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `textwrap` |
| `pydevtools.py` | 1150 | `undefined_name` | on execution | pylint | Possibly using variable 'meta' before assignment |
| `pydevtools.py` | 1392 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `textwrap` |
| `pydos2unix.py` | 37 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `f` |
| `pyget.py` | 517 | `attribute_error` | on execution | ty | Object of type `Iterator[tuple[StreamInfo, Iterator[bytes]]]` cannot be used with `with` because it does not implement `__enter__` |
| `pyjcal.py` | 337 | `call_signature` | on execution | mypy, pylint, ty | Too many positional arguments for staticmethod call |
| `qrcoder.py` | 16 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `decoded_objects` |
| `rmctools.py` | 960 | `undefined_name` | on execution | pylint | Possibly using variable 'cmd_libcst' before assignment |
| `sonic.py` | 39 | `undefined_name` | on execution | pylint | Using variable 'Generator' before assignment |
| `sonic.py` | 74 | `undefined_name` | on execution | pylint | Using variable 'Generator' before assignment |
| `sonic.py` | 92 | `undefined_name` | on execution | pylint | Using variable 'Generator' before assignment |
| `sonic.py` | 166 | `undefined_name` | on execution | pylint | Using variable 'Generator' before assignment |
| `sortbysize.py` | 18 | `undefined_name` | on execution | pylint | Possibly using variable 'size' before assignment |
| `sqltojson.py` | 154 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `_list_connections` |
| `sqltojson.py` | 163 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `_list_queries` |
| `sqltojson.py` | 165 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `_list_queries` |
| `sqltojson.py` | 523 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `_list_connections` |
| `sqltojson.py` | 532 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `_list_queries` |
| `sqltojson.py` | 534 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `_list_queries` |
| `tcs.py` | 444 | `undefined_name` | on execution | pylint | Possibly using variable 'source' before assignment |
| `tcs.py` | 446 | `undefined_name` | on execution | pylint | Possibly using variable 'ranged' before assignment |
| `tell_font_name.py` | 52 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `path` |
| `ter_ser.py` | 51 | `call_signature` | on execution | mypy, ty | Unexpected keyword argument "ext" for "extend" of "list" |
| `to_jpg.py` | 119 | `undefined_name` | on execution | mypy, pylint, ruff, ty | Undefined name `Union` |
| `xembed.py` | 166 | `call_signature` | on execution | mypy, ty | Unexpected keyword argument "walk_up" for "relative_to" of "PurePath" |

## Runtime risks (not counted as blocking)

Type/attribute errors can crash at runtime, but are frequently false positives with dynamic code or uninstalled libraries, so they are reported separately.

Total distinct runtime risks: **1519**. The full list is in `blocking_errors.json → runtime_risks`.

## Excluded import issues

**1600** diagnostics about missing / unresolvable modules were excluded:

- `ty:unresolved-import`: 1532
- `ruff:F401`: 67
- `pylint:IMPORT-CASCADE`: 1

## How to fix

1. Run `python3 reports/fix_small_errors.py` for a dry run of the safe, mechanical fixes (unused imports, stray `f` prefixes, trailing whitespace, missing final newline, invalid escape sequences).
2. Add `--apply` to actually edit files in place (use `--backup` to keep `.bak` copies). The script re-compiles every file it touches and reverts any change that breaks it.
3. Fix remaining blocking issues by hand using the file/line table above. `fix_small_errors.py` deliberately does not attempt semantic rewrites such as undefined names or PEP 695/701 syntax.

