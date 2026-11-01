#!/data/data/com.termux/files/usr/bin/env python

import sys

if __name__ == "__main__":
    celsius = int(sys.argv[1])
    farenheit = celsius * 9 / 5 + 32
    print(f"{farenheit:.2f}")
