#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import io
import multiprocessing as mp
import sys
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image

GREEN = "\033[92m"
RESET = "\033[0m"


def _fmt_bytes(n: int) -> str:
    neg = n < 0
    n = abs(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            s = f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
            return f"-{s}" if neg else s
        n /= 1024
    return f"{n} B"


def _relpath(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _compress_file(
    path: Path,
    max_dim: int = 1600,
    quality: int = 65,
    min_side: int = 256,
    min_bytes: int = 16384,
) -> tuple[Path, int, int]:
    orig_size = 0
    try:
        orig_size = path.stat().st_size
    except OSError:
        return path, 0, 0

    try:
        doc = pymupdf.open(path)
    except Exception:
        return path, orig_size, orig_size

    try:
        seen: set[int] = set()
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen:
                    continue
                seen.add(xref)

                try:
                    base = doc.extract_image(xref)
                except Exception:
                    continue

                raw: bytes = base["image"]
                w: int = base["width"]
                h: int = base["height"]
                if base.get("colorspace", 3) == 4 or base.get("smask", 0):
                    continue
                if w < min_side and h < min_side:
                    continue
                if len(raw) < min_bytes:
                    continue

                try:
                    pil = Image.open(io.BytesIO(raw))
                    pil.load()
                except Exception:
                    continue

                if pil.mode not in ("RGB", "L"):
                    try:
                        pil = pil.convert("RGB")
                    except Exception:
                        continue

                longest = max(w, h)
                if longest > max_dim:
                    scale = max_dim / longest
                    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                    try:
                        pil = pil.resize(new_size, Image.Resampling.LANCZOS)
                    except Exception:
                        continue

                buf = io.BytesIO()
                try:
                    pil.save(buf, format="JPEG", quality=quality, optimize=True)
                except Exception:
                    continue
                new_bytes = buf.getvalue()

                if len(new_bytes) >= len(raw):
                    continue

                try:
                    page.replace_image(xref, stream=new_bytes)
                except Exception:
                    try:
                        doc._replace_image(xref, new_bytes)
                    except Exception:
                        pass

        with tempfile.NamedTemporaryFile(suffix=".pdf", dir=str(path.parent), delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            doc.save(
                str(tmp_path),
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True,
                pretty=False,
            )
        finally:
            doc.close()

        new_size = tmp_path.stat().st_size
        if new_size < orig_size:
            tmp_path.replace(path)
            return path, orig_size, new_size

        tmp_path.unlink(missing_ok=True)
        return path, orig_size, orig_size
    except Exception:
        try:
            doc.close()
        except Exception:
            pass
        return path, orig_size, orig_size


def _collect(inputs: list[str]) -> list[Path]:
    roots: list[Path] = [Path(p) for p in inputs] if inputs else [Path.cwd()]
    found: list[Path] = []
    for root in roots:
        try:
            if root.is_file() and root.suffix.lower() == ".pdf":
                found.append(root.resolve())
            elif root.is_dir():
                for p in root.rglob("*.pdf"):
                    if p.is_file():
                        found.append(p.resolve())
        except OSError:
            continue
    return sorted(set(found))


def main() -> int:
    files = _collect(sys.argv[1:])
    if not files:
        print("no pdf files found")
        return 1

    workers = max(1, min(len(files), mp.cpu_count() or 1))
    print(f"compressing {len(files)} file(s) with {workers} worker(s)")

    ok_count = 0
    for path, orig, new in mp.Pool(workers).imap_unordered(_compress_file, files, chunksize=1):
        rel = _relpath(path)
        if new < orig:
            saved = orig - new
            pct = (saved / orig * 100) if orig else 0.0
            print(f"{rel}: {_fmt_bytes(orig)} -> {_fmt_bytes(new)} {GREEN}(-{_fmt_bytes(saved)}, -{pct:.1f}%){RESET}")
            ok_count += 1
        else:
            print(f"{rel}: {_fmt_bytes(orig)} (unchanged, result not smaller)")

    print(f"done: {ok_count}/{len(files)} compressed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
