# Python similarity and functional overlap

## Executive summary

The checkout contains **835 Python source files** (253,691 lines). All were tokenized and screened; 826 also parsed with the available Python 3.11 AST parser. The analysis found substantial duplication, not just shared imports: for example, `dt3.py`/`dtluna.py`, `cconsolidate.py`/`consolidate.py`, `mk_tree.py`/`mktree.py`, and `pydup.py`/`python_duplicate_finder.py` share extensive implementation. There are also distinct implementations of overlapping jobs such as PDF page splitting, HTML-to-PDF conversion, speech transcription, and type-annotation removal.

High structural similarity is **not** proof of interchangeable behavior. `dt3.py` and `dtluna.py` have a measured normalized score of 1.000 but choose backends in a different fallback order. The extractor and font-converter templates likewise differ in important literal values or target formats. Several utilities can modify or delete inputs; do not consolidate or run them solely on the strength of this report.

The findings below are manually checked, **representative relationships**, not an exhaustive inventory of every duplicate or every possible functional overlap. The SVG and Mermaid diagrams show 20 representative edges, labeled with the same finding IDs; they are a subset of this report, not a complete dependency graph. Edges mean similarity or overlap, not that one script calls or derives from the other.

## Scope, exclusions, and method

- **Snapshot:** session checkout at `8e218db0e90fec7a95d731bc9f9d6837833d99ef`. The instruction file `sim.txt` was read from the updated GitHub `main` (`f8e17eebf1f00df175af60beb907e8fc92ae88d1`); the intervening changes contain no Python source changes. Analysis used the checkout's `.gitignore` rules.
- **Discovery:** `git ls-files --cached --others --exclude-standard -- '*.py'`, recursively, followed by regular-file and directory checks. All 835 discovered files are tracked and at the repository root; there were no untracked, non-ignored Python files. Extensionless symlink launchers are not separate Python sources and were not counted. Git-ignored untracked paths are excluded; tracked files would remain included even if a later ignore rule matched them.
- **Excluded paths:** `.git/` and, if encountered, caches (`__pycache__/`, `.cache/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`), virtual environments (`.venv/`, `venv/`, `env/`, `.env/`, `.tox/`, `.nox/`), dependency/vendor locations (`node_modules/`, `site-packages/`), and `build/` and `dist/`. At inventory time the checkout had no nested source, generated, vendor, environment, build, or cache directories; `.git/` was the only existing subdirectory. `reports/` was created afterward and contains only these outputs. Individual root scripts cannot reliably be classified as third-party or generated solely from their location.
- **Static analysis only:** the Python standard library's `tokenize` and `ast` were used; repository scripts were read, not imported or executed. No dependencies were installed or upgraded, and no source files were modified.
- **Whole-file similarity:** comments and, where AST parsing succeeded, module/class/function docstrings were removed. Keywords, operators, logical newlines, indentation and dedentation were retained; all other identifiers became `ID`, numbers `NUM`, and other strings `STR`. Physical whitespace and comment differences were ignored. Each file was represented by its **set of distinct contiguous 10-token shingles**, using a 64-bit rolling hash. For two sets A and B, **J = |A ∩ B| / |A ∪ B|**; **containment C = |A ∩ B| / min(|A|, |B|)**. These are measured structural set similarities, not percentages of identical source lines or probabilities of equivalent behavior. Scores in findings are whole-file scores unless explicitly stated otherwise, rounded to three decimals.
- **Screening:** all 835 files were checked for identical normalized token streams. Of the 348,195 possible file pairs, 332,520 pairs had at least 80 distinct shingles in each file and were compared exhaustively. A pair was nominated with at least 50 shared shingles and J ≥ 0.28, or with at least 100 shared shingles and C ≥ 0.60. This produced 111 **candidates**, not 111 verified duplicate jobs; the other 19 short files could still be inspected through exact-token and intent screening.
- **Function screening:** 6,715 AST functions/methods with at least eight source lines, 60 normalized tokens, and 40 distinct shingles were indexed. Candidate pairs needed 20 shared shingles appearing in at most 40 indexed functions; then at least 50 shared shingles and J ≥ 0.60 or C ≥ 0.85. This yielded 773 candidates, including intra-file pairs; overlapping parent/child ranges in the same file were not compared. Identical non-comment, non-docstring *raw token* streams were also grouped, retaining identifiers and literal values. Function groups and file pairs overlap and must not be added together as counts of independent findings.
- **Functional screening and review:** filenames, module docstrings, argument descriptions/help, and function/class names were used only to propose candidates. The reported relationships were checked against actual operations and input/output handling; shared names, imports, and command-line boilerplate alone were not treated as proof of the same job. No numeric functional-equivalence score is claimed.

