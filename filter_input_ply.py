#!/usr/bin/env python3
import argparse
import os
import sys
import numpy as np
import open3d as o3d
from plyfile import PlyData, PlyElement

def apply_dbscan(input_ply: str, output_ply: str, epsilon: float, min_points: int) -> None:
    # ==========================================
    # STEP 1: Compute Dense Clusters using Open3D
    # ==========================================
    print(f"[*] Reading geometry with Open3D from: {input_ply}")
    pcd = o3d.io.read_point_cloud(input_ply)

    if not pcd.has_points():
        print(
            f"[!] Error: Open3D could not find points in {input_ply}",
            file=sys.stderr,
        )
        sys.exit(1)

    initial_count = len(pcd.points)
    print(f"[+] Loaded {initial_count:,} points into Open3D.")

    print(f"[*] Clustering via DBSCAN (eps={epsilon}, min_pts={min_points})...")
    labels = np.array(
        pcd.cluster_dbscan(
            eps=epsilon, min_points=min_points, print_progress=True
        )
    )

    num_clusters = labels.max() + 1
    print(f"[+] Found {num_clusters} valid dense clusters.")

    if num_clusters == 0:
        print(
            "[!] Error: No clusters found. The epsilon value might be too small.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Identify the largest dense cluster ID (ignoring noise labeled as -1)
    cluster_counts = np.bincount(labels[labels >= 0])
    largest_cluster_id = np.argmax(cluster_counts)
    print(
        f"[+] Largest cluster is ID {largest_cluster_id} ({cluster_counts[largest_cluster_id]:,} points)."
    )

    # Create a boolean mask of the exact indices we want to keep
    inlier_mask = labels == largest_cluster_id

    # ==========================================
    # STEP 2: Filter and Save Using plyfile
    # ==========================================
    print(f"[*] Re-opening file with plyfile to preserve raw metadata structure...")
    plydata = PlyData.read(input_ply)

    # Locate the vertex element group
    vertex_element = None
    vertex_element_idx = -1
    for idx, element in enumerate(plydata.elements):
        if element.name == "vertex":
            vertex_element = element
            vertex_element_idx = idx
            break

    if vertex_element is None:
        print(
            "[!] Error: Could not find 'vertex' element in the PLY file layout.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Apply our Open3D calculated mask directly to the raw plyfile structural data
    print("[*] Filtering vertex elements while locking structural properties...")
    filtered_vertex_data = vertex_element.data[inlier_mask]

    # Reconstruct the vertex element with the exact same layout schema but updated counts
    new_element = PlyElement.describe(
        filtered_vertex_data, "vertex"
    )
    new_ply = PlyData([new_element], text=False)

    # Save out the new file
    print(f"[*] Writing metadata-preserved cloud to: {output_ply}")
    new_ply.write(output_ply)

    final_count = len(filtered_vertex_data)
    removed_count = initial_count - final_count
    print(f"[+] Success! Removed {removed_count:,} outlier points.")
    print(f"    Final clean point count: {final_count:,}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter a PLY file using DBSCAN while preserving all custom metadata and properties via plyfile."
    )
    parser.add_argument(
        "-i", 
        "--input", 
        type=str, 
        required=True, 
        help="Path to the input .ply file"
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to save the filtered .ply file",
    )

    # DBSCAN Tuning Parameters
    parser.add_argument(
        "-e",
        "--eps",
        type=float,
        default=0.05,
        help="DBSCAN epsilon radius (default: 0.05)",
    )
    parser.add_argument(
        "-m",
        "--min_points",
        type=int,
        default=10,
        help="DBSCAN min points (default: 10)",
    )

    args = parser.parse_args()
    
    if not args.output:
        base_path, ext = os.path.splitext(args.input)
        output_file = base_path + f"_e{args.eps:1.5f}_m{args.min_points}".replace(".", "p") + ext
    else:
        output_file = args.output

    apply_dbscan(args.input, output_file, args.eps, args.min_points)

if __name__ == "__main__":
    main()