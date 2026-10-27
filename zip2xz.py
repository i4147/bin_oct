#!/data/data/com.termux/files/usr/bin/python
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def convert(zip_path: Path) -> Path:
    tarxz_path = zip_path.with_suffix(".tar.xz")
    parent = tarxz_path.parent
    fd, tmp_name = tempfile.mkstemp(dir=parent, suffix=".tar.xz.tmp")
    import os

    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with tempfile.TemporaryDirectory(dir=parent) as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)
            tar_proc = subprocess.Popen(
                ["tar", "-C", str(tmpdir), "-cf", "-", "."],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            with open(tmp_path, "wb") as out_f:
                xz_proc = subprocess.Popen(
                    ["xz", "-9e", "-T0", "-c"],
                    stdin=tar_proc.stdout,
                    stdout=out_f,
                    stderr=subprocess.PIPE,
                )
                assert tar_proc.stdout is not None
                tar_proc.stdout.close()
                _, xz_err = xz_proc.communicate()
                tar_rc = tar_proc.wait()
            if tar_rc != 0:
                raise RuntimeError(f"tar failed with rc={tar_rc}")
            if xz_proc.returncode != 0:
                raise RuntimeError(f"xz failed with rc={xz_proc.returncode}: {xz_err.decode(errors='replace').strip()}")
        tmp_path.replace(tarxz_path)
        with zipfile.ZipFile(zip_path) as zf:
            expect = zf.namelist()
        with subprocess.Popen(
            ["tar", "-tJf", str(tarxz_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError(f"verify failed: {err.decode(errors='replace')}")
        if expect and not out.strip():
            raise RuntimeError("verify produced empty listing")
        return tarxz_path
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def main() -> int:
    zips = sorted(p for p in Path(".").rglob("*.zip") if p.is_file())
    if not zips:
        print("No .zip files found.")
        return 0
    failures = 0
    for zp in zips:
        print(f"Converting: {zp}")
        try:
            target = convert(zp)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            failures += 1
            continue
        try:
            zp.unlink()
            print(f"  OK -> {target} (removed {zp})")
        except OSError as e:
            print(f"  WARNING: could not remove {zp}: {e}", file=sys.stderr)
    if failures:
        print(f"\n{failures} conversion(s) failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
