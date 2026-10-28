# Python script similarity report

Generated 2026-10-28T04:29:56+00:00 · **821 scripts** · **103 groups** · 285 scripts belong to a group (536 singletons).

Scripts that do nearly the same job are placed in the same group. The machine-readable version is `similarity_report.json`; the visual version is `similarity_report.svg`.

## Method (short)

Each script is turned into a weighted feature vector built from normalised token 5-grams, an AST node-type skeleton, imports, called APIs, CLI flags, function names and documentation/filename vocabulary. Features are IDF weighted so that boilerplate does not create false matches. Pairs are scored with `0.52*(0.55*cos_all + 0.30*containment + 0.15*cos_api) + 0.48*(0.50*cos_purpose + 0.25*cos_api + 0.25*name_sim); plus a filename-variant boost (name_sim >= 0.72) and a near-literal-copy boost (containment >= 0.85)`, and pairs at or above `0.55` are grouped by density-based leader clustering around a medoid script.

## Overview

| Group | Scripts | Avg. score | Medoid (best keeper) | What they do |
|---|---:|---:|---|---|
| G001 | 13 | 0.278 | `rmc2.py` | rmc  ·  fmt, found, noqa |
| G002 | 12 | 0.478 | `clean-js.py` | clean  ·  comment, found |
| G003 | 11 | 0.438 | `eximports2.py` | imports  ·  requirements, txt |
| G004 | 7 | 0.268 | `translate0.py` | translate  ·  found, failed, error, process |
| G005 | 6 | 0.601 | `dt3.py` | dt  ·  failed, chunks, api, key |
| G006 | 5 | 0.611 | `pdfv2.py` | pdfv-pdfview  ·  latin, replace, mutool, ppm |
| G007 | 5 | 0.482 | `html_to_md.py` | html  ·  style, parser |
| G008 | 5 | 0.428 | `deduper.py` | dedup  ·  duplicates, found, move, copy |
| G009 | 4 | 0.669 | `tco2.py` | tco  ·  failed, translator, region, endpoint |
| G010 | 4 | 0.876 | `woff2woff2.py` | woff |
| G011 | 4 | 0.749 | `showenc.py` | showenc.py  ·  confidence, encoding, usage, report |
| G012 | 4 | 0.421 | `cccpp.py` | cpp  ·  process |
| G013 | 4 | 0.369 | `rmshebang.py` | shebang  ·  spawn |
| G014 | 3 | 0.603 | `py_clean.py` | clean  ·  fmt, found, pyclean, error |
| G015 | 3 | 0.564 | `clean-bash.py` | clean-bash  ·  process, shellcheck, header |
| G016 | 3 | 0.760 | `delafter.py` | delafter.py |
| G017 | 3 | 0.818 | `pytoipynb.py` | ipynb |
| G018 | 3 | 0.638 | `pngq.py` | pngq.py  ·  found, error |
| G019 | 3 | 0.833 | `csv2json2.py` | json-csv |
| G020 | 3 | 0.712 | `consolidate.py` | rassingle.py  ·  check, multiline, logging, body |
| G021 | 3 | 0.683 | `merge_enfa.py` | merge |
| G022 | 3 | 0.752 | `url2pdf2.py` | pdf-url  ·  usage |
| G023 | 3 | 0.555 | `mhtml.py` | mht  ·  meta, location, found, ascii |
| G024 | 3 | 0.685 | `pysanity-check.py` | sanity-check  ·  packages, installed, summary, date |
| G025 | 3 | 0.585 | `rm_from_archive.py` | archive  ·  tar |
| G026 | 3 | 0.657 | `dostounix.py` | dos-unix  ·  process |
| G027 | 3 | 0.451 | `pyterser.py` | ser-ter  ·  summary, size, interrupted, bytes |
| G028 | 3 | 0.400 | `noneng.py` | noneng  ·  language, directory, report, found |
| G029 | 3 | 0.553 | `pkgtools.py` | pkg  ·  packages, points, missing, found |
| G030 | 3 | 0.377 | `merger.py` | merger |
| G031 | 3 | 0.537 | `migrate_git.py` | migrate-git  ·  new, ssh, github, agent |
| G032 | 3 | 0.403 | `dupfx.py` | dupfx.py  ·  found |
| G033 | 3 | 0.394 | `py_refact.py` | refactor  ·  lineno, split, class, makedirs |
| G034 | 3 | 0.464 | `gext0.py` | gext  ·  finished, class, successfully, tasks |
| G035 | 2 | 0.964 | `bcss.py` | bcss-ccss  ·  cyan, green, change, error |
| G036 | 2 | 0.940 | `spdf2.py` | spdf  ·  smaller, original |
| G037 | 2 | 0.631 | `h2md.py` | hmd-rst |
| G038 | 2 | 0.814 | `ghpy10.py` | py-gh  ·  github, token, ghpy, txt |
| G039 | 2 | 0.993 | `compy.py` | compy  ·  inputs, compressed, found, stdlib |
| G040 | 2 | 0.978 | `simple_pipdown.py` | pipdown-spdown  ·  saved, selected, cached, distribution |
| G041 | 2 | 0.978 | `pydup.py` | dup-find-duplicate  ·  failed, groups, skipped, scanned |
| G042 | 2 | 0.980 | `aitrans.py` | trans-inplace-translator  ·  gemini, key, api, openai |
| G043 | 2 | 0.618 | `getpyrepos.py` | get-repos  ·  github |
| G044 | 2 | 0.660 | `feloai.py` | feloai-wrapper  ·  interrupted |
| G045 | 2 | 0.968 | `docstring_formatter.py` | ter-format-docstring  ·  rrbbuuff |
| G046 | 2 | 0.568 | `dupdirs.py` | dup  ·  found |
| G047 | 2 | 0.555 | `tomlfmt.py` | fmt  ·  found, toml |
| G048 | 2 | 0.663 | `importz.py` | importz-collector-import  ·  imports, found, stdlib, party |
| G049 | 2 | 0.631 | `wheelinspector.py` | inspector-wheel  ·  directory, found, dist |
| G050 | 2 | 0.773 | `pdftools2.py` | pdf-pdftoolz  ·  shrink, split, complete, img |
| G051 | 2 | 0.672 | `exjs.py` | ex-js-css  ·  parser, red, cyan |
| G052 | 2 | 0.595 | `pdftotext.py` | text-pdf |
| G053 | 2 | 0.789 | `ewhl2.py` | ewhl  ·  info, empty, whl, wheels |
| G054 | 2 | 0.973 | `pbat.py` | pbat-bat  ·  pager, git, colorterm, less |
| G055 | 2 | 0.971 | `fssim.py` | fssim-ssdim  ·  threshold, matrix, similar, copied |
| G056 | 2 | 0.554 | `del10.py` | del-delemp |
| G057 | 2 | 0.758 | `timg.py` | timg-pycatimg  ·  image |
| G058 | 2 | 0.731 | `audio2txt.py` | audio-txt-text  ·  wav, loading |
| G059 | 2 | 0.733 | `pkltojson.py` | json-pkl |
| G060 | 2 | 0.674 | `mergecss.py` | css-merge |

_…and 43 more groups; see the JSON report._

## Groups in detail

### G001 — rmc  ·  fmt, found, noqa

- **13 scripts**, avg similarity **0.278** (range 0.000–0.761)
- **Suggested keeper:** `rmc2.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job

<details><summary>members</summary>

- `rmc2.py` — 705 lines, nearest `rmcst.py` (0.67)
- `crmc.py` — 559 lines, nearest `rmc2.py` (0.61)
- `drmc.py` — 845 lines, nearest `rmc2.py` (0.60)
- `felormc.py` — 318 lines, nearest `rmc2.py` (0.62)
- `grmc.py` — 258 lines, nearest `rmc.py` (0.58)
- `grmcst.py` — 138 lines, nearest `rmcst.py` (0.61)
- `rmc-ts.py` — 367 lines, nearest `rmc.py` (0.76)
- `rmc.py` — 390 lines, nearest `rmc-ts.py` (0.76)
- `rmc3.py` — 888 lines, nearest `rmcts.py` (0.59)
- `rmca.py` — 374 lines, nearest `rmc2.py` (0.64)
- `rmcst.py` — 204 lines, nearest `rmc2.py` (0.67)
- `rmcts.py` — 340 lines, nearest `rmc3.py` (0.59)
- `srmc1.py` — 726 lines, nearest `rmc2.py` (0.63)

</details>

### G002 — clean  ·  comment, found

- **12 scripts**, avg similarity **0.478** (range 0.000–0.973)
- **Suggested keeper:** `clean-js.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.66)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `pathlib`, `tree_sitter`

<details><summary>members</summary>

- `clean-js.py` — 215 lines, nearest `clean-ts.py` (0.97)
- `clean-css.py` — 224 lines, nearest `clean-toml.py` (0.97)
- `clean-html.py` — 227 lines, nearest `clean-css.py` (0.74)
- `clean-lua.py` — 205 lines, nearest `clean-toml.py` (0.97)
- `clean-rs.py` — 296 lines, nearest `cleanrs.py` (0.61)
- `clean-toml.py` — 196 lines, nearest `clean-css.py` (0.97)
- `clean-ts.py` — 216 lines, nearest `clean-js.py` (0.97)
- `cleanjsts.py` — 112 lines, nearest `clean-ts.py` (0.61)
- `cleanrs.py` — 154 lines, nearest `cleants2.py` (0.62)
- `cleants.py` — 646 lines, nearest `tscleaner.py` (0.60)
- `cleants2.py` — 429 lines, nearest `tscleaner.py` (0.64)
- `tscleaner.py` — 216 lines, nearest `cleants2.py` (0.64)

</details>

### G003 — imports  ·  requirements, txt

