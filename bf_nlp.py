#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file whose path is provided as the first command-line argument, splits its contents into sentences and into words using a text tokenization utility, and then prints the resulting word tokens to standard output. The script should be runnable directly from the command line, handle the file reading cleanly, and produce a readable output of the tokenized words. It should perform only this tokenization workflow, with the sentence segmentation computed alongside the word tokenization as part of the processing pipeline.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from blingfire_compat import text_to_sentences, text_to_words

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    text = fn.read_text()
    sents = text_to_sentences(text)
    words = text_to_words(text)
    print(words)
