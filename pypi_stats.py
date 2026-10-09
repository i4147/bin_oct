#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt instructing an AI coding agent to create a Python 3.12 command-line tool (for Termux on Android) called "pypistats" that queries the PyPI Stats API (https://pypistats.org/api/) to retrieve and display download statistics for PyPI packages.

The tool must support the following subcommands/endpoints, mirroring the official PyPI Stats API:
- recent download counts for a package, with an optional period filter (day, week, month)
- overall: overall download counts for a package, with an optional "mirrors" filter (true/false/with_mirrors/without_mirrors)
- python_major: downloads broken down by major Python version
- python_minor: downloads broken down by minor Python version
- system: downloads broken down by operating system

Each subcomm accept a mandatory package name arg notior:

1. **CLI argument parsing**sers for each endpoint/command. Support global options:
   - `--start-date` and `--end-date` (ISO format YYYY-MM-DD) to filter results by date range.
   - `--format` (or `-f`) to choose output format: options should include at least "pretty" (human-readable table), "markdown"/"md", "rst", "html", "json", "numpy", "pandas" (handle "md" as an alias for "markdown").
   - `--total` to control aggregation granularity, restricted to one of "daily", "monthly", "all"; raise a validation error if an invalid value is given (helper function to validate this` /no-sort` flag to toggle sorting of the output data.
   - `--color` option.g. "yes"/"no"/"auto") to controlminal output.
   - `ose diyPI Stats URL, the actual API URL being called, and the cache file path being used.
   - A version flag that prints the package version (expose `__version__` as a module-level string, e.g. "1.14.0", with an accompanying version tuple).

2. **HTTP requests with local caching**:
   - Build the API URL by joining a base URL constant with the lowercased endpoint path and any query string parameters.
   - Construct a cache file path deterministically derived from the full request URL (e.g., hashed or sanitized filename) and use a cache directory suitable for Termux (e.g., under the user's cache/config directory).
   - Before HTTP request, check whether a valid cache file exists for that URL; if so, load and reuse the cached JSON no valid cache exists, perform the Hllib3, im the form `pypistats/se the JSON response, and Includeat cache entries as stexpired after a cert same-day or config that data refreshes peri verbose logging should indicate whether the cache was used or a live request was made.