**Confidence:** high means the cited source directly supports the specific relationship described; medium means the intended overlap is apparent but important behavioral equivalence is uncertain. Neither level asserts that the code runs successfully or produces correct results. Line ranges are inclusive and repository-relative.

### Parsing and other limits

Python 3.11 could tokenize all 835 files but could not AST-parse nine: `afkco.py:418`, `codepener.py:9`, `fixescape.py:80`, `glow.py:77`, `minhtml.py:47`, `rmc3.py:130`, `rmh.py:210`, `srmc2.py:169`, and `zip_crack.py:129`. They were included in file-level token screening, but their docstrings were not AST-removed, and they were omitted from function/AST and AST-derived intent indexing. A parse failure under 3.11 may reflect syntax invalid in that version or newer-version syntax, not necessarily invalidity under the intended interpreter.

Set scores lose global ordering and multiplicity, normalize away semantically important names and literal values, and can miss short, reordered, or structurally dissimilar code. Python 3.11 tokenizes an f-string as a string token, so its expressions are not individually compared. Hash collisions are theoretically possible. Candidate thresholds, common-shingle suppression in function screening, and the manual-review subset also create false negatives. Dynamic behavior, dependencies, runtime correctness, and every possible input were not tested.

## A. Strong code duplication with overlapping purpose

### D01. Multi-backend translators — **high confidence**
`dt3.py:104-443`, `dt3.py:643-736`; `dtluna.py:104-443`, `dtluna.py:643-736`. Backend factories, chunk/retry orchestration and main are duplicated; their non-comment, non-docstring `main` token streams are identical. **J=1.000**, but the fallback tuples at `dt3.py:387-397` and `dtluna.py:387-397` order services differently. This is a direct example of normalized equality hiding a behavioral difference.

### D02. Python consolidation and related transforms — **high confidence**
`cconsolidate.py:868-1014`, `consolidate.py:868-1014`; `rassingle.py:259-335`. The first two merge and render refactored Python modules, with identical raw token streams for `render_module` and `refactor`; **J=0.996**. Their visible differences include return-type annotations. `rassingle.py:272-317` also duplicates the nontrivial `os.path` AST rewrite at `cconsolidate.py:279-324` and `consolidate.py:279-324`, but is not the same whole program.

### D03. Reconstructing directory trees — **high confidence**
`mk_tree.py:76-128`, `mk_tree.py:225-310`, `mk_tree.py:358-413`; `mktree.py:78-130`, `mktree.py:227-312`, `mktree.py:360-415`. Both parse tree text or OCR results and create a filesystem tree. The 86-line `image_to_entries` functions have identical retained raw tokens; **J=0.994**. Their shebang and a path expression differ.

### D04. In-place file translators — **high confidence**
`aitrans.py:55-113`, `aitrans.py:116-125`; `inplace_translator.py:51-109`, `inplace_translator.py:112-121`. Translation and file-processing functions are shared; **J=0.999**. The defaults differ: `aitrans.py` includes `py` and `rst`, while `inplace_translator.py` defaults to `txt,md`.

