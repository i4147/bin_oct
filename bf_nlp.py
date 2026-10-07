#!/data/data/com.termux/files/usr/bin/env python
from __future__ import annotations
from pathlib import Path
import sys

from blingfire import text_to_sentences, text_to_words


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    text = fn.read_text()
    sents = text_to_sentences(text)
    words = text_to_words(text)
    print(words)
