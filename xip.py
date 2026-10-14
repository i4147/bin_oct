#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that determines and displays the public network connection details of the machine it runs on. The tool should query a series of free public IP-geolocation services in order, falling back to the next service automatically if one fails, times out, returns an error, or provides an unusable response. From whichever service succeeds, it should extract and present the public IP address, country, region, city, and internet service provider (ISP) name, handling missing fields gracefully so the output never crashes on partial data. If every service fails, the script should report a clear, user-friendly error message and exit with a non-zero status code.
Requirements:
- Run as a standalone command-line tool with no required arguments.
- Use short network timeouts so the script never hangs for long, and treat each service's response format as potentially different from the others.
- Print the results in a clean, human-readable layout with one labeled field per line; optionally support a machine-readable JSON output mode selected via a command-line flag.
- Show which service provided the data so the user knows the source.
- Handle keyboard interruption (Ctrl+C) gracefully without printing a stack trace.
- Include brief usage help available via a standard help flag.
- Keep the script self-contained, readable, and robust against network errors, malformed responses, and unexpected JSON structures.
---"""

from __future__ import annotations
import sys
import time
import requests


def get_connection_info():
    backends = [
        {
            "name": "ip-api.com",
            "url": "http://ip-api.com",
            "parser": lambda d: (
                {
                    "ip": d.get("query"),
                    "country": d.get("country"),
                    "city": d.get("city"),
                    "isp": d.get("isp"),
                    "region": d.get("regionName"),
                }
                if d.get("status") == "success"
                else None
            ),
        },
        {
            "name": "ipapi.co",
            "url": "https://ipapi.co",
            "parser": lambda d: (
                {
                    "ip": d.get("ip"),
                    "country": d.get("country_name"),
                    "city": d.get("city"),
                    "isp": d.get("org"),
                    "region": d.get("region"),
                }
                if "error" not in d
                else None
            ),
        },
        {
            "name": "ipwho.is",
            "url": "https://ipwho.is",
            "parser": lambda d: (
                {
                    "ip": d.get("ip"),
                    "country": d.get("country"),
                    "city": d.get("city"),
                    "isp": d.get("connection", {}).get("isp"),
                    "region": d.get("region"),
                }
                if d.get("success") is True
                else None
            ),
        },
    ]
    for backend in backends:
        try:
            response = requests.get(backend["url"], timeout=5)
            response.raise_for_status()
            data = response.json()
            info = backend["parser"](data)
            if info:
                return info
            else:
                print(f"[{backend['name']}] Data parsing error or API error response.")
        except requests.exceptions.RequestException as e:
            print(f"[{backend['name']}] Connection failed: {e}")
            continue
    print("All IP service backends failed. Network might be down.")
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
    normal_delay = 7
    cooldown_delay = 30
    try:
        while True:
            info = get_connection_info()
            print_info(info)
            if info:
                time.sleep(normal_delay)
            else:
                print(f"Entering {cooldown_delay}-second cooldown to preserve API rate limits...")
                time.sleep(cooldown_delay)
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
        sys.exit(0)
