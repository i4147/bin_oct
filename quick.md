apply  these Changes  to python files in current repos root
- Any python file that has defined function named:
[atomic_write, write_atomic, atomic_save, save_stomic, atomic_replace, atomic_write_json, atomic write_text, atomic_write_file, replace_atomic]
Should be refactored as following:
functions body should be removed from file and be imported from atomicio library
i included atom8cio.py in deps for refrence
- any python file that imported `CSTStripper,TSStripper,ASTStripper, StripFileResult from dh module -> (should be replaced with) from codeutils import ... (should import it from codeutils)
- any python file that definded constant value named SKIP_DIRS or DEFAULT_SKIP_DIRS or names similar to that should be refactored as folows:
   the constant definition should be removed and should import it from dh
   do the same for constant values named MAX_WORKERS, DEFAULT_MAX_WORKERS, MAX_WORKERS, and any other variable that defines number of workers for multiprocessing
- any argument that defined via argparse for number of workers of mp should be removed and should use MAX_WORKERS imported from dh -> from dh import MAX_WORKERS
- migrate from os.path to pathlib in every files that use it
- migrate from stdlib logging to loguru in python files that use stdlib logging

skip symlinks (only process .py files in repo root)
process files in batches (batch-size=25)
- update files inplace, validate code before writing

report stats after finishing every batch
dont commit until all files processed
