#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 script designed to run in a Termux environment (using the Termux Python interpreter shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that continuously monitors and displ public.

The script should:

- Use the `requests` library to send an HTTP GET request to the free "ip-api.com" JSON endpoint (`http://ip-api.com/json/`) with a timeout of 5 seconds in order to fetch IP geolocation details.
- Define a function `get_connection_info()` that performs the request, checks for HTTP errors, parses the JSON response, and verifies that the API returned a "success" status. If successful, it should extract and return a dictionary containing the IP address (`query`), country, city, ISP, and region name. it should print an error message : Failed to retrie data.") and return `requests` exception occection failure), it should catch it, print an error message including the exception details, and return `None`.
- Define a function `print_info(info)` that takes the dictionary returned by `get_connection_info()` and neatly prints the IP address, location (city, region, country), and ISP, surrounded by separator lines of dashes. If `info` is `None`, it should print a message indicating the details could not be retrieved.
- In the main execution block (`if __name__ == "__main__":`), run an infinite loop that repeatedly calls `get_connection_info()` and `print_info()`, waiting 5 seconds between each iteration using `time.sleep(5)`, so the connection info is continuously refreshed and displayed.
- Handle a `KeyboardInterully by printing a message ("Process stopped by user.") and exiting c

The purpose of the script is to act-running network/ility—useful for checking if a VPN/proxy connection is active or for watching for IP/location changes in real time directly from a Termux terminal on Android.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/5S9FsuyngXMfNCpDgckBaR"""

from __future__ import annotations
from pathlib import Path
import sys
import time

import requests


def get_connection_info():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            return {
                "ip": data.get("query"),
                "country": data.get("country"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "region": data.get("regionName"),
            }
        else:
            print("Error: Failed to retrieve location data.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to IP service: {e}")
        return None


def print_info(info):
    if info:
        print("-" * 30)
        print(f"IP Address: {info['ip']}")
        print(f"Location:   {info['city']}, {info['region']}, {info['country']}")
        print(f"ISP:        {info['isp']}")
        print("-" * 30)
    else:
        print("Could not retrieve connection details.")


if __name__ == "__main__":
    try:
        while True:
            info = get_connection_info()
            print_info(info)
            time.sleep(7)
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
        sys.exit(0)