### D05. Python duplicate and similarity scanners — **high confidence**
`pydup.py:539-596`, `pydup.py:1209-1293`, `pydup.py:2531-2622`; `python_duplicate_finder.py:456-513`, `python_duplicate_finder.py:934-1018`, `python_duplicate_finder.py:2046-2137`. File discovery, duplicate grouping, and removal handling include identical retained raw-token functions; **J=0.848**, **C=0.986**. `pydup.py:1424-1502` adds similarity methods beyond the smaller variant, so the tools are not identical.

### D06. Moving repeated Python definitions — **high confidence**
`dduper.py:67-159`, `dduper.py:361-449`; `deduplicate_python.py:77-169`, `deduplicate_python.py:384-472`; `deduper.py:195-262`, `deduper.py:391-416`. The first pair shares AST/tree-sitter extraction and main-flow code for deduplicating/moving definitions; **J=0.866**. `deduper.py` implements a related workflow with different extraction and update logic. Dependency availability, archive handling, and output validation differ across variants.

### D07. Fuzzy grouping of files — **high confidence**
`fssim.py:38-68`, `fssim.py:83-145`; `ssdim.py:37-66`, `ssdim.py:81-143`. Both hash files, group similar ones, and write reports/matrices; **J=0.843**. One uses `ppdeep` hashing/comparison in the cited path, while the other uses `ssdeep` and different error handling/output defaults.

### D08. Git identity migration — **high confidence**
`migrate_git.py:161-189`, `migrate_git.py:203-317`, `migrate_git.py:320-366`; `migrate_repos.py:161-189`, `migrate_repos.py:203-317`, `migrate_repos.py:320-381`. Git-config updates, replacement previews and SSH-key creation share extensive code, including identical retained raw-token `preview_and_replace`; **J=0.803**. Old-key cleanup and skip rules differ. These paths describe potentially destructive operations; no migration was run.

### D09. Terminal PDF viewers — **high confidence**
`pdfv2.py:72-193`, `pdfv2.py:252-290`, `pdfv2.py:384-413`; `tpv.py:73-327`, `tpv.py:386-424`, `tpv.py:519-548`; `pdfviewer.py:89-146`, `pdfviewer.py:221-250`. The three share the terminal row painter and input handling, with identical retained raw tokens for `_paint_row`; `pdfv2.py` versus `tpv.py` has **J=0.732**. Rendering backends and capabilities differ, including `tpv.py`'s additional renderer paths.

### D10. SQL INSERT-to-JSONL — **high confidence**
`dbtools.py:672-717`, `dbtools.py:802-831`, `dbtools.py:895-954`; `sql2json.py:137-182`, `sql2json.py:269-320`, `sql2json.py:323-364`. Both parse SQL INSERT values and emit JSONL; the quote/depth-aware splitter and tuple extraction are near-identical after renaming. The standalone tool's normalized shingles are largely contained in the larger toolkit: **J=0.346, C=0.896**. The toolkit has additional unrelated database commands.

### D11. Python code compressors — **high confidence**
`compy.py:325-396`, `compy.py:709-758`; `compy2.py:329-400`, `compy2.py:713-762`. Both simplify/compress Python source using the same transformation pipeline; **J=0.952**. Output handling differs: the variants append different material and handle the clipboard/output file differently.

### D12. Syntax-highlighted file display — **high confidence**
`pbat.py:65-125`, `pbat.py:138-234`; `pybat.py:66-126`, `pybat.py:139-235`. Both display highlighted files with Git-diff line status; `_parse_hunks` has identical retained raw tokens; **J=0.962**. Some annotations and attribute names differ.

### D13. PyPI package downloaders — **high confidence**
`simple_pipdown.py:48-142`; `spdown.py:49-159`. Both select compatible PyPI links and download/check hashes; their selection functions have identical retained raw tokens; **J=0.859**. `spdown.py` adds a progress display to the download path.

