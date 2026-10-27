#!/data/data/com.termux/files/usr/bin/python
import os

if __name__ == "__main__":
    p_env = os.environ.get("PATH")
    pdirs = p_env.split(":")
    for p in pdirs:
        print(p)
