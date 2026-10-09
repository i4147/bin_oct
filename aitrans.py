#!/data/data/com.termux/files/usr/bin/env python
# -*- coding: utf-8 -*-
"""Write a prompt for an AI coding agent to generate a Python 3.12 command-line script (shebang targeting Termux's Python interpreter at `/data/data/comtermux/files3.12`, UTF-8 encoded) that acts as a universal subtitle (SRT) translator powered by LLMs.

Describe the following requirements clearly:

**Purpose**: The script translates `.srt` subtitle files into a target language using either the OpenAI API or Google Gemini API as the translation backend, automatically choosing whichever provider is configured (OpenAI takes priority if both keling back to Gemini otherwise).

**Configuration / startup, the script should load environment variables from a `. home directory (`~/.ple `KEY=VALUE` lines, skipping blank lines and comments (`#`), and stripping surrounding quotes from values. These loaded variables should populate `os.environ` without overwriting variables already set.
- It should read `OPENAI_API_KEY` and `GEMINI_API_KEY` from the environment.
- It should gracefully handle missing SDKs: import `openai` and `google.genai` inside try script doesn't crash if one package isn't installed; onlyantiate a client for provider if both its API key is and its SDK is importable. to check whether at least one provider is properly configured, and exit with a clear error message if neither is available.

**Core translation logic**:
- Implement a class (e.g., `UniversalTranslator`) encapsulating the configuration and translation behavior.
- A method to translate a single piece of text to a target language (default "English"), which:
  - Returns the input unchanged if it's empty/whitespace-only.
  - Builds a carefully worded prompt instructing the model to act as a professional, high-fidelity translation engine, preserving meaning, tone, and formatting, and to return only the translated text without- Sends the prompt to whichever client isured (OpenAI chat/completions API using a for each provider.
  - Returns the translated string, handling API errors gracefully (e.g., logging the error and returning the original text or a fallback).

**SRT file handling**:
- Parse `.srt` subtitle files (index numbers, timestamp lines, and multi-line subtitle text blocks separated by blank lines).
- Translate only the subtitle text content, leaving indices and timestamps untouched, and reconstruct the file in valid SRT format.
- Support processing a single file or a directory of `.srt` files (using `glob`/`Path` to discover files), writing translated output to new file(s) (e.g., with a suffix or in an output directory), preserving original filenames where sensible.

**CLI interface**:
- Use `argparse` to accept arguments such as: input file or directory path, target language, optional output path/directory, and anye.g., overwrite flag, verdebug flag).
- Print clear progress/status messages to ste.g., which file is being processed, success file) and useit codes on fe API keys configured, inval).

**Notable behavserve**:
- Lai` so the script runs even if only one SDK is installed.
- Environment variable loading from `~/.env` as a lightweight dotenv replacement (no external dependency).
- Provider selection logic: prefer OpenAI if its key and SDK are both available, otherwise fall back to Gemini.
- Designed to run specifically within a Termux (Android Linux environment) Python installation, as reflected by the shebang path.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/TtrvfNQ4bP5X464G8XXBLr"""

import os
import sys
import glob
import argparse
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


def load_env_file(env_path):
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            os.environ[key] = val


class UniversalTranslator:
    def __init__(self):

        home_env = Path.home() / ".env"
        load_env_file(home_env)

        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

        self.openai_client = None
        self.gemini_client = None

        if self.openai_key and OpenAI:
            self.openai_client = OpenAI(api_key=self.openai_key)
        elif self.gemini_key and genai:
            self.gemini_client = genai.Client(api_key=self.gemini_key)

    def is_configured(self):
        return self.openai_client is not None or self.gemini_client is not None

    def translate_text(self, text, target_lang="English"):
        if not text.strip():
            return text

        prompt = (
            f"You are a professional, high-fidelity translation engine.\n"
            f"Translate the following text into fluent {target_lang}.\n"
            f"Preserve all original formatting, paragraphs, code blocks, syntax markers, placeholders, and structure.\n"
            f"Only output the translated text. Do not include any explanations, preambles, notes, or markdown wrappers unless they were present in the source text.\n\n"
            f"Source Text:\n{text}"
        )

        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful translation assistant.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(
                    f"⚠️ OpenAI translation error: {e}. Falling back to alternative methods...",
                    file=sys.stderr,
                )

                if self.gemini_key and genai and not self.gemini_client:
                    self.gemini_client = genai.Client(api_key=self.gemini_key)

        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3),
                )
                return response.text.strip()
            except Exception as e:
                print(f"❌ Gemini translation error: {e}", file=sys.stderr)

        raise RuntimeError("No operational translation client or fallback API routes available.")


def process_file(file_path, translator, target_lang):
    print(f"📄 Processing: {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            print(f"   ℹ️ Skipping empty file: {file_path}")
            return

        translated_content = translator.translate_text(content, target_lang=target_lang)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(translated_content)
        print(f"   ✅ Done.")

    except Exception as e:
        print(f"   ❌ Error processing {file_path}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Inplace file translator using ChatGPT (with Gemini fallback).")
    parser.add_argument(
        "-e",
        "--extensions",
        default="txt,md,py,rst",
        help="Comma-separated file extensions to look for (default: txt,md)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        default="English",
        help="Target translation destination language (default: English)",
    )
    args = parser.parse_args()

    if OpenAI is None and genai is None:
        print(
            "❌ Error: Missing required packages. Run: pip install openai google-genai",
            file=sys.stderr,
        )
        sys.exit(1)

    translator = UniversalTranslator()
    if not translator.is_configured():
        print(
            "❌ Error: Valid credentials missing. Ensure OPENAI_API_KEY or GEMINI_API_KEY is defined in ~/.env",
            file=sys.stderr,
        )
        sys.exit(1)

    if translator.openai_client:
        print("🚀 Primary Translation Engine Active: ChatGPT (gpt-4o-mini)")
    else:
        print("🚀 Fallback Translation Engine Active: Gemini (gemini-2.5-flash)")

    extensions = [ext.strip().lstrip(".") for ext in args.extensions.split(",")]
    files_to_translate = []
    for ext in extensions:
        files_to_translate.extend(glob.glob(f"*.{ext}"))

    if not files_to_translate:
        print(f"No files found matching extensions ({', '.join(extensions)}) in the current directory.")
        return

    print(f"Found {len(files_to_translate)} target file(s) for inplace translation.")

    for path in files_to_translate:
        process_file(path, translator, args.lang)


if __name__ == "__main__":
    main()
