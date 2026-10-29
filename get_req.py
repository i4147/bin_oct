#!/data/data/com.termux/files/usr/bin/env python
import sys
import json
from importlib.metadata import distributions, metadata, PackageNotFoundError


def get_requires_dist(pkgname):
    try:
        return metadata(pkgname).get_all("Requires-Dist") or []
    except PackageNotFoundError:
        return []


if len(sys.argv) > 1:
    pkgname = sys.argv[1]
    deps = get_requires_dist(pkgname)

    if not deps:
        print(f"No Requires-Dist entries found for {pkgname}")
    else:
        print("\n".join(deps))
else:
    requirements = {}

    for dist in distributions():
        name = dist.metadata.get("Name")
        if name:
            requirements[name] = dist.metadata.get_all("Requires-Dist") or []

    with open("requirements.json", "w", encoding="utf-8") as f:
        json.dump(requirements, f, indent=2, sort_keys=True)

    print(f"Saved dependencies for {len(requirements)} packages to requirements.json")
