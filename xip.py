#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import os
from dotenv import load_dotenv
import ipinfo
from dh import cyan, reset

if __name__ == "__main__":
    env_path = Path.home() / ".env"
    load_dotenv(env_path)
    token = os.environ.get("IPINFO_TOKEN")
    handler = ipinfo.getHandler(token)
    details = handler.getDetails()
    print(type(details))
    print(f"ip: {cyan}{details.ip}{reset}")
    print(f"country: {cyan}{details.country}{reset}")
    print(f"city: {cyan}{details.city}{reset}")
#    print(f"loc: {cyan}{details.loc}{reset}")
#    print(f"hostname: {cyan}{details.hostname}{reset}")
