#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a Gregorian (Western) calendar date entered by the user into its Persian (Solar Hijri / Jalali) equivalent and displays it as a formatted Persian-language date line. The output should include the Persian weekday name corresponding to the given date, the Persian day number, the Persian month name, and the Persian year, all presented in a single readable string with the digits rendered in Persian (Eastern Arabic) numerals. Accept the Gregorian year, month, and day as inputs (either as function arguments or interactive prompts), validate that the date is a real calendar date, and handle the conversion using a correct Gregorian-to-Jalali algorithm so that results are accurate across typical modern date ranges. Provide clean helper components for the calendar conversion, weekday lookup, month naming, and digit translation, and ensure the final result can be printed or returned for display. The script should be self-contained, produce only the formatted date output for valid input, and give a clear error message for invalid dates.
---"""

from __future__ import annotations
import datetime as dt
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
    today = dt.date.today()
    return today.year, today.month, today.day


if __name__ == "__main__":
    y, m, d = get_current_ymd()
    faprint(georgian_to_hijri(y, m, d))
