#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that generates and displays random RGB colors directly in the terminal.
It should use the secrets module to securely generate random red, green, and blue values between 0 and 255, then print a block of that color using ANSI escape codes followed by the numeric RGB values.
The script should repeat this process a random number of times, up to 999 iterations, determined by a secure random number generator each time it runs."""

from secrets import randbelow
def show_random_color() -> None:
    red = randbelow(256)
    green = randbelow(256)
    blue = randbelow(256)
    print(f"\x1b[48;2;{red};{green};{blue}m        \x1b[0m {red!s} {green!s} {blue!s}")
if __name__ == "__main__":
    for _i in range(1, randbelow(1000)):
        show_random_color()