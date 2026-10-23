#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

VERSION = "2.0.0"


# ---------------------------------------------------------------------------
# Conversion options
# ---------------------------------------------------------------------------
@dataclass
class ConvertOptions:
    quality: int = 85
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    scale: Optional[float] = None
    fit: str = "contain"
    gravity: str = "center"
    background: str = "white"
    auto_orient: bool = True
    strip_metadata: bool = True
    lossless: bool = False
    progressive: bool = False
    target_size: Optional[int] = None
    min_quality: int = 30


# ---------------------------------------------------------------------------
# Backend registry
# ---------------------------------------------------------------------------
@dataclass
class Backend:
    name: str
    priority: int
    read: Set[str]
    write: Set[str]
    fn: Callable[[Path, Path, str, int, ConvertOptions], bool]
    available: bool = False


_REGISTRY: List[Backend] = []


def _register(
    name: str,
    priority: int,
    read: Iterable[str],
    write: Iterable[str],
    fn: Callable,
    probe: Optional[Callable[[], bool]] = None,
) -> None:
    try:
        ok = True if probe is None else bool(probe())
    except Exception:
        ok = False
    _REGISTRY.append(Backend(name, priority, {e.lower() for e in read}, {e.lower() for e in write}, fn, ok))
    _REGISTRY.sort(key=lambda b: b.priority)


def available_backends() -> List[Backend]:
    return [b for b in _REGISTRY if b.available]


def backend_by_name(name: str) -> Optional[Backend]:
    for b in _REGISTRY:
        if b.name == name:
            return b
    return None


def all_known_targets() -> Set[str]:
    out: Set[str] = set()
    for b in available_backends():
        out |= b.write
    return out


def backends_for(src_ext: str, to_ext: str) -> List[Backend]:
    src_ext, to_ext = src_ext.lower(), to_ext.lower()
    return [b for b in available_backends() if src_ext in b.read and to_ext in b.write]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
_NAMED = {
    "white": (255, 255, 255, 255),
    "black": (0, 0, 0, 255),
    "red": (255, 0, 0, 255),
    "green": (0, 128, 0, 255),
    "blue": (0, 0, 255, 255),
    "gray": (128, 128, 128, 255),
    "grey": (128, 128, 128, 255),
    "transparent": (0, 0, 0, 0),
}


def _parse_color(s: str) -> Tuple[int, int, int, int]:
    s = (s or "white").strip().lower()
    if s in _NAMED:
        return _NAMED[s]
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
    return (255, 255, 255, 255)


def _parse_size(s: Union[str, int]) -> int:
    if isinstance(s, int):
        return s
    t = s.strip().upper()
    mult = 1
    if t.endswith("KB"):
        mult, t = 1024, t[:-2]
    elif t.endswith("K"):
        mult, t = 1024, t[:-1]
    elif t.endswith("MB"):
        mult, t = 1024**2, t[:-2]
    elif t.endswith("M"):
        mult, t = 1024**2, t[:-1]
    elif t.endswith("GB"):
        mult, t = 1024**3, t[:-2]
    elif t.endswith("G"):
        mult, t = 1024**3, t[:-1]
    elif t.endswith("B"):
        t = t[:-1]
    return int(float(t) * mult)


def _geometry(s: str) -> Tuple[Optional[int], Optional[int], str]:
    s = s.strip().lower()
    fit_hint = ""
    for suf in ("!", "^", ">", "<"):
        if s.endswith(suf):
            fit_hint = suf
            s = s[:-1]
    if s.endswith("%"):
        return (None, None, "percent:" + s[:-1])
    if "x" in s:
        w, h = s.split("x", 1)
        return (int(w) if w else None, int(h) if h else None, fit_hint)
    if s:
        return (int(s), None, fit_hint)
    return (None, None, fit_hint)


def _human_size(nbytes: int) -> str:
    sign = "-" if nbytes < 0 else ""
    nbytes = abs(nbytes)
    size = float(nbytes)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or u == "TB":
            return f"{sign}{int(size)}{u}" if u == "B" else f"{sign}{size:.1f}{u}"
        size /= 1024.0
    return f"{sign}{size:.1f}TB"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 1
    while True:
        cand = parent / f"{stem}_{n}{suffix}"
        if not cand.exists():
            return cand
        n += 1


def _normalize_to(to: str) -> str:
    to = to.lower().lstrip(".")
    if to in ("jpg", "jpeg"):
        return ".jpg"
    if to in ("tif", "tiff"):
        return ".tiff"
    if to in ("heif", "heic"):
        return ".heic"
    return f".{to}"


def _remove_original(path: Path, use_trash: bool) -> None:
    if use_trash:
        try:
            from send2trash import send2trash

            send2trash(str(path))
            return
        except Exception:
            pass
    try:
        path.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Resize math
# ---------------------------------------------------------------------------
def _target_size(w: int, h: int, opts: ConvertOptions) -> Tuple[int, int]:
    if opts.scale is not None:
        return (max(1, int(round(w * opts.scale))), max(1, int(round(h * opts.scale))))
    mw, mh = opts.max_width, opts.max_height
    if mw is None and mh is None:
        return (w, h)
    if opts.fit == "fill":
        return (mw or w, mh or h)
    scales: List[float] = []
    if mw:
        scales.append(mw / w)
    if mh:
        scales.append(mh / h)
    if not scales:
        return (w, h)
    if opts.fit in ("contain", "inside"):
        scale = min(scales)
        if opts.fit == "inside":
            scale = min(scale, 1.0)
    elif opts.fit in ("cover", "outside"):
        scale = max(scales)
        if opts.fit == "outside":
            scale = max(scale, 1.0)
    else:
        scale = min(scales)
    return (max(1, int(round(w * scale))), max(1, int(round(h * scale))))


