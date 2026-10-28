# `bin_oct` code analysis reports

Two independent analyses of the **821 top-level `.py` scripts** in this repo:

1. **Similarity / grouping** — which scripts do nearly the same job.
2. **Errors** — which errors stop a script from running (import issues excluded).

All scripts were **read only**. Nothing in the repository was executed or edited;
the fixer was run in *dry-run* mode only. Generated on 2026-10-27 with CPython
3.11.2.

---

## Headline results

| | |
|---|---|
| Scripts analysed | 821 (235,033 lines) |
| Similarity groups | **103** groups covering **285** scripts; 536 singletons |
| Largest group | 13 scripts |
| Near-duplicate pairs (score ≥ 0.88) | 42 |
| Scripts with blocking errors | **69** (11 cannot start) |
| Distinct blocking issues | **138** — 110 undefined names, 14 broken calls, 7 syntax, 6 flow, 1 attribute |
| Runtime risks (reported separately) | 1,519 |
| Import issues ignored, by request | 1,600 |
| Python-3.12-only syntax files | 7 (fail on the sandbox's Python 3.11) |
| Mechanical fixes available | 51 files (dry run — not applied) |

### The single most important error finding

`codepener.py`, `fixescape.py`, `minhtml.py`, `rmc3.py`, `rmh.py`,
`srmc2.py` and `zip_crack.py` are **not broken**. They use PEP 695
(`type X = ...`, `def f[T]`) or PEP 701 (multiline / backslash f-string
expressions), which is valid Python **3.12+** but a `SyntaxError` on the
Python 3.11 interpreter in this environment. `ty --python-version 3.12`
reports zero syntax diagnostics for all seven. Either run them with CPython
≥ 3.12 or rewrite that syntax.

### Real blocking bugs (examples)

| File | Line | Problem |
|---|---:|---|
| `hunspeller.py` | 200 | `os.path.basename(...)` but `os` is never imported |
| `pydevtools.py` | 831, 1206, … | `textwrap` used but never imported (7 occurrences) |
| `summar.py` | 14 | typo `syd.argv` (should be `sys.argv`) |
| `h2md.py` | 16, 31 | `md_content` never defined; `p` used before assignment |
| `minhtml.py` | 264 | `contextlib` used but never imported |
| `addel.py` | 462, 479, 511 | too many arguments in a call (mypy + ty agree) |

Full list: `error_report.md` → "Blocking issues", or `blocking_errors.json`.

---

## Files in this directory

### Similarity (task 1)

| File | What it is |
|---|---|
| **`similarity_report.json`** | Machine-readable report: method, summary, 103 groups with members/shared imports/CLI flags/top pairs, all scored pairs, functional domains, per-file features |
| **`similarity_report.svg`** | Visual version of that JSON — KPI row, cluster treemap, similarity network, pairwise heatmap, strongest pairs, functional-domain bars |
| `similarity_report.md` | Readable group listing with suggested "keeper" script per group |
| `similarity_check.py` | Reproducible generator (pure stdlib, ~30 s) |

### Errors (task 2)

| File | What it is |
|---|---|
| **`error_report.md`** | Human-readable error report: counts, categories, per-file blocking issues, 3.12 syntax table, fix instructions |
| **`blocking_errors.json`** | Unified, de-duplicated blocking report: policy, summary, per-file status, blocking issues with multi-tool evidence, runtime risks, ignored imports |
| **`ruff_report.json`** | All 582 ruff diagnostics (with tier/category per diagnostic) |
| **`pylint_report.json`** | All 823 pylint diagnostics |
| **`mypy_report.json`** | All 1,360 mypy diagnostics |
| **`ty_report.json`** | All 2,539 ty diagnostics |
| `run_error_checks.py` | Reproducible driver for all four tools (~2.5 min) |
| `raw/` | Untouched stdout of each tool plus `compile_errors.json` (audit trail) |

### Fixer (task 2)

| File | What it is |
|---|---|
| **`fix_small_errors.py`** | Fixes small errors **in place** — dry-run by default, `--apply` to edit |
| `fix_report.json` | Result of the dry run: 51 files would change, 7 skipped |

---

## How the similarity grouping works

"Nearly the same job" is measured with five complementary signals rather than
plain text overlap. Every file is turned into an IDF-weighted feature vector:

| Signal | Meaning |
|---|---|
| `cos_all` | cosine over normalised token 5-grams, an anonymised-token variant, and an AST node-type skeleton |
| `containment` | \|shared 5-grams\| / smaller file — catches renamed copies |
| `cos_api` | cosine over imports, called APIs and CLI flags |
| `cos_purpose` | cosine over semantic features only (no code shingles) — catches different implementations of one task |
| `name_sim` | similarity of corpus-segmented filename stems (`csv2json` ↔ `csvtojson`) |

```
score = .52 * (.55*cos_all + .30*containment + .15*cos_api)
      + .48 * (.50*cos_purpose + .25*cos_api + .25*name_sim)
+ a filename-variant boost and a near-literal-copy boost
```

Pairs scoring ≥ 0.55 are clustered by **frontier expansion** from the densest
script (a group can grow through any member), with a cohesion test to stop
unrelated families chaining together. Each group carries `basis`,
`confidence`, `cohesion`, a medoid ("suggested keeper"), shared imports/CLI
flags/definitions and a recommendation. Thresholds and signal weights are in
`similarity_report.json → method`.

Largest families: `rmc*` (13 comment/string strippers), `clean-*` (12 code
cleaners), `ex_*`/`imports*` (11 import extractors), `translate*` (7),
`dt*` (6), `pdfv*` (5), `dedup*` (5).

**Caveat:** static analysis only — similarity means implementation/purpose
overlap, not proven equivalence. The 7 files that fail to parse on 3.11 use
lexical features only.

---

## Tool configurations (errors)

All four tools were given the same explicit list of 821 root-level `.py`
files. Import problems are suppressed by configuration **and** filtered in
the consolidator.

```bash
ruff check --no-cache --exit-zero --target-version py311 \
           --output-format json --select E4,E7,E9,F,W,PLE,B <files>

pylint --exit-zero --reports=n --score=n --output-format=json2 \
       --disable=all --enable=E,F,W \
       --disable=E0401,E0611,W0611,W0612,W0613,W0621,W0703,W0718,\
W1514,W3101,W0719,W0123,W0102,W0122 <files>

mypy --no-incremental --no-color-output --no-error-summary \
     --show-column-numbers --show-error-codes --ignore-missing-imports \
     --follow-imports=skip --scripts-are-modules --check-untyped-defs \
     --python-version 3.11 <files>

ty check --output-format concise --no-progress --no-respect-ignore-files \
         --python-version 3.11 --exit-zero <files>
```

A second `ty --python-version 3.12` pass on the files with syntax errors
confirms they are 3.12-only. A direct `compile()` check with CPython 3.11 is
the ground truth for "cannot start".

### Classification policy

* **Blocking** — `syntax_error`, `undefined_name`, `call_signature`,
  `invalid_flow`, `invalid_expression`. These stop a script or raise
  `NameError`/`TypeError`/`SyntaxError`.
* **Runtime risk** — `attribute_error`, `type_mismatch`, `redefinition`.
  Often real, but type checkers produce false positives on dynamic code and
  missing libraries, so they are reported separately.
* **Ignored import issues** — `unresolved-import`, `import-error`,
  `no-name-in-module`, `F401` unused imports, missing stubs, "cannot import X
  due to …". Excluded by request.
* **Non-blocking** — style/lint warnings. Counted, not listed individually.

Two conservative anti-false-positive filters are applied: calls to
click/typer-wrapped entry points are not linted, and a call-signature error
seen by only **one** tool is demoted to a runtime risk. 37 diagnostics were
filtered this way. Confidence is `high` when ≥ 2 tools agree (or `compile()`
fails), otherwise `medium`. A blocking issue at module level is labelled
`startup` (script cannot start); one inside a function is `on execution`.

---

## How to reproduce

```bash
# one-time tool install (outside the repo so nothing is committed)
python3 -m venv ~/.venv
~/.venv/bin/pip install ruff pylint mypy ty

# task 1 — JSON + Markdown + SVG (~30 s, stdlib only)
python3 reports/similarity_check.py

# task 2 — all four tools + reports (~2.5 min)
python3 reports/run_error_checks.py
# or rebuild reports from the saved raw output without re-running tools:
python3 reports/run_error_checks.py --from-raw

# regenerate all similarity deliverables (JSON + Markdown + SVG):
python3 reports/similarity_check.py --threshold 0.55
```

Both scripts accept `--root`, `--out-dir` and auto-detect tools in `$PATH`,
`$ANALYSIS_TOOLS_DIR`, `~/.venv/bin` or `--tools-dir`.

---

## Fixing the small errors

```bash
python3 reports/fix_small_errors.py                    # DRY RUN (default)
python3 reports/fix_small_errors.py --apply            # fix in place
python3 reports/fix_small_errors.py --apply --backup   # keep .bak copies
python3 reports/fix_small_errors.py --files a.py b.py --apply
```

What it fixes:

* trailing whitespace, whitespace on blank lines, missing/duplicate final
  newline (`W291/W292/W293`);
* invalid escape sequences in normal string literals (`W605`), e.g.
  `"\d"` → `"\\d"` — same value, no warning;
* unused imports (`F401`) and pointless `f` prefixes (`F541`) via ruff's safe
  autofix, when ruff is available.

Safety: files that do not already compile are skipped (including the seven
3.12-only files), every modified file is re-compiled and reverted if it
breaks, multi-line string contents are protected from whitespace edits, and
`--backup` writes `.bak` copies. It deliberately does **not** attempt
semantic fixes (undefined names, broken calls, PEP 695/701 syntax).

Current dry run: 51 files would change (all ruff `F401`/`F541`), 7 files
skipped as unparsable, 0 whitespace/escape fixes needed. **No file has been
modified** — run with `--apply` when you want the changes.
