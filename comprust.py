#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a command-line Python script that reads a file path from the first command-line argument, loads its full text content, and compresses it using the Compressor class from a compression_prompt module.
The script should instantiate the Compressor, call its compress method with the file's text as input, and extract the compressed_text from the returned result.
Finally, it should write the compressed output to a new file with the same name as the input but with a ".compressed" extension, placed alongside the original file."""

from __future__ import annotations

import sys
from pathlib import Path

from compression_prompt import Compressor

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    text = fn.read_text()
    c = Compressor()
    result = Compressor.compress(input_text=text)
    outf = fn.with_suffix(".compressed")
    outf.write_text(result.compressed_text)
