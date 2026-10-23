#!/data/data/com.termux/files/usr/bin/python
import os
import cv2
import numpy as np

def load_tiles(tiles_folder, tile_size=(50, 50)):
    """
    Loads all images from a folder, resizes them to a fixed square size,
    and calculates their average BGR color values.
    """
    tiles = []
    tile_avg_colors = []
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    
    print("Loading and processing tile images...")
    for filename in os.listdir(tiles_folder):
        if filename.lower().endswith(valid_extensions):
            img_path = os.path.join(tiles_folder, filename)
            img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            
            if img is not None:
                img_resized = cv2.resize(img, tile_size)
                tiles.append(img_resized)
                
                # Calculate average color across all pixels (B, G, R)
                avg_color = img_resized.mean(axis=(0, 1))
                tile_avg_colors.append(avg_color)
                
    if not tiles:
        raise ValueError(f"No valid images found in folder: {tiles_folder}")
        
    print(f"Successfully loaded {len(tiles)} tile images.")
    return np.array(tiles), np.array(tile_avg_colors)

def create_mosaic_blended(target_image_path, tiles, tile_avg_colors, grid_size=(100, 100), alpha=0.3):
    """
    Generates a mosaic and blends it with the original master image for sharp details.
    alpha: 0.0 means pure tiles. 1.0 means pure original image. (0.2 to 0.4 is optimal)
    """
    # Load target master image
    target_img = cv2.imread(target_image_path, cv2.IMREAD_COLOR)
    if target_img is None:
        raise FileNotFoundError(f"Could not open target image: {target_image_path}")
        
    # Calculate output canvas dimensions based on grid and tile sizes
    num_cols, num_rows = grid_size
    tile_h, tile_w, _ = tiles[0].shape
    new_w = num_cols * tile_w
    new_h = num_rows * tile_h
    
    # Resize target to match exact mosaic dimensions
    target_resized = cv2.resize(target_img, (new_w, new_h))
    
    # Initialize empty canvas for tiles
    tile_layer = np.zeros((new_h, new_w, 3), dtype=np.uint8)
    
    print("Generating tile layout...")
    # Loop over the grid coordinates
    for i in range(num_rows):        # Rows
        for j in range(num_cols):    # Columns
            y1, y2 = i * tile_h, (i + 1) * tile_h
            x1, x2 = j * tile_w, (j + 1) * tile_w
            
            # Extract target cell region and get its average color
            cell = target_resized[y1:y2, x1:x2]
            cell_avg = cell.mean(axis=(0, 1))
            
            # Find closest matching tile using Euclidean distance
            distances = np.linalg.norm(tile_avg_colors - cell_avg, axis=1)
            best_match_idx = np.argmin(distances)
            
            # Paste the best tile onto the tile canvas
            tile_layer[y1:y2, x1:x2] = tiles[best_match_idx]
            
    # Apply alpha blending: final = (1 - alpha) * tiles + alpha * original
    print(f"Applying alpha blend overlay (Strength: {alpha})...")
    blended_mosaic = cv2.addWeighted(tile_layer, 1.0 - alpha, target_resized, alpha, 0)
    
    return blended_mosaic

if __name__ == "__main__":
    # --- CONFIGURATION START ---
    FOLDER_OF_IMAGES = "path/to/your/tile/folder"  
    IMAGE_TO_MAKE = "path/to/your/target_image.jpg" 
    OUTPUT_IMAGE = "mosaic_blended_result.png"
    
    GRID_ROWS_COLS = (120, 120)     # Number of tiles (Columns, Rows) across the picture
    INDIVIDUAL_TILE_SIZE = (40, 40) # Resolution of each individual tile (Width, Height)
    
    # Blend intensity: 0.0 (only tiles) to 1.0 (only original photo)
    OVERLAY_STRENGTH = 0.35          
    # --- CONFIGURATION END ---

    try:
        # 1. Process database images
        tiles, tile_avgs = load_tiles(FOLDER_OF_IMAGES, tile_size=INDIVIDUAL_TILE_SIZE)
        
        # 2. Build blended mosaic
        result = create_mosaic_blended(
            IMAGE_TO_MAKE, 
            tiles, 
            tile_avgs, 
            grid_size=GRID_ROWS_COLS, 
            alpha=OVERLAY_STRENGTH
        )
        
        # 3. Save final image
        cv2.imwrite(OUTPUT_IMAGE, result)
        print(f"Success! Sharp blended mosaic saved as '{OUTPUT_IMAGE}'")
        
    except Exception as e:
        print(f"Error: {e}")
