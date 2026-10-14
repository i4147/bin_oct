#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that runs from the command line and converts a temperature given in degrees Fahrenheit into Celsius and Kelvin. The script should accept a single integer temperature value as a command-line argument, perform the standard Fahrenheit-to-Celsius conversion, derive the corresponding Kelvin value from that Celsius result, and print both values to the console on one line, labeled "celecius" and "kelvin" respectively, each rounded to two decimal places. The output should follow the format: celecius followed by the Celsius value, two spaces, then kelvin followed by the Kelvin value. The script should only execute its conversion logic when run directly as the main program rather than when imported as a module. Keep the tool minimal and focused on this single conversion task, with straightforward, self-contained behavior and no additional interactive prompts.
---"""

from __future__ import annotations
import sys

if __name__ == "__main__":
    farenheit = int(sys.argv[1])
    celecius = (farenheit - 32) * 5 / 9
    kelvin = celecius + 273.15
    print(f"celecius: {celecius:.2f}  kelvin:{kelvin:.2f}")
