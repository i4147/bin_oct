#!/data/data/com.termux/files/usr/bin/env python
"""alone Python 3.12 script designed to run under Termux (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that acts as a reusable URL downloader utility module named `url_downloader` (version "1.0.5"), exposing exactly three public names via `__all__`: `get_resource`, `save_file`, and `SaveToDisk`.

Purpose:
The script downloads a file from a given URL to a target location on disk, with support for resuming interrupted downloads, retrying on failure, and avoiding re-downloading files that already exist.

Key requirements:

1. ** standard library modules (`hashlib.sha224`, `logging` functions `error`/`exception`/`info`, `pathlib.Path`, `re.findall`, `shutil.move`, `tempfile.gettempdir`, `time.sleep`, `typing` helpers `Any`/`Callable`/`Optional`) plus the third-party `requests` library (`Response`, `get`).

2. **Class `SaveToDisk`**:
   - Constructor takes a destination `file_path: Path` and the source `url: str`.
   - Computes a temporary file path inside the system temp directory (`tempfile.gettempdir()`), named using the SHA-224 hex digest of the URL (UTF-8 encoded) plus the original file's suffix/extension. This temp path is used as a staging location for partial/in-progress downloads.
   - A private method `_move_temporary(url that: if the finals an info message ("File already exists") and returns `True` without overwriting; otherwise moves the completed temp file to the final destination path, logs an info message confirming the download (including the URL and destination path), and returns `True`.
   - A `get(url, headers, timeout)` method that performs the actual HTTP download:
     - Determines how many bytes have already been downloaded by checking the size of the temp file if it exists (0 otherwise), enabling resume support.
     - Adds a `Range: bytes=<resume_pos>-` header to request only the remaining bytes.
     - Issues a streaming GET request via `requests.get` with the given headers and timeout.
     - If the HTTP status code is not 200 or 206, logs an info message with the status code and response text, and returns `False`.
     herwise iterates over the response content in chunks (chunk size 256 bytes), appending each non-empty chunk to the disk (opbinary mode), progressively building up the downloaded file to support res successful completion of the streamed download, calls `_move_temporary` to finalize the file and returns its result.

3. **Module-level function `get_resource`**: should wrap `SaveToDisk` to provide a higher-level convenience API — accepting parameters such as the target file path, URL, HTTP headers, request timeout, and retry/backoff behavior (e.g., a number of retries and a sleep interval between attempts using `time.sleep`), catching and logging exceptions (via `logging.exception`/`logging.error`) on failure, and returning a boolean or similar success indicator. It should handle transient network errors gracefully by retrying rather than crashing.

4. **Module-level function `save_file`**: a simpler/higher-level helper that orchestrates writing downloaded content to disk (potentially used standalone or in conjunction with `get_resource`), ensuring parent directories exist as needed and returning status information about whether the save succeeded.

5. **Logging**logging` module's `info`, `error`, and `exception` functions throughout to report progress, warnings (e.g., unexpected HTTP status codes), and ex operations, rather than raors.

6. **Robustness**: The script should beilient to network interruptions — partially downloaded files rem temp directory and are resempts via the `Range` scratch. Avoid red checking if the destination file already exists beforeferring the explicit type annotations throughPath`, `dict[str, str]`, `int`, `bool`ern Python 12 style and include.

8. **Module metadata**: = "url_downloader"`, and `__version__ = "1.0.5"ope asown.

The final script should be directly executable/importable, self-contained, and suitable for use as a lightweight, dependency-minimal download helper in a Termux/Android or general Linux environment.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/gLsKg9sYA9JbwRbjPMNzDo"""

from __future__ import annotations
from hashlib import sha224
from logging import error, exception, info
from pathlib import Path
from re import findall
from shutil import move
import sys
from tempfile import gettempdir
from time import sleep
from typing import Any, Callable, Optional

from requests import Response, get


__all__ = ["SaveToDisk", "get_resource", "save_file"]
__name__ = "url_downloader"
__version__ = "1.0.5"


class SaveToDisk:
    def __init__(self, file_path: Path, url: str) -> None:
        self._temp_path: Path = Path(
            gettempdir(),
            sha224(bytes(url, encoding="UTF-8")).hexdigest() + file_path.suffix,
        )
        self._file_path: Path = file_path

    def _move_temporary(self, url: str) -> bool:
        if self._file_path.exists():
            info("File already exists")
            return True
        move(self._temp_path, self._file_path)
        info("DOWNLOADED: %s TO %s" % (url, self._file_path))
        return True

    def get(self, url: str, headers: dict[str, str], timeout: int) -> bool:
        resume_byte_pos: int = self._temp_path.stat().st_size if self._temp_path.exists() else 0
        headers["Range"] = "bytes=%d-" % resume_byte_pos
        response: Response = get(url, headers=headers, stream=True, timeout=timeout)
        if response.status_code not in (200, 206):
            info("Wrong http response %s %s" % (response.status_code, response.text))
            return False
        for chunk in response.iter_content(chunk_size=256):
            if chunk:
                with open(self._temp_path, "ab") as f:
                    f.write(chunk)
        return self._move_temporary(url)


def _get_url_data(
    url: str,
    get_function: Callable[..., Any],
    tries: int,
    timeout: int,
    wait: int,
) -> Optional[Any]:
    for i in range(wait, tries):
        try:
            sleep(i)
            result = get_function(url, headers={"User-agent": "Chrome"}, timeout=timeout)
            if result:
                return result
        except ConnectionError as e:
            if "Read timed out" in str(e):
                info("Read timeout (try %s)" % i)
            else:
                error("Error on try %s" % i)
                exception(e)
    return None


def _get_file_name(url: str) -> str:
    url = url.strip("/")
    result = findall(r"/(\w+\.\w+)[?|$]", url)
    if result:
        return result[-1]
    return url.split("/")[-1]


def save_file(
    url: str,
    file_path: str,
    file_name: str = "",
    timeout: int = 4,
    wait: int = 2,
    tries: int = 10,
    save_class: Callable[..., SaveToDisk] = SaveToDisk,
) -> bool:
    if not file_name:
        file_name = _get_file_name(url=url)
    path = Path(file_path, file_name)
    if path.exists():
        info("File exists %s" % file_name)
        return True
    return _get_url_data(
        url,
        save_class(file_path=path, url=url).get,
        tries=tries,
        timeout=timeout,
        wait=wait,
    )


def get_resource(
    url: str,
    timeout: int = 4,
    wait: int = 2,
    tries: int = 10,
    get_function: Callable[..., Response] = get,
) -> Optional[str]:
    data = _get_url_data(url, get_function, tries=tries, timeout=timeout, wait=wait)
    if data:
        return data.text
    return data
