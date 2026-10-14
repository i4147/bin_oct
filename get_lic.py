#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line license generator tool. The tool should accept a license type chosen from the set of license templates available in a bundled "files" directory relative to the script's location, along with the holder's name and the license's effective year or date, and produce a complete license text for that type.
Key behaviors:
- Discover the available license types automatically from the templates shipped with the tool, so new templates are recognized without changing the code.
- Let the user specify the license type, the copyright holder, and the year (defaulting to the current year) via command-line options, and provide clear help text for each.
- Validate inputs: reject unknown license types with a clear, colored error message listing the valid options, and reject malformed or implausible years or dates.
- Fill placeholders in the selected template with the supplied name and date, and output the result either to standard output or to a file path given by the user.
- Maintain a small per-user cache file in the user's home directory that remembers recently generated or requested license values, so repeated requests can be answered quickly; report to the user whether each lookup was a cache hit or miss, with colored status messages.
- Handle missing files, unreadable or unwritable paths, and corrupted cache contents gracefully, with informative errors instead of crashes, and exit with appropriate non-zero status codes on failure.
- Use colored terminal output for success, warning, and error messages to improve readability.
- Keep the interface simple and self-documenting, and structure the code so that the license-generation logic, cache handling, and command-line interface are clearly separated.
---"""

from __future__ import annotations
from datetime import date
import os
import re
import sys
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
        msg = "Could not read from cache."
        raise LicenseError(msg)


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
        msg = "No cache found. You must supply at least -a and -k."
        raise LicenseError(msg)
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
        msg = f"Invalid author: {author}. Must match '{author_pattern}'."
        raise LicenseError(msg)
    if not re.match(year_pattern, year):
        msg = f"Invalid year: {year}. Must match '{year_pattern}'."
        raise LicenseError(msg)
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
