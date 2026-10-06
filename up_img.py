#!/data/data/com.termux/files/usr/bin/python3.12
# -*- coding: utf-8 -*-

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

# Third-party dependencies (Requires: pip install Pillow pyperclip upyun)
from PIL import Image, ImageGrab
from pyperclip import copy as copy2clipboard
import upyun

SYSTEM = platform.system()
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".upimg_config.pkl")
CONFIG_FIELDS = ["service", "username", "password", "upload_path", "url_base"]
CONFIG_DEFAULTS = ["", "", "", "/", "https://test.upimg.com"]
ConfigTuple = namedtuple("ConfigTuple", CONFIG_FIELDS)


# ==========================================
# SYSTEM NOTIFICATIONS (Cross-Platform)
# ==========================================
def send_notify(title="UpImg", message=""):
    """Sends a system notification without heavy external libraries."""
    try:
        if SYSTEM == "Darwin":  # macOS
            cmd = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", cmd], check=True)
        elif SYSTEM == "Windows":  # Windows
            # Fallback to PowerShell to prevent installing complex Windows runtime wheels
            ps_script = f'[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");$objNotifyIcon=New-Object System.Windows.Forms.NotifyIcon;$objNotifyIcon.Icon=[System.Drawing.SystemIcons]::Information;$objNotifyIcon.BalloonTipTitle="{title}";$objNotifyIcon.BalloonTipText="{message}";$objNotifyIcon.Visible=$True;$objNotifyIcon.ShowBalloonTip(5000);'
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        return True
    except Exception:
        return False


# ==========================================
# CLIPBOARD MANAGEMENT (Cross-Platform)
# ==========================================
def get_clipboard_file_paths():
    """Gets files paths copied directly to the clipboard."""
    paths = []
    if SYSTEM == "Darwin":
        try:
            # Use AppleScript to cleanly query native file targets from the general pasteboard
            script = 'tell application "Finder" to set theFiles to selection\nreturn POSIX path of (theFiles as text)'
            proc = subprocess.run(["osascript", "-e", "clipboard info"], capture_output=True, text=True)
            if "file" in proc.stdout:
                file_path_proc = subprocess.run(
                    ["osascript", "-e", "POSIX path of (the clipboard as alias)"], capture_output=True, text=True
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

        # Handle explicit file selections copied to clipboard
        if file_paths:
            for path in file_paths:
                if os.path.isfile(path):
                    fp = open(path, "rb")
                    ext = os.path.splitext(path)[1].lower()
                    yield fp, ext
            return

        # Fallback to direct raw pixel screenshots/images on the clipboard
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            image_bytes_io = BytesIO()
            image.save(image_bytes_io, format="PNG")
            image_bytes_io.seek(0)
            yield image_bytes_io, ".png"


# ==========================================
# CONFIGURATION & RECOVERY
# ==========================================
def set_config():
    args = {}
    print("--- UpImg Configuration Setup ---")
    for field, default in zip(CONFIG_FIELDS, CONFIG_DEFAULTS):
        display_default = f" [{default}]" if default else ""
        value = input(f"{field.replace('_', ' ')}{display_default}: ").strip()
        args[field] = value if value else default

    with open(CONFIG_PATH, "wb") as fp:
        pickle.dump(ConfigTuple(**args), fp)

    # Optional: Configure Windows Global Shortcut Hook via Desktop shortcut
    if SYSTEM == "Windows":
        try:
            import winreg
            import pythoncom
            from win32com.shell import shell

            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            desktop_path = winreg.QueryValueEx(reg_key, "Desktop")[0]

            exe_path = os.path.abspath(sys.argv[0])
            lnk_path = os.path.join(desktop_path, "UpImg.lnk")

            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
            )
            shortcut.SetPath(sys.executable)
            shortcut.SetArguments(f'"{exe_path}"')
            shortcut.SetHotkey((0x02 << 8) | 0x31)  # Ctrl + 1
            shortcut.SetWorkingDirectory(os.path.dirname(exe_path))
            shortcut.SetShowCmd(7)  # Minimized window focus
            shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(lnk_path, 0)
        except Exception:
            print("Notice: Desktop hotkey link shortcut could not be configured.")


def get_config():
    with open(CONFIG_PATH, "rb") as fp:
        return pickle.load(fp)


# ==========================================
# UPLOAD CORE LOGIC
# ==========================================
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
            file.close()  # Ensure IO descriptor gets cleanly recycled
            path_list.append(full_path)
        return path_list


# ==========================================
# CLI MAIN ROUTINE ENTRYPOINT
# ==========================================
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
            send_notify("Config Missing", "Execute configuration step via terminal instruction profile.")
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
                send_notify(title=f"{files_count} Upload Success", message="Link ready to paste via Ctrl+V / ⌘+V")
                print(joined_markdown)
            else:
                send_notify(title="Upload Cancelled", message="No valid file object image data parsed from clipboard.")

        except Exception:
            error_log = os.path.abspath("./upimg-error.log")
            with open(error_log, "w") as fp:
                print_exc(file=fp)
            send_notify("Execution Error!!!", message=f"Trace log written to: {error_log}")
            print(f"Error detected. Visual diagnostic footprint isolated inside {error_log}")


if __name__ == "__main__":
    main()
