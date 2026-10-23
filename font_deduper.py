#!/data/data/com.termux/files/usr/bin/python
import os
from fontTools.ttLib import TTFont

DRY_RUN = False
FONT_EXTENSIONS = (".ttf", ".woff2", ".woff")


def get_font_ps_name(file_path):
    """Extracts the unique PostScript name from a TTF or WOFF2 font file."""
    try:
        # fontNumber=0 handles TrueType collections safely; lazy=True speeds up reading
        font = TTFont(file_path, fontNumber=0, lazy=True)
        name_table = font["name"]
        # Name ID 6 is the unique PostScript name
        ps_name = name_table.getDebugName(6)
        # Fallback to Name ID 4 (Full Font Name) or 1 (Font Family)
        if not ps_name:
            ps_name = name_table.getDebugName(4) or name_table.getDebugName(1)
        font.close()
        return ps_name.strip() if ps_name else None
    except Exception:
        # Skips corrupted files or font fragments safely
        return None


def main():
    seen_fonts = {}
    duplicates = []
    print("Scanning directories recursively...")
    font_count = 0
    # os.walk handles deep recursive searches through all nested subfolders
    for root, dirs, files in os.walk("."):
        for file_name in files:
            if file_name.lower().endswith(FONT_EXTENSIONS):
                font_count += 1
                file_path = os.path.join(root, file_name)
                ps_name = get_font_ps_name(file_path)
                if not ps_name:
                    print(f"⚠️ Skipped (could not read metadata): {file_path}")
                    continue
                file_size = os.path.getsize(file_path)
                if ps_name in seen_fonts:
                    existing_path, existing_size = seen_fonts[ps_name]
                    # Size-based tie-breaker logic
                    if file_size > existing_size:
                        # The new file is larger; mark the old file for deletion
                        duplicates.append(existing_path)
                        seen_fonts[ps_name] = (file_path, file_size)
                        print(
                            f"🏷️ Duplicate '{ps_name}': Keeping {file_path} ({file_size} bytes) over {existing_path} ({existing_size} bytes)"
                        )
                    else:
                        # The old file is larger or identical; mark the new file for deletion
                        duplicates.append(file_path)
                        print(
                            f"🏷️ Duplicate '{ps_name}': Keeping {existing_path} ({existing_size} bytes) over {file_path} ({file_size} bytes)"
                        )
                else:
                    seen_fonts[ps_name] = (file_path, file_size)
    print(f"\n--- Scan Complete: Processed {font_count} fonts. Found {len(duplicates)} duplicates ---")
    if DRY_RUN:
        print("[DRY-RUN] No files were deleted. Files marked for removal:")
        for dup in duplicates:
            print(f"  - {dup}")
        print(
            "\n👉 To permanently delete these files, open the script and change 'DRY_RUN = True' to 'DRY_RUN = False'."
        )
    else:
        print("Deleting duplicate fonts...")
        for dup in duplicates:
            try:
                os.remove(dup)
                print(f"❌ Deleted: {dup}")
            except Exception as e:
                print(f"📁 Error deleting {dup}: {e}")


if __name__ == "__main__":
    main()
