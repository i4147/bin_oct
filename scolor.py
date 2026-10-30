#!/data/data/com.termux/files/usr/bin/env python
from secrets import randbelow

RESET = "\033[0m;"


def _bg(r: int, g: int, b: int) -> str:
    return f"\x1b[48;2;{r};{g};{b}m"


def showcolor(n=998) -> int:
    for _ in range(1, n):
        r = randbelow(256)
        g = randbelow(256)
        b = randbelow(256)
        print(f"{_bg(r, g, b)}       {RESET} {r!s} {g!s} {b!s}")
    return 0


for i in range(3):
    showcolor(50)
    ans = input("continue ?")
    if ans != "y":
        break
