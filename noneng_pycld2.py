#!/data/data/com.termux/files/usr/bin/env python
import os
import pycld2 as cld2


def detect_language(text):
    try:
        is_reliable, text_bytes_found, details = cld2.detect(text)
        lang = details[0][1] if details else "unknown"
        prob = details[0][2] if details else 0.0
    except Exception as e:
        lang, prob = f"error ({str(e)})", 0.0
    return lang, prob


def scan_and_detect(root_dir="."):
    print(f"Scanning directory: {os.path.abspath(root_dir)}\n", flush=True)
    print(f"{'File Path':<40} | {'pycld2':<15} | Snippet", flush=True)
    print("-" * 100, flush=True)

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.startswith("."):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                if not content:
                    continue

                lang, prob = detect_language(content)
                snippet = content[:40].replace("\n", " ") + ("..." if len(content) > 40 else "")

                # Live output: every file is printed immediately as it's processed
                print(f"{file_path:<40} | {lang:<7} ({prob:2.0f}%) | {snippet}", flush=True)

            except Exception:
                pass


scan_and_detect(".")
