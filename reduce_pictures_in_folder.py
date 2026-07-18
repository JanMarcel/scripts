import os
import argparse

def reduce_images(folder_path, factor):
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    # Supported image formats
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    
    # Get and sort all image files to ensure we reduce them in correct sequential order
    all_files = sorted([
        f for f in os.listdir(folder_path) 
        if f.lower().endswith(valid_extensions) and os.path.isfile(os.path.join(folder_path, f))
    ])

    total_images = len(all_files)
    if total_images == 0:
        print(f"No images found in '{folder_path}'.")
        return

    # Determine which images to keep (slicing with step F)
    # This selects indices 0, F, 2F, 3F, etc.
    images_to_keep = all_files[::factor]
    keep_set = set(images_to_keep)
    
    images_to_delete = [f for f in all_files if f not in keep_set]
    
    print(f"Total images found: {total_images}")
    print(f"Reducing by factor {factor}:")
    print(f"  -> Keeping: {len(images_to_keep)} images")
    print(f"  -> Deleting: {len(images_to_delete)} images")

    if not images_to_delete:
        print("Nothing to delete (factor is likely 1 or folder has too few images).")
        return

    # Prompt user for confirmation
    confirm = input(f"\nAre you sure you want to permanently delete these {len(images_to_delete)} images? (y/N): ")
    if confirm.lower() != 'y':
        print("Operation cancelled. No files were deleted.")
        return

    # Delete the extra files
    deleted_count = 0
    for filename in images_to_delete:
        file_path = os.path.join(folder_path, filename)
        try:
            os.remove(file_path)
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete {filename}: {e}")

    print(f"\nSuccessfully removed {deleted_count} images.")

def check_factor(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 50:
        raise argparse.ArgumentTypeError(f"Factor must be an integer between 1 and 50. You provided: {value}")
    return ivalue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reduce the number of images in a folder by a factor of F (keeps every F-th image)."
    )
    parser.add_argument(
        "folder", 
        type=str, 
        help="The path to the folder containing the images"
    )
    parser.add_argument(
        "-f", "--factor", 
        type=check_factor,
        default=5.0, 
        help="Reduction factor f (integer between 1 and 50)"
    )
    
    args = parser.parse_args()
    reduce_images(args.folder, args.factor)