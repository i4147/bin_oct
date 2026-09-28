#!/data/data/com.termux/files/home/.local/bin/python
import json
import sys
from pathlib import Path
from typing import Any, Callable


def main() -> None:
    args = sys.argv[1:]
    verbose = False
    if args and args[0] == "-v":
        verbose = True
        args = args[1:]
    if not args:
        sys.exit(1)
    path: Path = Path(args[0])
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    key_func: Callable[[tuple[str, Any]], int]
    if verbose:
        key_func = lambda item: len(item[1]) if isinstance(item[1], list) else 0
    else:
        key_func = lambda item: len(item[0])
    sorted_data: dict[str, Any] = dict(sorted(data.items(), key=key_func))
    serialized: str = json.dumps(sorted_data, ensure_ascii=False, indent=2)
    json.loads(serialized)
    path.write_text(serialized, encoding="utf-8")


if __name__ == "__main__":
    main()
