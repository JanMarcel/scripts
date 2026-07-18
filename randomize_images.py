import os
import random
import argparse
import uuid

def scramble_images(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    # Supported image formats
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    
    # Get all matching image files in the directory
    image_files = [
        f for f in os.listdir(folder_path) 
        if f.lower().endswith(valid_extensions) and os.path.isfile(os.path.join(folder_path, f))
    ]

    if not image_files:
        print(f"No images found in '{folder_path}'.")
        return

    print(f"Found {len(image_files)} images. Shuffling them now...")

    # Shuffle the list of images in place randomly
    random.shuffle(image_files)

    # 1. First pass: Rename to unique temporary names to prevent overwrite collisions
    temp_renames = []
    for original_name in image_files:
        ext = os.path.splitext(original_name)[1]
        temp_name = f"temp_{uuid.uuid4()}{ext}"
        
        src = os.path.join(folder_path, original_name)
        temp_dst = os.path.join(folder_path, temp_name)
        
        os.rename(src, temp_dst)
        temp_renames.append((temp_dst, ext))

    # 2. Second pass: Rename from temporary names to the final scrambled sequence
    for idx, (temp_path, ext) in enumerate(temp_renames, start=1):
        new_name = f"scrambled_{idx:06d}{ext}"
        final_dst = os.path.join(folder_path, new_name)
        os.rename(temp_path, final_dst)

    print(f"Successfully scrambled and renamed files to 'scrambled_xxxxxx{ext}' format!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Randomly scramble and sequentially rename all images in a target folder."
    )
    parser.add_argument(
        "folder", 
        type=str, 
        help="The path to the folder containing the images"
    )
    
    args = parser.parse_args()
    scramble_images(args.folder)