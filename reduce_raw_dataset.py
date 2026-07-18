import os
import re
import shutil
import argparse

def get_image_id(filename):
    """
    Extracts a base ID/index from the filename to match associated files.
    e.g., 'frame_0001.png', 'depth_0001.png', 'meta_0001.json' -> '0001'
    """
    match = re.search(r'\d+', filename)
    return match.group(0) if match else None

def calculate_keep_indices(total_count, factor):
    """
    Generates indices to keep using a floating-point accumulator step.
    For a factor of 3 and 10 items, this yields: [0, 3, 6, 9]
    """
    keep_indices = []
    current = 0.0
    while current < total_count:
        idx = int(current)
        if idx not in keep_indices and idx < total_count:
            keep_indices.append(idx)
        current += factor
    return keep_indices

def main():
    parser = argparse.ArgumentParser(
        description="Prune a dataset sequentially by reducing folders and image sequences (keeping complete tuples intact)."
    )
    
    # Required positional argument
    parser.add_argument(
        "target_dir", 
        type=str, 
        help="Path to the main folder containing subfolders"
    )
    
    # Optional parameters with constraints
    parser.add_argument(
        "-f", "--folder-factor", 
        type=float, 
        default=2.0,
        help="Reduction factor for 'Hoehenlinie' folders. Must be between 1.5 and 4.0 (default: 2.0)"
    )
    parser.add_argument(
        "-i", "--image-factor", 
        type=float, 
        default=4.0,
        help="Reduction factor for image sequences inside kept folders. Must be between 2.0 and 10.0 (default: 4.0)"
    )
    
    # Safety flag
    parser.add_argument(
        "--execute", 
        action="store_true", 
        help="Actually execute the deletion. If not provided, the script runs in DRY-RUN mode."
    )

    args = parser.parse_args()

    # --- Argument Validation ---
    if not (1.5 <= args.folder_factor <= 4.0):
        parser.error(f"Folder reduction factor must be between 1.5 and 4.0. Got {args.folder_factor}")
        
    if not (2.0 <= args.image_factor <= 10.0):
        parser.error(f"Image reduction factor must be between 2.0 and 10.0. Got {args.image_factor}")

    target_dir = args.target_dir
    folder_factor = args.folder_factor
    image_factor = args.image_factor
    dry_run = not args.execute

    if not os.path.exists(target_dir):
        print(f"Error: Target directory '{target_dir}' does not exist.")
        return

    # 1. Gather all subfolders
    all_subfolders = sorted([
        f for f in os.listdir(target_dir) 
        if os.path.isdir(os.path.join(target_dir, f))
    ])
    
    # 2. Filter folders based on rules
    protected_folders = [f for f in all_subfolders if not f.startswith("Hoehenlinie")]
    reducible_folders = [f for f in all_subfolders if f.startswith("Hoehenlinie")]
    
    print(f"Total folders found: {len(all_subfolders)}")
    print(f"Protected folders (keeping all): {len(protected_folders)}")
    print(f"Reducible folders ('Hoehenlinie'): {len(reducible_folders)}")
    
    # Determine which 'Hoehenlinie' folders to keep using sequential steps
    keep_reducible_indices = calculate_keep_indices(len(reducible_folders), folder_factor)
    keep_reducible = [reducible_folders[idx] for idx in keep_reducible_indices]
            
    folders_to_keep = set(protected_folders + keep_reducible)
    folders_to_delete = [f for f in all_subfolders if f not in folders_to_keep]
    
    print(f"-> Folders to KEEP: {len(folders_to_keep)}")
    print(f"-> Folders to DELETE: {len(folders_to_delete)}\n")
    
    # --- Execute Folder Deletion ---
    for folder in folders_to_delete:
        path = os.path.join(target_dir, folder)
        if dry_run:
            print(f"[DRY RUN] Would delete folder: {path}")
        else:
            print(f"Deleting folder: {path}")
            shutil.rmtree(path)
            
    print("\n" + "="*50 + "\nProcessing remaining folders...\n" + "="*50)

    # 3. Process remaining folders to downsample images
    for folder in folders_to_keep:
        folder_path = os.path.join(target_dir, folder)
        print(f"\nProcessing folder: {folder}")
        
        files = sorted(os.listdir(folder_path))
        
        # Group files by their sequence ID (numeric digits)
        # e.g., groups['0001'] = ['color_0001.png', 'depth_0001.png', 'depth_vis_0001.png', 'meta_0001.json']
        groups = {}
        for f in files:
            file_id = get_image_id(f)
            if file_id:
                if file_id not in groups:
                    groups[file_id] = []
                groups[file_id].append(f)
                
        sorted_ids = sorted(groups.keys())
        total_groups = len(sorted_ids)
        
        # Select which image groups to keep using sequential steps
        keep_ids_indices = calculate_keep_indices(total_groups, image_factor)
        keep_ids = [sorted_ids[idx] for idx in keep_ids_indices]
                
        keep_ids_set = set(keep_ids)
        ids_to_delete = [fid for fid in sorted_ids if fid not in keep_ids_set]
        
        print(f"  Total image sequences: {total_groups}")
        print(f"  Keeping: {len(keep_ids_set)} sequences (complete tuples preserved)")
        print(f"  Deleting: {len(ids_to_delete)} sequences (color, depth, depth_vis, & meta deleted)")
        
        # Delete ALL files in the discarded groups (ensures depth and depth_vis are wiped out)
        for fid in ids_to_delete:
            for file_to_del in groups[fid]:
                file_path = os.path.join(folder_path, file_to_del)
                if dry_run:
                    print(f"    [DRY RUN] Would delete file: {file_to_del}")
                else:
                    os.remove(file_path)

    if dry_run:
        print("\n" + "!"*50)
        print("DRY RUN COMPLETED. No files or folders were actually deleted.")
        print("To execute the deletion, run the command again with the '--execute' flag.")
        print("!"*50)

if __name__ == "__main__":
    main()