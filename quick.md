apply  these Changes  to python files in current repos root
1.  migrate from stdlib logging to loguru
2. replace `from dh import atomic_write` to `from atomicio import atomic_write`
Any other python file that hace defined   function named
atomic _write, write_atomic, atomic_save, save_stomic, atomic_replace, atomic_write_json, atomic write_text, atomic_write_file, replace_atomic 
Should be refactored as following:
functions body should be removed from file and be imported from atomicio library
All compatibility measures are done before, if ur curious, the atomicio defines (see reqs folder):
def atomic_write(
    path: Incomplete,
    data: Incomplete,
    opt: Incomplete = None,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    newline: str | None = None,
    mode: int | None = None,
    mode_from: Incomplete = None,
    backup: bool | str | os.PathLike = False,
    backup_suffix: str = ".bak",
    as_json: bool | None = None,
    indent: int | None = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    trailing_newline: bool = True,
    mkdir: bool = True,
    fsync: bool = True,
    follow_symlinks: bool = True,
    skip_unchanged: bool = False,
    lock: Incomplete = None,
    suppress_errors: bool = False,
    fallback: bool = True,
) -> bool: ...
With proper aliases for above func names
- from dh import  CSTStripper,TSStripper,ASTStripper, StripFileResult -> (should be replaced with) from codeutils import...
- update files inplace, validate code before writing
-Use generator style fs walker & mp.apply_async with 4 workers
-Report bytes reduced or increased for every file
-Use libcst to parse python file to preserve orig formatting
Example output:
[1/23]   fname.py    23
Adjust cokumns by term width, and show size vhange column in greem, if reducwd, or yellow if increased, (dim=0=nochange)
-Log any ertors with loguru
-Migrate from os.path to pathlib
-Migrate from cf.(Process or Thred)PoolExecutor to mp.pool.imap_unordered with 4 workers
-Migrate from argparse to typer+rich
-Migrate from click to typer
-Use rich lib to print output

process files in batches batch-size=25
report stats after finish8ng every batch
