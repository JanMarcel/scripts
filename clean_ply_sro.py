#!/usr/bin/env python3
import argparse
import sys
import open3d as o3d
import os

def clean_cloud(input_ply: str, output_ply: str, n_neighbors: int, std_ratio: float):
    # 1. Load the point cloud
    print(f"[*] Loading point cloud from: {input_ply}")
    pcd = o3d.io.read_point_cloud(input_ply)

    if not pcd.has_points():
        print(
            f"[!] Error: Could not read any points from {input_ply}. Is it a valid PLY file?",
            file=sys.stderr,
        )
        sys.exit(1)

    initial_count = len(pcd.points)
    print(f"[+] Successfully loaded {initial_count:,} points.")

    # 2. Run Statistical Outlier Removal
    print(
        f"[*] Running SOR filter (neighbors={n_neighbors}, std_ratio={std_ratio})..."
    )
    clean_pcd, inlier_indices = pcd.remove_statistical_outlier(
        nb_neighbors=n_neighbors, std_ratio=std_ratio
    )

    final_count = len(clean_pcd.points)
    removed_count = initial_count - final_count
    print(f"[+] Filtering complete!")
    print(f"    - Points kept: {final_count:,}")
    print(
        f"    - Outliers removed: {removed_count:,} ({ (removed_count/initial_count)*100:.2f}%)"
    )

    # 3. Save the output
    print(f"[*] Saving clean point cloud to: {output_ply}")
    success = o3d.io.write_point_cloud(output_ply, clean_pcd)

    if success:
        print("[+] Done! File saved successfully.")
    else:
        print(
            f"[!] Error: Failed to write the output file to {output_ply}",
            file=sys.stderr,
        )
        sys.exit(1)

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Remove statistical outliers and ghost layers from a PLY point cloud."
    )

    # Required arguments
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to the input .ply file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path where the filtered .ply file will be saved",
    )

    # Optional filtering tuning arguments (with sensible defaults)
    parser.add_argument(
        "-n",
        "--neighbors",
        type=int,
        default=30,
        help="Number of neighbors to analyze for each point (default: 30)",
    )
    parser.add_argument(
        "-s",
        "--std_ratio",
        type=float,
        default=1.0,
        help="Standard deviation multiplier. Lower = stricter/more aggressive filtering (default: 1.0)",
    )

    args = parser.parse_args()
    
    if not args.output:
        base_path, ext = os.path.splitext(args.input)
        output_file = base_path + f"_{args.neighbors}_s{args.std_ratio:1.3f}".replace(".", "p") + ext
    else:
        output_file = args.output
    
    if args.input == output_file:
        raise ValueError("Input PLY path and output PLY path should not be the same!")

    clean_cloud(args.input, output_file, args.neighbors, args.std_ratio)


if __name__ == "__main__":
    main()