### D14. PDF command suites — **high confidence**
`pdftools2.py:225-313`, `pdftools2.py:395-490`, `pdftools2.py:529-602`; `pdftoolz.py:271-360`, `pdftoolz.py:440-535`, `pdftoolz.py:580-646`. Merge, page-image conversion, shrinking, and splitting overlap; the Ghostscript mobile-shrink function has identical retained raw tokens; **J=0.611**. Outline/destination handling and some options differ.

### D15. PDF shrink-in-place wrappers — **high confidence**
`spdf.py:12-53`; `spdf2.py:12-38`. Both generate a temporary PDF and replace the original only if it is smaller; **J=0.745**. Their actual engines differ: Ghostscript with image downsampling versus qpdf linearization/object streams. Similar purpose does not imply identical output quality or bytes.

### D16. Encoding diagnostics — **high confidence**
`detect_encoding.py:51-100`, `detect_encoding.py:101-170`; `showenc.py:38-129`; `getenc.py:33-112`. They run multiple encoding detectors over a file and report results; `detect_encoding.py` versus `showenc.py` has **J=0.686**. In the charset-normalizer path, `getenc.py:62-68` reports `chaos`, whereas `detect_encoding.py:80-85` and `showenc.py:67-72` use `1 - chaos`; interpretations are not interchangeable.

### D17. Extracting Python entities from files/archives — **high confidence**
`gexcst.py:30-114`, `gexcst.py:184-221`; `gext0.py:28-87`, `gext0.py:156-193`. Both extract definitions/assignments and share similar archive traversal and output handling; **J=0.599**. One uses a concrete-syntax-tree visitor and the other an AST visitor, so preserved syntax and covered nodes differ.

### D18. Unused-import analysis — **high confidence**
`afk2.py:75-186`; `pycleaner.py:103-215`, `pycleaner.py:264-297`. Both collect `TYPE_CHECKING` and `__all__` information, identify used names, and analyze imports; the corresponding normalized name-collection functions are identical, and **J=0.320, C=0.729**. They differ in implementation details; static similarity does not validate either implementation.

### D19. Rebuilding wheels from installed packages — **high confidence**
`siter.py:65-80`, `siter.py:128-256`; `siter2.py:76-92`, `siter2.py:143-273`. Both read distribution `RECORD` data, select wheel tags, and assemble wheels from installed files; **J=0.424**. `build_wheel` has a measured function-level **J=0.673** under the same shingle definition, not an equivalence guarantee.

### D20. Empty-wheel checks — **high confidence**
`ewhl.py:10-27`; `ewhl2.py:12-26`; `wheelinspector.py:22-92`. The first two use nearly the same ZIP-entry heuristic, and `wheelinspector.py` has a similar basic method plus RECORD- and extension-based alternatives. For `ewhl.py` versus `ewhl2.py`, **J=0.277, C=0.759**. The different heuristics can disagree; no correctness claim is made.

### D21. Environment-variable name collection — **high confidence**
`collect_env_vars.py:8-25`; `xenv_vars.py:9-30`. Both recursively scan text lines matching uppercase `NAME=` and write sorted unique names; **J=0.471**. `xenv_vars.py` skips `.git` and handles output errors differently.

### D22. Import collection — **high confidence**
`import_collector.py:30-42`; `importz.py:22-34`. Both parse Python files and collect top-level package names from absolute AST imports; **J=0.410** for the whole files. The larger programs add different reporting and package-status behavior.

### D23. Merge/refactor Python sources — **high confidence**
`py_refact.py:85-112`, `py_refact.py:124-169`; `refactor_as_single.py:57-84`, `refactor_as_single.py:104-155`. Both load/merge Python sources and apply overlapping rewrite passes; the normalized `parse_merged_file` and `load_sources` functions match exactly; **J=0.308, C=0.675**. The larger refactorer has additional deduplication and ordering stages.

