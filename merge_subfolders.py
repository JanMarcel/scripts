from __future__ import annotations

import os
import shutil
import glob
import re
import argparse

def merge_images(folder_patterns: list[str], output_folder: str|None=None):
    # 1. Create the output folder if it doesn't exist
    if output_folder is None:
        folder_pattern_wo_trailing_slash = folder_patterns[0].rstrip("/")   # if folder_pattern ends in '/', remove it s.t. dirname finds the correct folder
        output_folder = os.path.join(os.path.dirname(folder_pattern_wo_trailing_slash.split("*", 1)[0]), "0000_MERGED")
    os.makedirs(output_folder, exist_ok=True)
    
    # 2. Find and aggregate all unique source directories across all patterns
    unique_dirs = set()
    for pattern in folder_patterns:
        matched_paths = glob.glob(pattern)
        for path in matched_paths:
            if os.path.isdir(path):
                # Normalize path to prevent duplicate entries (e.g., ./folder/ vs ./folder)
                unique_dirs.add(os.path.normpath(path))
                
    source_dirs = sorted(list(unique_dirs))
    
    if not source_dirs:
        print(f"Error: No directories found matching patterns: {folder_patterns}")
        return

    print(f"Found {len(source_dirs)} unique folders to merge.")
    
    # Helper function to extract the number from 'color_xxxxxx.png' for numerical sorting
    def get_image_number(file_path):
        match = re.search(r'color_(\d+)\.png$', os.path.basename(file_path))
        return int(match.group(1)) if match else -1

    global_counter = 1

    # 3. Process folders and images in sorted order
    for directory in source_dirs:
        # Find all png files matching 'color_*.png' in the current folder
        img_pattern = os.path.join(directory, "color_*.png")
        images = glob.glob(img_pattern)
        
        # Sort images numerically based on their original number
        images.sort(key=get_image_number)
        
        if not images:
            continue
            
        print(f"Copying {len(images)} images from '{directory}'...")
        
        for img_path in images:
            # Generate the new name with 6-digit zero padding (e.g., color_000001.png)
            new_filename = f"color_{global_counter:06d}.png"
            dest_path = os.path.join(output_folder, new_filename)
            
            # Copy the file to the merged directory
            shutil.copy2(img_path, dest_path)
            global_counter += 1

    print(f"\nDone! Merged {global_counter - 1} images into '{output_folder}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge and sequentially rename 'color_xxxxxx.png' images from multiple folder patterns."
    )
    # nargs='+' allows one or more patterns to be passed
    parser.add_argument(
        "patterns", 
        type=str, 
        nargs="+",
        help="One or more glob patterns matching your folders (e.g., './folder/scan*' './folder/round*')"
    )
    
    args = parser.parse_args()
    merge_images(args.patterns)