#!/data/data/com.termux/files/usr/bin/python
"""You are writing a Python 3 command-line script that performs AES-CBC file encryption and decryption over a directory tree. Reproduce it from scratch with the following specification.

**Purpose:** The script recursively walks a target directory and either encrypts or decrypts every regular file found in it, in place, using a key that is either supplied by the user or generated randomly.

**Target platform and shebang:** Start the file with a shebang pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/python`. Include `from __future__ import annotations` as the first import.

**Dependencies:** Use the standard library (`argparse`, `os`, `random`, `string`, `collections.abc` for `Callable` and `Iterator`, `pathlib.Path`) and the third-party `cryptography` package. Use `cryptography.hazmat` primitives: `default_backend`, `padding`, and `Cipher`/`algorithms`/`modes`.

**Constants:** Define `AES_BLOCK_SIZE = 128` (in bits, for PKCS7 padding).

**Helper functions:**

1. `walk_files(directory: Path) -> Iterator[Path]`: recursively yield the full path of every file under `directory` using `Path.walk()`, joining each root with each filename in the file list. Ignore directory names.

2. `random_key(length: int = 32) -> str`: return a string of `length` characters chosen with `random.choice` from ASCII letters and digits. Note that this uses the non-cryptographic `random` module; the key is therefore 32 characters, which is 32 bytes and suits AES-256 when encoded as UTF-8 (ASCII only).

3. `encrypt_file(path: Path, key: str) -> None`:
   - Generate a 16-byte IV with `os.urandom(16)`.
   - Build an AES-CBC cipher using `key.encode()` as the key and the IV.
   - Read the whole file as bytes.
   - Apply PKCS7 padding with block size 128 bits, using `update` then `finalize`.
   - Encrypt the padded data with `update` then `finalize`.
   - Overwrite the file with `iv + ciphertext` (IV prepended).

4. `decrypt_file(path: Path, key: str) -> None`:
   - Read the whole file as bytes.
   - Split the first 16 bytes as the IV and the remainder as ciphertext.
   - Build the same AES-CBC cipher with the given key and extracted IV.
   - Decrypt, then remove PKCS7 padding with an unpadder of block size 128 bits, and write the plaintext back over the file.
   - The remainder of this function (decrypt and unpad, then write) must be completed consistently with the encrypt logic.

**Main logic and CLI:**

- Use `argparse` with a positional or required directory argument (a path to walk), a mode selector between encrypt and decrypt (for example, a required choice of `encrypt` or `decrypt`), and an optional key argument. If no key is supplied in encrypt mode, generate one with `random_key()` and print it so the user can save it; in decrypt mode, require the key.
- Wrap the directory into a `Path`, then iterate `walk_files` and apply the chosen function to each file, passing the key through.
- Use a `Callable[[Path, str], None]` type hint to select the operation function from the mode.

**Edge cases and error handling:**

- Validate that the target directory exists and is a directory before walking; exit with a clear message otherwise.
- Validate that the key length is correct for AES (16, 24, or 32 bytes when UTF-8 encoded); reject invalid lengths with a clear error before any file is modified.
- Handle empty files: encryption must still produce a valid IV plus one full padding block. Decryption must reject files shorter than 16 bytes or whose ciphertext length is not a multiple of 16, and should report such files without aborting the whole run.
- If unpadding fails during decryption (wrong key or corrupted file), report the file and continue or stop with a clear message, and do not write partial output for that file.
- Handle `PermissionError` and `OSError` per file so one unreadable file does not stop the run; report each failure.
- Skip symbolic links or handle them explicitly, and avoid following links that point outside the target tree.
- Warn the user that encryption is irreversible without the printed key and that operations overwrite files in place.

**Execution and usage:** Run as `python <script> <directory> encrypt` or `python <script> <directory> decrypt --key <key>`. Print a summary at the end with counts of processed and failed files. Make the script executable and runnable from the Termux shell.
---"""

from __future__ import annotations

import argparse
import os
import random
import string
from collections.abc import Callable, Iterator
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

AES_BLOCK_SIZE = 128


def walk_files(directory: Path) -> Iterator[Path]:
    for root, _dirs, files in directory.walk():
        for name in files:
            yield root / name


def random_key(length: int = 32) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def encrypt_file(path: Path, key: str) -> None:
    backend = default_backend()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    data = path.read_bytes()
    padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
    padded_data = padder.update(data) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    path.write_bytes(iv + encrypted_data)


def decrypt_file(path: Path, key: str) -> None:
    backend = default_backend()
    raw = path.read_bytes()
    iv = raw[:16]
    ciphertext = raw[16:]
    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    path.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--encrypt", action="store_true")
    parser.add_argument("--decrypt", action="store_true")
    parser.add_argument("--key", help="Encryption/decryption key")
    args = parser.parse_args()
    msg = "Please specify --encrypt or --decrypt with --key if decrypting"
    action: Callable[[Path, str], None]
    if args.encrypt:
        key = random_key()
        print(f"Encryption key: {key}")
        action = encrypt_file
        with Path("key").open("a", encoding="utf-8") as f:
            f.write("\n")
            f.write(key)
    elif args.decrypt:
        if not args.key:
            raise SystemExit(msg)
        key = args.key
        action = decrypt_file
    else:
        raise SystemExit(msg)
    for path in walk_files(Path(".")):
        if path.is_file() and path.name != "key":
            action(path, key)


if __name__ == "__main__":
    raise SystemExit(main())
