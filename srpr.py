#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 script intended to run under Termux (on Android) using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`. The script's purpose is to iterate over every lowercase letter of the English alphabet (a–z) and, for each letter, execute an external command named `srp` passing that letter as its single argument, using a helper function `runcmd` imported from a local module named `dh`.

Main requirements and behavior:
- Import `annotations` from `__future__`, import `sys`, and import `runcmd` from a module called `dh`.
- Only execute the main logic when the script is run directly (i.e., inside an `if __name__ == "__main__":` block).
- Inside the main block, import `ascii_lowercase` from the `string` module.
- Loop through each character in `ascii_lowercase` (a through z).
- For each character, build a command list in the form `["srp", char]` and call `runcmd(cmd, show_output=True)` to execute it, ensuring the command's output is shown/displayed during execution.
- After the loop finishes processing all 26 letters, print the string `"done"` to indicate completion.

Inputs: No command-line arguments or stdin input are required; the input is simply the fixed sequence of lowercase alphabet characters generated internally.

Outputs: The script produces whatever output the external `srp` command generates for each letter (displayed via `show_output=True`), followed by a final printed line `"done"` once all iterations complete.

Notable behavior: The script relies on an external helper module `dh` providing a `runcmd` function capable of executing shell-like commands given as a list, with an option to show command output. There is no error handling, return value capture, or conditional logic beyond the simple loop—it is a straightforward batch invocation of the same command with 26 different single-character arguments.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/VZNS98iH967VsVbSmwX8n7"""

from __future__ import annotations
from pathlib import Path
import sys

from dh import runcmd


if __name__ == "__main__":
    from string import ascii_lowercase

    for char in ascii_lowercase:
        cmd = ["srp", char]
        runcmd(cmd, show_output=True)
    print("done")
