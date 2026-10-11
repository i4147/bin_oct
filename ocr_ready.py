#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that an AI coding agent could use to recreate a Python OCR batch-processing script. The prompt should describe purpose, inputs/outputs, dependencies, preprocessing logic, multiprocessing, fallback behavior, error handling, and usage, without including code or snippets.

Note: the provided code is truncated mid-statement (inside the CLAHE setup), so the prompt below describes the intended behavior as far as it is evident, and leaves the unseen remainder to reasonable inference.

---

Create a Python 3 command-line OCR (optical character recognition) batch-processing script designed to run on Android via Termux (shebang targets the Termux Python path). The script scans a directory of images, preprocesses each image to improve text recognition, runs Tesseract OCR on it in parallel, and writes the extracted text out.

**Purpose**
Automate OCR across many image files, producing cleaned-up, higher-accuracy text extractions by applying image enhancement and deskewing before recognition.

**Inputs**
- Image files in the current working directory (treated as the base directory), filtered by extension: .jpg, .jpeg, .png, .tiff, .bmp, .webp (case-insensitive matching is recommended).
- Optional command-line arguments for input/output paths and options may be added, but the default behavior is to process the current directory.

**Outputs**
- For each successfully processed image, write the recognized text to an output file (e.g., a .txt file with the same base name) or aggregate results in a clearly structured form.
- Log progress, warnings, and errors to the console using the loguru logging library (informational messages for progress, warnings for images that cannot be read, errors for OCR or processing failures).

**Dependencies**
- numpy for array operations.
- pytesseract as the Python wrapper for the Tesseract OCR engine (the Tesseract binary must be installed and available on the system path).
- loguru for logging.
- OpenCV (cv2) is optional. Import it inside a try block; set a boolean flag HAS_CV2 to True on success. On ImportError, set the flag to False and fall back to Pillow (PIL) with its Image, ImageEnhance, and ImageFilter modules.
- Standard library: multiprocessing, sys, pathlib.Path, typing (Any, Union), and `from __future__ import annotations`.

**Constants and configuration**
- A set of supported extensions as listed above.
- BASE_DIR set to the current working directory at import time.
- POOL_SIZE set to 8 worker processes.
- A type alias for an image that is either a NumPy array or a PIL Image.

**Key logic**

1. **Deskew function**: Takes a grayscale/binary image array. When OpenCV is available, find the coordinates of nonzero (foreground) pixels, compute the minimum-area bounding rectangle angle, normalize the angle (if below -45 degrees, add 90 degrees before negating; otherwise negate), compute the rotation matrix around the image center, and apply the rotation with cubic interpolation and replicate border mode. If there are no foreground pixels, return the image unchanged. When OpenCV is unavailable, return the image unchanged.

2. **OpenCV preprocessing pipeline** (preprocess_image_cv2): Read the image from a path using OpenCV. If reading fails (returns None), return None so the caller can skip the file. Otherwise:
   - Convert BGR to grayscale.
   - Upscale by 2x in both dimensions using cubic interpolation to help Tesseract on small text.
   - Apply non-local means denoising (filter strength 30, template window 7, search window 21).
   - Apply CLAHE (contrast-limited adaptive histogram equalization) to boost local contrast; the clip limit and tile grid size are configured in the truncated portion.
   - Subsequent steps (not shown) are expected to include adaptive or Otsu thresholding to binarize, possibly morphological cleanup, and deskewing via the deskew function before returning a NumPy array for OCR.

3. **Pillow fallback preprocessing**: When OpenCV is not available, load the image with PIL, convert to grayscale, optionally upscale, apply enhancement (e.g., contrast via ImageEnhance), apply filters such as sharpening or median filtering from ImageFilter, and return a PIL Image.

4. **OCR step**: Pass the preprocessed image to pytesseract (image_to_string), returning the text. Handle exceptions from pytesseract (for example, if the Tesseract binary is missing or the language data is unavailable) and log them without crashing the whole batch.

5. **Parallel processing**: Use multiprocessing.Pool with POOL_SIZE workers to process the list of discovered image files concurrently. Each worker handles one file end to end: preprocess, OCR, and save or return the result. Guard the main entry point with the `if __name__ == "__main__":` idiom and ensure the multiprocessing start is safe for the platform (e.g., call freeze-support style setup if needed).

6. **File discovery**: Scan BASE_DIR (non-recursively unless specified) for files whose suffix (lowercased) is in the supported set. Sort results for deterministic ordering.

**Error handling and edge cases**
- Unreadable or corrupt image files: log a warning and skip, returning None rather than raising.
- Empty foreground during deskew: return the image unchanged.
- Missing OpenCV: transparently switch to the Pillow path; log which backend is in use.
- Missing Tesseract binary or language packs: log a clear error and continue or exit gracefully.
- Empty OCR output: still record the result (possibly as empty) and log it.
- Non-supported extensions are ignored silently.
- Ensure per-file exceptions in worker processes are caught so one failure does not abort the pool.
- Exit with a nonzero status code via sys.exit on fatal startup problems (e.g., no images found is a warning, not necessarily a fatal error).

**Execution and usage**
- Run as a script: `python <scriptname>.py`, executed from the directory containing the images (or with an optional path argument if implemented).
- The shebang line uses the Termux Python interpreter path, so the script should be executable with chmod +x.
- Results appear as text files or aggregated output in the working directory, with progress logged to the console.

