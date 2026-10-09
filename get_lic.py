#!/data/data/com.termux/files/usr/bin/env python
"""Create a Termux-targeted Python 3.12 (using the `click` library for the command-line interface and the `ecstasy` library for colored/styled terminal text) that generates an open-source LICENSE file in the current directory (or a specified location) based on license templates stored in a sibling "files" directory relative to the script's location.

**Purpose:**
The tool should let a user quickly generate a license file (e.g., MIT, Apache-2.0, GPL, et specifying a license "kind" and an author name, while supporting a caching mechanism so the user doesn't have to repeatedly type the same author name or license kind on every invocation.

**Behavior details:**
1. **License discovery**: On startup, scan a `files` directory located one level up from the script's directory, treat each file's name (without extension) as alicense kind" (e.git`), and build a set of valid kinds validation.
2. **Caching**: Maintain a cache file at `~/.license` storing the last-used `author` and `kind` as simple `key = value` lines (similar to an INI-style snippet).
   - Provide a `read_cache()` function that reads the raw cache file content, raising a custom `LicenseError` (with a red "<Error>:" prefix styled via `ecstasy`) if the file can't be read.
   - Provide a `read_author(cache)` function that uses a regex to extract the `author` value from the cached content. If found, print a green styled "Cache-Hit for author: '<value>'." message to stderr and return it. If not found, raise a `LicenseError` with a red styled "Cache-Miss for author." message instructing the user to supply an author via the `-a` switch.
   - Provide an analogous `read_kind(cache)` function that does the same for the `kind` value (extracting it via regex, emitting Cache-Hit/Cache-Miss messages styled with `ecstasy`, and raising `LicenseError` with instructions to use the appropriate switch when missing).
3. **Command-line interface**: Use `click` to define options such as an `-a/--author` option to explicitly pass the author name and a similar option to pass the license kind, overriding or supplementing the cache. Validate the supplied kind against the discovered `LICENSE_KINDS` set, erroring out (via `LicenseError`) if it's invalid.
4. **License rendering**: Load the chosen template text file from the `files` directory, substitute placeholders (such as author name and current year, obtained via `datetime.date`) into the template, and write the final result to a `LICENSE` file.
5. **Cache update**: After successfully resolving/validating the author and kind (whether from CLI flags or cache), update `~/.license` with the latest values for future runs.
6. **Error handling & styling**: All error messages should go through the custom `LicenseError` exception (prefixed with a red "<Error>:" tag via `ecstasy.beautify`), and informational cache hit/miss messages should be printed to stderr with green/red `ecstasy`-styled text respectively.
7. **Shebang**: The script should be written for Termux on Android, with the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`, and should rely only on standard library modules (`os`, `re`, `sys`, `datetime`, `typing`) plus the third-party `click` and `ecstasy` packages.

Ensure the generated code is self-contained, well-typed (using `typing.Final` and type hints throughout), and follows the structure of: constants/messages defined at module level, small single-purpose helper functions (`get_license_kinds`, `read_cache`, ` etc.), and a final `click`-decorated command function that ties everything together to produce the LICENSE file.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/4MFMRobLUkFbPpNVZrBnqF"""

import os
import re
import sys
from datetime import date
from typing import Final

import click
import ecstasy


class LicenseError(Exception):
    ERROR: Final[str] = ecstasy.beautify("<Error>: ", ecstasy.Color.Red)

    def __init__(self, message: str) -> None:
        self.message: str = self.ERROR + message
        super().__init__(self.message)


CACHE_PATH: Final[str] = os.path.join(os.environ["HOME"], ".license")
HIT_MESSAGE: Final[str] = ecstasy.beautify("Cache-<Hit> for {0}: '{1}'.", ecstasy.Color.Green)
MISS_MESSAGE: Final[str] = ecstasy.beautify("Cache-<Miss> for {0}.", ecstasy.Color.Red)


def get_license_kinds() -> set[str]:
    kinds: set[str] = set()
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
    for license_path in os.listdir(os.path.join(root, "files")):
        name = os.path.splitext(os.path.basename(license_path))[0]
        kinds.add(name)
    return kinds


LICENSE_KINDS: Final[set[str]] = get_license_kinds()


def read_cache() -> str:
    try:
        with open(CACHE_PATH, "rt") as source:
            return source.read()
    except OSError:
        raise LicenseError("Could not read from cache.")


def read_author(cache: str) -> str:
    match = re.search(r"\s*author\s*=\s*([a-zA-Z -]+)", cache)
    if match is None:
        raise LicenseError(MISS_MESSAGE.format("author") + "You must supply an author with the -a switch. ")
    author = match.group(1)
    click.echo(HIT_MESSAGE.format("author", author), file=sys.stderr)
    return author


def read_kind(cache: str) -> str:
    match = re.search(r"\s*kind\s*=\s*(\w+)", cache)
    if match is None:
        raise LicenseError(MISS_MESSAGE.format("kind") + "You must supply a kind with the -k switch.")
    kind = match.group(1)
    click.echo(HIT_MESSAGE.format("kind", kind), file=sys.stderr)
    return kind


def read(author: str | None, kind: str | None) -> tuple[str, str]:
    if not os.path.exists(CACHE_PATH):
        raise LicenseError("No cache found. You must supply at least -a and -k.")
    cache_data = read_cache()
    if author is None:
        author = read_author(cache_data)
    if kind is None:
        kind = read_kind(cache_data)
    return author, kind


def write(author: str, kind: str) -> None:
    assert all(i is not None for i in [author, kind])
    template = "author={0}\nkind={1}"
    with open(CACHE_PATH, "wt") as destination:
        destination.write(template.format(author, kind))


def fetch(kind: str) -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, f"files/{kind}.txt")
    with open(path, "rt") as source:
        return source.read()


def insert(template: str, author: str, year: str) -> str:
    template = re.sub(r"<author>", author, template)
    template = re.sub(r"<year>", year, template)
    return template


def validate(author: str, year: str, kind: str) -> None:
    author_pattern = r"^[a-zA-Z -]+$"
    year_pattern = r"^\d{4}$"
    if not re.match(author_pattern, author):
        raise LicenseError(f"Invalid author: {author}. Must match '{author_pattern}'.")
    if not re.match(year_pattern, year):
        raise LicenseError(f"Invalid year: {year}. Must match '{year_pattern}'.")
    if kind not in LICENSE_KINDS:
        raise LicenseError(f"Invalid license kind: {kind}. Must be one of: " + ", ".join(LICENSE_KINDS))


def get(author: str | None, year: str, kind: str | None) -> str:
    assert year is not None, "Year should have been defaulted by click"
    if not author or not kind:
        author, kind = read(author, kind)
    validate(author, year, kind)
    template = fetch(kind)
    text = insert(template, author, year)
    write(author, kind)
    return text


@click.command(help="A license fetcher.")
@click.option("-a", "--author", nargs=1, help="The name of the author.")
@click.option(
    "-y",
    "--year",
    nargs=1,
    default=str(date.today().year),
    help="The year the program was created in.",
)
@click.option(
    "-k",
    "--kind",
    nargs=1,
    help="The kind of license to fetch.",
    type=click.Choice(list(LICENSE_KINDS)),
)
def li(author: str | None, year: str, kind: str | None) -> None:
    try:
        result = get(author, year, kind.lower() if kind else None)
        click.echo(result, nl=False)
    except LicenseError as e:
        click.echo(e.message)


def main() -> None:
    li()


if __name__ == "__main__":
    main()
