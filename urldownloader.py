#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that downloads files from URLs and saves them to a specified local path, with resilient, resumable downloading. The tool should accept a source URL and a destination file path, along with optional request headers and a timeout, and fetch the remote resource efficiently. It should support resuming partially completed downloads by storing in-progress data in a temporary location and continuing from where it left off when possible, rather than starting over. Downloads should be written to a temporary staging area first and only moved to the final destination once complete, so that interrupted transfers never leave corrupted or incomplete files at the target path. If the destination file already exists, the tool should skip the download and report that the file is already present instead of overwriting it.
The script should handle network and HTTP errors gracefully: retry failed attempts a limited number of times with a short delay between tries, log meaningful status messages for successes, skips, and failures, and return a clear success or failure result to the caller rather than crashing unexpectedly. It should expose a simple public interface for downloading a single resource and saving it, along with a reusable helper class that manages the save-to-disk workflow, including the temporary file naming scheme derived from the URL so that the same URL maps consistently to the same staging file across runs. Include version metadata for the module and make the code reusable as an importable utility as well as runnable on its own.
---"""

from __future__ import annotations
from hashlib import sha224
from logging import error, exception, info
from pathlib import Path
from re import findall
from shutil import move
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