def _gravity_offset(sw: int, sh: int, cw: int, ch: int, gravity: str) -> Tuple[int, int]:
    g = gravity.lower()
    left, top = (sw - cw) // 2, (sh - ch) // 2
    if "west" in g or g in ("w", "left"):
        left = 0
    if "east" in g or g in ("e", "right"):
        left = sw - cw
    if "north" in g or g in ("n", "top"):
        top = 0
    if "south" in g or g in ("s", "bottom"):
        top = sh - ch
    if g in ("northwest", "nw"):
        left, top = 0, 0
    if g in ("northeast", "ne"):
        left, top = sw - cw, 0
    if g in ("southwest", "sw"):
        left, top = 0, sh - ch
    if g in ("southeast", "se"):
        left, top = sw - cw, sh - ch
    return (max(0, left), max(0, top))


# ---------------------------------------------------------------------------
# Backend: Pillow
# ---------------------------------------------------------------------------
def _pil_probe() -> bool:
    try:
        import PIL  # noqa

        return True
    except ImportError:
        return False


def _pil_exts() -> Set[str]:
    base = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif", ".ico", ".ppm", ".pgm", ".pbm", ".pnm"}
    for mod, exts in (
        ("pillow_heif", {".heic", ".heif"}),
        ("pillow_avif", {".avif"}),
        ("pillow_jxl", {".jxl"}),
    ):
        try:
            __import__(mod)
            base |= exts
        except ImportError:
            pass
    return base


def _pil_resize(img, opts: ConvertOptions):
    from PIL import Image

    if opts.scale is None and opts.max_width is None and opts.max_height is None:
        return img
    w, h = img.size
    nw, nh = _target_size(w, h, opts)
    if (nw, nh) == (w, h) and opts.fit not in ("cover", "outside"):
        return img
    if opts.fit in ("cover", "outside") and opts.max_width and opts.max_height:
        scale = max(opts.max_width / w, opts.max_height / h)
        if opts.fit == "outside":
            scale = max(scale, 1.0)
        sw, sh = int(round(w * scale)), int(round(h * scale))
        img = img.resize((sw, sh), Image.LANCZOS)
        cw, ch = min(opts.max_width, sw), min(opts.max_height, sh)
        left, top = _gravity_offset(sw, sh, cw, ch, opts.gravity)
        return img.crop((left, top, left + cw, top + ch))
    return img.resize((nw, nh), Image.LANCZOS)


def _pil_flatten(img, background: Tuple[int, int, int, int]):
    from PIL import Image

    if img.mode in ("RGBA", "LA"):
        if img.mode == "LA":
            img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, background[:3])
        bg.paste(img, mask=img.split()[-1])
        return bg
    if img.mode == "P":
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, background[:3])
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def _pil_target_mode(img, to_ext: str) -> str:
    if to_ext in (".jpg", ".jpeg", ".bmp"):
        return "RGB"
    if to_ext in (".png", ".webp", ".gif", ".tiff", ".tif", ".avif", ".heic", ".heif", ".jxl", ".ico"):
        if img.mode in ("RGBA", "LA", "P") or "transparency" in img.info:
            return "RGBA"
        return "RGB"
    return img.mode


def _pil_save_kwargs(to_ext: str, quality: int, opts: ConvertOptions) -> Dict[str, Any]:
    if to_ext in (".jpg", ".jpeg"):
        return {"quality": quality, "optimize": True, "progressive": opts.progressive}
    if to_ext == ".webp":
        return {"lossless": True, "method": 4} if opts.lossless else {"quality": quality, "method": 4}
    if to_ext == ".png":
        return {"optimize": True, "compress_level": 9 if opts.lossless else 6}
    if to_ext == ".gif":
        return {"optimize": True}
    if to_ext == ".avif":
        return {"quality": 100 if opts.lossless else quality}
    if to_ext in (".heic", ".heif"):
        return {"quality": 100 if opts.lossless else quality}
    if to_ext == ".jxl":
        return {"quality": 100 if opts.lossless else quality}
    return {}


_META_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".avif", ".heic", ".heif", ".jxl"}
_PIL_FMT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".tif": "TIFF",
    ".webp": "WEBP",
    ".gif": "GIF",
    ".ico": "ICO",
    ".avif": "AVIF",
    ".heic": "HEIF",
    ".heif": "HEIF",
    ".jxl": "JXL",
    ".ppm": "PPM",
}


def _pil_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    from PIL import Image, ImageOps, ImageFile

    ImageFile.LOAD_TRUNCATED_IMAGES = True
    with Image.open(str(src)) as img:
        if opts.auto_orient:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

        # animated path
        if getattr(img, "n_frames", 1) > 1 and to_ext in (".gif", ".webp", ".png"):
            frames, durations = [], []
            for i in range(img.n_frames):
                img.seek(i)
                fr = img.convert("RGBA") if img.mode != "RGBA" else img.copy()
                frames.append(_pil_resize(fr, opts))
                durations.append(img.info.get("duration", 100))
            kw = _pil_save_kwargs(to_ext, quality, opts)
            frames[0].save(
                str(dst),
                format=_PIL_FMT[to_ext],
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                **kw,
            )
            return dst.is_file()

        img = _pil_resize(img, opts)
        target_mode = _pil_target_mode(img, to_ext)
        if img.mode != target_mode:
            if target_mode == "RGB" and img.mode in ("RGBA", "LA", "P"):
                img = _pil_flatten(img, _parse_color(opts.background))
            else:
                img = img.convert(target_mode)

        kw = _pil_save_kwargs(to_ext, quality, opts)
        if to_ext in _META_FORMATS:
            if opts.strip_metadata:
                kw["exif"] = b""
                kw["icc_profile"] = None
            else:
                if img.info.get("icc_profile"):
                    kw["icc_profile"] = img.info["icc_profile"]
                if img.info.get("exif"):
                    kw["exif"] = img.info["exif"]

        fmt = _PIL_FMT.get(to_ext, to_ext[1:].upper())
        try:
            img.save(str(dst), format=fmt, **kw)
        except Exception:
            safe = {k: v for k, v in kw.items() if k in ("quality", "lossless", "method", "optimize")}
            img.save(str(dst), format=fmt, **safe)
    return dst.is_file()


