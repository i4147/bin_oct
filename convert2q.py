#!/data/data/com.termux/files/usr/bin/env python

from pathlib import Path
import re

EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".log"}

AUXILIARIES = (
    "is",
    "are",
    "am",
    "was",
    "were",
    "has",
    "have",
    "had",
    "can",
    "could",
    "will",
    "would",
    "shall",
    "should",
    "may",
    "might",
    "must",
)


def to_question(sentence):
    sentence = sentence.strip()

    if not sentence:
        return None

    # Skip existing questions
    if sentence.endswith("?"):
        return None

    sentence = re.sub(r"[.!;]+$", "", sentence).strip()

    if not sentence:
        return None

    words = sentence.split()
    first = words[0].lower()

    # Move existing auxiliary to the beginning
    if first in AUXILIARIES:
        return sentence[0].lower() + sentence[1:] + "?"

    # Handle contractions
    if first.endswith(("n't", "'re", "'ve", "'ll", "'d")):
        return sentence[0].lower() + sentence[1:] + "?"

    # Handle simple past tense
    if len(words) >= 2:
        subject = words[0]
        verb = words[1]

        # Simple past irregular/common verbs
        if verb.lower() in {
            "went",
            "came",
            "saw",
            "made",
            "took",
            "gave",
            "found",
            "knew",
            "bought",
            "wrote",
            "ate",
            "ran",
            "spoke",
        }:
            return f"Did {sentence[0].lower() + sentence[1:]}?"

        # Regular past tense
        if verb.lower().endswith("ed"):
            return f"Did {sentence[0].lower() + sentence[1:]}?"

    # Simple present: third-person singular
    if len(words) >= 2:
        verb = words[1].lower()

        if verb.endswith(("s", "es")) and verb not in {"is", "has", "does"}:
            subject = words[0]
            rest = " ".join(words[1:])
            return f"Does {subject} {rest}?"

    # General fallback
    return "Is it true that " + sentence[0].lower() + sentence[1:] + "?"


def main() -> None:
    results = []

    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue

        if path.name in {"qmade.txt"}:
            continue

        if path.suffix.lower() not in EXTENSIONS:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            question = to_question(sentence)

            if question:
                results.append(question)

    # Remove duplicates while preserving order
    results = list(dict.fromkeys(results))

    Path("qmade.txt").write_text("\n".join(results), encoding="utf-8")

    print(f"Converted {len(results)} sentences.")
    print("Saved to qmade.txt")


if __name__ == "__main__":
    main()
