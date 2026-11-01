#!/usr/bin/env python3
"""Merge a batch payload into the docstring overrides file.

The docstring task generated one JSON payload per batch; each payload was folded
into a single ``overrides.json`` with this merge, which preserves insertion order
so that earlier batches keep their precedence.

Payload shape::

    {
      "modules":   {"name.py": "text"},
      "functions": {"name.py::func": "text"},
      "classes":   {"name.py::Class": "text"},
      "comments":  {"name.py::anchor": "text"}
    }

Usage
    python3 arena/merge_payload.py OVERRIDES.json PAYLOAD.json [PAYLOAD.json ...]

Prints the resulting entry counts. The file is rewritten only when something
actually changed.
"""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

SECTIONS = ("modules", "functions", "classes", "comments")


def load(path: Path) -> OrderedDict[str, dict[str, str]]:
    """Load a JSON file preserving key order."""
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


def main(argv: list[str]) -> int:
    """Merge every payload into the overrides file and report the counts."""
    if len(argv) < 3:
        print(__doc__)
        return 2

    overrides_path = Path(argv[1])
    overrides = load(overrides_path) if overrides_path.exists() else OrderedDict()

    added = 0
    for payload_name in argv[2:]:
        payload = load(Path(payload_name))
        for section in SECTIONS:
            incoming = payload.get(section)
            if not incoming:
                continue
            target = overrides.setdefault(section, OrderedDict())
            for key, value in incoming.items():
                if key not in target:
                    added += 1
                target[key] = value

    overrides_path.write_text(
        json.dumps(overrides, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    counts = ", ".join(f"{section}: {len(overrides.get(section, {}))}" for section in SECTIONS)
    print(f"merged {len(argv) - 2} payload(s), {added} new entries | {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