- **11 scripts**, avg similarity **0.438** (range 0.000–0.980)
- **Suggested keeper:** `eximports2.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.70)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`

<details><summary>members</summary>

- `eximports2.py` — 62 lines, nearest `ex_ex.py` (0.96)
- `ex_class.py` — 44 lines, nearest `ex_func.py` (0.98)
- `ex_comments.py` — 44 lines, nearest `ex_ex.py` (0.98)
- `ex_ex.py` — 44 lines, nearest `ex_comments.py` (0.98)
- `ex_func.py` — 44 lines, nearest `ex_class.py` (0.98)
- `ex_imports.py` — 44 lines, nearest `eximports2.py` (0.76)
- `eximports.py` — 123 lines, nearest `ex_imports.py` (0.73)
- `eximports3.py` — 43 lines, nearest `ex_imports.py` (0.68)
- `imports.py` — 328 lines, nearest `eximports3.py` (0.64)
- `imports4.py` — 369 lines, nearest `imports5.py` (0.62)
- `imports5.py` — 793 lines, nearest `imports4.py` (0.62)

</details>

### G004 — translate  ·  found, failed, error, process

- **7 scripts**, avg similarity **0.268** (range 0.000–0.613)
- **Suggested keeper:** `translate0.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `deep_translator`, `pathlib`, `re`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `translate0.py` — 359 lines, nearest `translate_files.py` (0.61)
- `fa_translator.py` — 707 lines, nearest `fatrans.py` (0.57)
- `fatrans.py` — 558 lines, nearest `fatranslate.py` (0.60)
- `fatranslate.py` — 434 lines, nearest `translate_files.py` (0.61)
- `translate_code_comments.py` — 805 lines, nearest `translate0.py` (0.58)
- `translate_files.py` — 633 lines, nearest `translate0.py` (0.61)
- `translate_py_literals.py` — 171 lines, nearest `translate0.py` (0.56)

</details>

### G005 — dt  ·  failed, chunks, api, key

- **6 scripts**, avg similarity **0.601** (range 0.000–0.980)
- **Suggested keeper:** `dt3.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.64)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `deep_translator`, `json`, `loguru`, `pathlib`, `sys`, `threading`, `time`, `typing`
- **Shared CLI flags:** `--source`, `--target`, `-o`, `-s`, `-t`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `dt3.py` — 761 lines, nearest `dtluna.py` (0.98)
- `dt1.py` — 578 lines, nearest `dt4.py` (0.78)
- `dt2.py` — 417 lines, nearest `dt4.py` (0.63)
- `dt4.py` — 484 lines, nearest `dt1.py` (0.78)
- `dt5.py` — 685 lines, nearest `dt4.py` (0.74)
- `dtluna.py` — 761 lines, nearest `dt3.py` (0.98)

</details>

### G006 — pdfv-pdfview  ·  latin, replace, mutool, ppm

- **5 scripts**, avg similarity **0.611** (range 0.000–0.973)
- **Suggested keeper:** `pdfv2.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.68)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `os`, `shutil`, `sys`, `termios`, `tty`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `pdfv2.py` — 470 lines, nearest `tpv.py` (0.97)
- `pdfv.py` — 293 lines, nearest `pdfv2.py` (0.74)
- `pdfview.py` — 567 lines, nearest `pdfviewer.py` (0.60)
- `pdfviewer.py` — 318 lines, nearest `pdfv2.py` (0.79)
- `tpv.py` — 625 lines, nearest `pdfv2.py` (0.97)

</details>

### G007 — html  ·  style, parser

- **5 scripts**, avg similarity **0.482** (range 0.000–0.963)
- **Suggested keeper:** `html_to_md.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.60)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `pathlib`, `sys`

<details><summary>members</summary>

- `html_to_md.py` — 51 lines, nearest `tomd.py` (0.96)
- `htmltomd.py` — 156 lines, nearest `mkhtml.py` (0.58)
- `htmltools.py` — 1146 lines, nearest `htmltomd.py` (0.56)
- `mkhtml.py` — 24 lines, nearest `html_to_md.py` (0.60)
- `tomd.py` — 45 lines, nearest `html_to_md.py` (0.96)

</details>

### G008 — dedup  ·  duplicates, found, move, copy

- **5 scripts**, avg similarity **0.428** (range 0.000–0.976)
- **Suggested keeper:** `deduper.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.68)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `ast`, `hashlib`, `pathlib`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `deduper.py` — 502 lines, nearest `dduper.py` (0.66)
- `dduper.py` — 454 lines, nearest `deduplicate_python.py` (0.98)
- `deduplicate_python.py` — 477 lines, nearest `dduper.py` (0.98)
- `deduptools.py` — 488 lines, nearest `deduper.py` (0.57)
- `pydeduper.py` — 830 lines, nearest `deduper.py` (0.65)

</details>

### G009 — tco  ·  failed, translator, region, endpoint

- **4 scripts**, avg similarity **0.669** (range 0.583–0.759)
- **Suggested keeper:** `tco2.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.67)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `json`, `pathlib`, `sys`, `time`
- **Shared CLI flags:** `--source`, `--target`, `-s`, `-t`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `tco2.py` — 693 lines, nearest `tco1.py` (0.76)
- `tco.py` — 310 lines, nearest `tco3.py` (0.60)
- `tco1.py` — 761 lines, nearest `tco2.py` (0.76)
- `tco3.py` — 664 lines, nearest `tco2.py` (0.76)

</details>

### G010 — woff

- **4 scripts**, avg similarity **0.876** (range 0.744–0.978)
- **Suggested keeper:** `woff2woff2.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.88)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `dh`, `fontTools.ttLib`, `pathlib`, `sys`
- **Shared definitions:** `main`, `process_file`

<details><summary>members</summary>

- `woff2woff2.py` — 39 lines, nearest `otf2woff2.py` (0.98)
- `otf2woff2.py` — 38 lines, nearest `woff2woff2.py` (0.98)
- `ttf2woff2.py` — 37 lines, nearest `woff2woff2.py` (0.97)
- `woff22woff.py` — 39 lines, nearest `woff2woff2.py` (0.92)

</details>

### G011 — showenc.py  ·  confidence, encoding, usage, report

- **4 scripts**, avg similarity **0.749** (range 0.424–0.978)
- **Suggested keeper:** `showenc.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.75)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `chardet`, `charset_normalizer`, `pathlib`, `sys`

<details><summary>members</summary>

- `showenc.py` — 134 lines, nearest `detect_encoding.py` (0.98)
- `detect_encoding.py` — 175 lines, nearest `showenc.py` (0.98)
- `getenc.py` — 117 lines, nearest `showenc.py` (0.97)
- `show_encodings.py` — 38 lines, nearest `showenc.py` (0.69)

</details>

### G012 — cpp  ·  process

- **4 scripts**, avg similarity **0.421** (range 0.000–0.764)
- **Suggested keeper:** `cccpp.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.63)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`, `sys`

<details><summary>members</summary>

- `cccpp.py` — 280 lines, nearest `clean-cpp.py` (0.76)
- `clean-cpp.py` — 179 lines, nearest `cccpp.py` (0.76)
- `cppnew.py` — 44 lines, nearest `cpprun.py` (0.65)
- `cpprun.py` — 86 lines, nearest `cppnew.py` (0.65)

</details>

### G013 — shebang  ·  spawn

- **4 scripts**, avg similarity **0.369** (range 0.000–0.570)
- **Suggested keeper:** `rmshebang.py`
- **Basis:** mixed: shared code + shared purpose (confidence: low, cohesion 0.55)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `rmshebang.py` — 50 lines, nearest `mkpyc.py` (0.57)
- `ensurebracket.py` — 51 lines, nearest `rmshebang.py` (0.56)
- `mkpyc.py` — 49 lines, nearest `rmshebang.py` (0.57)
- `shebangtools.py` — 666 lines, nearest `rmshebang.py` (0.55)

</details>

### G014 — clean  ·  fmt, found, pyclean, error

- **3 scripts**, avg similarity **0.603** (range 0.586–0.635)
- **Suggested keeper:** `py_clean.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.60)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `libcst`, `pathlib`, `sys`, `typing`
- **Shared definitions:** `__init__`, `leave_ClassDef`, `leave_FunctionDef`, `leave_Module`, `main`

<details><summary>members</summary>

- `py_clean.py` — 779 lines, nearest `cleanpy.py` (0.64)
- `cleanpy.py` — 275 lines, nearest `py_clean.py` (0.64)
- `pyclean.py` — 741 lines, nearest `py_clean.py` (0.59)

</details>

### G015 — clean-bash  ·  process, shellcheck, header

- **3 scripts**, avg similarity **0.564** (range 0.000–0.965)
- **Suggested keeper:** `clean-bash.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.85)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `collections.abc`, `multiprocessing`, `pathlib`, `sys`, `tree_sitter`, `tree_sitter_bash`, `typing`
- **Shared definitions:** `main`, `process_file`, `strip_comments`

<details><summary>members</summary>

- `clean-bash.py` — 200 lines, nearest `tsrmc.py` (0.97)
- `cleanbash.py` — 171 lines, nearest `clean-bash.py` (0.73)
- `tsrmc.py` — 298 lines, nearest `clean-bash.py` (0.97)

</details>

### G016 — delafter.py

- **3 scripts**, avg similarity **0.760** (range 0.697–0.843)
- **Suggested keeper:** `delafter.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.76)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`, `sys`
- **Shared definitions:** `read_lines`

<details><summary>members</summary>

- `delafter.py` — 26 lines, nearest `delbefor.py` (0.84)
- `abline.py` — 46 lines, nearest `delafter.py` (0.74)
- `delbefor.py` — 28 lines, nearest `delafter.py` (0.84)

</details>

### G017 — ipynb

