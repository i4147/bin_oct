#!/data/data/com.termux/files/usr/bin/env python
import os

if __name__ == "__main__":
    p_env = os.environ.get("PATH")
    pdirs = p_env.split(":")
    for p in pdirs:
        print(p)
