#!/bin/bash
# build_python312.sh -- build CPython 3.12 from source for the refactor run.
#
# refactor.md requires a 3.12 floor, but the sandbox ships 3.11.2 and the
# python-build-standalone CDN is unreachable from here. codeload.github.com is
# reachable, so the interpreter is built from source instead.
#
# The resulting interpreter has zlib, hashlib, multiprocessing, tarfile,
# zipfile and venv. ssl, ctypes, bz2, lzma, sqlite3, readline and curses DO NOT
# build (no dev headers in the image) -- scripts that need them will fail their
# --help smoke run for environmental reasons.
#
# Usage:  bash arena/build_python312.sh [PREFIX]
#         PREFIX defaults to /tmp/py312
set -euo pipefail

VERSION="${CPYTHON_VERSION:-3.12.16}"
PREFIX="${1:-/tmp/py312}"
SRC="/tmp/cpython-src"
TARBALL="/tmp/cpython-${VERSION}.tar.gz"
LIBDIR="/tmp/devlib"

# Linkable zlib/openssl live under the node install in this image.
if [ ! -f "$TARBALL" ]; then
  echo "downloading CPython ${VERSION} ..."
  curl -sSL -o "$TARBALL" \
    "https://codeload.github.com/python/cpython/tar.gz/refs/tags/v${VERSION}"
fi

rm -rf "$SRC" && mkdir -p "$SRC" "$LIBDIR"
tar xzf "$TARBALL" -C "$SRC" --strip-components=1

# configure wants libz.so / libssl.so without a version suffix
ln -sf /usr/lib/x86_64-linux-gnu/libz.so.1      "$LIBDIR/libz.so"
ln -sf /usr/lib/x86_64-linux-gnu/libssl.so.3    "$LIBDIR/libssl.so"
ln -sf /usr/lib/x86_64-linux-gnu/libcrypto.so.3 "$LIBDIR/libcrypto.so"

cd "$SRC"
CFLAGS="-I/usr/local/include/node" LDFLAGS="-L${LIBDIR}" \
  ./configure --prefix="$PREFIX" --with-ensurepip=install --disable-test-modules \
  > /tmp/cfg.log 2>&1
make -j"$(nproc)" > /tmp/make.log 2>&1
make install > /tmp/install.log 2>&1

"$PREFIX/bin/python3.12" --version
"$PREFIX/bin/python3.12" - <<'PY'
"""Report which optional stdlib extensions linked."""
import importlib

for name in (
    "zlib", "ssl", "ctypes", "sqlite3", "bz2", "lzma",
    "hashlib", "multiprocessing", "tarfile", "zipfile", "venv",
):
    try:
        importlib.import_module(name)
    except Exception:
        print(f"  MISS {name}")
    else:
        print(f"  ok   {name}")
PY