### D24. Download/progress framework — **high confidence**
`pyget.py:93-154`, `pyget.py:255-288`; `python_downloader.py:75-135`, `python_downloader.py:235-265`. Both provide HTTP download backends, range handling and terminal progress reporting; **J=0.327**. Shared progress code is substantial, while stream interfaces and download strategies differ.

## B. Shared code or templates, but different targets

These findings describe duplicated implementation, **not** a claim that the scripts perform the same complete job.

### T01. Language-specific comment cleaners — **high confidence**
`clean-css.py:28-63`, `clean-css.py:95-140`; `clean-js.py:28-63`, `clean-js.py:88-133`; `clean-ts.py:28-64`, `clean-lua.py:24-66`, `clean-html.py:26-88`, `clean-toml.py:30-71`. These share tree-sitter comment-range removal and file-processing scaffolding; `clean-css.py` versus `clean-js.py` has **J=0.913**. They target different languages and sometimes different fallback minifiers.

### T02. File optimization runner — **high confidence**
`opng.py:93-158`, `opng.py:185-210`, `opng.py:475-605`; `pyterser.py:94-160`, `pyterser.py:193-235`, `pyterser.py:455-607`. Directory traversal, temporary-file handling, summaries and the normalized main flow are closely related; **J=0.693**. `opng.py` optimizes PNGs, while `pyterser.py` runs a JavaScript minifier.

### T03. Python node-extractor template — **high confidence**
`ex_class.py:10-41`, `ex_func.py:10-41`, `ex_comments.py:10-41`, `ex_ex.py:10-41`, `eximports2.py:10-57`. The same recursive tree-sitter extraction/output structure is reused with different `VALID` node-type strings. `ex_class.py` versus `ex_func.py` and `ex_comments.py` versus `ex_ex.py` each have **J=1.000** after literals are normalized; those literals select different intended targets. The configured node names were not runtime-validated.

### T04. Font conversion templates — **high confidence**
`otf2woff2.py:13-33`, `ttf2woff2.py:13-32`, `woff22woff.py:13-34`, `woff2woff2.py:13-34`. They reuse the `TTFont` load/flavor/save workflow and input handling, but use different source/target formats. `woff22woff.py` versus `woff2woff2.py` has **J=0.922** despite reversing the conversion direction; some paths remove the original file.

### T05. Comment-removal helpers across languages — **high confidence**
`clean-bash.py:49-117`; `tsrmc.py:82-123`, `tsrmc.py:147-215`; `clean-cpp.py:49-113`; `cccpp.py:49-114`; `cleanlua.py:27-71`. These reuse similar tree-sitter comment-range collection and byte-splicing routines. `clean-bash.py` versus the multi-language `tsrmc.py` has **J=0.680**. Their applicability overlaps for supported Bash inputs, but the language-specific scripts are not generally interchangeable.

### T06. Python and Rust cleaner runners — **high confidence**
`clean-rs.py:187-213`, `clean-rs.py:216-291`; `rmc.py:276-302`, `rmc.py:305-385`; `rmc-ts.py:178-264`. The walkers and application/parallel-reporting structure are similar; `clean-rs.py` versus `rmc.py` has **J=0.425**. The former targets Rust, while the Python cleaners use different parsing approaches.

### T07. HTML embedded-asset extraction — **high confidence**
`excss.py:15-40`; `exjs.py:16-40`. Both parse HTML, gather embedded elements and save their content with similar control flow; **J=0.564**. One selects `<style>` and the other `<script>`, so their outputs serve different purposes.

### T08. CSS formatting versus deduplication — **high confidence**
`bcss.py:14-33`; `ccss.py:10-37`. The command wrappers and size-reporting code are similar; **J=0.649**. The former requests `cleancss --format beautify`, while the latter requests duplicate-rule removal/optimization. Do not infer equivalent output from the shared wrapper.

