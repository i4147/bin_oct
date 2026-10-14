#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that runs an external command-line tool once for each letter of the lowercase English alphabet (a through z), passing the current letter as the single argument each time. Each invocation should display the command's output as it runs. The script should execute only when started directly, and after all letters have been processed, it should print the word "done" to indicate completion. Rely on a helper utility module that provides the ability to run shell commands and show their output.
---"""

from __future__ import annotations
from dh import runcmd

if __name__ == "__main__":
    from string import ascii_lowercase

    for char in ascii_lowercase:
        cmd = ["srp", char]
        runcmd(cmd, show_output=True)
    print("done")
