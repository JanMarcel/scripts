#!/usr/bin/env python3
import argparse
import numpy as np
import sys
import plyfile
import os

def clean_cloud(input_ply: str, output_ply: str, opacity_threshold: float):
    ply = plyfile.PlyData.read(input_ply)
    
    point_opacities_norm = 1 / (1 + np.exp(-ply.elements[0]["opacity"]))
    
    mask = point_opacities_norm > opacity_threshold
    
    new_elements = ply.elements[0][mask]
    new_vertex_element = plyfile.PlyElement.describe(new_elements, "vertex")
    new_ply = plyfile.PlyData([new_vertex_element], text=False)
    new_ply.write(output_ply)

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
        "--opacity",
        type=int,
        default=0.75,
        help="Normalized opacity threshold, under which the points are omitted.",
    )

    args = parser.parse_args()
    
    if not args.output:
        base_path, ext = os.path.splitext(args.input)
        output_file = base_path + f"_fil_t{args.opacity:1.4f}".replace(".", "p") + ext
    else:
        output_file = args.output
    
    if args.input == output_file:
        raise ValueError("Input PLY path and output PLY path should not be the same!")

    clean_cloud(args.input, output_file, args.neighbors, args.std_ratio)


if __name__ == "__main__":
    main()