- **3 scripts**, avg similarity **0.818** (range 0.803–0.848)
- **Suggested keeper:** `pytoipynb.py`
- **Basis:** same job family, different implementations (confidence: high, cohesion 0.82)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `nbformat`, `pathlib`

<details><summary>members</summary>

- `pytoipynb.py` — 29 lines, nearest `py2ipynb.py` (0.85)
- `ipynb2md.py` — 24 lines, nearest `pytoipynb.py` (0.80)
- `py2ipynb.py` — 82 lines, nearest `pytoipynb.py` (0.85)

</details>

### G018 — pngq.py  ·  found, error

- **3 scripts**, avg similarity **0.638** (range 0.549–0.687)
- **Suggested keeper:** `pngq.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.64)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `dataclasses`, `multiprocessing`, `pathlib`, `shutil`, `subprocess`, `sys`, `typing`
- **Shared CLI flags:** `--dry-run`, `--jobs`, `--root`, `-j`, `-n`
- **Shared definitions:** `Result`, `main`, `optimize_one`, `saved`

<details><summary>members</summary>

- `pngq.py` — 142 lines, nearest `jpo.py` (0.69)
- `jpo.py` — 112 lines, nearest `pngq.py` (0.69)
- `pysvg.py` — 148 lines, nearest `pngq.py` (0.68)

</details>

### G019 — json-csv

- **3 scripts**, avg similarity **0.833** (range 0.820–0.843)
- **Suggested keeper:** `csv2json2.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.83)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `csv`, `json`, `pathlib`, `sys`

<details><summary>members</summary>

- `csv2json2.py` — 25 lines, nearest `csvtojson.py` (0.84)
- `csv2json.py` — 44 lines, nearest `csv2json2.py` (0.84)
- `csvtojson.py` — 22 lines, nearest `csv2json2.py` (0.84)

</details>

### G020 — rassingle.py  ·  check, multiline, logging, body

- **3 scripts**, avg similarity **0.712** (range 0.577–0.980)
- **Suggested keeper:** `consolidate.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.71)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `argparse`, `ast`, `pathlib`, `re`, `sys`, `typing`
- **Shared CLI flags:** `--merged-file`, `--output`, `-f`, `-o`
- **Shared definitions:** `ExecutorTransformer`, `LoggingTransformer`, `OsPathTransformer`, `SixImportRewriter`, `SixTransformer`, `_ExecutorMethodRenamer`, `__init__`, `_is_executor_ref`, `_is_named_assign`, `_is_ospath`, `_make_assign`, `_module_imports_path_bare`

<details><summary>members</summary>

- `consolidate.py` — 1079 lines, nearest `cconsolidate.py` (0.98)
- `cconsolidate.py` — 1079 lines, nearest `consolidate.py` (0.98)
- `rassingle.py` — 653 lines, nearest `consolidate.py` (0.58)

</details>

### G021 — merge

- **3 scripts**, avg similarity **0.683** (range 0.647–0.717)
- **Suggested keeper:** `merge_enfa.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.68)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`

<details><summary>members</summary>

- `merge_enfa.py` — 99 lines, nearest `merge_faen.py` (0.72)
- `merge_faen.py` — 162 lines, nearest `merge_enfa.py` (0.72)
- `mergepy.py` — 37 lines, nearest `merge_enfa.py` (0.69)

</details>

### G022 — pdf-url  ·  usage

- **3 scripts**, avg similarity **0.752** (range 0.683–0.851)
- **Suggested keeper:** `url2pdf2.py`
- **Basis:** same job family, different implementations (confidence: high, cohesion 0.75)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `sys`

<details><summary>members</summary>

- `url2pdf2.py` — 31 lines, nearest `url2pdf3.py` (0.85)
- `url2pdf.py` — 22 lines, nearest `url2pdf2.py` (0.72)
- `url2pdf3.py` — 38 lines, nearest `url2pdf2.py` (0.85)

</details>

### G023 — mht  ·  meta, location, found, ascii

- **3 scripts**, avg similarity **0.555** (range 0.366–0.686)
- **Suggested keeper:** `mhtml.py`
- **Basis:** same job family, different implementations (confidence: low, cohesion 0.55)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `base64`, `email.parser`, `pathlib`, `re`, `sys`, `urllib.parse`, `urllib.request`
- **Shared CLI flags:** `--output`
- **Shared definitions:** `convert_file`, `main`, `parse_mhtml`

<details><summary>members</summary>

- `mhtml.py` — 561 lines, nearest `mhtml-to-html.py` (0.69)
- `mht.py` — 1869 lines, nearest `mhtml.py` (0.61)
- `mhtml-to-html.py` — 599 lines, nearest `mhtml.py` (0.69)

</details>

### G024 — sanity-check  ·  packages, installed, summary, date

- **3 scripts**, avg similarity **0.685** (range 0.667–0.698)
- **Suggested keeper:** `pysanity-check.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.68)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `sys`

<details><summary>members</summary>

- `pysanity-check.py` — 88 lines, nearest `sanity-check.py` (0.70)
- `pip_sanity_check.py` — 75 lines, nearest `pysanity-check.py` (0.69)
- `sanity-check.py` — 73 lines, nearest `pysanity-check.py` (0.70)

</details>

### G025 — archive  ·  tar

- **3 scripts**, avg similarity **0.585** (range 0.563–0.604)
- **Suggested keeper:** `rm_from_archive.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `shutil`, `sys`, `tarfile`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `rm_from_archive.py` — 80 lines, nearest `archive_dir.py` (0.60)
- `archive_dir.py` — 147 lines, nearest `rm_from_archive.py` (0.60)
- `archive_tools.py` — 885 lines, nearest `rm_from_archive.py` (0.59)

</details>

### G026 — dos-unix  ·  process

- **3 scripts**, avg similarity **0.657** (range 0.622–0.723)
- **Suggested keeper:** `dostounix.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `multiprocessing`, `pathlib`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `dostounix.py` — 113 lines, nearest `pydos2unix.py` (0.72)
- `pydos2unix.py` — 142 lines, nearest `dostounix.py` (0.72)
- `pydos2unix2.py` — 147 lines, nearest `dostounix.py` (0.63)

</details>

### G027 — ser-ter  ·  summary, size, interrupted, bytes

- **3 scripts**, avg similarity **0.451** (range 0.000–0.742)
- **Suggested keeper:** `pyterser.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.68)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`, `sys`
- **Shared definitions:** `main`, `process_file`

<details><summary>members</summary>

- `pyterser.py` — 612 lines, nearest `opng.py` (0.74)
- `opng.py` — 610 lines, nearest `pyterser.py` (0.74)
- `ter_ser.py` — 62 lines, nearest `pyterser.py` (0.61)

</details>

### G028 — noneng  ·  language, directory, report, found

- **3 scripts**, avg similarity **0.400** (range 0.000–0.645)
- **Suggested keeper:** `noneng.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.60)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `multiprocessing`, `pathlib`, `typing`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `noneng.py` — 422 lines, nearest `copilot_noneng.py` (0.65)
- `copilot_noneng.py` — 251 lines, nearest `noneng.py` (0.65)
- `noneng_langdet.py` — 539 lines, nearest `noneng.py` (0.55)

</details>

### G029 — pkg  ·  packages, points, missing, found

- **3 scripts**, avg similarity **0.553** (range 0.551–0.555)
- **Suggested keeper:** `pkgtools.py`
- **Basis:** same job family, different implementations (confidence: low, cohesion 0.55)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `concurrent.futures`, `os`, `pathlib`, `shutil`, `sys`, `typing`
- **Shared CLI flags:** `--workers`
- **Shared definitions:** `build_parser`, `main`

<details><summary>members</summary>

- `pkgtools.py` — 775 lines, nearest `pkgtools2.py` (0.56)
- `pkg_tools.py` — 1003 lines, nearest `pkgtools.py` (0.55)
- `pkgtools2.py` — 984 lines, nearest `pkgtools.py` (0.56)

</details>

### G030 — merger

- **3 scripts**, avg similarity **0.377** (range 0.000–0.576)
- **Suggested keeper:** `merger.py`
- **Basis:** loosely related (review before merging) (confidence: low, cohesion 0.57)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `argparse`, `pathlib`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `merger.py` — 276 lines, nearest `reqmerger.py` (0.58)
- `archive_merger.py` — 91 lines, nearest `merger.py` (0.55)
- `reqmerger.py` — 53 lines, nearest `merger.py` (0.58)

</details>

### G031 — migrate-git  ·  new, ssh, github, agent

- **3 scripts**, avg similarity **0.537** (range 0.000–0.969)
- **Suggested keeper:** `migrate_git.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.81)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `os`, `pathlib`, `subprocess`
- **Shared definitions:** `main`, `remove_old_ssh_keys`, `should_skip_dir`

<details><summary>members</summary>

- `migrate_git.py` — 425 lines, nearest `migrate_repos.py` (0.97)
- `migrate_git_user.py` — 282 lines, nearest `migrate_git.py` (0.64)
- `migrate_repos.py` — 493 lines, nearest `migrate_git.py` (0.97)

</details>

### G032 — dupfx.py  ·  found

- **3 scripts**, avg similarity **0.403** (range 0.000–0.619)
- **Suggested keeper:** `dupfx.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.60)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `argparse`, `collections`, `pathlib`, `typing`, `xxhash`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `dupfx.py` — 417 lines, nearest `dupf.py` (0.62)
- `dupf.py` — 117 lines, nearest `dupfx.py` (0.62)
- `gdupfx.py` — 303 lines, nearest `dupfx.py` (0.59)

</details>

### G033 — refactor  ·  lineno, split, class, makedirs

- **3 scripts**, avg similarity **0.394** (range 0.000–0.628)
- **Suggested keeper:** `py_refact.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `ast`, `pathlib`, `re`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `py_refact.py` — 484 lines, nearest `refactor_as_single.py` (0.63)
- `py_refactor.py` — 652 lines, nearest `py_refact.py` (0.55)
- `refactor_as_single.py` — 272 lines, nearest `py_refact.py` (0.63)

