# Python similarity and functional overlap

## Executive summary

A static repository-wide screening of **814 Python files** identified strong near-duplicate script pairs and shared implementations, particularly tree reconstruction (D01), resumable translation (D02), in-place translation (D03), Python compression (D05), and duplicate finders (D06–D07). These are especially strong matches, but their differences can affect behavior. Other scripts overlap in purpose while employing different approaches, notably CSV conversion, web-to-PDF, HTML-to-Markdown, language scanning, and empty-wheel detection (F01–F05). The diagrams use the same finding IDs and file relationships as this report; they are a curated overview, not a complete clone inventory.

## Scope, exclusions and method

- Enumerated recursively with `git ls-files -co --exclude-standard -- '*.py'`, deduplicated paths, and analyzed regular files rather than following symlinks. The checkout has 813 root Python files and `reqs/atomicio.py`; `reqs/` is included because no evidence establishes it as generated or vendored. Extensionless symlink entry points are not separate Python sources. There were no untracked Python sources at analysis time.
- Excluded `.git/` metadata, Git-ignored paths according to the repository `.gitignore`, and symlink aliases. The only non-Git subdirectory present initially was `reqs/`; no actual virtual-environment, vendored, generated, build or cache directory was found. The ignore file already excludes e.g. `venv/`, `.venv/`, `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, and `target/`. Reports are outputs, not source inputs.
- Used Python 3.11 standard-library tokenization and AST parsing, without installing or running project dependencies or executing the scripts. All 814 files were token-screened. Parsed functions of at least 8 source lines were compared using AST dumps after normalizing function names, argument names and `Name` identifiers; attributes, literals and other syntax remain significant. This identifies exact *normalized structures*, not necessarily exact text or semantic equivalence.
- For whole-file candidate retrieval, removed comments and layout tokens, replaced non-keyword `NAME` tokens with `NAME`, and made sets of consecutive 8-token sequences. An inverted index nominated file pairs with at least 40 shared sequences occurring in at most 80 files; pairs were retained when set Jaccard (intersection/union) was at least 0.23 or containment (intersection/smaller set) at least 0.55. These are **screening thresholds**, not reported measurements or probabilities of equivalence. Identifier normalization and common code can create false positives; set-based matching loses ordering and frequency. Manual reading/diffs checked selected candidates, plus purpose-oriented review of script behavior; shared imports or generic boilerplate alone were not treated as functional overlap.
- AST parsing failed under Python 3.11 for `minhtml.py:45`, `rmc3.py:113`, `srmc2.py:151`, and `zip_crack.py:128`; token screening still covered these. Syntax-version differences or invalid source may explain failures. This is a static, curated review: no runtime equivalence tests were performed, dynamically invoked behavior is uncertain, and lower-similarity, short, or reordered clones and unreviewed functional relationships may be missed. Confidence expresses confidence in the stated overlap, not interchangeability.

## Code duplication and near-duplication

### D01 — Tree reconstruction — especially strong match

- **Paths and evidence ranges:** `mk_tree.py:76–128, 131–310, 358–507`; `mktree.py:77–129, 132–311, 359–508`.
- **Finding:** Near-identical parsing, OCR, and tree creation, including identical normalized `image_to_entries` and `main` functions. The diff is a blank line and `Path(".")` versus `Path()`.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D02 — Resumable translation — especially strong match

- **Paths and evidence ranges:** `dt3.py:116–363, 387–443, 446–568, 577–730`; `dtluna.py:116–363, 387–443, 446–568, 577–730`.
- **Finding:** Same backend implementations, chunking, retry, and main flow. The substantive diff is the order of fallback translation providers; this can change the selected service.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D03 — In-place AI translation — especially strong match

- **Paths and evidence ranges:** `aitrans.py:20–152`; `inplace_translator.py:20–152`.
- **Finding:** Same environment loading, ChatGPT/Gemini translator, recursive file processing and CLI. Default extensions differ: the former includes Python and RST; the latter only text and Markdown.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D04 — Highlighted file viewer — especially strong match

- **Paths and evidence ranges:** `pbat.py:33–233, 275–387`; `pybat.py:34–234, 276–388`.
- **Finding:** Matching bat-like viewer, diff handling and CLI; changes include type annotation spelling and a renamed path attribute. Multiple CLI and rendering functions have identical normalized ASTs.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D05 — Python compression — especially strong match

- **Paths and evidence ranges:** `compy.py:143–423, 553–759`; `compy2.py:147–427, 557–761`.
- **Finding:** The same AST simplification, renaming and spacing pipeline; normalized `join_simple_lines` and `compact_spacing` match. Output and clipboard behavior differs, including prompt/notice handling and single-file output.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D06 — Python object deduplication — especially strong match

- **Paths and evidence ranges:** `dduper.py:67–159, 238–285, 288–442`; `deduplicate_python.py:77–169, 248–295, 298–465`.
- **Finding:** Shared AST/tree-sitter extraction and duplicate-object move/copy workflow; `extract_with_ast` and `main` normalize identically. Optional dependency handling, generated-code validation, snippet removal and tar extraction behavior differ.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D07 — Python duplicate finder — especially strong match

- **Paths and evidence ranges:** `pydup.py:539–596, 848–894, 1209–1293, 2504–2595`; `python_duplicate_finder.py:456–513, 698–744, 934–1018, 2019–2110`.
- **Finding:** Shared discovery, source processing, duplicate grouping and removal machinery; these four functions normalize identically. `pydup.py` has additional structures and logic; do not assume complete feature parity.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D08 — PyPI artifact downloader — especially strong match

- **Paths and evidence ranges:** `simple_pipdown.py:47–113, 116–173`; `spdown.py:48–114, 117–190`.
- **Finding:** Same Simple API link selection, compatibility checks and download flow, including normalized-identical `select` and `main`. `spdown.py` adds a Rich download progress display.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D09 — Fuzzy file grouping — especially strong match

- **Paths and evidence ranges:** `fssim.py:28–99, 111–175`; `ssdim.py:27–97, 109–173`.
- **Finding:** Similar file collection, fuzzy-hash grouping, copy/report and matrix workflow. `fssim.py` uses ppdeep for hashing/comparison and additionally writes `similars.json`; `ssdim.py` uses ssdeep and has different reporting defaults.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D10 — Git identity migration — especially strong match

- **Paths and evidence ranges:** `migrate_git.py:108–291, 294–395`; `migrate_repos.py:108–291, 294–463`.
- **Finding:** Matching local config update, text replacement and SSH key creation functions; key cleanup and main flow diverge. Both can change identity-related files, so differences matter operationally.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D11 — Language-specific cleaners

- **Paths and evidence ranges:** `clean-js.py:26–61, 86–208`; `clean-ts.py:26–62, 87–209`; `clean-css.py:26–61, 93–218`; `clean-lua.py:22–64, 78–199`; `clean-toml.py:28–69, 72–190`; `clean-html.py:24–86, 100–221`.
- **Finding:** The six cleaners reuse a similar file-walk, processing and CLI design; JavaScript and CSS `process_file_tree_sitter` normalize identically and JS/TS `main` does too. The actual grammars, fallback parsers and target suffixes differ, so these are not interchangeable tools.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D12 — Terminal PDF viewer — especially strong match

- **Paths and evidence ranges:** `pdfv2.py:30–65, 72–174, 196–213, 216–413`; `tpv.py:31–66, 73–306, 330–347, 350–548`; `pdfviewer.py:31–48, 51–250`.
- **Finding:** Shared keyboard handling and terminal viewer drawing/navigation: `_paint_row` and `handle` normalize identically in all three. `pdfv2.py` and `tpv.py` also share PPM parsing and external renderer functions; renderer capabilities differ.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D13 — PDF toolkits

- **Paths and evidence ranges:** `pdftools2.py:395–526, 529–603`; `pdftoolz.py:440–577, 580–647`.
- **Finding:** Shared Ghostscript and qpdf shrink implementations, plus split commands. Normalized `_shrink_gs_mobile` and `_shrink_qpdf` are identical; other toolkit commands and options may differ.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D14 — SQL dump conversion inside toolkit — especially strong match

- **Paths and evidence ranges:** `dbtools.py:665–909`; `sql2json.py:105–126, 137–367`.
- **Finding:** The standalone converter and the database toolkit share substantial SQL INSERT parsing: `_split_top_level` / `split_top_level`, `_parse_sql_literal` / `parse_value`, and `_iter_tuple_bodies` / `extract_tuples` have identical normalized ASTs despite renamed functions and variables. The toolkit has unrelated additional database commands.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D15 — Python consolidation transforms

- **Paths and evidence ranges:** `consolidate.py:210–341, 363–506`; `rassingle.py:176–332, 365–511`.
- **Finding:** Both consolidate modules and share substantial AST rewrites for six, os.path, executors and logging. For example, the `OsPathTransformer.visit_Call` methods normalize identically; surrounding module merging and name resolution differ.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D16 — Text reformatter core

- **Paths and evidence ranges:** `docstring_formatter.py:14–33, 36–81`; `prompt-reformatter.py:12–42`.
- **Finding:** The core reformat function has an identical normalized AST and splits marker/comma/long-semicolon text while retaining surrounding whitespace. Their callers target different inputs: Python module docstrings versus text files.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### D17 — Encoding diagnostics

- **Paths and evidence ranges:** `detect_encoding.py:38–169`; `showenc.py:33–129`; `getenc.py:33–113`.
- **Finding:** The diagnostic routines read a file and report several encoding detectors using closely related code. `getenc.py` reports charset-normalizer chaos directly while the other two report one minus chaos; other backends/output handling also differ.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.


## Functional overlap (not necessarily shared implementation)

### F01 — CSV to JSON

- **Paths and evidence ranges:** `csv2json.py:9–31`; `csv2json2.py:9–19`; `csvtojson.py:9–15`.
- **Finding:** All turn a CSV file into a sibling JSON file. `csv2json.py` maps the first column to the second, while the other two produce arrays of dictionaries and use different JSON formatting/Unicode settings; outputs are not equivalent.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### F02 — Web page to PDF

- **Paths and evidence ranges:** `url2pdf.py:8–20`; `url2pdf2.py:10–25`; `url2pdf3.py:7–32`; `web2pdf.py:38–49, 122–190`.
- **Finding:** All produce PDFs from URLs; `url2pdf.py` uses WeasyPrint with a hard-coded example when run as a script, the numbered CLI variants use pdfkit, and `web2pdf.py` supports local HTML and configurable rendering. Equivalent rendering is not established.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### F03 — HTML to Markdown

- **Paths and evidence ranges:** `html2markdown.py:129–175, 193–243`; `htmltomarkdown.py:220–574, 592–663`.
- **Finding:** Both convert HTML to Markdown: the first dispatches to multiple engines and supports batch inputs; the second uses its own tag classes and parser. They need not preserve identical markup or offer the same interface.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### F04 — Non-English content scanning

- **Paths and evidence ranges:** `detect_noneng.py:26–29, 42–68, 70–187`; `detect_nonenglish.py:114–238, 258–357, 501–592`; `noneng.py:52–94, 107–219, 333–398`.
- **Finding:** All scan files for non-English content, but `detect_noneng.py` uses selected Unicode ranges (including an Arabic-range label of Persian), whereas the others use language-detection backends and different sampling/reporting. Their detection coverage and results differ.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

### F05 — Empty wheel identification

- **Paths and evidence ranges:** `ewhl.py:9–64`; `ewhl2.py:11–26, 103–204`; `find_empty_wheels.py:7–37`; `emptypkg.py:26–42, 55–82`; `emptywhl.py:8–49`.
- **Finding:** All inspect wheels for emptiness, but use different definitions and actions: e.g. source/extension absence, archive entries, or RECORD-based checks. `ewhl.py` and `ewhl2.py` also share very similar predicate code; no equivalence of classifications or safe interchangeability is implied.
- **Confidence:** High (static evidence); behavior outside the cited ranges has not been established as equivalent.

## Verification

All three report files were created. The SVG was parsed as XML, and the Mermaid source was structurally checked for balanced subgraphs, declared edge endpoints and standard flowchart syntax. No Mermaid renderer was available locally, so an actual rendered Mermaid preview was not verified.

## Reading the diagrams

Each labeled edge connects the first file in a finding to another file in that finding. Solid **D** edges denote reported code similarity; dashed **F** edges denote functional overlap, not proof of code duplication. A group can have both kinds of overlap; the chosen label describes the finding, not an exclusive classification. See the details above before consolidating or replacing scripts.
