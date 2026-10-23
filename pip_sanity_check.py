#!/data/data/com.termux/files/usr/bin/python
import sys
import importlib
import importlib.metadata
from dh import PKG_MAPPING as pkg_mapping

# ANSI Escape Sequences for Colorization
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def sanity_check_packages():
    print(f"Python Version: {sys.version.split()[0]}")
    print("Starting system site-packages sanity check in Termux...\n")

    # Get all installed distributions sorted alphabetically
    installed_dists = sorted(importlib.metadata.distributions(), key=lambda d: d.name.lower())

    healthy_packages = []
    problematic_packages = []

    for dist in installed_dists:
        pkg_name = dist.name
        version = dist.version

        # 1. Determine correct top-level import names using package metadata
        top_levels = []
        try:
            top_level_text = dist.read_text("top_level.txt")
            if top_level_text:
                top_levels = [line.strip() for line in top_level_text.splitlines() if line.strip()]
                print(f"{pkg_name}: {top_levels}")
        except Exception:
            pass

        # Fallback if top_level.txt is missing: sanitize package name
        if not top_levels:
            top_levels = [pkg_name.replace("-", "_").lower()]

        pkg_ok = True
        error_details = ""
        if pkg_name in pkg_mapping.keys():
            mod_name = pkg_mapping.get(pkg_name)
            try:
                importlib.import_module(mod_name)
                continue
            except:
                pass
        for mod_name in top_levels:
            try:
                importlib.import_module(mod_name)
                importlib.import_module(mod_name)
            except Exception as e:
                pkg_ok = False
                error_details = f"{type(e).__name__}: {e}"
                break

        # 3. Categorize results and print styled output
        if pkg_ok:
            healthy_packages.append(f"{pkg_name}=={version}")
            print(f"{GREEN}[\u2713] {pkg_name}   {version}{RESET}")
        else:
            problematic_packages.append({"name": pkg_name, "version": version, "error": error_details})
            print(f"{YELLOW}[\u2717]  {pkg_name}{RESET}")

    # 4. Summary & File Generation
    print("\n" + "=" * 50)
    print("Sanity Check Complete:")
    print(f"  - Healthy packages: {len(healthy_packages)}")
    print(f"  - Problematic packages: {len(problematic_packages)}")
    print("=" * 50)

    # Save healthy packages to requirements.txt
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("# Verified healthy packages\n")
        for pkg in healthy_packages:
            f.write(f"{pkg}\n")
    print("Saved healthy package list to 'requirements.txt'")

    # Save problematic packages to a separate log if any exist
    if problematic_packages:
        with open("problematic_packages.log", "w", encoding="utf-8") as f:
            f.write("Package,Version,Error\n")
            for item in problematic_packages:
                f.write(f"{item['name']},{item['version']},{item['error']}\n")
        print("Saved problematic packages to 'problematic_packages.log'")


if __name__ == "__main__":
    sanity_check_packages()