</details>

### G034 — gext  ·  finished, class, successfully, tasks

- **3 scripts**, avg similarity **0.464** (range 0.000–0.742)
- **Suggested keeper:** `gext0.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.70)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `multiprocessing`, `os`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `gext0.py` — 240 lines, nearest `gexcst.py` (0.74)
- `gexcst.py` — 269 lines, nearest `gext0.py` (0.74)
- `gext.py` — 135 lines, nearest `gext0.py` (0.65)

</details>

### G035 — bcss-ccss  ·  cyan, green, change, error

- **2 scripts**, avg similarity **0.964** (range 0.964–0.964)
- **Suggested keeper:** `bcss.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.96)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `dh`, `pathlib`, `sys`
- **Shared definitions:** `main`, `process_file`

<details><summary>members</summary>

- `bcss.py` — 44 lines, nearest `ccss.py` (0.96)
- `ccss.py` — 52 lines, nearest `bcss.py` (0.96)

</details>

### G036 — spdf  ·  smaller, original

- **2 scripts**, avg similarity **0.940** (range 0.940–0.940)
- **Suggested keeper:** `spdf2.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.94)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `dh`, `pathlib`, `sys`
- **Shared definitions:** `main`, `process_file`

<details><summary>members</summary>

- `spdf2.py` — 58 lines, nearest `spdf.py` (0.94)
- `spdf.py` — 73 lines, nearest `spdf2.py` (0.94)

</details>

### G037 — hmd-rst

- **2 scripts**, avg similarity **0.631** (range 0.631–0.631)
- **Suggested keeper:** `h2md.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.63)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `dh`, `markdownify`, `pathlib`, `sys`
- **Shared definitions:** `process_file`

<details><summary>members</summary>

- `h2md.py` — 33 lines, nearest `rst2md.py` (0.63)
- `rst2md.py` — 52 lines, nearest `h2md.py` (0.63)

</details>

### G038 — py-gh  ·  github, token, ghpy, txt

- **2 scripts**, avg similarity **0.814** (range 0.814–0.814)
- **Suggested keeper:** `ghpy10.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.81)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `dotenv`, `os`, `pathlib`, `requests`

<details><summary>members</summary>

- `ghpy10.py` — 38 lines, nearest `ghpy.py` (0.81)
- `ghpy.py` — 38 lines, nearest `ghpy10.py` (0.81)

</details>

### G039 — compy  ·  inputs, compressed, found, stdlib

- **2 scripts**, avg similarity **0.993** (range 0.993–0.993)
- **Suggested keeper:** `compy.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.99)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `ast`, `builtins`, `dh`, `io`, `keyword`, `multiprocessing`, `pathlib`, `re`, `sys`, `sysconfig`
- **Shared definitions:** `AnnotationStripper`, `ImportCleaner`, `NameCollector`, `NameRenamer`, `Simplifier`, `__init__`, `_add_name`, `_can_rename`, `_clean_block`, `_collect_arguments`, `_convert_boolean_return_pattern`, `_fold_expression_if_shorter`

<details><summary>members</summary>

- `compy.py` — 762 lines, nearest `compy2.py` (0.99)
- `compy2.py` — 764 lines, nearest `compy.py` (0.99)

</details>

### G040 — pipdown-spdown  ·  saved, selected, cached, distribution

- **2 scripts**, avg similarity **0.978** (range 0.978–0.978)
- **Suggested keeper:** `simple_pipdown.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.98)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `dataclasses`, `hashlib`, `httpx`, `loguru`, `packaging.requirements`, `packaging.specifiers`, `packaging.tags`, `packaging.utils`, `packaging.version`, `pathlib`
- **Shared CLI flags:** `--dest`, `--verbose`, `-d`, `-v`
- **Shared definitions:** `Link`, `current_tags`, `download`, `fetch_links`, `main`, `py_ok`, `select`

<details><summary>members</summary>

- `simple_pipdown.py` — 176 lines, nearest `spdown.py` (0.98)
- `spdown.py` — 194 lines, nearest `simple_pipdown.py` (0.98)

</details>

### G041 — dup-find-duplicate  ·  failed, groups, skipped, scanned

- **2 scripts**, avg similarity **0.978** (range 0.978–0.978)
- **Suggested keeper:** `pydup.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.98)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `ast`, `collections`, `collections.abc`, `concurrent.futures`, `copy`, `csv`, `dataclasses`, `datetime`, `difflib`, `fnmatch`
- **Shared CLI flags:** `--baseline`, `--changed-since`, `--diff`, `--dry-run`, `--exclude`, `--exit-code`, `--fail-on-dupes`, `--fail-on-error`, `--follow-symlinks`, `--format`, `--functions`, `--ignore-imports`
- **Shared definitions:** `CacheEntry`, `DefinitionGroup`, `DefinitionRef`, `DuplicateGroup`, `FileEntry`, `NearPair`, `RunStats`, `ScanConfig`, `ScanOutcome`, `SourceNormalizer`, `WorkerConfig`, `WorkerResult`

<details><summary>members</summary>

- `pydup.py` — 2958 lines, nearest `python_duplicate_finder.py` (0.98)
- `python_duplicate_finder.py` — 2433 lines, nearest `pydup.py` (0.98)

</details>

### G042 — trans-inplace-translator  ·  gemini, key, api, openai

- **2 scripts**, avg similarity **0.980** (range 0.980–0.980)
- **Suggested keeper:** `aitrans.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.98)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `glob`, `google`, `google.genai`, `openai`, `os`, `pathlib`, `sys`
- **Shared CLI flags:** `--extensions`, `--lang`, `-e`, `-l`
- **Shared definitions:** `UniversalTranslator`, `__init__`, `is_configured`, `load_env_file`, `main`, `process_file`, `translate_text`

<details><summary>members</summary>

- `aitrans.py` — 158 lines, nearest `inplace_translator.py` (0.98)
- `inplace_translator.py` — 158 lines, nearest `aitrans.py` (0.98)

</details>

### G043 — get-repos  ·  github

- **2 scripts**, avg similarity **0.618** (range 0.618–0.618)
- **Suggested keeper:** `getpyrepos.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.62)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `json`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `getpyrepos.py` — 121 lines, nearest `getrepos.py` (0.62)
- `getrepos.py` — 96 lines, nearest `getpyrepos.py` (0.62)

</details>

### G044 — feloai-wrapper  ·  interrupted

- **2 scripts**, avg similarity **0.660** (range 0.660–0.660)
- **Suggested keeper:** `feloai.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `datetime`, `os`, `pathlib`, `subprocess`, `sys`
- **Shared definitions:** `create_log_file`, `main`, `write_log_footer`, `write_log_header`

<details><summary>members</summary>

- `feloai.py` — 99 lines, nearest `wrapper_gh.py` (0.66)
- `wrapper_gh.py` — 105 lines, nearest `feloai.py` (0.66)

</details>

### G045 — ter-format-docstring  ·  rrbbuuff

- **2 scripts**, avg similarity **0.968** (range 0.968–0.968)
- **Suggested keeper:** `docstring_formatter.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.97)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `pathlib`, `re`
- **Shared definitions:** `main`, `process_file`

<details><summary>members</summary>

- `docstring_formatter.py` — 125 lines, nearest `prompt-reformatter.py` (0.97)
- `prompt-reformatter.py` — 76 lines, nearest `docstring_formatter.py` (0.97)

</details>

### G046 — dup  ·  found

- **2 scripts**, avg similarity **0.568** (range 0.568–0.568)
- **Suggested keeper:** `dupdirs.py`
- **Basis:** loosely related (review before merging) (confidence: low, cohesion 0.57)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `collections`, `pathlib`, `sys`, `xxhash`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `dupdirs.py` — 199 lines, nearest `duptools.py` (0.57)
- `duptools.py` — 684 lines, nearest `dupdirs.py` (0.57)

</details>

### G047 — fmt  ·  found, toml

- **2 scripts**, avg similarity **0.555** (range 0.555–0.555)
- **Suggested keeper:** `tomlfmt.py`
- **Basis:** loosely related (review before merging) (confidence: low, cohesion 0.55)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `dataclasses`, `multiprocessing`, `pathlib`, `sys`, `typing`
- **Shared definitions:** `__init__`, `main`

<details><summary>members</summary>

- `tomlfmt.py` — 686 lines, nearest `fmt_toml.py` (0.55)
- `fmt_toml.py` — 294 lines, nearest `tomlfmt.py` (0.55)

</details>

### G048 — importz-collector-import  ·  imports, found, stdlib, party

- **2 scripts**, avg similarity **0.663** (range 0.663–0.663)
- **Suggested keeper:** `importz.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `ast`, `pathlib`, `sys`
- **Shared definitions:** `get_imports_from_file`, `main`

<details><summary>members</summary>

- `importz.py` — 59 lines, nearest `import_collector.py` (0.66)
- `import_collector.py` — 95 lines, nearest `importz.py` (0.66)

</details>

### G049 — inspector-wheel  ·  directory, found, dist

- **2 scripts**, avg similarity **0.631** (range 0.631–0.631)
- **Suggested keeper:** `wheelinspector.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.63)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `pathlib`, `zipfile`
- **Shared CLI flags:** `--verbose`, `-v`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `wheelinspector.py` — 534 lines, nearest `wheel_inspector.py` (0.63)
- `wheel_inspector.py` — 142 lines, nearest `wheelinspector.py` (0.63)

</details>

### G050 — pdf-pdftoolz  ·  shrink, split, complete, img