**Style expectations**
- Use type hints throughout (including `from __future__ import annotations`), concise functions with docstrings, and loguru-based logging rather than print statements.
- Keep the module importable without side effects other than constant setup and the optional OpenCV import check.
---"""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path
from typing import Any, Union

import numpy as np
import pytesseract
from loguru import logger

try:
    import cv2

    HAS_CV2: bool = True
except ImportError:
    HAS_CV2 = False
    from PIL import Image, ImageEnhance, ImageFilter
SUPPORTED_EXT: set[str] = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"}
BASE_DIR: Path = Path.cwd()
POOL_SIZE: int = 8
ImageType = Union[np.ndarray, "Image.Image"]


def deskew(image: np.ndarray) -> np.ndarray:
    if HAS_CV2:
        coords = np.column_stack(np.where(image > 0))
        if coords.size == 0:
            return image
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return image


def preprocess_image_cv2(img_path: Path) -> np.ndarray | None:
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return deskew(cleaned)


def preprocess_image_pillow(img_path: Path) -> Image.Image | None:
    try:
        img = Image.open(str(img_path))
        if img.mode != "L":
            img = img.convert("L")
        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.Resampling.BICUBIC)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.point(lambda p: 255 if p > 128 else 0)
        img = img.filter(ImageFilter.SHARPEN)
        return img
    except Exception:
        return None


def preprocess_image(img_path: Path) -> ImageType | None:
    if HAS_CV2:
        return preprocess_image_cv2(img_path)
    return preprocess_image_pillow(img_path)


def should_skip(path: Path) -> bool:
    return path.suffix.lower() not in SUPPORTED_EXT


def save_processed_image(img: ImageType, img_path: Path) -> None:
    if HAS_CV2 and isinstance(img, np.ndarray):
        cv2.imwrite(str(img_path), img)
    elif not HAS_CV2 and not isinstance(img, np.ndarray):
        img.save(str(img_path))
    else:
        msg = "Unsupported image format"
        raise ValueError(msg)


def process_single_image(image_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(image_path),
        "success": False,
        "error": None,
        "size_before": 0,
        "size_after": 0,
    }
    try:
        result["size_before"] = image_path.stat().st_size
        processed = preprocess_image(image_path)
        if processed is None:
            result["error"] = "Failed to process image"
            return result
        save_processed_image(processed, image_path)
        txt_path = image_path.with_suffix(".txt")
        text = pytesseract.image_to_string(processed, config="--oem 1 --psm 6")
        txt_path.write_text(text, encoding="utf-8")
        result["size_after"] = image_path.stat().st_size
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def get_image_files() -> list[Path]:
    image_files: list[Path] = []
    for path in BASE_DIR.rglob("*"):
        if path.is_file() and not should_skip(path):
            image_files.append(path)
    return image_files


def process() -> None:
    if not HAS_CV2:
        logger.warning("OpenCV not found, using Pillow as fallback (limited functionality)")
    image_files = get_image_files()
    total_images = len(image_files)
    if total_images == 0:
        print("No images found to process.")
        return
    print(f"📊 Found {total_images} images to process")
    print(f"⚡ Using {POOL_SIZE} workers for parallel processing")
    print("🔄 Processing images in-place...\n")
    processed_count = 0
    error_count = 0
    total_before = 0
    total_after = 0
    pool = multiprocessing.Pool(processes=POOL_SIZE)
    try:
        async_results = [(path, pool.apply_async(process_single_image, (path,))) for path in image_files]
        for path, async_result in async_results:
            try:
                result = async_result.get()
                if result["success"]:
                    processed_count += 1
                    total_before += result["size_before"]
                    total_after += result["size_after"]
                    status = "✅"
                else:
                    error_count += 1
                    status = "❌"
                relative = path.relative_to(BASE_DIR)
                print(f"{status} [{processed_count + error_count}/{total_images}] {relative}")
                if result.get("error"):
                    logger.warning(f"   ⚠️ Error: {result['error']}")
            except Exception as e:
                error_count += 1
                logger.error(f"❌ [{processed_count + error_count}/{total_images}] {path.name}: {e}")
    finally:
        pool.close()
        pool.join()
    print("=" * 40)
    print("📊 Processing Summary:")
    print(f"   ✅ Successfully processed: {processed_count} images")
    print(f"   ❌ Errors: {error_count} images")
    print(f"   📁 Total images: {total_images}")
    if processed_count > 0:
        size_reduction = (total_before - total_after) / total_before * 100 if total_before > 0 else 0
        print(f"   📦 Total size before: {total_before / (1024 * 1024):.2f} MB")
        print(f"   📦 Total size after: {total_after / (1024 * 1024):.2f} MB")
        print(f"   📉 Size reduction: {size_reduction:.1f}%")
    print("-" * 40)


def main() -> None:
    logger.warning("⚠️  WARNING: This script will MODIFY original image files in-place!")
    logger.warning("⚠️  NO BACKUPS will be created.")
    logger.warning("⚠️  CTRL+C to cancel, ENTER to continue...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user.")
        sys.exit(0)
    process()


if __name__ == "__main__":
    main()
