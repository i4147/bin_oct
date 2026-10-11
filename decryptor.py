#!/data/data/com.termux/files/usr/bin/env python
"""You are writing a single self-contained prompt for an AI coding agent. The agent will use it to recreate a Python command-line utility from scratch. Output only that prompt, in English, with no preamble or commentary.

The utility is an in-place file encryption and decryption tool for Termux on Android. Its shebang points to the Termux Python interpreter path. Describe it as follows:

**Purpose:** A command-line tool that encrypts or decrypts a given file in place using AES-256 in CBC mode with PKCS7 padding. It can also generate a random key.

**Dependencies:** Python 3 standard library modules (argparse, random, string, pathlib, os) plus the third-party `cryptography` package, specifically its default backend, PKCS7 padding, and AES cipher and CBC mode primitives. Use `from __future__ import annotations` for type hint compatibility.

**Constants and key generation:**
- Define an AES block size constant of 16 bytes.
- A random key generator produces a string of 32 characters by default, drawn from ASCII letters and digits, using the `random` module (not a cryptographically secure source, so note this as a known weakness). The key is used directly as the AES key bytes, so 32 ASCII characters yields a 256-bit key.

**Encryption behavior:**
- Read the entire file as bytes.
- Generate a fresh 16-byte IV from the OS random source.
- Encrypt the PKCS7-padded data with AES-CBC using the key encoded as UTF-8.
- Overwrite the file with the IV prepended to the ciphertext.

**Decryption behavior:**
- Read the entire file as bytes.
- The first 16 bytes are the IV; the remainder is ciphertext.
- Decrypt, then remove PKCS7 padding and write the plaintext back to the same file.
- Wrong keys typically raise a padding error from the unpadder. Surface this as a clear error message rather than a raw traceback where practical.

**CLI interface (argparse):**
- Subcommands or flags for encrypt, decrypt, and key generation. Include a positional or option for the target file path and a key argument for encrypt/decrypt.
- Keys must be exactly 32 bytes for AES-256; validate length and reject other lengths with a clear message.
- Handle missing files and unreadable paths with a clean error and nonzero exit status.
- Warn that encryption and decryption overwrite the original file with no backup.

**Edge cases:**
- Empty files: encryption should still produce a valid IV plus one full padding block; decryption must handle this.
- Files shorter than 16 bytes during decryption are invalid and should be rejected.
- Non-ASCII key characters: the key is UTF-8 encoded, so a key whose encoded length is not 32 bytes must be rejected.

**Execution:** Run as an executable script with the Termux Python shebang. A `main` guard should invoke the argument parser. Print the generated key to stdout when generating one, so the user can save it.

**Notes for the agent:** Keep the implementation compact and idiomatic, with type hints. Preserve the in-place overwrite semantics. Do not add features beyond these.
---"""

from __future__ import annotations

import argparse
import random
import string
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

AES_BLOCK_SIZE = 16


def random_key(length: int = 32) -> LiteralString:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def encrypt_file(path, key) -> None:
    from os import urandom

    backend = default_backend()
    iv = urandom(AES_BLOCK_SIZE)
    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    data = Path(path).read_bytes()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    Path(path).write_bytes(iv + encrypted_data)


def decrypt_file(path, key) -> None:
    backend = default_backend()
    raw = Path(path).read_bytes()
    iv = raw[:AES_BLOCK_SIZE]
    ciphertext = raw[AES_BLOCK_SIZE:]
    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    Path(path).write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--encrypt", action="store_true")
    parser.add_argument("--decrypt", action="store_true")
    parser.add_argument("--key", help="Encryption/decryption key")
    args = parser.parse_args()
    if args.encrypt:
        key = random_key()
        print(f"Encryption key: {key}")
        action = encrypt_file
    elif args.decrypt:
        if not args.key:
            print("Error: Decryption key is required.")
            return
        key = args.key
        action = decrypt_file
    else:
        print("Error: Specify either --encrypt or --decrypt.")
        return
    for path in Path.cwd().glob("*"):
        if path.is_file() and path.name != Path(__file__).name:
            print(f"Processing {path}...")
            action(path, key)


if __name__ == "__main__":
    raise SystemExit(main())
