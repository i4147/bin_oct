#!/data/data/com.termux/files/usr/bin/env python
"""You are reproducing a Python 3 script from scratch. Write one complete, self-contained script that converts a Gregorian (Western) calendar date into a Persian (Jalali/Solar Hijri) date and prints it as a formatted Persian-language string. Follow the specification below exactly.

**Purpose**
The script converts a Gregorian date to the Jalali (Persian solar) calendar and outputs a single line in Persian: the weekday name, the day of the month, the Persian month name, and the Jalali year, all written with Persian (Eastern Arabic) digits.

**Module and file conventions**
- Start the file with a shebang line pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.
- Begin the module with `from __future__ import annotations`.
- Use `import datetime` as a top-level import, and use a function-local import of `date` from `datetime` (aliased as `datetime_date`) inside the conversion function.
- Import a helper named `faprint` from a module called `faprint` at the top of the file. Use it to print the final result. Treat it as an existing external dependency; do not implement it.
- Use type hints throughout (Python 3.9+ compatible with postponed annotations).

**Functions to implement**

1. `georgian_to_hijri(year: int, month: int, day: int) -> str`
   - Despite the name, it returns the Persian (Jalali) date string.
   - Define two lists of Persian strings:
     - Seven weekday names, ordered Monday through Sunday, in this exact order: "دو شنبه", "سه شنبه", "چهار شنبه", "پنج شنبه", "جمعه", "شنبه", "یکشنبه". Note that the Python `date.weekday()` value (0 = Monday) indexes directly into this list.
     - Twelve Persian month names in order: "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند".
   - Call `gregorian_to_jalali(year, month, day)` to get `(jy, jm, jd)`.
   - Get the weekday index via `datetime_date(year, month, day).weekday()`.
   - Return a string formatted as: weekday, two spaces, Jalali day (in Persian digits), two spaces, month name (indexed by `jm - 1`), two spaces, Jalali year (in Persian digits). Example shape: `<weekday>  <day>  <month>  <year>`.

2. `to_persian_digits(s: str) -> str`
   - Import `digits` from the `string` module locally (aliased as `string_digits`).
   - Translate ASCII digits 0–9 to Persian digits ۰۱۲۳۴۵۶۷۸۹ using `str.maketrans`, and return the translated string.

3. `gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]`
   - Use the standard arithmetic algorithm based on day counts:
     - A list of cumulative day offsets for the start of each Gregorian month (non-leap base): `[0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]`.
     - Compute `gy2 = gy - 1600`, `gm2 = gm - 1`, `gd2 = gd - 1`.
     - Compute the Gregorian day number: `365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400`, then add `g_days[gm2] + gd2`.
     - Add a leap-day correction of one when the Gregorian year is leap and the month is after February (`gm > 2`), using the standard leap rule (divisible by 4, except centuries unless divisible by 400).
     - Convert to a Jalali day number by subtracting the epoch offset of 79 days from the Gregorian day count (relative to the 1600 base) and then deriving the Jalali year using 33-year cycles of 12053 days (or the equivalent 365-day-year arithmetic with leap years where the remainder falls in the standard Jalali leap pattern).
     - Derive the Jalali year, month, and day from the resulting day number, with the first six months having 31 days, the next five having 30 days, and the last month (Esfand) having 29 days, plus one extra day in leap Jalali years.
     - Return `(jy, jm, jd)` as integers, where `jm` and `jd` are 1-based.

**Main execution**
- Under a standard `if __name__ == "__main__":` guard, call `georgian_to_hijri` with a fixed example date (for example, year 2024, month 3, day 20) and pass the result to `faprint`.
- Do not read command-line arguments or stdin; the date is hard-coded in the main block.

**Edge cases and behavior notes**
- The input must be a valid Gregorian date; `datetime.date` will raise `ValueError` for invalid dates, and the script does not need to catch it, but the conversion should be correct for dates on and after 1600-03-01.
- Output must use Persian digits for the day and year only; the weekday and month are already Persian words.
- Keep the spacing in the output exactly two spaces between each component.
- Only standard library modules plus the external `faprint` helper are permitted.

**Output requirement**
Produce only the complete Python source file, with the shebang, imports, all three functions, and the main guard.
---"""

from __future__ import annotations

import datetime

from faprint import faprint


def georgian_to_hijri(year: int, month: int, day: int) -> str:
    from datetime import date as datetime_date

    weekdays: list[str] = [
        "دو شنبه",
        "سه شنبه",
        "چهار شنبه",
        "پنج شنبه",
        "جمعه",
        "شنبه",
        "یکشنبه",
    ]
    months: list[str] = [
        "فروردین",
        "اردیبهشت",
        "خرداد",
        "تیر",
        "مرداد",
        "شهریور",
        "مهر",
        "آبان",
        "آذر",
        "دی",
        "بهمن",
        "اسفند",
    ]
    jy, jm, jd = gregorian_to_jalali(year, month, day)
    weekday_index: int = datetime_date(year, month, day).weekday()
    weekday: str = weekdays[weekday_index]
    return f"{weekday}  {to_persian_digits(str(jd))}  {months[jm - 1]}  {to_persian_digits(str(jy))}"


def to_persian_digits(s: str) -> str:
    from string import digits as string_digits

    return s.translate(str.maketrans(string_digits, "۰۱۲۳۴۵۶۷۸۹"))


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_days: list[int] = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2: int = gy - 1600
    gm2: int = gm - 1
    gd2: int = gd - 1
    g_day_no: int = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    g_day_no += g_days[gm2] + gd2
    j_day_no: int = g_day_no - 79
    j_np: int = j_day_no // 12053
    j_day_no %= 12053
    jy: int = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    if j_day_no < 186:
        jm = 1 + j_day_no // 31
        jd = 1 + j_day_no % 31
    else:
        j_day_no -= 186
        jm = 7 + j_day_no // 30
        jd = 1 + j_day_no % 30
    return jy, jm, jd


def get_current_ymd() -> tuple[int, int, int]:
    today = datetime.date.today()
    return today.year, today.month, today.day


if __name__ == "__main__":
    y, m, d = get_current_ymd()
    faprint(georgian_to_hijri(y, m, d))