- **2 scripts**, avg similarity **0.773** (range 0.773–0.773)
- **Suggested keeper:** `pdftools2.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.77)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `concurrent.futures`, `contextlib`, `pathlib`, `re`, `shutil`, `subprocess`, `sys`, `typing`, `urllib.parse`
- **Shared CLI flags:** `-`, `------------------------`, `---Conversion Summary---`, `--check-titles`, `--directory`, `--dpi`, `--engine`, `--html_path`, `--keep`, `--max-mb`, `--output`, `--output-subdir`
- **Shared definitions:** `TreeNode`, `__init__`, `__str__`, `_convert_one_pdf`, `_merge_sort_key`, `_outline_id`, `_rename_one`, `_shrink_dispatch`, `_shrink_gs_basic`, `_shrink_gs_mobile`, `_shrink_gs_screen`, `_shrink_qpdf`

<details><summary>members</summary>

- `pdftools2.py` — 662 lines, nearest `pdftoolz.py` (0.77)
- `pdftoolz.py` — 710 lines, nearest `pdftools2.py` (0.77)

</details>

### G051 — ex-js-css  ·  parser, red, cyan

- **2 scripts**, avg similarity **0.672** (range 0.672–0.672)
- **Suggested keeper:** `exjs.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.67)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `bs4`, `bs4.element`, `dh`, `pathlib`, `sys`, `typing`
- **Shared definitions:** `main`, `process_file`

<details><summary>members</summary>

- `exjs.py` — 54 lines, nearest `excss.py` (0.67)
- `excss.py` — 55 lines, nearest `exjs.py` (0.67)

</details>

### G052 — text-pdf

- **2 scripts**, avg similarity **0.595** (range 0.595–0.595)
- **Suggested keeper:** `pdftotext.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `pathlib`, `pdfplumber`
- **Shared definitions:** `extract_pages`, `main`

<details><summary>members</summary>

- `pdftotext.py` — 110 lines, nearest `pdf2text.py` (0.59)
- `pdf2text.py` — 210 lines, nearest `pdftotext.py` (0.59)

</details>

### G053 — ewhl  ·  info, empty, whl, wheels

- **2 scripts**, avg similarity **0.789** (range 0.789–0.789)
- **Suggested keeper:** `ewhl2.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.79)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `pathlib`, `shutil`, `zipfile`
- **Shared CLI flags:** `--dest`, `-d`
- **Shared definitions:** `is_empty_wheel`, `main`

<details><summary>members</summary>

- `ewhl2.py` — 250 lines, nearest `ewhl.py` (0.79)
- `ewhl.py` — 95 lines, nearest `ewhl2.py` (0.79)

</details>

### G054 — pbat-bat  ·  pager, git, colorterm, less

- **2 scripts**, avg similarity **0.973** (range 0.973–0.973)
- **Suggested keeper:** `pbat.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.97)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `argparse`, `dataclasses`, `io`, `os`, `pathlib`, `pygments`, `pygments.formatters`, `pygments.lexers`, `pygments.styles`, `pygments.util`, `re`
- **Shared CLI flags:** `-`, `--color`, `--highlight-line`, `--language`, `--line-range`, `--list-languages`, `--list-themes`, `--paging`, `--plain`, `--style`, `--tabs`, `--theme`
- **Shared definitions:** `BatConfig`, `GitDiffCalculator`, `Printer`, `__init__`, `_compute`, `_get_formatter`, `_get_lexer`, `_highlight_lines`, `_parse_hunks`, `_print_header`, `_print_line`, `_resolve_range`

<details><summary>members</summary>

- `pbat.py` — 395 lines, nearest `pybat.py` (0.97)
- `pybat.py` — 396 lines, nearest `pbat.py` (0.97)

</details>

### G055 — fssim-ssdim  ·  threshold, matrix, similar, copied

- **2 scripts**, avg similarity **0.971** (range 0.971–0.971)
- **Suggested keeper:** `fssim.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.97)
- **Recommendation:** near-duplicate: consolidate into one script
- **Shared imports:** `__future__`, `colorama`, `csv`, `json`, `os`, `pathlib`, `shutil`, `ssdeep`, `sys`, `tabulate`
- **Shared definitions:** `colorize_score`, `compute_hashes`, `copy_groups`, `get_all_files`, `group_similar_files`, `main`, `write_matrix`, `write_report`

<details><summary>members</summary>

- `fssim.py` — 180 lines, nearest `ssdim.py` (0.97)
- `ssdim.py` — 178 lines, nearest `fssim.py` (0.97)

</details>

### G056 — del-delemp

- **2 scripts**, avg similarity **0.554** (range 0.554–0.554)
- **Suggested keeper:** `del10.py`
- **Basis:** loosely related (review before merging) (confidence: low, cohesion 0.55)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `pathlib`, `sys`

<details><summary>members</summary>

- `del10.py` — 24 lines, nearest `delemp.py` (0.55)
- `delemp.py` — 287 lines, nearest `del10.py` (0.55)

</details>

### G057 — timg-pycatimg  ·  image

- **2 scripts**, avg similarity **0.758** (range 0.758–0.758)
- **Suggested keeper:** `timg.py`
- **Basis:** same job family, different implementations (confidence: high, cohesion 0.76)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `PIL`, `__future__`, `argparse`, `cairosvg`, `io`, `sys`, `typing`
- **Shared CLI flags:** `--height`, `--width`, `-H`
- **Shared definitions:** `load_image`, `main`

<details><summary>members</summary>

- `timg.py` — 129 lines, nearest `pycatimg.py` (0.76)
- `pycatimg.py` — 187 lines, nearest `timg.py` (0.76)

</details>

### G058 — audio-txt-text  ·  wav, loading

- **2 scripts**, avg similarity **0.731** (range 0.731–0.731)
- **Suggested keeper:** `audio2txt.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.73)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `os`, `pydub`, `speech_recognition`, `sys`, `tempfile`

<details><summary>members</summary>

- `audio2txt.py` — 56 lines, nearest `audio2text.py` (0.73)
- `audio2text.py` — 114 lines, nearest `audio2txt.py` (0.73)

</details>

### G059 — json-pkl

- **2 scripts**, avg similarity **0.733** (range 0.733–0.733)
- **Suggested keeper:** `pkltojson.py`
- **Basis:** same job family, different implementations (confidence: high, cohesion 0.73)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `json`, `pickle`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `pkltojson.py` — 80 lines, nearest `pkl2json.py` (0.73)
- `pkl2json.py` — 59 lines, nearest `pkltojson.py` (0.73)

</details>

### G060 — css-merge

- **2 scripts**, avg similarity **0.674** (range 0.674–0.674)
- **Suggested keeper:** `mergecss.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.67)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`

<details><summary>members</summary>

- `mergecss.py` — 9 lines, nearest `merge_css.py` (0.67)
- `merge_css.py` — 112 lines, nearest `mergecss.py` (0.67)

</details>

### G061 — ssdiper  ·  score, similarity

- **2 scripts**, avg similarity **0.691** (range 0.691–0.691)
- **Suggested keeper:** `ssdiper2.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.69)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `argparse`, `collections`, `dh`, `json`, `operator`, `pathlib`, `ssdeep`
- **Shared CLI flags:** `--group-similar`, `-g`
- **Shared definitions:** `group_similar`

<details><summary>members</summary>

- `ssdiper2.py` — 165 lines, nearest `ssdiper.py` (0.69)
- `ssdiper.py` — 380 lines, nearest `ssdiper2.py` (0.69)

</details>

### G062 — guard-main-check

- **2 scripts**, avg similarity **0.663** (range 0.663–0.663)
- **Suggested keeper:** `main_guard_checker.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `ast`, `pathlib`, `typing`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `main_guard_checker.py` — 315 lines, nearest `check_main_guard.py` (0.66)
- `check_main_guard.py` — 63 lines, nearest `main_guard_checker.py` (0.66)

</details>

### G063 — siter  ·  info, points, txt, generator

- **2 scripts**, avg similarity **0.839** (range 0.839–0.839)
- **Suggested keeper:** `siter.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.84)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `argparse`, `base64`, `csv`, `hashlib`, `multiprocessing`, `packaging.tags`, `pathlib`, `platform`, `shutil`, `sys`, `tempfile`, `zipfile`
- **Shared CLI flags:** `-`, `--no-parallel`
- **Shared definitions:** `WheelBuilder`, `__init__`, `_compute_hash`, `_detect_purity`, `_find_bin_dir`, `_find_data_for_package`, `_find_scripts_for_package`, `_find_venv_root`, `_get_wheel_tags`, `_read_record`, `build_all`, `build_wheel`

<details><summary>members</summary>

- `siter.py` — 393 lines, nearest `siter2.py` (0.84)
- `siter2.py` — 328 lines, nearest `siter.py` (0.84)

</details>

### G064 — decryptor-encryptor  ·  key

- **2 scripts**, avg similarity **0.835** (range 0.835–0.835)
- **Suggested keeper:** `decryptor.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.83)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `cryptography.hazmat.backends`, `cryptography.hazmat.primitives`, `cryptography.hazmat.primitives.ciphers`, `os`, `pathlib`, `random`, `string`
- **Shared CLI flags:** `--decrypt`, `--encrypt`, `--key`
- **Shared definitions:** `decrypt_file`, `encrypt_file`, `main`, `random_key`

<details><summary>members</summary>

- `decryptor.py` — 74 lines, nearest `encryptor.py` (0.83)
- `encryptor.py` — 84 lines, nearest `decryptor.py` (0.83)

</details>

### G065 — dedup-func  ·  failed, enter, please, duplicates

- **2 scripts**, avg similarity **0.656** (range 0.656–0.656)
- **Suggested keeper:** `dedup_func.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `ast`, `collections`, `pathlib`, `re`
- **Shared CLI flags:** `--backup`, `--remove`, `-r`
- **Shared definitions:** `__init__`, `main`, `visit_FunctionDef`

<details><summary>members</summary>

