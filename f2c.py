#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that accepts a temperature value in Fahrenheit as a single argument via sys.argv, then converts it to both Celsius and Kelvin using standard conversion formulas.
The script should print a single line displaying the Celsius and Kelvin values, each formatted to two decimal places, labeled clearly as "celecius" and "kelvin".
Assume the input argument is a valid integer and no error handling for invalid input is required."""

import sys

if __name__ == "__main__":
    farenheit = int(sys.argv[1])
    celecius = (farenheit - 32) * 5 / 9
    kelvin = celecius + 273.15
    print(f"celecius: {celecius:.2f}  kelvin:{kelvin:.2f}")
