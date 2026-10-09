#!/data/data/com.termux/files/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create aility script (intended to run on Termg" tool whose purpose is to quickly upload an image to a UpYun (又拍云) cloud storage bucket and copy the resulting public URL to the system clipboard.

The script should behave as follows:

**Purpose:**
A command-line image-upload helper that takes an image from a file path, the system clipboard (either an actual image or a file path copipboard image data configured UpYun stor, and returns/copies the final acc

**Main inifying the image file path to upload.
- If no path is given, the script should attempt to read an image directly from the system clipboard (screenshot/copied image) using `PIL.ImageGrab`, or alternatively detect a file path copied to the clipboard (supporting macOS via AppleScript/Finder, Windows, and Linux/Termux clipboard file references).
- Configuration is persally in a pickle file at `~/.upimg_config.pkl`, storing: `service` (UpYun bucket/service name), `username`, `password`, `upload_path` (remote directory prefix, default `/`), and `url_base` (public domain used to build the final URL, default `https://test.upimg.com`).
- Support a command-line flag/subcommand to set or update these configuration values (service, username, password, upload_path, url_base), persisting them via `pickle`.

**Main outputs:**
- Uploads the resolved image file to UpYun using the `upyun` Python SDK, placing it under the configured `upload_path`, typically naming the remote file using a timestamp (e.g., based on `datetime.now()`) to avoid collisions.
- Constructs the final public URL by joining `url_base` with the uploaded file's remote path (using `urljoin`).
- Copies the resulting URL to the system clipboard using `pyperclip.copy`.
- Sends a desktop/system notification (title "UpImg") indicating success or failure of the upload, using `osascript` on macOS and a PowerShell balloon-tip notification on Windows (withallback/no-op if notification isn't supported, e.g., on Termux/Linux).

**Notable behavior / requirements:**
- Must detect the current OS via `platform.system()` and branch logic for Darwin (macOS), Windows, and other (Linux/Termux) platforms, particularly for clipboard file-path detection and system notifications.
- Must handle both image-binary clipboard content and clipboard content that is a plain file path string, converting/loading it appropriately via `PIL.Image` and `io.BytesIO` where needed.
- Should validate that required configuration fields areempting an upload, prompting the user to configure the tool if settings are missing or incomplete.
- Should catch and report errors gracefully (e.g., using `traceback.print_exc()`), printing clear error messages to the console and/or sending a failure notification, rather than crashing silently.
- Use `argparse` to parse command-line arguments/options (e.g., image path positional argument, a flag to enter configuration/setup mode).
- The script should be aneting Termux's Python 3.12 (`#!/data/data/com.termux/files/usr/bin/python3.12`) with UTF-8 encoding declaration, usable as a quick CLI tool for grabbing a screenshot or file and instantly getting a shareable hosted image URL on the clipboard.
- Define a `ConfigTuple` namedtuple (fields: service, username, password, upload_path, url_base) with sensible defaults for `upload_path` ("/") and `url_base` ("https://test.upimg.com") to structure and validate the loaded/saved configuration.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/EML4UYv7jbxTG3riWa9Jv9"""

import argparse
import os
import sys
import pickle
import platform
import subprocess
from datetime import datetime
from collections import namedtuple
from io import BytesIO
from traceback import print_exc
from urllib.parse import urljoin

from PIL import Image, ImageGrab
from pyperclip import copy as copy2clipboard
import upyun

SYSTEM = platform.system()
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".upimg_config.pkl")
CONFIG_FIELDS = ["service", "username", "password", "upload_path", "url_base"]
CONFIG_DEFAULTS = ["", "", "", "/", "https://test.upimg.com"]
ConfigTuple = namedtuple("ConfigTuple", CONFIG_FIELDS)


def send_notify(title="UpImg", message=""):
    try:
        if SYSTEM == "Darwin":
            cmd = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", cmd], check=True)
        elif SYSTEM == "Windows":
            ps_script = f'[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");$objNotifyIcon=New-Object System.Windows.Forms.NotifyIcon;$objNotifyIcon.Icon=[System.Drawing.SystemIcons]::Information;$objNotifyIcon.BalloonTipTitle="{title}";$objNotifyIcon.BalloonTipText="{message}";$objNotifyIcon.Visible=$True;$objNotifyIcon.ShowBalloonTip(5000);'
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        return True
    except Exception:
        return False


def get_clipboard_file_paths():
    paths = []
    if SYSTEM == "Darwin":
        try:
            script = 'tell application "Finder" to set theFiles to selection\nreturn POSIX path of (theFiles as text)'
            proc = subprocess.run(["osascript", "-e", "clipboard info"], capture_output=True, text=True)
            if "file" in proc.stdout:
                file_path_proc = subprocess.run(
                    ["osascript", "-e", "POSIX path of (the clipboard as alias)"],
                    capture_output=True,
                    text=True,
                )
                path = file_path_proc.stdout.strip()
                if path and os.path.exists(path):
                    paths.append(path)
        except Exception:
            pass

    elif SYSTEM == "Windows":
        from ctypes import c_uint, c_void_p, c_wchar_p, create_unicode_buffer, windll

        user32 = windll.user32
        kernel32 = windll.kernel32
        cf_hdrop = 15

        if user32.OpenClipboard(None):
            h_global = user32.GetClipboardData(cf_hdrop)
            if h_global:
                h_drop = kernel32.GlobalLock(h_global)
                if h_drop:
                    count = windll.shell32.DragQueryFileW(h_drop, 0xFFFFFFFF, None, 0)
                    for i in range(count):
                        length = windll.shell32.DragQueryFileW(h_drop, i, None, 0)
                        buffer = create_unicode_buffer(length)
                        windll.shell32.DragQueryFileW(h_drop, i, buffer, length + 1)
                        paths.append(buffer.value)
                    kernel32.GlobalUnlock(h_global)
            user32.CloseClipboard()
    return paths


class ClipboardFile:
    @property
    def file_objects(self):
        file_paths = get_clipboard_file_paths()

        if file_paths:
            for path in file_paths:
                if os.path.isfile(path):
                    fp = open(path, "rb")
                    ext = os.path.splitext(path)[1].lower()
                    yield fp, ext
            return

        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            image_bytes_io = BytesIO()
            image.save(image_bytes_io, format="PNG")
            image_bytes_io.seek(0)
            yield image_bytes_io, ".png"


def set_config():
    args = {}
    print("--- UpImg Configuration Setup ---")
    for field, default in zip(CONFIG_FIELDS, CONFIG_DEFAULTS):
        display_default = f" [{default}]" if default else ""
        value = input(f"{field.replace('_', ' ')}{display_default}: ").strip()
        args[field] = value if value else default

    with open(CONFIG_PATH, "wb") as fp:
        pickle.dump(ConfigTuple(**args), fp)

    if SYSTEM == "Windows":
        try:
            import winreg
            import pythoncom
            from win32com.shell import shell

            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            )
            desktop_path = winreg.QueryValueEx(reg_key, "Desktop")[0]

            exe_path = os.path.abspath(sys.argv[0])
            lnk_path = os.path.join(desktop_path, "UpImg.lnk")

            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                shell.IID_IShellLink,
            )
            shortcut.SetPath(sys.executable)
            shortcut.SetArguments(f'"{exe_path}"')
            shortcut.SetHotkey((0x02 << 8) | 0x31)
            shortcut.SetWorkingDirectory(os.path.dirname(exe_path))
            shortcut.SetShowCmd(7)
            shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(lnk_path, 0)
        except Exception:
            print("Notice: Desktop hotkey link shortcut could not be configured.")


def get_config():
    with open(CONFIG_PATH, "rb") as fp:
        return pickle.load(fp)


class UpImage:
    def __init__(self, config):
        self.upyun = upyun.UpYun(config.service, config.username, config.password)
        self.upload_path = config.upload_path

    def upload(self):
        path_list = []
        clipboard_file = ClipboardFile()
        for file, ext in clipboard_file.file_objects:
            full_path = self.upload_path.rstrip("/") + "/" + datetime.now().strftime("%Y%m%d%H%M%S%f") + ext
            self.upyun.put(full_path, file)
            file.close()
            path_list.append(full_path)
        return path_list


def parse_args():
    parser = argparse.ArgumentParser(description="Upload image from clipboard and return Markdown link.")
    parser.add_argument("-c", "--config", action="store_true", help="file upload config")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.config:
        try:
            set_config()
            print('\nConfig success! Execute script or use global hotkey "Ctrl + 1" (Windows).')
        except Exception:
            print_exc()
    else:
        if not os.path.exists(CONFIG_PATH):
            message = "Config file is not found. Please setup profile parameters first.\nUsage: upimg --config"
            send_notify(
                "Config Missing",
                "Execute configuration step via terminal instruction profile.",
            )
            print(message)
            return

        config = get_config()
        try:
            send_notify(title="UpImg", message="Uploading file payload...")
            up = UpImage(config)

            markdown_links = [f"![]({urljoin(config.url_base, path)})" for path in up.upload()]
            files_count = len(markdown_links)

            if files_count > 0:
                joined_markdown = "\n".join(markdown_links)
                copy2clipboard(joined_markdown)
                send_notify(
                    title=f"{files_count} Upload Success",
                    message="Link ready to paste via Ctrl+V / ⌘+V",
                )
                print(joined_markdown)
            else:
                send_notify(
                    title="Upload Cancelled",
                    message="No valid file object image data parsed from clipboard.",
                )

        except Exception:
            error_log = os.path.abspath("./upimg-error.log")
            with open(error_log, "w") as fp:
                print_exc(file=fp)
            send_notify("Execution Error!!!", message=f"Trace log written to: {error_log}")
            print(f"Error detected. Visual diagnostic footprint isolated inside {error_log}")


if __name__ == "__main__":
    main()
