#!/usr/bin/env bash
set -euo pipefail
prefix="${PREFIX:-/data/data/com.termux/files/usr}"
new_shebang="#!${prefix}/bin/env python"
shopt -s nullglob
for f in *.py; do
    [ -f "$f" ] || continue
    first_line=$(head -n 1 "$f" || true)
    if [[ "$first_line" == '#!'* ]]; then
        sed -i "1s|^#!.*|${new_shebang}|" "$f"
        printf 'Updated  : %s\n' "$f"
    else
        tmp=$(mktemp)
        { printf '%s\n' "$new_shebang"; cat "$f"; } > "$tmp" && mv "$tmp" "$f"
        printf 'Prepended: %s\n' "$f"
    fi
    chmod +x "$f"
done