_register("pillow", 20, _pil_exts(), _pil_exts(), _pil_convert, _pil_probe)


# ---------------------------------------------------------------------------
# Backend: cv2
# ---------------------------------------------------------------------------
try:
    import cv2 as _cv2
    import numpy as _np

    _HAS_CV2 = True
except ImportError:
    _cv2, _np, _HAS_CV2 = None, None, False


def _cv2_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    if not _HAS_CV2:
        return False
    flags = _cv2.IMREAD_UNCHANGED
    if opts.auto_orient and to_ext in (".jpg", ".jpeg"):
        flags = _cv2.IMREAD_COLOR
    img = _cv2.imread(str(src), flags)
    if img is None:
        img = _cv2.imread(str(src), _cv2.IMREAD_UNCHANGED)
    if img is None:
        return False
    if opts.max_width or opts.max_height or opts.scale:
        h, w = img.shape[:2]
        nw, nh = _target_size(w, h, opts)
        if (nw, nh) != (w, h):
            interp = _cv2.INTER_AREA if (nw < w or nh < h) else _cv2.INTER_CUBIC
            img = _cv2.resize(img, (nw, nh), interpolation=interp)
    if img.ndim == 3 and img.shape[2] == 4 and to_ext in (".jpg", ".jpeg", ".bmp"):
        b, g, r, a = _cv2.split(img)
        bg = _parse_color(opts.background)
        alpha = a.astype(_np.float32) / 255.0
        b = (b.astype(_np.float32) * alpha + bg[2] * (1 - alpha)).astype(_np.uint8)
        g = (g.astype(_np.float32) * alpha + bg[1] * (1 - alpha)).astype(_np.uint8)
        r = (r.astype(_np.float32) * alpha + bg[0] * (1 - alpha)).astype(_np.uint8)
        img = _cv2.merge((b, g, r))
    params: List[int] = []
    if to_ext in (".jpg", ".jpeg"):
        params = [int(_cv2.IMWRITE_JPEG_QUALITY), quality]
        if opts.progressive:
            params += [int(_cv2.IMWRITE_JPEG_PROGRESSIVE), 1]
    elif to_ext == ".png":
        params = [int(_cv2.IMWRITE_PNG_COMPRESSION), max(0, min(9, (100 - quality) // 10))]
    elif to_ext == ".webp":
        params = [int(_cv2.IMWRITE_WEBP_QUALITY), quality]
    return bool(_cv2.imwrite(str(dst), img, params))


_register(
    "cv2",
    30,
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".jp2", ".exr", ".hdr", ".pbm", ".pgm", ".ppm"},
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".jp2", ".exr", ".hdr", ".pbm", ".pgm", ".ppm"},
    _cv2_convert,
    lambda: _HAS_CV2,
)


# ---------------------------------------------------------------------------
# Backend: skimage
# ---------------------------------------------------------------------------
try:
    from skimage import io as _ski_io, color as _ski_color

    _HAS_SKI = True
except ImportError:
    _ski_io = _ski_color = None
    _HAS_SKI = False


def _ski_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    if not _HAS_SKI:
        return False
    img = _ski_io.imread(str(src))
    if img is None:
        return False
    if opts.max_width or opts.max_height or opts.scale:
        from skimage.transform import resize as _skresize

        h, w = img.shape[:2]
        nw, nh = _target_size(w, h, opts)
        if (nw, nh) != (w, h):
            img = _skresize(img, (nh, nw), anti_aliasing=True, preserve_range=True).astype(img.dtype)
    if img.ndim == 3 and img.shape[-1] == 4 and to_ext in (".jpg", ".jpeg", ".bmp"):
        bg = _parse_color(opts.background)[:3]
        img = _ski_color.rgba2rgb(img, background=bg)
        if img.max() <= 1.0:
            img = (_np.clip(img, 0, 1) * 255).astype(_np.uint8)
        else:
            img = img.astype(_np.uint8)
    kw = {"quality": quality} if to_ext in (".jpg", ".jpeg") else {}
    _ski_io.imsave(str(dst), img, **kw)
    return dst.is_file()


_register(
    "skimage",
    50,
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".ppm", ".pgm", ".pbm"},
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"},
    _ski_convert,
    lambda: _HAS_SKI,
)


# ---------------------------------------------------------------------------
# Backend: pyvips
# ---------------------------------------------------------------------------
def _probe_vips() -> bool:
    try:
        import pyvips  # noqa

        return True
    except Exception:
        return False