### T09. Extracting fenced code from different sources — **high confidence**
`xcodepy.py:32-43`, `xcodepy.py:46-99`; `xmetadata.py:32-42`, `xmetadata.py:60-124`. Both extract fenced code blocks and use nearly the same collision-free naming helper; **J=0.652**. One processes Markdown documents and the other installed-package METADATA.

### T10. Repeated methods within one file — **high confidence**
`rmctools.py:222-238` and `rmctools.py:240-256`. `leave_ClassDef` and `leave_FunctionDef` contain the same normalized body for removing docstrings from indented and simple suites; node types and method names differ. This is a localized intra-file code clone, not two separate script jobs.

### T11. Opposite line-trimming operations — **high confidence**
`delafter.py:12-25`; `delbefor.py:14-27`. The read/iterate/write pattern is similar; **J=0.575**. One retains text before a delimiter, the other text after it. The distinction is central to their behavior.

### T12. Shared formatting algorithm, different inputs — **high confidence**
`docstring_formatter.py:34-53`, `docstring_formatter.py:69-100`; `prompt-reformatter.py:22-51`. The nontrivial formatting bodies match after renaming the function; **J=0.534**. One applies the algorithm to a Python module docstring; the other reformats the whole input text.

### T13. Duplicate-cache helper in different scanners — **high confidence**
`dufpy.py:239-272`; `dupfx.py:134-167`. `load_duplicates_cache` has an identical retained raw-token stream and handles the same cache representation. This is localized code reuse; it does not imply the two scanners use the same duplicate-detection strategy.

## C. Functional overlap with different or only partially shared implementations

### F01. Split PDFs or extract text by page — **high confidence**
`perpage.py:26-51`; `ppage.py:11-35`; `pdf2page.py:227-298`. The first two split PDFs into per-page PDFs and optionally per-page text, using different libraries. `pdf2page.py` overlaps their text-extraction mode and offers additional backend/parallel options; it is not a replacement for the PDF-splitting mode.

### F02. Render a web page to PDF — **high confidence**
`url2pdf.py:9-21`; `url2pdf2.py:19-26`; `url2pdf3.py:19-33`; `web2pdf.py:152-181`. All contain a URL-to-PDF path; the first and last use WeasyPrint, the middle two use pdfkit. `url2pdf.py`'s main invocation is hard-coded to an example, and the full CLI/options are different.

### F03. CSV to JSON — **high confidence**
`csv2json.py:10-32`; `csvtojson.py:10-16`. Both read CSV and write a JSON file, but the former produces a mapping from the first two columns whereas the latter emits a list of row dictionaries. Their JSON schemas are not interchangeable.

### F04. Speech-to-text — **high confidence**
`audio2text.py:27-89`; `audio2txt.py:16-50`; `whisper2txt.py:10-25`. All transcribe audio to text. The first two use Google recognition with different input/chunk handling; the third loads a Whisper model. Backend, input and failure behavior differ.

### F05. Remove Python type annotations — **high confidence**
`clean_type_annotations.py:22-65`; `unnotate.py:51-110`. Both use concrete-syntax-tree transformations to remove parameter/return annotations and convert or remove annotated assignments. Their handling of type parameters, whitespace, and comments differs.

### F06. Gregorian/Jalali calendar conversion — **medium confidence**
`facal.py:40-94`, `facal.py:121-134`; `pyjcal.py:72-143`, `pyjcal.py:212-226`. Both implement Gregorian/Jalali conversion and calendar output. The algorithms and interfaces differ, and date correctness/edge cases were not tested; this finding is about intended scope, not numerical agreement.

### F07. Read text aloud — **high confidence**
`tts_from_file.py:9-32`, `tts_from_file.py:35-49`; `txt2wav.py:8-35`, `txt2wav.py:38-47`. Both chunk text from a file and call `termux-tts-speak`. The latter's name suggests WAV output, but the cited implementation invokes speech playback and does not write a WAV file; its main path is hard-coded.

