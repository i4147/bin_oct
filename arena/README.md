# Module-docstring tooling

Helper scripts used to add the Google-style module docstrings to the repository's scripts
(see `mdoc.md` for the task description).

| Script | Purpose |
| --- | --- |
| `signals.py` | AST scanner: per-file structure (docstring present, argparse description, options, subcommands, entry point). |
| `gist.py` | Compact digest of one or more scripts, used while authoring a summary. |
| `next.py` | Worklist of the scripts that still lack a summary (`--only weak` for the ones without an argparse description, `--only desc` for the described ones). |
| `apply_module_docs.py` | Builds the docstring from `summaries/*.json` + the argparse metadata, and inserts / checks it (`--show`, `--check`, `--write`). |
| `summaries/batch_NN.json` | The authored summaries: `{file: {summary, details[], example[], optional usage/notes}}`. |

Usage:

```console
$ python3 arena/next.py --limit 16 --only desc --source
$ python3 arena/apply_module_docs.py --check
$ python3 arena/apply_module_docs.py --write
```

The generator escapes the backslashes and the triple quotes of the generated text, keeps the
shebang (and a `# coding:` line) first, and only ever inserts text: an already documented module
is skipped, so the existing docstrings are preserved byte for byte.

Remaining work at the time of the first pull request: 93 scripts still need an authored summary
(`python3 arena/apply_module_docs.py --check` lists them).