3. **Data processing and output formatting**:
   - Parse the JSON API response into a tabular/structured form (e.g., list of dicts or rows with columns like date, category, downloads).
   - Support date filtering between start_date and end_date.
   - Support aggregation by day, month, or total based on the `total` parameter, including correctly summing/rolling up download counts per period (use calendar utilities for month-end calculations).
   - Support sorting rows (e.g., by date or downloads) when sort Render the final in the requested outputcolprinted table for terminal display ( optional ggled by the colorTML table, raw JS--friendly structures (NumPy array / pandas programmatic use.

4. **Configu Read optsuch as default formatavior) from a config file (using ConfigParser) so users can override defaults without passing CLI flags every time.

5. **Error handling and cleanup**:
   - Validate inputs (like the `total` granularity) and raise clear errors (e.g., ValueError) with descriptive messages on invalid values.
   - Use `atexit` to ensure any necessary cleanup (such as closing resources or flushing cache) happens on program exit.
   - Suppress or manage non-critical warnings appropriately.

6. **Code structure**:
   - Target Python 3.12, with a shebang line for Termux (`#!/data/data/com.termux/files/us12from __future__ import annotations` for forward-compatible type hints.
   - Organize functionality into small, testable helper functions (e.g., a helper, a totalularity validator, cename/load/ main API--level `__version__`, `version__version_tuple__`, and `version_tupleributes for version introifying the sub and optional filters/formatting options. The main output is downded package statistics from pypistats.org rendered to stdout in the user-selected format, with optional verbose diagnostic messages written to stderr and API responses cached locally to speed up repeated queries and reduce network calls.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/caDo8LfYouJMgNCiHXJAhe"""

from __future__ import annotations
import argparse
import atexit
import calendar
from configparser import ConfigParser
import datetime as dt
import json
from pathlib import Path
import re
import sys
import warnings


__version__ = version = "1.14.0"
__version_tuple__ = version_tuple = (1, 14, 0)

BASE_URL = "https://pypistats.org/api/"
USER_AGENT = f"pypistats/{__version__}"

_verbose = False


def _print_verbose(*args, **kwargs):
    if _verbose:
        print(*args, file=sys.stderr, **kwargs)


def _validate_total(total):
    supported_granularities = ("daily", "monthly", "all")
    if total not in supported_granularities:
        msg = f"total must be one of {supported_granularities}"
        raise ValueError(msg)


def pypi_stats_api(
    endpoint,
    params=None,
    format="pretty",
    start_date=None,
    end_date=None,
    sort=True,
    total="all",
    color="yes",
):
    _validate_total(total)
    if format == "md":
        format = "markdown"
    if params:
        params = "?" + params
    else:
        params = ""
    url = BASE_URL + endpoint.lower() + params
    cache_file = _cache_filename(url)
    if _verbose:
        package = endpoint.split("/")[1]
        human_url = f"https://pypistats.org/packages/{package}"
        _print_verbose(f"Human URL:\t{human_url}")
        _print_verbose(f"API URL:\t{url}")
        _print_verbose(f"Cache file:\t{cache_file}")
    res = {}
    if cache_file.is_file():
        _print_verbose("Cache file exists")
        res = _cache_load(cache_file)
    if res == {}:
        import urllib3

        r = urllib3.request("GET", url, headers={"User-Agent": USER_AGENT})
        _print_verbose("HTTP status code:", r.status)
        if r.status >= 400:
            msg = f"HTTP Error {r.status} for url: {url}"
            raise urllib3.exceptions.HTTPError(msg)
        res = json.loads(r.data.decode("utf-8"))
        _cache_save(cache_file, res)
    if not res.get("data", []):
        return f"No data found for https://pypi.org/project/{res.get('package', '')}/"
    first, last = _date_range(res["data"])
    if end_date:
        assert first is not None
        if end_date < first:
            msg = (
                f"Requested end date ({end_date}) is before earliest available "
                f"data ({first}), because data is only available for 180 days. "
                "See https://pypistats.org/about#data"
            )
            raise ValueError(msg)
    if start_date:
        assert first is not None
        if start_date < first:
            warnings.warn(
                f"Requested start date ({start_date}) is before earliest available "
                f"data ({first}), because data is only available for 180 days. "
                "See https://pypistats.org/about#data",
                stacklevel=3,
            )
    if start_date or end_date:
        res["data"] = _filter(res["data"], start_date, end_date)
    if start_date:
        first = start_date
    if end_date:
        last = end_date
    if total == "monthly":
        res["data"] = _monthly_total(res["data"])
    elif total == "all":
        res["data"] = _total(res["data"])
    if format == "json":
        return json.dumps(res)
    data = res["data"]
    data = _percent(data)
    if sort:
        data = _sort(data, sort)
    data = _grand_total(data)
    if format is None:
        return data
    if color != "no" and format in ("markdown", "pretty", "rst", "tsv"):
        data = _colourify(data)
    output = _tabulate(data, format, color)
    if first and format not in ["numpy", "pandas"]:
        return f"{output}\nDate range: {first} - {last}\n"
    else:
        return output


def _filter(data, start_date=None, end_date=None):
    temp_data = []
    if start_date:
        for row in data:
            if "date" in row and row["date"] >= start_date:
                temp_data.append(row)
        data = temp_data
    temp_data = []
    if end_date:
        for row in data:
            if "date" in row and row["date"] <= end_date:
                temp_data.append(row)
        data = temp_data
    return data


def _sort(data, sort=True):
    if isinstance(data, dict):
        return data
    if sort is False:
        return data
    if sort is True:
        sort = "downloads"
    if not data or sort not in data[0]:
        return data
    reverse = sort in ("downloads", "percent")
    if sort == "percent":
        data = sorted(data, key=lambda k: float(k[sort].rstrip("%")), reverse=reverse)
    else:
        data = sorted(data, key=lambda k: k[sort], reverse=reverse)
    return data


def _monthly_total(data):
    totalled = {}
    for row in data:
        category = row["category"]
        downloads = row["downloads"]
        month = row["date"][:7]
        if category in totalled:
            if month in totalled[category]:
                totalled[category][month] += downloads
            else:
                totalled[category][month] = downloads
        else:
            totalled[category] = {month: downloads}
    data = []
    for category, month_downloads in totalled.items():
        for month, downloads in month_downloads.items():
            data.append({"category": category, "date": month, "downloads": downloads})
    return data


def _total(data):
    if isinstance(data, dict):
        return data
    totalled = {}
    for row in data:
        try:
            totalled[row["category"]] += row["downloads"]
        except KeyError:
            totalled[row["category"]] = row["downloads"]
    data = []
    for k, v in totalled.items():
        data.append({"category": k, "downloads": v})
    return data


def _date_range(data):
    if isinstance(data, dict):
        return None, None
    try:
        dates = {row["date"] for row in data}
    except KeyError:
        return None, None
    return min(dates), max(dates)


def _grand_total_value(data):
    if data[0]["category"] in ["with_mirrors", "without_mirrors"]:
        count_with_mirrors = sum(row["downloads"] for row in data if row["category"] == "with_mirrors")
        count_without_mirrors = sum(row["downloads"] for row in data if row["category"] == "without_mirrors")
        grand_total = max(count_with_mirrors, count_without_mirrors)
    else:
        grand_total = sum(row["downloads"] for row in data)
    return grand_total


def _grand_total(data):
    if isinstance(data, dict):
        return data
    if len(data) == 1:
        return data
    grand_total = _grand_total_value(data)
    new_row = {"category": "Total", "downloads": grand_total}
    data.append(new_row)
    return data


def _percent(data):
    if isinstance(data, dict):
        return data
    if len(data) == 1:
        return data
    grand_total = _grand_total_value(data)
    for row in data:
        row["percent"] = "{:.2%}".format(row["downloads"] / grand_total)
    return data


def _colourify(data):
    for row in data:
        if "percent" not in row:
            continue
        from termcolor import colored

        percent = float(row["percent"].rstrip("%"))
        if percent <= 5:
            colour = "red"
        elif percent <= 15:
            colour = "yellow"
        else:
            colour = "green"
        row["percent"] = colored(row["percent"], colour)
    return data


def _tabulate(data, format_="markdown", color="yes"):
    if isinstance(data, dict):
        headers = list(data.keys())
    else:
        headers = sorted(set().union(*(d.keys() for d in data)))
    headers.append("downloads")
    headers.remove("downloads")
    if format_ in ("numpy", "pandas"):
        return _dataframe(headers, data, format_)
    else:
        return _prettytable(headers, data, format_, color)


def _prettytable(headers, data, format_, color="yes"):
    from prettytable import PrettyTable, TableStyle

    table = PrettyTable()
    if format_ == "html":
        table.border = False
    elif format_ == "markdown":
        table.set_style(TableStyle.MARKDOWN)
    elif format_ == "rst":
        table.set_style(TableStyle.RST)
    elif format_ == "pretty":
        table.set_style(TableStyle.SINGLE_BORDER)
    if isinstance(data, dict):
        data = [data]

    def h(header):
        if color != "no" and format_ == "pretty":
            from termcolor import colored

            return colored(header, attrs=["bold"])
        return header

    for header in headers:
        col_data = [row.get(header, "") for row in data]
        table.add_column(h(header), col_data)
    table.align[h("last_day")] = "r"
    table.align[h("last_month")] = "r"
    table.align[h("last_week")] = "r"
    table.align[h("category")] = "l"
    table.align[h("percent")] = "r"
    table.align[h("downloads")] = "r"
    table.custom_format[h("last_day")] = lambda f, v: f"{v:,}"
    table.custom_format[h("last_month")] = lambda f, v: f"{v:,}"
    table.custom_format[h("last_week")] = lambda f, v: f"{v:,}"
    table.custom_format[h("downloads")] = lambda f, v: f"{v:,}"
    if format_ == "html":
        return table.get_html_string(format=True) + "\n"
    elif format_ == "tsv":
        return table.get_csv_string(delimiter="\t", lineterminator="\n")
    else:
        return table.get_string() + "\n"


def _dataframe(headers, data, format_):
    if isinstance(data, dict):
        data = [data]
    rows = [[row.get(header, "") for header in headers] for row in data]
    if format_ == "numpy":
        import numpy as np

        return np.array(rows, dtype=object)
    import pandas as pd

    return pd.DataFrame(rows, columns=headers)


def _paramify(param_name, param_value):
    if isinstance(param_value, bool):
        param_value = str(param_value).lower()
    if param_value:
        return "&" + param_name + "=" + str(param_value)
    return ""


def recent(package, period=None, **kwargs):
    endpoint = f"packages/{package}/recent"
    params = _paramify("period", period)
    return pypi_stats_api(endpoint, params, **kwargs)


def overall(package, mirrors=None, **kwargs):
    endpoint = f"packages/{package}/overall"
    params = _paramify("mirrors", mirrors)
    return pypi_stats_api(endpoint, params, **kwargs)


def python_major(package, version=None, **kwargs):
    endpoint = f"packages/{package}/python_major"
    params = _paramify("version", version)
    return pypi_stats_api(endpoint, params, **kwargs)


def python_minor(package, version=None, **kwargs):
    endpoint = f"packages/{package}/python_minor"
    params = _paramify("version", version)
    return pypi_stats_api(endpoint, params, **kwargs)


def system(package, os=None, **kwargs):
    endpoint = f"packages/{package}/system"
    params = _paramify("os", os)
    return pypi_stats_api(endpoint, params, **kwargs)


import contextlib

from platformdirs import user_cache_dir
from slugify import slugify


CACHE_DIR = Path(user_cache_dir("pypistats"))


def _cache_filename(url):
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(url)
    return CACHE_DIR / f"{today}-{slug}.json"


def _cache_load(cache_file):
    if not cache_file.exists():
        return {}
    with cache_file.open("r") as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError:
            return {}
    return data


def _cache_save(cache_file, data):
    try:
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True)
        with cache_file.open("w") as f:
            json.dump(data, f)
    except OSError:
        pass


def _cache_clear():
    cache_files = CACHE_DIR.glob("**/*.json")
    this_month = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
    for cache_file in cache_files:
        if not cache_file.name.startswith(this_month):
            cache_file.unlink()


atexit.register(_cache_clear)

cli = argparse.ArgumentParser()
subparsers = cli.add_subparsers(dest="subcommand")


def argument(*name_or_flags, **kwargs):
    return list(name_or_flags), kwargs


def subcommand(args=None, parent=subparsers):
    if args is None:
        args = []

    def decorator(func):
        func2 = globals()[func.__name__]
        parser = parent.add_parser(
            func.__name__,
            description=func2.__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def _package(value):
    directory = Path(value)
    if not directory.is_dir():
        return value
    pyproject_toml = directory / Path("pyproject.toml")
    if pyproject_toml.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads(pyproject_toml.read_text())
        try:
            return data["project"]["name"]
        except KeyError:
            msg = "no 'project.name' in pyproject.toml"
    else:
        msg = "pyproject.toml not found"
    setup_cfg = directory / Path("setup.cfg")
    if setup_cfg.exists():
        config = ConfigParser()
        config.read(setup_cfg)
        try:
            return config["metadata"]["name"]
        except KeyError:
            msg += " and no 'metadata.name' in setup.cfg"
    else:
        msg += " and setup.cfg not found"
    if msg == "pyproject.toml not found and setup.cfg not found":
        msg = "pyproject.toml and setup.cfg not found"
    raise argparse.ArgumentTypeError(msg)


def _month_name_to_yyyy_mm(date_string, date_format):
    today = dt.date.today()
    new = dt.datetime.strptime(f"{date_string} {today.year}", f"{date_format} %Y").date()
    if new < today:
        return new.isoformat()[:7]
    new = dt.datetime.strptime(f"{date_string} {today.year - 1}", f"{date_format} %Y").date()
    return new.isoformat()[:7]


def _valid_date(date_string, date_format):
    try:
        dt.datetime.strptime(date_string, date_format)
        return date_string
    except ValueError:
        msg = f"Not a valid date: '{date_string}'."
        raise argparse.ArgumentTypeError(msg)


def _valid_yyyy_mm_dd(date_string):
    return _valid_date(date_string, "%Y-%m-%d")


def _valid_yyyy_mm(date_string):
    with contextlib.suppress(ValueError):
        date_string = _month_name_to_yyyy_mm(date_string, "%b")
    with contextlib.suppress(ValueError):
        date_string = _month_name_to_yyyy_mm(date_string, "%B")
    return _valid_date(date_string, "%Y-%m")


def _valid_yyyy_mm_optional_dd(date_string):
    try:
        return _valid_yyyy_mm_dd(date_string)
    except argparse.ArgumentTypeError:
        return _valid_yyyy_mm(date_string)


def _define_format(args):
    if args.json:
        return "json"
    return args.format


def _python_major_version(value):
    pattern = r"^\d+$"
    if not re.match(pattern, value):
        msg = "Invalid major version format. Expected a positive integer value."
        raise argparse.ArgumentTypeError(msg)
    return value


def _python_minor_version(value):
    pattern = r"^\d+\.\d+$"
    if not re.match(pattern, value):
        msg = "Invalid minor version format. Expected a positive float value in x.x pattern."
        raise argparse.ArgumentTypeError(msg)
    return value


FORMATS = ("html", "json", "pretty", "md", "markdown", "rst", "tsv")

arg_start_date = argument(
    "-sd",
    "--start-date",
    metavar="yyyy-mm[-dd]|name",
    type=_valid_yyyy_mm_optional_dd,
    help="Start date",
)
arg_end_date = argument(
    "-ed",
    "--end-date",
    metavar="yyyy-mm[-dd]|name",
    type=_valid_yyyy_mm_optional_dd,
    help="End date",
)
arg_month = argument(
    "-m",
    "--month",
    metavar="yyyy-mm|name",
    type=_valid_yyyy_mm,
    help="Shortcut for -sd & -ed for a single month",
)
arg_last_month = argument(
    "-l",
    "--last-month",
    help="Shortcut for -sd & -ed for last month",
    action="store_true",
)
arg_this_month = argument(
    "-t",
    "--this-month",
    help="Shortcut for -sd for this month",
    action="store_true",
)
arg_json = argument("-j", "--json", action="store_true", help='Shortcut for "-f json"')
arg_daily = argument("-d", "--daily", action="store_true", help="Show daily downloads")
arg_monthly = argument("--monthly", action="store_true", help="Show monthly downloads")
arg_format = argument(
    "-f",
    "--format",
    default="pretty",
    choices=FORMATS,
    help="The format of output",
)
arg_color = argument(
    "-c",
    "--color",
    default="auto",
    choices=("yes", "no", "auto"),
    help="Color terminal output",
)
arg_verbose = argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Print debug messages to stderr",
)
arg_sort = argument(
    "-s",
    "--sort",
    default="downloads",
    help="Column to sort by (for example: downloads, date, category)",
)
package_argument = argument(
    "package",
    default=".",
    type=_package,
    nargs="?",
    help="package name, or dir to check pyproject.toml/setup.cfg",
)
common_arguments = [
    arg_format,
    arg_json,
    arg_start_date,
    arg_end_date,
    arg_month,
    arg_last_month,
    arg_this_month,
    arg_daily,
    arg_monthly,
    arg_sort,
    arg_color,
    arg_verbose,
]


@subcommand([
    package_argument,
    argument("-p", "--period", choices=("day", "week", "month")),
    arg_format,
    arg_json,
    arg_verbose,
])
def recent(args):
    print(recent(args.package, period=args.period, format=args.format))


@subcommand([
    package_argument,
    argument("--mirrors", choices=("true", "false", "with", "without")),
    *common_arguments,
])
def overall(args):
    if args.mirrors in ["with", "without"]:
        args.mirrors = args.mirrors == "with"
    print(
        overall(
            args.package,
            mirrors=args.mirrors,
            start_date=args.start_date,
            end_date=args.end_date,
            format=args.format,
            total="daily" if args.daily else ("monthly" if args.monthly else "all"),
            sort=args.sort,
            color="no",
        )
    )


@subcommand([
    package_argument,
    argument("-V", "--version", help="eg. 2 or 3", type=_python_major_version),
    *common_arguments,
])
def python_major(args):
    print(
        python_major(
            args.package,
            version=args.version,
            start_date=args.start_date,
            end_date=args.end_date,
            format=args.format,
            total="daily" if args.daily else ("monthly" if args.monthly else "all"),
            sort=args.sort,
            color=args.color,
        )
    )


@subcommand([
    package_argument,
    argument("-V", "--version", help="eg. 2.7 or 3.6", type=_python_minor_version),
    *common_arguments,
])
def python_minor(args):
    print(
        python_minor(
            args.package,
            version=args.version,
            start_date=args.start_date,
            end_date=args.end_date,
            format=args.format,
            total="daily" if args.daily else ("monthly" if args.monthly else "all"),
            sort=args.sort,
            color=args.color,
        )
    )


@subcommand([
    package_argument,
    argument("-o", "--os", help="eg. windows, linux, darwin or other"),
    *common_arguments,
])
def system(args):
    print(
        system(
            args.package,
            os=args.os,
            start_date=args.start_date,
            end_date=args.end_date,
            format=args.format,
            total="daily" if args.daily else ("monthly" if args.monthly else "all"),
            sort=args.sort,
            color=args.color,
        )
    )


def _month(yyyy_mm):
    year, month = list(map(int, yyyy_mm.split("-")))
    first = dt.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = dt.date(year, month, last_day)
    return str(first), str(last)


def _last_month():
    today = dt.date.today()
    if today.month == 1:
        year, month = today.year - 1, 12
    else:
        year, month = today.year, today.month - 1
    return _month(f"{year}-{month:02d}")


def _this_month():
    today = dt.date.today()
    return _month(today.isoformat()[:7])[0]


def main():
    cli.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        if hasattr(args, "start_date") and args.start_date:
            with contextlib.suppress(ValueError):
                args.start_date, _ = _month(args.start_date)
        if hasattr(args, "end_date") and args.end_date:
            with contextlib.suppress(ValueError):
                _, args.end_date = _month(args.end_date)
        if hasattr(args, "month") and args.month:
            args.start_date, args.end_date = _month(args.month)
        elif hasattr(args, "last_month") and args.last_month:
            args.start_date, args.end_date = _last_month()
        elif hasattr(args, "this_month") and args.this_month:
            args.start_date = _this_month()
        args.format = _define_format(args)
        globals()["_verbose"] = args.verbose
        args.func(args)


if __name__ == "__main__":
    main()