### F08. Strip HTML markup — **high confidence**
`htmlstrip.py:132-173`; `strip_html_tags.py:117-166`, `strip_html_tags.py:169-200`. Both remove tags from HTML text, but the former's cited mode uses regex and can preserve marked lines, while the latter uses an HTML parser and suppresses content inside selected tags. Output text and write behavior differ.

### F09. Strip Bash comments — **high confidence**
`clean-bash.py:32-117`; `cleanbash.py:32-110`. Both identify Bash files, remove parsed comment spans, and validate or process the result. Their preservation, blank-line and write/report handling are not identical.

### F10. Crawl pages for email addresses — **high confidence**
`email_collector.py:227-321`; `email_crawler.py:227-300`. Both retrieve search results/pages, find addresses, follow links and queue crawl results. The latter decodes response bytes and checks same-host links differently; the scripts should not be assumed to crawl the same URLs or return identical sets.

### F11. Extract Python definitions and imports — **high confidence**
`pyextract.py:191-305`, `pyextract.py:308-321`; `xpy_entities.py:215-368`. Both walk ASTs to collect classes, functions, assignments and imports with source locations; they also provide additional extraction backends/output modes. Scope, metadata and nested-node behavior differ.

### F12. Detect similar Python code — **high confidence**
`detect_code_similarity.py:116-212`; `pydup.py:624-758`, `pydup.py:1209-1352`; `similarity_check.py:240-284`, `similarity_check.py:559-648`. All analyze code similarity or duplicate structure, but their normalizers, candidate generation, scores and output goals differ. This report did not execute any of these repository tools.

### F13. Detect non-English or other languages in files — **high confidence**
`noneng.py:72-113`, `noneng.py:211-238`; `noneng_pycld2.py:6-41`. Both detect languages in file contents; `noneng.py` supports multiple backends and filters for non-English findings, while `noneng_pycld2.py` prints detected languages more generally.

### F14. Chunked translation with fallback backends — **high confidence**
`dt1.py:97-187`, `dt1.py:220-248`; `tco3.py:127-232`, `tco3.py:342-397`; `dt3.py:116-248`, `dt3.py:403-470`. These expose overlapping translation backends and chunking/selection behavior, but the supported services, order and retries differ. This is broader than the near-clone pair in D01.

### F15. General font conversion — **high confidence**
`fontconverter.py:79-121`; `fco.py:132-188`; `gfco.py:23-50`. All support overlapping font-format conversions, including WOFF/WOFF2 paths. The general tools differ in outline checks, format support, overwrite and source-removal policies; they are not assumed to be identical to the single-format templates in T04.

### F16. Find duplicate Python definitions — **high confidence**
`dedup_func.py:52-116`; `remove_duplicate_functions.py:18-70`, `remove_duplicate_functions.py:73-117`; `find_dup_func_class_const.py:13-36`, `find_dup_func_class_const.py:39-65`. All inspect Python AST definitions for repeated code and have removal-related paths. Their normalization, scope (including classes/constants), reference model and application behavior differ.

### F17. Extract JSON keys — **high confidence**
`get_keys.py:11-31`; `getkeys.py:11-34`. Both read JSON and expose key information, but `get_keys.py` recursively emits paths and leaf values while `getkeys.py` extracts only top-level keys or list indices. The overlap is limited to the broad key-extraction task.

### F18. Collect words from text files — **high confidence**
`word_freq_counter.py:19-51`; `wfreq.py:128-153`, `wfreq.py:173-189`. Both traverse text and extract lowercase word tokens. `word_freq_counter.py` counts occurrences; the cited `wfreq.py` functions collect unique words, so their results are not equivalent frequency tables.

## Practical follow-up

Prioritize D01-D06 and D09-D10 for a careful, test-backed comparison before considering shared libraries or retiring variants. Preserve differences in defaults, parser backends, output formats, destructive behavior, and platform-specific launchers; the measured structural scores are triage signals rather than refactoring approval. The diagrams intentionally show only the representative edges identified above.
