from __future__ import annotations
from typing import Literal

import argparse
import numpy as np
from plyfile import PlyData


def get_rotation_matrix(axis: Literal["x", "y", "z"], degrees: float):
    """Calculates the 3D rotation matrix for a given axis and angle in degrees."""
    radians = np.radians(degrees)
    cos_a = np.cos(radians)
    sin_a = np.sin(radians)

    if axis == "x":
        return np.array([[1, 0, 0], [0, cos_a, -sin_a], [0, sin_a, cos_a]])
    elif axis == "y":
        return np.array([[cos_a, 0, sin_a], [0, 1, 0], [-sin_a, 0, cos_a]])
    elif axis == "z":
        return np.array([[cos_a, -sin_a, 0], [sin_a, cos_a, 0], [0, 0, 1]])
    else:
        raise ValueError(f"Unknown axis: {axis}")


def rotate_point_cloud_preserve_meta(input_path, output_path, axis, degrees):
    print(f"Loading point cloud from: {input_path}")
    
    # Read the PLY file using plyfile. 
    # mmap=False ensures we can modify the data directly in memory.
    plydata = PlyData.read(input_path)

    # Check if 'vertex' elements exist
    if "vertex" not in plydata:
        print("Error: The PLY file does not contain a 'vertex' element.")
        return

    print(f"Loaded point cloud. Found properties: {', '.join(p.name for p in plydata['vertex'].properties)}")

    # 1. Extract coordinates (x, y, z)
    x = plydata["vertex"]["x"]
    y = plydata["vertex"]["y"]
    z = plydata["vertex"]["z"]
    coords = np.stack([x, y, z], axis=-1)

    print(f"Rotating {len(coords)} points {degrees}° around the {axis.upper()}-axis...")

    # 2. Calculate the center of the cloud (pivot point)
    center = coords.mean(axis=0)

    # 3. Apply the rotation
    R = get_rotation_matrix(axis, degrees)
    # Shift to origin, rotate, and shift back
    rotated_coords = np.dot(coords - center, R.T) + center

    # 4. Write ONLY the modified x, y, z coordinates back into the plydata structure
    # All other properties (intensity, colors, etc.) are untouched!
    plydata["vertex"]["x"] = rotated_coords[:, 0]
    plydata["vertex"]["y"] = rotated_coords[:, 1]
    plydata["vertex"]["z"] = rotated_coords[:, 2]

    # Force binary output format
    plydata.text = False

    print(f"Saving point cloud to: {output_path}")
    plydata.write(output_path)
    print("Done! Point cloud rotated with 100% metadata preserved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rotate a binary PLY point cloud while preserving all custom metadata properties."
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input binary PLY file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to save the output PLY file.",
    )
    parser.add_argument(
        "-a",
        "--axis",
        choices=["x", "y", "z"],
        default="z",
        help="The axis to rotate around: 'x', 'y', or 'z'. Default is 'z'.",
    )
    parser.add_argument(
        "-d",
        "--degrees",
        type=float,
        default=180.0,
        help="The amount of rotation in degrees. Default is 180.0.",
    )

    args = parser.parse_args()

    rotate_point_cloud_preserve_meta(
        args.input, args.output, args.axis.lower(), args.degrees
    )