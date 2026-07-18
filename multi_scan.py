from __future__ import annotations

import json
from glob import glob
from typing import Any
import os
import shutil
import sys

from calculate_poses import calculate_poses_for_folder, META_INFO_FOLDER_NAME, DEPTH_IMAGES_FOLDER_NAME, COLOR_INPUT_IMAGES_FOLDER_NAME

def get_frame_idx_from_fn(fn: str) -> str:
    return os.path.basename(fn).rsplit("_", maxsplit=1)[1].rsplit(".")[0]

def apply_calculate_poses(subfolders: list[str]) -> None:
    for sf in subfolders:
        os.makedirs(os.path.join(sf, COLOR_INPUT_IMAGES_FOLDER_NAME), exist_ok=True)
        os.system(f"mv {sf}/color*.png {sf}/{COLOR_INPUT_IMAGES_FOLDER_NAME}")
        
        os.makedirs(os.path.join(sf, META_INFO_FOLDER_NAME), exist_ok=True)
        os.system(f"mv {sf}/meta*.json {sf}/{META_INFO_FOLDER_NAME}")
        
        os.makedirs(os.path.join(sf, DEPTH_IMAGES_FOLDER_NAME), exist_ok=True)
        os.system(f"mv {sf}/depth*.png {sf}/{DEPTH_IMAGES_FOLDER_NAME}")
        calculate_poses_for_folder(sf)

def append_to_database(db: dict[str, tuple[int, str, str]], subfolder: str) -> dict[str, tuple[int, str, str]]:
    def gen_key(subfolder: str, meta_filename: str) -> str:
        # meta_filename = "meta_000241.json" -> frame_idx = "000241"
        return f"{subfolder}__{get_frame_idx_from_fn(meta_filename)}"
        
    pattern = os.path.join(subfolder, META_INFO_FOLDER_NAME, "meta*.json")
    meta_files = sorted(glob(pattern))

    for mf in meta_files:
        color_filepath = os.path.join(os.path.dirname(mf), '..', COLOR_INPUT_IMAGES_FOLDER_NAME, f"color_{get_frame_idx_from_fn(mf)}.png")
        db[gen_key(subfolder, mf)] = (db["ELEMENT_COUNT"], mf, color_filepath)
        db["ELEMENT_COUNT"] += 1
    
    return db

def update_merged_metafile(mf: str) -> None:
    with open(mf) as fptr:
        metadata = json.load(fptr)
    
    new_frame_idx = int(get_frame_idx_from_fn(mf))
    metadata["original_frame_index"] = metadata["frame_index"]
    metadata["frame_index"] = new_frame_idx
    
    # update refs to color, depth and depth vis if available
    metadata["color_file"] = f"color_{new_frame_idx:0>7d}.png"
    if metadata["depth_file"] is not None:
        metadata["depth_file"] = f"depth_{new_frame_idx:0>7d}.png"
    if metadata["depth_visual_file"] is not None:
        metadata["depth_visual_file"] = f"depth_vis_{new_frame_idx:0>7d}.png"
        
    with open(mf, "w") as fptr:
        json.dump(metadata, fptr)

def merge_into_folder(root_folder: str, db: dict[str, tuple[int, str, str]]) -> None:
    MERGE_FOLDER_NAME = "0000_MERGED"
    MERGE_FOLDER_PATH = os.path.join(root_folder, MERGE_FOLDER_NAME)
    os.makedirs(MERGE_FOLDER_PATH, exist_ok=True)
    os.makedirs(os.path.join(MERGE_FOLDER_PATH, COLOR_INPUT_IMAGES_FOLDER_NAME), exist_ok=True)
    os.makedirs(os.path.join(MERGE_FOLDER_PATH, META_INFO_FOLDER_NAME), exist_ok=True)
    os.makedirs(os.path.join(MERGE_FOLDER_PATH, DEPTH_IMAGES_FOLDER_NAME), exist_ok=True)
    
    for key, (elem_idx, meta_filepath, color_filepath) in db.items():
        new_color_filename = os.path.join(COLOR_INPUT_IMAGES_FOLDER_NAME, f"color_{elem_idx:0>7d}.png")
        new_meta_filename  = os.path.join(META_INFO_FOLDER_NAME, f"meta_{elem_idx:0>7d}.json")
        
        new_color_filepath = os.path.join(MERGE_FOLDER_PATH, new_color_filename)
        new_meta_filepath  = os.path.join(MERGE_FOLDER_PATH, new_meta_filename)

        shutil.copy(src=color_filepath, dst=new_color_filepath)
        shutil.copy(src=meta_filepath, dst=new_meta_filepath)
        
    # update meta*.json with new color*.png filename
    merged_meta_filenames = glob(os.path.join(MERGE_FOLDER_PATH, META_INFO_FOLDER_NAME, "meta*.json"))
    for mf in merged_meta_filenames:
        update_merged_metafile(mf)

def main(folder: str):
    # get all subfolders in that folder. assume each subfolder is a scan
    subfolders = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, f))
    ]
    
    apply_calculate_poses(subfolders)
    
    # build database, which holds as key : f"{subfolder_name}__{meta_filename}"
    db = { "ELEMENT_COUNT" : 0 }
    for sf in subfolders:
        db = append_to_database(db, sf)

    print(f"Collected in total: {db['ELEMENT_COUNT']} images!")
    del db["ELEMENT_COUNT"] # is not needed anymore
        
    merge_into_folder(folder, db)

if __name__ == '__main__':
    # get folder consisting of multiple subfolders as command line arg
    if len(sys.argv) != 2:
        print("Usage: python multi_scan.py <multi_scan_root_folder>")
        sys.exit(1)
    folder = sys.argv[1]

    main(folder)