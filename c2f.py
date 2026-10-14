#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that runs from the command line and converts a temperature given in degrees Celsius to degrees Fahrenheit. The script should accept a single integer argument representing the Celsius value, perform the standard Celsius-to-Fahrenheit conversion, and print the result to standard output as a number rounded to two decimal places. It should be executable directly as a program, with the conversion logic only running when the script is launched as the main program rather than when imported. Keep the script minimal and focused on this single conversion task.
---"""

from __future__ import annotations
import sys

if __name__ == "__main__":
    celsius = int(sys.argv[1])
    farenheit = celsius * 9 / 5 + 32
    print(f"{farenheit:.2f}")
