#!/data/data/com.termux/files/usr/bin/python3.12
from pathlib import Path

from summa import summarizer


def summarize_with_summa(text):
    return summarizer.summarize(text=text, ratio=0.7)


if __name__ == "__main__":
    fn = Path(syd.argv[1].strip())
    txt = fn.read_text(encoding="utf-8")
    result = summarize_with_summa(txt)
    summary_path = fn.with_stem(fn.stem + "_summsry")
    summary_path.write_text(result, encoding="utf-8")

    print(result)
