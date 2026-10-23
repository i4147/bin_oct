#!/data/data/com.termux/files/usr/bin/python
import os
from collections import defaultdict
from PIL import Image
import imagehash
# CONFIGURATION
# Set to False to actually delete the duplicate files!
DRY_RUN = True
# Supported image formats
IMAGE_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png", ".tiff", ".tif")
def main():
    # Map to group paths by their calculated visual hash
    # Key: ImageHash object, Value: list of tuples (file_path, total_pixels, file_size)
    hash_groups = defaultdict(list)
    print("Scanning directories recursively for images...")
    image_count = 0
    # Walk through folders recursively
    for root, dirs, files in os.walk("."):
        for file_name in files:
            if file_name.lower().endswith(IMAGE_EXTENSIONS):
                image_count += 1
                file_path = os.path.join(root, file_name)
                try:
                    with Image.open(file_path) as img:
                        # 1. Calculate the perceptual hash (phash is excellent for scale/format changes)
                        v_hash = imagehash.phash(img)
                        # 2. Extract resolution metrics to identify the highest quality image
                        width, height = img.size
                        total_pixels = width * height
                        file_size = os.path.getsize(file_path)
                        # Store properties for comparison
                        hash_groups[v_hash].append((file_path, total_pixels, file_size))
                except Exception:
                    # Skip corrupt files or unreadable formats gracefully
                    print(f"⚠️ Could not read image: {file_path}")
                    continue
    print(f"\nScan complete. Processed {image_count} images.")
    print("Analyzing visual duplicates...\n")
    duplicates_to_remove = []
    # Process each visual group
    for v_hash, instances in hash_groups.items():
        if len(instances) > 1:
            # Sort instances so the HIGHEST quality image is FIRST
            # Priority 1: Most pixels (resolution)
            # Priority 2: Largest file size (retains more detail/less compression)
            instances.sort(key=lambda x: (x[1], x[2]), reverse=True)
            # The first item is our champion (to keep)
            keep_path, keep_pixels, keep_size = instances[0]
            print(f"🖼️  Visual Group [Hash: {v_hash}]")
            print(f"   ✅ KEEP: {keep_path} ({keep_pixels} px, {keep_size} bytes)")
            # All other items in this hash bucket are duplicates
            for dup_path, dup_pixels, dup_size in instances[1:]:
                duplicates_to_remove.append(dup_path)
                print(f"   ❌ DUP : {dup_path} ({dup_pixels} px, {dup_size} bytes)")
            print("-" * 50)
    # Process deletions
    print(f"\n--- Found {len(duplicates_to_remove)} duplicate images ---")
    if DRY_RUN:
        print("[DRY-RUN] No files were deleted.")
        print("👉 Set 'DRY_RUN = False' inside the script to permanently delete duplicate copies.")
    else:
        print("Deleting duplicate images, preserving highest resolutions...")
        for dup in duplicates_to_remove:
            try:
                os.remove(dup)
                print(f"Deleted: {dup}")
            except Exception as e:
                print(f"📁 Error deleting {dup}: {e}")
if __name__ == "__main__":
    main()
