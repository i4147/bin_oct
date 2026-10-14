#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line, reads the file's text content, compresses that text using a prompt-compression utility, and saves the compressed result to a new file placed alongside the original. The output file should keep the same name as the input but use a distinct extension indicating it is compressed. The script should run as a standalone command-line tool, expect exactly one argument (the path to the input file), and handle the compression step through a reusable compressor component that returns both the compressed text and related result data. Focus on reliable reading and writing of text files, clear use of the compressor's output, and a simple, dependable command-line workflow.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from compression_prompt import Compressor

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    text = fn.read_text()
    c = Compressor()
    result = Compressor.compress(input_text=text)
    outf = fn.with_suffix(".compressed")
    outf.write_text(result.compressed_text)
