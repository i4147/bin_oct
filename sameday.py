#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that retrieves extended file metadata for a given file path on Linux, including the file's creation (birth) time, and reports it alongside the standard modification, access, and change timestamps. The tool should accept a file or directory path as input, query the operating system's low-level file status facility to obtain detailed attributes such as size, permissions, ownership, inode number, and link count, and display the results in a clear, human-readable format with timestamps converted to UTC datetime strings. It should handle cases where the birth time is unavailable on the underlying filesystem by reporting that gracefully rather than failing, and should report clear error messages for missing paths, permission problems, or unsupported platforms. Optionally, the script may support a machine-readable output mode (such as JSON) for use in other tools or scripts. Use only the standard library, and design the command-line interface so that it is simple to run and easy to understand.
---"""

from __future__ import annotations
import ctypes
import ctypes.util
from datetime import UTC, datetime


class StatxTimestamp(ctypes.Structure):
    _fields_ = [
        ("tv_sec", ctypes.c_int64),
        ("tv_nsec", ctypes.c_uint32),
        ("__reserved", ctypes.c_int32),
    ]


class Statx(ctypes.Structure):
    _fields_ = [
        ("stx_mask", ctypes.c_uint32),
        ("stx_blksize", ctypes.c_uint32),
        ("stx_attributes", ctypes.c_uint64),
        ("stx_nlink", ctypes.c_uint32),
        ("stx_uid", ctypes.c_uint32),
        ("stx_gid", ctypes.c_uint32),
        ("stx_mode", ctypes.c_uint16),
        ("__spare0", ctypes.c_uint16 * 1),
        ("stx_ino", ctypes.c_uint64),
        ("stx_size", ctypes.c_uint64),
        ("stx_blocks", ctypes.c_uint64),
        ("stx_attributes_mask", ctypes.c_uint64),
        ("stx_atime", StatxTimestamp),
        ("stx_btime", StatxTimestamp),
        ("stx_ctime", StatxTimestamp),
        ("stx_mtime", StatxTimestamp),
        ("stx_rdev_major", ctypes.c_uint32),
        ("stx_rdev_minor", ctypes.c_uint32),
        ("stx_dev_major", ctypes.c_uint32),
        ("stx_dev_minor", ctypes.c_uint32),
        ("__spare2", ctypes.c_uint64 * 14),
    ]


libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
AT_FDCWD = -100
STATX_BTIME = 2048


def get_creation_time_statx(path: str) -> datetime | None:
    statx_buf = Statx()
    result = libc.statx(AT_FDCWD, path.encode(), 0, STATX_BTIME, ctypes.byref(statx_buf))
    if result == 0 and statx_buf.stx_mask & STATX_BTIME:
        timestamp = statx_buf.stx_btime.tv_sec
        return datetime.fromtimestamp(timestamp, tz=UTC)
    return None


creation_time = get_creation_time_statx("filename.txt")
print(f"Creation time: {creation_time}")