- `dedup_func.py` — 809 lines, nearest `dedupfunc.py` (0.66)
- `dedupfunc.py` — 209 lines, nearest `dedup_func.py` (0.66)

</details>

### G066 — tcg  ·  error, bash, clipboard, found

- **2 scripts**, avg similarity **0.814** (range 0.814–0.814)
- **Suggested keeper:** `tcg.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.81)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`, `subprocess`, `sys`
- **Shared definitions:** `create_symlink`, `get_clipboard_content`, `main`, `replace_shebang`

<details><summary>members</summary>

- `tcg.py` — 123 lines, nearest `tcg3.py` (0.81)
- `tcg3.py` — 172 lines, nearest `tcg.py` (0.81)

</details>

### G067 — annotate-types  ·  typing, pyi

- **2 scripts**, avg similarity **0.783** (range 0.783–0.783)
- **Suggested keeper:** `annotate.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.78)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `ast`, `difflib`, `libcst`, `libcst.codemod`, `libcst.codemod.visitors`, `pathlib`, `shutil`, `subprocess`, `sys`
- **Shared CLI flags:** `--diff`, `--dry-run`, `--future-annotations`, `--no-overwrite`, `--quiet`, `--stub-file`, `-d`, `-n`, `-q`, `-s`
- **Shared definitions:** `TypeshedSanitizer`, `apply_type_annotations`, `compute_diff`, `leave_Attribute`, `leave_Import`, `leave_ImportFrom`, `leave_Name`, `main`, `sanitize_stub_cst`, `validate_python_code`

<details><summary>members</summary>

- `annotate.py` — 615 lines, nearest `annotate_types.py` (0.78)
- `annotate_types.py` — 280 lines, nearest `annotate.py` (0.78)

</details>

### G068 — hunspeller-spell  ·  words, autofix, misspelled, found

- **2 scripts**, avg similarity **0.773** (range 0.773–0.773)
- **Suggested keeper:** `hunspeller.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.77)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `multiprocessing`, `re`
- **Shared CLI flags:** `--autofix`, `--processes`, `-a`, `-p`
- **Shared definitions:** `check_and_replace`, `process_file`, `process_line`

<details><summary>members</summary>

- `hunspeller.py` — 219 lines, nearest `speller.py` (0.77)
- `speller.py` — 119 lines, nearest `hunspeller.py` (0.77)

</details>

### G069 — cliner

- **2 scripts**, avg similarity **0.773** (range 0.773–0.773)
- **Suggested keeper:** `cliner.py`
- **Basis:** near-duplicate / heavily shared code (confidence: high, cohesion 0.77)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`, `re`
- **Shared definitions:** `clean_line`, `main`

<details><summary>members</summary>

- `cliner.py` — 101 lines, nearest `cliner2.py` (0.77)
- `cliner2.py` — 57 lines, nearest `cliner.py` (0.77)

</details>

### G070 — email-collector-crawler  ·  stopping, sgr, csv, crawled

- **2 scripts**, avg similarity **0.762** (range 0.762–0.762)
- **Suggested keeper:** `email_collector.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.76)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `curses`, `logging`, `logging.config`, `logging.handlers`, `pathlib`, `re`, `sqlalchemy`, `sys`, `traceback`, `urllib.error`, `urllib.parse`
- **Shared definitions:** `ColorStreamHandler`, `CrawlerDb`, `__init__`, `close`, `color`, `connect`, `crawl`, `crawled`, `dequeue`, `emit`, `enqueue`, `find_emails_2_level_deep`

<details><summary>members</summary>

- `email_collector.py` — 356 lines, nearest `email_crawler.py` (0.76)
- `email_crawler.py` — 343 lines, nearest `email_collector.py` (0.76)

</details>

### G071 — get-keys  ·  txt

- **2 scripts**, avg similarity **0.734** (range 0.734–0.734)
- **Suggested keeper:** `get_keys.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.73)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `json`, `pathlib`, `sys`, `typing`
- **Shared CLI flags:** `--output`, `--sort`, `-o`
- **Shared definitions:** `load_json`, `main`, `parse_args`

<details><summary>members</summary>

- `get_keys.py` — 103 lines, nearest `getkeys.py` (0.73)
- `getkeys.py` — 81 lines, nearest `get_keys.py` (0.73)

</details>

### G072 — split  ·  error

- **2 scripts**, avg similarity **0.730** (range 0.730–0.730)
- **Suggested keeper:** `pysplit.py`
- **Basis:** same job family, different implementations (confidence: high, cohesion 0.73)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `pysplit.py` — 56 lines, nearest `splitby.py` (0.73)
- `splitby.py` — 30 lines, nearest `pysplit.py` (0.73)

</details>

### G073 — pyhead-cleanhistory

- **2 scripts**, avg similarity **0.565** (range 0.565–0.565)
- **Suggested keeper:** `pyhead.py`
- **Basis:** mixed: shared code + shared purpose (confidence: low, cohesion 0.56)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`

<details><summary>members</summary>

- `pyhead.py` — 15 lines, nearest `cleanhistory.py` (0.56)
- `cleanhistory.py` — 15 lines, nearest `pyhead.py` (0.56)

</details>

### G074 — cf-fc

- **2 scripts**, avg similarity **0.723** (range 0.723–0.723)
- **Suggested keeper:** `c2f.py`
- **Basis:** mixed: shared code + shared purpose (confidence: high, cohesion 0.72)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `sys`

<details><summary>members</summary>

- `c2f.py` — 10 lines, nearest `f2c.py` (0.72)
- `f2c.py` — 11 lines, nearest `c2f.py` (0.72)

</details>

### G075 — pret

- **2 scripts**, avg similarity **0.714** (range 0.714–0.714)
- **Suggested keeper:** `pret.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.71)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `pret.py` — 56 lines, nearest `pret2.py` (0.71)
- `pret2.py` — 134 lines, nearest `pret.py` (0.71)

</details>

### G076 — transliterate-fnames  ·  nfkd

- **2 scripts**, avg similarity **0.709** (range 0.709–0.709)
- **Suggested keeper:** `transliterate_fnames.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.71)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `argparse`, `pathlib`, `re`, `unicodedata`
- **Shared definitions:** `main`, `transliterate`

<details><summary>members</summary>

- `transliterate_fnames.py` — 257 lines, nearest `transliterate_fnames2.py` (0.71)
- `transliterate_fnames2.py` — 216 lines, nearest `transliterate_fnames.py` (0.71)

</details>

### G077 — pkgs-system-reinstall

- **2 scripts**, avg similarity **0.707** (range 0.707–0.707)
- **Suggested keeper:** `reinstall_system_pkgs.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.71)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `reinstall_system_pkgs.py` — 37 lines, nearest `system_pkgs_reinstaller.py` (0.71)
- `system_pkgs_reinstaller.py` — 134 lines, nearest `reinstall_system_pkgs.py` (0.71)

</details>

### G078 — top

- **2 scripts**, avg similarity **0.705** (range 0.705–0.705)
- **Suggested keeper:** `top11.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.71)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`

<details><summary>members</summary>

- `top11.py` — 40 lines, nearest `top12.py` (0.71)
- `top12.py` — 30 lines, nearest `top11.py` (0.71)

</details>

### G079 — distinfo

- **2 scripts**, avg similarity **0.702** (range 0.702–0.702)
- **Suggested keeper:** `distinfo.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.70)
- **Recommendation:** strong overlap: pick one canonical script, retire the rest
- **Shared imports:** `__future__`, `pathlib`

<details><summary>members</summary>

- `distinfo.py` — 47 lines, nearest `distinfo2.py` (0.70)
- `distinfo2.py` — 77 lines, nearest `distinfo.py` (0.70)

</details>

### G080 — sort

- **2 scripts**, avg similarity **0.687** (range 0.687–0.687)
- **Suggested keeper:** `fasort.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.69)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `sys`

<details><summary>members</summary>

- `fasort.py` — 113 lines, nearest `sort_pyfile.py` (0.69)
- `sort_pyfile.py` — 107 lines, nearest `fasort.py` (0.69)

</details>

### G081 — fco-gfco

- **2 scripts**, avg similarity **0.672** (range 0.672–0.672)
- **Suggested keeper:** `fco.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.67)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `fontTools.ttLib`, `multiprocessing`, `pathlib`, `sys`, `typing`
- **Shared CLI flags:** `--output-dir`, `--remove`, `--to`, `-r`
- **Shared definitions:** `convert_font`, `main`

<details><summary>members</summary>

- `fco.py` — 495 lines, nearest `gfco.py` (0.67)
- `gfco.py` — 175 lines, nearest `fco.py` (0.67)

</details>

### G082 — shebang-fix-opt

- **2 scripts**, avg similarity **0.663** (range 0.663–0.663)
- **Suggested keeper:** `fix_shebang_opt.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `fix_shebang_opt.py` — 106 lines, nearest `fixshebang.py` (0.66)
- `fixshebang.py` — 124 lines, nearest `fix_shebang_opt.py` (0.66)

</details>

### G083 — mkinit

- **2 scripts**, avg similarity **0.663** (range 0.663–0.663)
- **Suggested keeper:** `mkinit.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `ast`, `pathlib`, `sys`
- **Shared definitions:** `get_public_names`, `main`

<details><summary>members</summary>

- `mkinit.py` — 243 lines, nearest `mkinit2.py` (0.66)
- `mkinit2.py` — 154 lines, nearest `mkinit.py` (0.66)

</details>

### G084 — get-downloader  ·  status, isatty, content, interrupted

