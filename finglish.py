#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts Persian (Farsi) text into Finglish, a romanized, phonetic in Latin letters. The tool should accept a Persian string (or read text from a file) and output a readable Latin-script transliteration that approximates how the words are pronounced.
Key requirements:
- Input: Persian text provided directly as a string argument or read from a text file path. Support multi-word sentences, preserving word boundaries and spacing.
- Output: The transliterated Finglish text, either printed to the console or written to an output file.
- Character mapping: Map each Persian letter to a sensible Latin equivalent, including digraphs where appropriate (for example, multi-letter sounds such as "sh", "ch", "kh", "zh", "gh"). Handle letters that represent multiple sounds, such as the Persian "و" and "ی", using context: the position of the letter within a word (word-initial, word-medial, word-final) should determine whether it becomes a consonant or vowel sound.
- Positional rules: Apply contextual logic so that vowels and glides are rendered correctly depending on whin, occur inside, or end a word.
- Diacritics and short vowels: Handle Persian vowel marks and zero-width characters gracefully, stripping or ignoring them where they are not part of the base text, and normalizing Unicode input before processing.
- Edge cases: Handle empty strings, extra whitespace, punctuation, numerals, mixed Persian and Latin text, and Arabic-script variants of common letters (such as Arabic yeh and kaf) by normalizing them to their Persian forms.
- Robustness: Characters not present in the mapping should pass through unchanged rather than causing errors. Report clear messages for missing input files or unreadable encodings.
- Usability: Provide a simple command-line interface that accepts either inline text or a file path, with an optional output file argument. Default to UTF-8 encoding for all reading and writing.
- Code quality: The script should be self-contained, well-structured, and include brief documentation explaining the transliteration approach and its known limitations, such as the fact that Finglish is an informal, non-standardized system and that the output is phonetic approximation rather than a precise linguistic standard.
---"""

from __future__ import annotations
from pathlib import Path
import unicodedata


def custom_persian_to_finglish(text: str) -> str:
    persian_map = {
        "ا": "a",
        "آ": "a",
        "ب": "b",
        "پ": "p",
        "ت": "t",
        "ث": "s",
        "ج": "j",
        "چ": "ch",
        "ح": "h",
        "خ": "kh",
        "د": "d",
        "ذ": "z",
        "ر": "r",
        "ز": "z",
        "ژ": "zh",
        "س": "s",
        "ش": "sh",
        "ص": "s",
        "ض": "z",
        "ط": "t",
        "ظ": "z",
        "ع": "a",
        "غ": "gh",
        "ف": "f",
        "ق": "gh",
        "ک": "k",
        "گ": "g",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ه": "h",
    }
    words = text.split(" ")
    processed_words = []
    for word in words:
        if not word:
            processed_words.append("")
            continue
        processed_word = ""
        chars = list(word)
        for i, char in enumerate(chars):
            if char == "و":
                if i == 0:
                    processed_word += "v"
                else:
                    processed_word += "o"
            elif char == "ی":
                if i == 0 or i == len(chars) - 1:
                    processed_word += "y"
                else:
                    processed_word += "i"
            else:
                processed_word += persian_map.get(char, char)
        processed_words.append(processed_word)
    return "_".join(processed_words)


def convert_filenames_with_pathlib(directory: str = ".") -> None:
    start_path = Path(directory)
    for path in start_path.rglob("*"):
        original_filename_stem = path.stem
        original_extension = path.suffix
        normalized_stem = unicodedata.normalize("NFKD", original_filename_stem)
        finglish_stem = custom_persian_to_finglish(normalized_stem)
        finglish_stem_cleaned = "_".join(filter(None, finglish_stem.split("_")))
        new_filename = finglish_stem_cleaned + original_extension
        if new_filename != path.name:
            new_path = path.with_name(new_filename)
            try:
                path.rename(new_path)
                print(f"Renamed: {path} -> {new_path}")
            except OSError as e:
                print(f"Error renaming {path}: {e}")


if __name__ == "__main__":
    convert_filenames_with_pathlib()
