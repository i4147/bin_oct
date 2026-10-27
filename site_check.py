#!/data/data/com.termux/files/usr/bin/python
import os
import sys
import site
import json
import py_compile
import pkgutil
import importlib


def run_sanity_check():
    issues = {"compilation_errors": [], "import_errors": []}
    site_dirs = site.getsitepackages()
    if hasattr(site, "getusersitepackages"):
        user_site = site.getusersitepackages()
        if os.path.exists(user_site):
            site_dirs.append(user_site)
    print(f"Scanning site-packages directories: {site_dirs}")
    seen_modules = set()
    for site_dir in site_dirs:
        if not os.path.exists(site_dir):
            continue
        for root, dirs, files in os.walk(site_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    try:
                        py_compile.compile(full_path, doraise=True)
                    except Exception as e:
                        issues["compilation_errors"].append({"file": full_path, "error": str(e)})
        for finder, name, ispkg in pkgutil.iter_modules([site_dir]):
            if name in seen_modules:
                continue
            seen_modules.add(name)
            try:
                importlib.import_module(name)
            except Exception as e:
                issues["import_errors"].append({"module": name, "error": str(e)})
    return issues


if __name__ == "__main__":
    print("Starting package sanity check...")
    report = run_sanity_check()
    report_filename = "site_packages_sanity_report.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"\nSanity check complete. Report saved to '{report_filename}'.")
    print(f"- Compilation Errors Found: {len(report['compilation_errors'])}")
    print(f"- Import/Dependency Errors Found: {len(report['import_errors'])}")