- **2 scripts**, avg similarity **0.662** (range 0.662–0.662)
- **Suggested keeper:** `pyget.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `concurrent.futures`, `contextlib`, `pathlib`, `pycurl`, `queue`, `re`, `requests`, `shutil`, `sys`, `threading`
- **Shared CLI flags:** `--backend`, `--file`, `--jobs`, `--no-resume`, `--output`, `--quiet`, `--timeout`, `--version`, `-V`, `-b`, `-f`, `-j`
- **Shared definitions:** `Backend`, `Bar`, `Progress`, `PycurlBackend`, `RequestsBackend`, `__enter__`, `__exit__`, `__init__`, `_eta`, `_loop`, `_paint`, `_sanitize`

<details><summary>members</summary>

- `pyget.py` — 753 lines, nearest `python_downloader.py` (0.66)
- `python_downloader.py` — 779 lines, nearest `pyget.py` (0.66)

</details>

### G085 — escape-fix-sequence

- **2 scripts**, avg similarity **0.661** (range 0.661–0.661)
- **Suggested keeper:** `fix_escape_sequence.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job

<details><summary>members</summary>

- `fix_escape_sequence.py` — 225 lines, nearest `fixescape.py` (0.66)
- `fixescape.py` — 153 lines, nearest `fix_escape_sequence.py` (0.66)

</details>

### G086 — dj

- **2 scripts**, avg similarity **0.660** (range 0.660–0.660)
- **Suggested keeper:** `dj.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `pathlib`, `shutil`

<details><summary>members</summary>

- `dj.py` — 224 lines, nearest `dj2.py` (0.66)
- `dj2.py` — 62 lines, nearest `dj.py` (0.66)

</details>

### G087 — vars-collect-env

- **2 scripts**, avg similarity **0.658** (range 0.658–0.658)
- **Suggested keeper:** `collect_env_vars.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`, `re`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `collect_env_vars.py` — 30 lines, nearest `xenv_vars.py` (0.66)
- `xenv_vars.py` — 35 lines, nearest `collect_env_vars.py` (0.66)

</details>

### G088 — whl-fix-names  ·  metadata

- **2 scripts**, avg similarity **0.658** (range 0.658–0.658)
- **Suggested keeper:** `fixwhl.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.66)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `email.parser`, `pathlib`, `zipfile`

<details><summary>members</summary>

- `fixwhl.py` — 74 lines, nearest `fixwhlnames.py` (0.66)
- `fixwhlnames.py` — 254 lines, nearest `fixwhl.py` (0.66)

</details>

### G089 — move  ·  found

- **2 scripts**, avg similarity **0.651** (range 0.651–0.651)
- **Suggested keeper:** `move_tests_dirs.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.65)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `loguru`, `pathlib`, `shutil`, `typing`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `move_tests_dirs.py` — 91 lines, nearest `move_tests_files.py` (0.65)
- `move_tests_files.py` — 177 lines, nearest `move_tests_dirs.py` (0.65)

</details>

### G090 — utf-iso

- **2 scripts**, avg similarity **0.625** (range 0.625–0.625)
- **Suggested keeper:** `iso8859toutf8.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.63)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`

<details><summary>members</summary>

- `iso8859toutf8.py` — 20 lines, nearest `toutf8.py` (0.63)
- `toutf8.py` — 124 lines, nearest `iso8859toutf8.py` (0.63)

</details>

### G091 — dup-objects-gdetect  ·  scan

- **2 scripts**, avg similarity **0.622** (range 0.622–0.622)
- **Suggested keeper:** `gdetect_dup_objects.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.62)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `ast`, `json`, `pathlib`, `typing`
- **Shared definitions:** `TypeAnnotationChecker`, `__init__`, `get_canonical_structure`, `main`, `visit_AnnAssign`, `visit_AsyncFunctionDef`, `visit_FunctionDef`

<details><summary>members</summary>

- `gdetect_dup_objects.py` — 154 lines, nearest `gdupfunc.py` (0.62)
- `gdupfunc.py` — 321 lines, nearest `gdetect_dup_objects.py` (0.62)

</details>

### G092 — folderize-sim-names  ·  found

- **2 scripts**, avg similarity **0.611** (range 0.611–0.611)
- **Suggested keeper:** `folderize.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.61)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `pathlib`, `shutil`

<details><summary>members</summary>

- `folderize.py` — 95 lines, nearest `folderize_by_sim_names.py` (0.61)
- `folderize_by_sim_names.py` — 87 lines, nearest `folderize.py` (0.61)

</details>

### G093 — crun-find

- **2 scripts**, avg similarity **0.608** (range 0.608–0.608)
- **Suggested keeper:** `crun.py`
- **Basis:** mixed: shared code + shared purpose (confidence: medium, cohesion 0.61)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `dh`, `os`, `pathlib`
- **Shared definitions:** `get_filez`, `main`, `process_file`

<details><summary>members</summary>

- `crun.py` — 57 lines, nearest `find_big_files.py` (0.61)
- `find_big_files.py` — 52 lines, nearest `crun.py` (0.61)

</details>

### G094 — pnr  ·  operation, cancelled

- **2 scripts**, avg similarity **0.605** (range 0.605–0.605)
- **Suggested keeper:** `pnr.py`
- **Basis:** same job family, different implementations (confidence: medium, cohesion 0.60)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `pathlib`
- **Shared CLI flags:** `--dry-run`, `--remove`, `--replace`, `--template`, `-r`, `-s`, `-t`
- **Shared definitions:** `main`, `should_skip`

<details><summary>members</summary>

- `pnr.py` — 208 lines, nearest `pnr2.py` (0.60)
- `pnr2.py` — 359 lines, nearest `pnr.py` (0.60)

</details>

### G095 — afk-afkx

- **2 scripts**, avg similarity **0.604** (range 0.604–0.604)
- **Suggested keeper:** `afk.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.60)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `ast`, `concurrent.futures`, `dataclasses`, `difflib`, `pathlib`, `re`, `sys`, `tarfile`, `typing`, `zipfile`
- **Shared CLI flags:** `--diff`, `--dry-run`, `--exclude`, `--workers`
- **Shared definitions:** `FileResult`, `UnusedImport`, `__init__`, `analyze_source`, `build_parser`, `main`, `visit_Name`

<details><summary>members</summary>

- `afk.py` — 880 lines, nearest `afkx.py` (0.60)
- `afkx.py` — 650 lines, nearest `afk.py` (0.60)

</details>

### G096 — facal-hijri

- **2 scripts**, avg similarity **0.604** (range 0.604–0.604)
- **Suggested keeper:** `facal.py`
- **Basis:** near-duplicate / heavily shared code (confidence: medium, cohesion 0.60)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `datetime`, `faprint`
- **Shared definitions:** `gregorian_to_jalali`, `to_persian_digits`

<details><summary>members</summary>

- `facal.py` — 153 lines, nearest `hijri.py` (0.60)
- `hijri.py` — 80 lines, nearest `facal.py` (0.60)

</details>

### G097 — markdowntopdf-pdf

- **2 scripts**, avg similarity **0.593** (range 0.593–0.593)
- **Suggested keeper:** `markdowntopdf.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `markdown`, `pathlib`, `sys`, `weasyprint`
- **Shared CLI flags:** `--css`, `--output`, `-o`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `markdowntopdf.py` — 123 lines, nearest `topdf.py` (0.59)
- `topdf.py` — 881 lines, nearest `markdowntopdf.py` (0.59)

</details>

### G098 — strip-tags-html

- **2 scripts**, avg similarity **0.592** (range 0.592–0.592)
- **Suggested keeper:** `strip_html_tags.py`
- **Basis:** loosely related (review before merging) (confidence: medium, cohesion 0.59)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`

<details><summary>members</summary>

- `strip_html_tags.py` — 214 lines, nearest `striptags.py` (0.59)
- `striptags.py` — 259 lines, nearest `strip_html_tags.py` (0.59)

</details>

### G099 — tts-wav-txt

