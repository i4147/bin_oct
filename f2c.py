#!/data/data/com.termux/files/usr/bin/env python

import sys

if __name__ == "__main__":
    farenheit = int(sys.argv[1])
    celecius = (farenheit - 32) * 5 / 9
    kelvin = celecius + 273.15
    print(f"celecius: {celecius:.2f}  kelvin:{kelvin:.2f}")
