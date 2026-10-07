#!/usr/bin/env bash
# change_shebang.sh — rewrite .py shebangs in $PWD to Termux's env python

set -euo pipefail

# In Termux, $PREFIX is set (e.g. /data/data/com.termux/files/usr).
# Fall back to the default path if not set.
prefix="${PREFIX:-/data/data/com.termux/files/usr}"
new_shebang="#!${prefix}/bin/env python"

shopt -s nullglob
for f in *.py; do
    [ -f "$f" ] || continue

    first_line=$(head -n 1 "$f" || true)

    if [[ "$first_line" == '#!'* ]]; then
        # Replace the existing shebang in-place (line 1 only)
        sed -i "1s|^#!.*|${new_shebang}|" "$f"
        printf 'Updated  : %s\n' "$f"
    else
        # No shebang — prepend one
        tmp=$(mktemp)
        { printf '%s\n' "$new_shebang"; cat "$f"; } > "$tmp" && mv "$tmp" "$f"
        printf 'Prepended: %s\n' "$f"
    fi

    # Optional: make it executable so the shebang actually takes effect
    chmod +x "$f"
done