- **2 scripts**, avg similarity **0.576** (range 0.576–0.576)
- **Suggested keeper:** `tts_from_file.py`
- **Basis:** mixed: shared code + shared purpose (confidence: low, cohesion 0.58)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`, `subprocess`
- **Shared definitions:** `chunk_text`, `speak_text`

<details><summary>members</summary>

- `tts_from_file.py` — 54 lines, nearest `txt2wav.py` (0.58)
- `txt2wav.py` — 48 lines, nearest `tts_from_file.py` (0.58)

</details>

### G100 — stats-pypi  ·  downloads

- **2 scripts**, avg similarity **0.567** (range 0.567–0.567)
- **Suggested keeper:** `pypi_stats.py`
- **Basis:** same job family, different implementations (confidence: low, cohesion 0.57)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `json`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `pypi_stats.py` — 743 lines, nearest `pypistats.py` (0.57)
- `pypistats.py` — 76 lines, nearest `pypi_stats.py` (0.57)

</details>

### G101 — get-sub  ·  search, searching, title, content

- **2 scripts**, avg similarity **0.557** (range 0.557–0.557)
- **Suggested keeper:** `get_sub.py`
- **Basis:** same job family, different implementations (confidence: low, cohesion 0.56)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `argparse`, `re`, `requests`, `typing`
- **Shared definitions:** `__init__`, `main`

<details><summary>members</summary>

- `get_sub.py` — 1104 lines, nearest `getsub.py` (0.56)
- `getsub.py` — 364 lines, nearest `get_sub.py` (0.56)

</details>

### G102 — xem-xembed

- **2 scripts**, avg similarity **0.557** (range 0.557–0.557)
- **Suggested keeper:** `xem.py`
- **Basis:** loosely related (review before merging) (confidence: low, cohesion 0.56)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `base64`, `hashlib`, `pathlib`, `re`, `sys`
- **Shared definitions:** `main`

<details><summary>members</summary>

- `xem.py` — 74 lines, nearest `xembed.py` (0.56)
- `xembed.py` — 517 lines, nearest `xem.py` (0.56)

</details>

### G103 — downloader-pycurl-url

- **2 scripts**, avg similarity **0.552** (range 0.552–0.552)
- **Suggested keeper:** `pycurl_downloader.py`
- **Basis:** loosely related (review before merging) (confidence: low, cohesion 0.55)
- **Recommendation:** review: scripts appear to do the same job
- **Shared imports:** `__future__`, `pathlib`

<details><summary>members</summary>

- `pycurl_downloader.py` — 159 lines, nearest `urldownloader.py` (0.55)
- `urldownloader.py` — 118 lines, nearest `pycurl_downloader.py` (0.55)

</details>


## Strongest pairs overall

| A | B | score | containment | name |
|---|---|---:|---:|---:|
| `compy.py` | `compy2.py` | 0.993 | 0.983 | 1.000 |
| `aitrans.py` | `inplace_translator.py` | 0.980 | 1.000 | 0.275 |
| `ex_comments.py` | `ex_ex.py` | 0.980 | 1.000 | 0.236 |
| `dt3.py` | `dtluna.py` | 0.980 | 1.000 | 0.275 |
| `ex_class.py` | `ex_func.py` | 0.980 | 1.000 | 0.254 |
| `cconsolidate.py` | `consolidate.py` | 0.980 | 0.998 | 0.792 |
| `ex_class.py` | `ex_comments.py` | 0.979 | 0.989 | 0.259 |
| `ex_ex.py` | `ex_func.py` | 0.979 | 0.989 | 0.220 |
| `ex_class.py` | `ex_ex.py` | 0.979 | 0.989 | 0.200 |
| `ex_comments.py` | `ex_func.py` | 0.979 | 0.989 | 0.206 |
| `detect_encoding.py` | `showenc.py` | 0.978 | 0.984 | 0.157 |
| `otf2woff2.py` | `woff2woff2.py` | 0.978 | 0.984 | 0.665 |
| `pydup.py` | `python_duplicate_finder.py` | 0.978 | 0.981 | 0.211 |
| `simple_pipdown.py` | `spdown.py` | 0.978 | 0.979 | 0.347 |
| `dduper.py` | `deduplicate_python.py` | 0.976 | 0.963 | 0.239 |
| `getenc.py` | `showenc.py` | 0.974 | 0.952 | 0.254 |
| `detect_encoding.py` | `getenc.py` | 0.973 | 0.945 | 0.275 |
| `pbat.py` | `pybat.py` | 0.973 | 0.945 | 0.489 |
| `pdfv2.py` | `tpv.py` | 0.973 | 0.944 | 0.314 |
| `clean-js.py` | `clean-ts.py` | 0.973 | 0.940 | 0.921 |
| `fssim.py` | `ssdim.py` | 0.971 | 0.926 | 0.440 |
| `migrate_git.py` | `migrate_repos.py` | 0.969 | 0.909 | 0.500 |
| `clean-css.py` | `clean-toml.py` | 0.969 | 0.904 | 0.548 |
| `docstring_formatter.py` | `prompt-reformatter.py` | 0.968 | 0.901 | 0.602 |
| `clean-css.py` | `clean-js.py` | 0.968 | 0.896 | 0.665 |
| `clean-js.py` | `clean-toml.py` | 0.967 | 0.895 | 0.825 |
| `clean-lua.py` | `clean-toml.py` | 0.967 | 0.892 | 0.613 |
| `ttf2woff2.py` | `woff2woff2.py` | 0.967 | 0.889 | 0.592 |
| `clean-css.py` | `clean-lua.py` | 0.967 | 0.888 | 0.494 |
| `clean-toml.py` | `clean-ts.py` | 0.966 | 0.884 | 0.863 |

## Functional domains

Broad filename-derived job keywords, including scripts that remained singletons (useful for deciding where to start consolidating).

| Keyword | Scripts | In a group | Examples |
|---|---:|---:|---|
| `clean` | 31 | 18 | `clean-bash.py`, `clean-cpp.py`, `clean-css.py`, `clean-html.py` |
| `html` | 18 | 7 | `clean-html.py`, `csshtmlpret.py`, `fix_html_md_broken_links.py`, `html_entity.py` |
| `pdf` | 13 | 7 | `ocrpdf.py`, `pdf2img.py`, `pdf2page.py`, `pdf2png.py` |
| `check` | 12 | 5 | `check_conflicts.py`, `check_exports.py`, `check_fname_conflict.py`, `check_funcs.py` |
| `fix` | 12 | 6 | `filefixer.py`, `fix_encoding.py`, `fix_escape_sequence.py`, `fix_html_md_broken_links.py` |
| `get` | 12 | 7 | `get_keys.py`, `get_latest_pkgs_added_to_pypi.py`, `get_lic.py`, `get_pypi_rssfeed.py` |
| `json` | 11 | 5 | `csv2json.py`, `csv2json2.py`, `csvtojson.py`, `jsontools.py` |
| `dedup` | 8 | 5 | `dedup_func.py`, `deduper.py`, `dedupfunc.py`, `deduptools.py` |
| `imports` | 8 | 7 | `ex_imports.py`, `eximports.py`, `eximports2.py`, `eximports3.py` |
| `merge` | 8 | 5 | `merge_css.py`, `merge_enfa.py`, `merge_faen.py`, `merge_pkg.py` |
| `pkgs` | 8 | 2 | `detect_empty_pkgs.py`, `get_latest_pkgs_added_to_pypi.py`, `pypi_user_pkgs.py`, `reinstall_system_pkgs.py` |
| `rmc` | 8 | 6 | `rmc-ts.py`, `rmc.py`, `rmc2.py`, `rmc3.py` |
| `text` | 8 | 3 | `audio2text.py`, `compress_text.py`, `html_to_text_with_pyppeteer.py`, `pdf2text.py` |
| `dup` | 7 | 4 | `dup_detector.py`, `dupdirs.py`, `duptools.py`, `find_dup_folders.py` |
| `find` | 7 | 2 | `find_big_files.py`, `find_dup_folders.py`, `find_dup_func_class_const.py`, `find_empty_wheels.py` |
| `img` | 7 | 0 | `img2asci.py`, `img2txt.py`, `img_similarity.py`, `imgdownloader.py` |
| `name` | 7 | 0 | `change_project_name.py`, `rename-project.py`, `rename_by_parent.py`, `rename_html_by_title.py` |
| `pypi` | 7 | 2 | `get_latest_pkgs_added_to_pypi.py`, `get_pypi_rssfeed.py`, `latestpypi.py`, `pypi_stats.py` |
| `strip` | 7 | 2 | `htmlstrip.py`, `strip_comments.py`, `strip_html_tags.py`, `strip_installed_pkgs.py` |
| `cpp` | 6 | 4 | `cccpp.py`, `clean-cpp.py`, `cppnew.py`, `cpprun.py` |
| `format` | 6 | 2 | `docstring_formatter.py`, `format_python_code.py`, `htmlformat.py`, `prompt-reformatter.py` |
| `noneng` | 6 | 3 | `copilot_noneng.py`, `detect_noneng.py`, `noneng.py`, `noneng_langdet.py` |
| `pkg` | 6 | 3 | `emptypkg.py`, `merge_pkg.py`, `pkg_insoector.py`, `pkg_tools.py` |
| `translate` | 6 | 5 | `fatranslate.py`, `translate0.py`, `translate_code_comments.py`, `translate_files.py` |
| `wheel` | 6 | 2 | `inject_wheel_to_pip_cache.py`, `wheel_cleaner.py`, `wheel_inspector.py`, `wheel_tools.py` |
| `archive` | 5 | 4 | `archive_convert.py`, `archive_dir.py`, `archive_merger.py`, `archive_tools.py` |
| `bash` | 5 | 2 | `bash2py.py`, `bat2bash.py`, `clean-bash.py`, `cleanbash.py` |
| `css` | 5 | 4 | `clean-css.py`, `csshtmlpret.py`, `excss.py`, `merge_css.py` |
| `detect` | 5 | 1 | `detect_code_similarity.py`, `detect_empty_pkgs.py`, `detect_encoding.py`, `detect_noneng.py` |
| `downloader` | 5 | 3 | `imgdownloader.py`, `pip_downloader.py`, `pycurl_downloader.py`, `python_downloader.py` |
| `empty` | 5 | 0 | `detect_empty_pkgs.py`, `emptypkg.py`, `emptywhl.py`, `find_empty_wheels.py` |
| `font` | 5 | 0 | `apk_font_extractor.py`, `font_deduper.py`, `fontconverter.py`, `random_font.py` |
| `migrate` | 5 | 3 | `migrate2newaccount.py`, `migrate_git.py`, `migrate_git_user.py`, `migrate_repos.py` |
| `move` | 5 | 2 | `move_tests_dirs.py`, `move_tests_files.py`, `movebin.py`, `remove_duplicate_functions.py` |
| `ocr` | 5 | 0 | `ocr_ready.py`, `ocrpdf.py`, `ocrtools.py`, `pyocr.py` |
| `pip` | 5 | 1 | `inject_wheel_to_pip_cache.py`, `pip_downloader.py`, `pip_reinstaller.py`, `pip_sanity_check.py` |
| `repos` | 5 | 3 | `get_trending_py_repos.py`, `getpyrepos.py`, `getrepos.py`, `gitrepos.py` |
| `sub` | 5 | 2 | `compress_subdirs.py`, `get_sub.py`, `getsub.py`, `subdir.py` |
| `tco` | 5 | 4 | `fixextco.py`, `tco.py`, `tco1.py`, `tco2.py` |
| `ter` | 5 | 4 | `docstring_formatter.py`, `java_serialization_data_converter.py`, `prompt-reformatter.py`, `pyterser.py` |

## Caveats

- Static analysis only: no script was executed.
- Files that fail to parse on Python 3.11 use lexical features only.
- Similarity measures implementation/purpose overlap, not proven equivalence.