def _vips_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    import pyvips

    img = pyvips.Image.new_from_file(str(src), access="sequential", fail_on="error")
    if opts.auto_orient and to_ext not in (".png", ".tiff", ".tif"):
        try:
            img = img.autorot()
        except Exception:
            pass
    h, w = img.height, img.width
    if opts.scale is not None or opts.max_width or opts.max_height:
        if opts.fit in ("cover", "outside") and opts.max_width and opts.max_height:
            scale = max(opts.max_width / w, opts.max_height / h)
            if opts.fit == "outside":
                scale = max(scale, 1.0)
            img = img.resize(scale, vscale=scale, kernel="lanczos3")
            cw, ch = min(opts.max_width, img.width), min(opts.max_height, img.height)
            left = max(0, (img.width - cw) // 2)
            top = max(0, (img.height - ch) // 2)
            img = img.crop(left, top, cw, ch)
        else:
            nw, nh = _target_size(w, h, opts)
            if (nw, nh) != (w, h):
                img = img.resize(nw / w, vscale=nh / h, kernel="lanczos3")
    if opts.strip_metadata:
        try:
            for f in list(img.get_fields()):
                if f.startswith(("exif-", "icc-", "xml-", "png-")):
                    try:
                        img = img.remove(f)
                    except Exception:
                        pass
        except Exception:
            pass
    strip = opts.strip_metadata
    if to_ext in (".jpg", ".jpeg"):
        if img.hasalpha():
            bg = _parse_color(opts.background)
            img = img.flatten(background=bg[:3])
        img.jpegsave(str(dst), Q=quality, strip=strip, optimize_coding=True)
    elif to_ext == ".png":
        img.pngsave(str(dst), compression=9 if opts.lossless else 6, strip=strip)
    elif to_ext == ".webp":
        img.webpsave(str(dst), Q=quality, strip=strip)
    elif to_ext in (".tiff", ".tif"):
        img.tiffsave(str(dst), compression="jpeg" if quality < 100 else "none", Q=quality, strip=strip)
    elif to_ext in (".heic", ".heif"):
        img.heifsave(str(dst), Q=quality, strip=strip)
    elif to_ext == ".avif":
        img.heifsave(str(dst), Q=quality, compression="av1", strip=strip)
    else:
        img.write_to_file(str(dst), Q=quality)
    return dst.is_file()


_register(
    "vips",
    10,
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".gif",
        ".heic",
        ".heif",
        ".avif",
        ".svg",
        ".ppm",
        ".pgm",
        ".exr",
        ".hdr",
        ".jp2",
        ".jxl",
        ".fits",
    },
    {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jp2", ".jxl", ".exr", ".hdr"},
    _vips_convert,
    _probe_vips,
)


# ---------------------------------------------------------------------------
# Backend: Wand (ImageMagick bindings)
# ---------------------------------------------------------------------------
def _probe_wand() -> bool:
    try:
        from wand.image import Image as _WI  # noqa

        return True
    except Exception:
        return False


def _wand_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    from wand.image import Image as WImage
    from wand.color import Color

    with WImage(filename=str(src)) as img:
        if opts.auto_orient:
            try:
                img.auto_orient()
            except Exception:
                pass
        if opts.max_width or opts.max_height:
            geom = f"{opts.max_width or ''}x{opts.max_height or ''}"
            mod = "^" if opts.fit == "cover" else "!" if opts.fit == "fill" else ">"
            try:
                img.transform(resize=geom + mod)
            except Exception:
                pass
        if opts.strip_metadata:
            try:
                img.strip()
            except Exception:
                pass
        try:
            img.background_color = Color(opts.background)
        except Exception:
            pass
        if to_ext in (".jpg", ".jpeg"):
            if img.alpha_channel:
                try:
                    img.alpha_channel = "remove"
                except Exception:
                    pass
            img.format = "jpeg"
            img.compression_quality = max(1, min(100, quality))
        elif to_ext == ".png":
            img.format = "png"
        elif to_ext == ".webp":
            img.format = "webp"
            img.compression_quality = max(1, min(100, quality))
        elif to_ext in (".tiff", ".tif"):
            img.format = "tiff"
        else:
            img.format = to_ext[1:]
            try:
                img.compression_quality = max(1, min(100, quality))
            except Exception:
                pass
        img.save(filename=str(dst))
    return dst.is_file()


_register(
    "wand",
    40,
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".gif",
        ".heic",
        ".heif",
        ".avif",
        ".pdf",
        ".svg",
        ".eps",
        ".ppm",
        ".pgm",
        ".pbm",
        ".exr",
        ".hdr",
        ".jp2",
        ".jxl",
        ".ico",
        ".tga",
        ".dds",
    },
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".gif",
        ".heic",
        ".heif",
        ".avif",
        ".jp2",
        ".jxl",
        ".ico",
        ".tga",
        ".ppm",
        ".pgm",
        ".exr",
    },
    _wand_convert,
    _probe_wand,
)


# ---------------------------------------------------------------------------
# Backend: ImageMagick (subprocess)
# ---------------------------------------------------------------------------
def _probe_magick() -> bool:
    return bool(shutil.which("magick") or shutil.which("convert"))


def _magick_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    cmd = shutil.which("magick") or shutil.which("convert")
    if not cmd:
        return False
    args = [cmd, str(src)]
    if opts.auto_orient:
        args.append("-auto-orient")
    if opts.max_width or opts.max_height:
        geom = f"{opts.max_width or ''}x{opts.max_height or ''}"
        mod = "^" if opts.fit == "cover" else "!" if opts.fit == "fill" else ">"
        args += ["-resize", geom + mod]
    if opts.strip_metadata:
        args.append("-strip")
    args += [
        "-background",
        opts.background,
        "-alpha",
        "remove",
        "-alpha",
        "off",
        "-quality",
        str(max(1, min(100, quality))),
        str(dst),
    ]
    try:
        subprocess.run(args, check=True, capture_output=True, timeout=180)
        return dst.is_file()
    except Exception:
        return False


_register(
    "imagemagick",
    45,
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".gif",
        ".heic",
        ".heif",
        ".avif",
        ".pdf",
        ".svg",
        ".eps",
        ".ppm",
        ".pgm",
        ".pbm",
        ".exr",
        ".hdr",
        ".jp2",
        ".jxl",
        ".ico",
        ".tga",
        ".dds",
        ".psd",
    },
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".gif",
        ".heic",
        ".heif",
        ".avif",
        ".jp2",
        ".jxl",
        ".ico",
        ".tga",
        ".ppm",
        ".pgm",
        ".exr",
    },
    _magick_convert,
    _probe_magick,
)


# ---------------------------------------------------------------------------
# Backend: ffmpeg
# ---------------------------------------------------------------------------
def _probe_ffmpeg() -> bool:
    return bool(shutil.which("ffmpeg"))


