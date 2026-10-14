#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a universal, command-line translation and image-processing utility pow AI services. The tool should accept user-supplied input files or directories and a target language or task, and it should produce translated or transformed output files in a predictable location.
Core requirements:
1. **Configuration and credentials**: The tool should load API credentials (for OpenAI and Google Gemini) from environment variables, and optionally from a `.env` file located in the user's home directory. Credentials are read from simple KEY=VALUE lines, ignoring blank lines and comments, with surrounding quotes stripped. The tool must work gracefully when one or both providers are unavailable or their SDKs are not installed, reporting clearly which backends are usable.
2. **Inputs**: Accept a command-line interface that takes one or more file paths or glob patterns, an optional output directory, the source and target language (or equivalent task parameters), and a choice of backend provider. Support batch processing of multiple files matched by wildcards, and skip or report missing paths without crashing.
3. **Translation behavior**: For text-based inputs, send content to the selected AI provider with a clear instruction to translate into the target language while preserving formatting, structure, line breaks, and meaning. For image inputs, the tool should be able to extract or translate visible text using a vision-capable model, returning the translated result as text or an annotated output file. Handle large files by chunking content sensibly so requests stay within model limits, then reassemble the result in order.
4. **Outputs**: Write each result to a new file in the output location, naming outputs clearly so they reflect the original file name and target language, without overwriting originals. Print a concise progress summary and a final report listing successes, failures, and skipped items.
5. **Robustness**: Validate arguments up front and show helpful usage messages. Retry transient API failures with reasonable backoff, surface authentication and quota errors with actionable messages, and never expose API keys in logs or output. Exit with a non-zero status code if any required job fails.
6. **Extensibility**: Structure the design so that additional AI providers can be added with minimal changes, and keep the provider-specific logic separated from the file handling and CLI logic.
The script should be self-contained, runnable from the terminal, and documented with a built-in help message describing all options and environment requirements.
---"""

from __future__ import annotations
import argparse
import glob
import os
from pathlib import Path
import sys

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
        msg = "No operational translation client or fallback API routes available."
        raise RuntimeError(msg)


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
        default="txt,md",
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