def _ffmpeg_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    cmd = shutil.which("ffmpeg")
    if not cmd:
        return False
    vf: List[str] = []
    if opts.max_width or opts.max_height:
        w = opts.max_width or -1
        h = opts.max_height or -1
        vf.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease")
    args = [cmd, "-y", "-loglevel", "error", "-i", str(src)]
    if vf:
        args += ["-vf", ",".join(vf)]
    if to_ext in (".jpg", ".jpeg"):
        args += ["-q:v", str(max(2, 31 - quality // 3))]
    elif to_ext == ".webp":
        args += ["-quality", str(quality)]
    args.append(str(dst))
    try:
        subprocess.run(args, check=True, capture_output=True, timeout=180)
        return dst.is_file()
    except Exception:
        return False


_register(
    "ffmpeg",
    60,
    {
        ".mp4",
        ".mkv",
        ".mov",
        ".avi",
        ".webm",
        ".gif",
        ".exr",
        ".hdr",
        ".dpx",
        ".tga",
        ".qoi",
        ".jxl",
        ".avif",
        ".heic",
        ".heif",
        ".mxf",
        ".vob",
        ".m4v",
        ".mts",
        ".3gp",
        ".flv",
        ".wmv",
    },
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif", ".exr", ".tga"},
    _ffmpeg_convert,
    _probe_ffmpeg,
)


# ---------------------------------------------------------------------------
# Backend: pymupdf (PDF → image)
# ---------------------------------------------------------------------------
def _probe_pymupdf() -> bool:
    try:
        import fitz  # noqa

        return True
    except ImportError:
        return False


def _pymupdf_convert(src: Path, dst: Path, to_ext: str, quality: int, opts: ConvertOptions) -> bool:
    import fitz
    from PIL import Image

    doc = fitz.open(str(src))
    try:
        if doc.page_count == 0:
            return False
        page = doc[0]
        zoom = 2.0
        if opts.max_width:
            zoom = opts.max_width / page.rect.width
        elif opts.max_height:
            zoom = opts.max_height / page.rect.height
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        with Image.open(io.BytesIO(pix.tobytes("png"))) as img:
            img = _pil_resize(img, opts)
            tm = _pil_target_mode(img, to_ext)
            if img.mode != tm:
                img = img.convert(tm)
            kw = _pil_save_kwargs(to_ext, quality, opts)
            fmt = _PIL_FMT.get(to_ext, to_ext[1:].upper())
            img.save(str(dst), fmt, **kw)
    finally:
        doc.close()
    return dst.is_file()


_register(
    "pymupdf",
    5,
    {".pdf"},
    {".png", ".jpg", ".jpeg", ".webp", ".bmp"},
    _pymupdf_convert,
    _probe_pymupdf,
)


# ---------------------------------------------------------------------------
# THE FALLBACK ENGINE
# ---------------------------------------------------------------------------
def _try_backends_to_file(
    src: Path,
    dst: Path,
    to_ext: str,
    quality: int,
    opts: ConvertOptions,
    preferred: Optional[str] = None,
) -> Tuple[bool, Optional[str], str]:
    """Try every viable backend until one succeeds.

    Never raises. Never touches the source. Writes each attempt to a
    unique `.part.<backend>` sibling of `dst`, only moving it into
    place once a non-empty output is confirmed.
    """
    src_ext = src.suffix.lower()
    candidates = backends_for(src_ext, to_ext)

    if preferred:
        pref = backend_by_name(preferred)
        if pref and pref.available and pref in candidates:
            candidates = [pref] + [b for b in candidates if b.name != pref.name]
        elif pref and pref.available:
            candidates = candidates + [pref]

    if not candidates:
        candidates = available_backends()

    errors: List[str] = []
    for b in candidates:
        tmp = dst.with_name(f"{dst.name}.part.{b.name}")
        try:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
            ok = bool(b.fn(src, tmp, to_ext, quality, opts))
        except Exception as exc:
            errors.append(f"{b.name}: {exc}")
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass
            continue

        if ok and tmp.is_file() and tmp.stat().st_size > 0:
            try:
                if dst.exists():
                    dst.unlink()
                tmp.replace(dst)
                return (True, b.name, "")
            except OSError as exc:
                errors.append(f"{b.name}: move failed: {exc}")
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass
                continue
        else:
            errors.append(f"{b.name}: produced no output")
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass

    return (False, None, "; ".join(errors) or "no backend could convert this file")


def _encode_with_target_size(
    src: Path,
    dst: Path,
    to_ext: str,
    base_quality: int,
    opts: ConvertOptions,
    preferred: Optional[str],
) -> Tuple[bool, Optional[str], str]:
    if not opts.target_size:
        return _try_backends_to_file(src, dst, to_ext, base_quality, opts, preferred)

    tmp_hi = dst.with_name(dst.name + ".hi")
    ok, backend, err = _try_backends_to_file(src, tmp_hi, to_ext, base_quality, opts, preferred)
    if not ok:
        return (False, None, err)
    if tmp_hi.stat().st_size <= opts.target_size:
        try:
            if dst.exists():
                dst.unlink()
            tmp_hi.replace(dst)
            return (True, backend, "")
        except OSError as exc:
            return (False, None, f"move failed: {exc}")
    try:
        tmp_hi.unlink()
    except OSError:
        pass

    lo = max(1, opts.min_quality)
    hi = max(lo, base_quality - 1)
    best: Optional[Path] = None
    used_backend = backend
    while lo <= hi:
        mid = (lo + hi) // 2
        tmp = dst.with_name(f"{dst.name}.q{mid}")
        ok, u, err = _try_backends_to_file(src, tmp, to_ext, mid, opts, used_backend)
        if not ok:
            return (False, None, f"q={mid}: {err}")
        used_backend = u or used_backend
        if tmp.stat().st_size <= opts.target_size:
            if best is not None:
                try:
                    best.unlink()
                except OSError:
                    pass
            best = tmp
            lo = mid + 1
        else:
            try:
                tmp.unlink()
            except OSError:
                pass
            hi = mid - 1

    if best is None:
        tmp = dst.with_name(dst.name + ".min")
        ok, u, err = _try_backends_to_file(src, tmp, to_ext, max(1, opts.min_quality), opts, used_backend)
        if not ok:
            return (False, None, f"min-q: {err}")
        best = tmp
        used_backend = u or used_backend

    try:
        if dst.exists():
            dst.unlink()
        best.replace(dst)
    except OSError as exc:
        return (False, None, f"move failed: {exc}")
    return (True, used_backend, "")


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------
@dataclass
class FileResult:
    src: Path
    out: Optional[Path]
    status: str  # ok | skip | error | predict
    backend: Optional[str] = None
    before: Optional[int] = None
    after: Optional[int] = None
    message: str = ""


def _would_change(src: Path, to_ext: str, opts: ConvertOptions) -> bool:
    if src.suffix.lower() != to_ext:
        return True
    if opts.max_width or opts.max_height or opts.scale or opts.target_size:
        return True
    return False


def _determine_dst(src: Path, to_ext: str, out_dir: Optional[Path], preserve_tree: bool) -> Path:
    if out_dir is None:
        return src.with_suffix(to_ext)
    if preserve_tree:
        try:
            rel = src.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            rel = Path(src.name)
        return out_dir / rel.with_suffix(to_ext)
    return out_dir / (src.stem + to_ext)


def process_file(
    src: Path,
    to_ext: str,
    opts: ConvertOptions,
    out_dir: Optional[Path] = None,
    preserve_tree: bool = True,
    keep: bool = False,
    force: bool = False,
    no_clobber: bool = True,
    backup: bool = False,
    trash: bool = False,
    preferred_backend: Optional[str] = None,
    predict: bool = False,
) -> FileResult:
    src = Path(src)
    if not src.is_file():
        return FileResult(src, None, "skip", message="not a file")

    if not force and not _would_change(src, to_ext, opts):
        return FileResult(src, None, "skip", message="already target format; use --force to re-encode")

    before = src.stat().st_size
    dst = _determine_dst(src, to_ext, out_dir, preserve_tree)
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    if dst.exists() and no_clobber and not force:
        dst = _unique_path(dst)

    if predict:
        tmp = dst.with_name(dst.name + ".predict")
        ok, used, err = _encode_with_target_size(src, tmp, to_ext, opts.quality, opts, preferred_backend)
        if not ok:
            return FileResult(src, None, "error", message=err)
        size = tmp.stat().st_size
        try:
            tmp.unlink()
        except OSError:
            pass
        return FileResult(
            src, dst, "predict", used, before, size, message=f"{_human_size(before)} → {_human_size(size)} (predicted)"
        )

    ok, used, err = _encode_with_target_size(src, dst, to_ext, opts.quality, opts, preferred_backend)
    if not ok:
        # FALLBACK CONTRACT: source untouched, run continues.
        return FileResult(src, None, "error", message=err)

    after = dst.stat().st_size if dst.is_file() else 0

    if not keep:
        if backup:
            bak = src.with_name(src.name + ".bak")
            try:
                if not bak.exists():
                    shutil.copy2(src, bak)
            except OSError:
                pass
        _remove_original(src, trash)

    return FileResult(src, dst, "ok", used, before, after, message=f"{_human_size(before)} → {_human_size(after)}")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def collect_images(
    paths: Sequence[Path],
    exts: Sequence[str],
    recursive: bool,
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
) -> List[Path]:
    ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts}
    found: List[Path] = []

    def accept(p: Path) -> bool:
        if p.suffix.lower() not in ext_set:
            return False
        name = p.name
        if include and not any(fnmatch.fnmatch(name, pat) for pat in include):
            return False
        if exclude and any(fnmatch.fnmatch(name, pat) for pat in exclude):
            return False
        try:
            sz = p.stat().st_size
        except OSError:
            return False
        if min_size is not None and sz < min_size:
            return False
        if max_size is not None and sz > max_size:
            return False
        return True

    for p in paths:
        try:
            p = p.resolve()
        except OSError:
            continue
        if p.is_file():
            if accept(p):
                found.append(p)
        elif p.is_dir():
            if recursive:
                for root, _, files in os.walk(p, followlinks=False):
                    for name in files:
                        fp = Path(root) / name
                        if accept(fp):
                            found.append(fp)
            else:
                try:
                    with os.scandir(p) as it:
                        for entry in it:
                            if entry.is_file(follow_symlinks=False):
                                fp = Path(entry.path)
                                if accept(fp):
                                    found.append(fp)
                except OSError:
                    pass
    return found


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
_PRESETS: Dict[str, Dict[str, Any]] = {
    "web": {
        "to": "webp",
        "quality": 82,
        "max_width": 1920,
        "max_height": 1920,
        "fit": "contain",
        "strip_metadata": True,
    },
    "email": {
        "to": "jpg",
        "quality": 80,
        "max_width": 1280,
        "max_height": 1280,
        "fit": "contain",
        "strip_metadata": True,
    },
    "thumb": {"to": "jpg", "quality": 80, "max_width": 256, "max_height": 256, "fit": "cover", "strip_metadata": True},
    "social": {
        "to": "jpg",
        "quality": 85,
        "max_width": 1080,
        "max_height": 1080,
        "fit": "cover",
        "strip_metadata": True,
    },
    "archive": {"to": "png", "lossless": True, "strip_metadata": False},
    "print": {"to": "tiff", "quality": 95, "strip_metadata": False},
}


def _apply_preset(args: argparse.Namespace) -> None:
    if not args.preset:
        return
    p = _PRESETS.get(args.preset)
    if not p:
        return
    for k, v in p.items():
        if k == "to":
            if args.to is None:
                args.to = v
        elif k in ("max_width", "max_height", "fit", "quality", "lossless", "strip_metadata"):
            if getattr(args, k, None) is None:
                setattr(args, k, v)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    installed = " ".join(b.name for b in available_backends()) or "(none)"
    p = argparse.ArgumentParser(
        description="Convert images to a target format; fall back across backends on failure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"installed backends: {installed}",
    )
    p.add_argument("paths", nargs="*", type=Path, help="files or directories (default: current dir)")
    p.add_argument(
        "-b", "--backend", default=None, metavar="NAME", help="prefer this backend; still falls back if it fails"
    )
    p.add_argument(
        "--backends", default=None, metavar="LIST", help="comma-separated preferred backends (fallback still applies)"
    )
    p.add_argument("-o", "--to", default=None, metavar="EXT")
    p.add_argument("-j", "--jobs", type=int, default=1, metavar="N", help="parallel workers (0 = cpu_count)")
    p.add_argument("-q", "--quality", type=int, default=None, metavar="Q")
    p.add_argument("-r", "--recursive", action="store_true")
    p.add_argument("-k", "--keep", action="store_true")
    p.add_argument("-f", "--force", action="store_true", help="overwrite / reconvert even if already target format")
    p.add_argument("--no-clobber", dest="no_clobber", action="store_true", default=True)
    p.add_argument("--overwrite", dest="no_clobber", action="store_false")
    p.add_argument("--backup", action="store_true")
    p.add_argument("--trash", action="store_true")
    p.add_argument("-e", "--ext", action="append", default=None, metavar="EXT")
    p.add_argument("--include", action="append", default=None, metavar="GLOB")
    p.add_argument("--exclude", action="append", default=None, metavar="GLOB")
    p.add_argument("--min-size", default=None, metavar="SIZE")
    p.add_argument("--max-size", default=None, metavar="SIZE")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--predict", action="store_true", help="encode-only to predict output size (no writes)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--progress", action="store_true")
    p.add_argument("--list-targets", action="store_true")
    p.add_argument("--list-backends", action="store_true")
    p.add_argument("--benchmark", action="store_true", help="encode the first file with each backend and compare")
    p.add_argument("-d", "--output-dir", type=Path, default=None, metavar="DIR")
    p.add_argument("--preserve-tree", dest="preserve_tree", action="store_true", default=True)
    p.add_argument("--flat", dest="preserve_tree", action="store_false")
    p.add_argument("--resize", default=None, metavar="WxH")
    p.add_argument("--max-width", type=int, default=None, metavar="N")
    p.add_argument("--max-height", type=int, default=None, metavar="N")
    p.add_argument("--scale", type=float, default=None, metavar="FACTOR")
    p.add_argument("--fit", default=None, choices=["contain", "cover", "fill", "inside", "outside"])
    p.add_argument(
        "--gravity",
        default=None,
        choices=["center", "north", "south", "east", "west", "northwest", "northeast", "southwest", "southeast"],
    )
    p.add_argument("--background", default=None, metavar="COLOR")
    p.add_argument("--auto-orient", dest="auto_orient", action="store_true", default=None)
    p.add_argument("--no-auto-orient", dest="auto_orient", action="store_false")
    p.add_argument("--strip-metadata", dest="strip_metadata", action="store_true", default=None)
    p.add_argument("--keep-metadata", dest="strip_metadata", action="store_false")
    p.add_argument("--lossless", action="store_true")
    p.add_argument("--progressive", action="store_true")
    p.add_argument("--target-size", default=None, metavar="SIZE")
    p.add_argument("--min-quality", type=int, default=30, metavar="Q")
    p.add_argument("--preset", default=None, choices=list(_PRESETS.keys()))
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def _resolve_defaults(args: argparse.Namespace) -> None:
    _apply_preset(args)
    if args.to is None:
        args.to = "jpg"
    if args.quality is None:
        ext = _normalize_to(args.to)
        args.quality = (
            85
            if ext in (".jpg", ".jpeg")
            else 82
            if ext == ".webp"
            else 60
            if ext in (".avif", ".heic", ".heif")
            else 80
            if ext == ".jxl"
            else 90
        )
    if args.fit is None:
        args.fit = "contain"
    if args.gravity is None:
        args.gravity = "center"
    if args.background is None:
        args.background = "white"
    if args.auto_orient is None:
        args.auto_orient = True
    if args.strip_metadata is None:
        args.strip_metadata = True
    if args.resize:
        w, h, hint = _geometry(args.resize)
        if hint.startswith("percent:"):
            args.scale = float(hint.split(":", 1)[1]) / 100.0
        else:
            if w is not None:
                args.max_width = w
            if h is not None:
                args.max_height = h
            if hint == "!":
                args.fit = "fill"
            elif hint == "^":
                args.fit = "cover"
            elif hint == ">":
                args.fit = "inside"
            elif hint == "<":
                args.fit = "outside"


def _build_opts(args: argparse.Namespace) -> ConvertOptions:
    return ConvertOptions(
        quality=max(1, min(100, args.quality)),
        max_width=args.max_width,
        max_height=args.max_height,
        scale=args.scale,
        fit=args.fit,
        gravity=args.gravity,
        background=args.background,
        auto_orient=args.auto_orient,
        strip_metadata=args.strip_metadata,
        lossless=args.lossless,
        progressive=args.progressive,
        target_size=_parse_size(args.target_size) if args.target_size else None,
        min_quality=max(1, min(100, args.min_quality)),
    )


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------
def _benchmark(files: List[Path], to_ext: str, opts: ConvertOptions) -> None:
    if not files:
        print("no files to benchmark")
        return
    src = files[0]
    print(f"benchmarking on {src.name} → {to_ext}")
    print(f"{'backend':<14}{'status':<10}{'size':>10}{'time':>10}")
    with tempfile.TemporaryDirectory() as td:
        for b in available_backends():
            tmp = Path(td) / f"bench.{b.name}{to_ext}"
            t0 = time.time()
            try:
                ok = bool(b.fn(src, tmp, to_ext, opts.quality, opts))
            except Exception as exc:
                print(f"{b.name:<14}{'error':<10}{str(exc)[:40]:>10}")
                continue
            dt = time.time() - t0
            if ok and tmp.is_file():
                print(f"{b.name:<14}{'ok':<10}{_human_size(tmp.stat().st_size):>10}{dt:>9.3f}s")
            else:
                print(f"{b.name:<14}{'failed':<10}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
_DEFAULT_INPUT_EXTS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".gif",
    ".heic",
    ".heif",
    ".avif",
    ".jxl",
    ".jp2",
    ".ico",
    ".svg",
    ".pdf",
    ".ppm",
    ".pgm",
    ".pbm",
    ".exr",
    ".hdr",
    ".qoi",
    ".tga",
    ".dds",
    ".psd",
]


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    if args.list_backends:
        print("backends:")
        for b in _REGISTRY:
            print(f"  {b.name:<14} available={'yes' if b.available else 'no':<3} priority={b.priority}")
        return 0

    _resolve_defaults(args)
    to_ext = _normalize_to(args.to)
    opts = _build_opts(args)

    if args.list_targets:
        print(f"target extensions: {' '.join(sorted(all_known_targets())) or '(none)'}")
        return 0

    jobs = args.jobs or (os.cpu_count() or 1)
    jobs = max(1, jobs)

    exts = list(_DEFAULT_INPUT_EXTS)
    if args.ext:
        exts.extend(e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext)
    exts = list(dict.fromkeys(exts))

    search_paths = args.paths if args.paths else [Path.cwd()]
    files = collect_images(
        search_paths,
        exts,
        args.recursive,
        include=args.include or [],
        exclude=args.exclude or [],
        min_size=_parse_size(args.min_size) if args.min_size else None,
        max_size=_parse_size(args.max_size) if args.max_size else None,
    )

    if args.benchmark:
        _benchmark(files, to_ext, opts)
        return 0

    if not files:
        print("no images found")
        return 0

    if args.dry_run and not args.predict:
        for f in files:
            print(f)
        print(f"\n{len(files)} file(s) would be processed → {to_ext}")
        return 0

    preferred = args.backend
    if not preferred and args.backends:
        for name in args.backends.split(","):
            b = backend_by_name(name.strip())
            if b and b.available:
                preferred = b.name
                break

    def worker(f: Path) -> FileResult:
        try:
            return process_file(
                f,
                to_ext,
                opts,
                out_dir=args.output_dir,
                preserve_tree=args.preserve_tree,
                keep=args.keep,
                force=args.force,
                no_clobber=args.no_clobber,
                backup=args.backup,
                trash=args.trash,
                preferred_backend=preferred,
                predict=args.predict,
            )
        except Exception as exc:
            return FileResult(f, None, "error", message=f"unhandled: {exc}")

    results: List[FileResult] = []
    progress = None
    if args.progress:
        try:
            from tqdm import tqdm

            progress = tqdm(total=len(files), unit="file")
        except ImportError:
            progress = None

    if jobs == 1:
        for f in files:
            r = worker(f)
            results.append(r)
            if args.verbose and not args.quiet:
                print(f"{r.status}: {r.src.name} → {r.out.name if r.out else '-'} [{r.backend or '?'}] {r.message}")
            if progress:
                progress.update(1)
    else:
        if sys.version_info >= (3, 14) and hasattr(concurrent.futures, "InterpreterPoolExecutor"):
            Executor = concurrent.futures.InterpreterPoolExecutor
        else:
            Executor = concurrent.futures.ProcessPoolExecutor
        try:
            with Executor(max_workers=jobs) as ex:
                futs = {ex.submit(worker, f): f for f in files}
                for fut in concurrent.futures.as_completed(futs):
                    try:
                        r = fut.result()
                    except Exception as exc:
                        r = FileResult(futs[fut], None, "error", message=str(exc))
                    results.append(r)
                    if args.verbose and not args.quiet:
                        print(
                            f"{r.status}: {r.src.name} → {r.out.name if r.out else '-'} "
                            f"[{r.backend or '?'}] {r.message}"
                        )
                    if progress:
                        progress.update(1)
        except Exception:
            done = {r.src for r in results}
            for f in files:
                if f in done:
                    continue
                r = worker(f)
                results.append(r)
                if progress:
                    progress.update(1)

    if progress:
        progress.close()

    ok = sum(1 for r in results if r.status == "ok")
    err = sum(1 for r in results if r.status == "error")
    skip = sum(1 for r in results if r.status == "skip")
    pred = sum(1 for r in results if r.status == "predict")

    total_saved = sum((r.before - r.after) for r in results if r.before is not None and r.after is not None)

    if args.json:
        payload = {
            "summary": {"ok": ok, "errors": err, "skipped": skip, "predicted": pred, "space_change": total_saved},
            "results": [
                {
                    "src": str(r.src),
                    "out": str(r.out) if r.out else None,
                    "status": r.status,
                    "backend": r.backend,
                    "before": r.before,
                    "after": r.after,
                    "message": r.message,
                }
                for r in results
            ],
        }
        print(json.dumps(payload, indent=2))
        return 1 if err else 0

    if not args.verbose and not args.quiet:
        for r in results:
            if r.status == "error":
                print(f"error: {r.src.name} ({r.message})", file=sys.stderr)

    print(f"to={to_ext}  processed={ok}  errors={err}  skipped={skip}" + (f"  predicted={pred}" if pred else ""))
    if total_saved:
        label = "predicted space change" if pred else "space change"
        print(f"{label}: {_human_size(total_saved)}")

    # Per-file failures do not stop the run; exit code reflects totals.
    return 1 if err else 0


if __name__ == "__main__":
    raise SystemExit(main())
