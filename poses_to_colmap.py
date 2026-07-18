from __future__ import annotations

from glob import glob
import json
import numpy as np
from numpy.typing import NDArray
import os
from scipy.spatial.transform import Rotation as R
import sys
import yaml

# # 1. Paste your calibration matrix directly from the YAML file
# # T_end_effector_camera
# T_ee_cam = np.array([
#     [ 0.9999249492669029, -0.012050044093201309,  0.0022118478549487254,  0.030043765102666358],
#     [ 0.012044859861057826, 0.999924714442741,     0.0023423914126668444,  0.0002548251899627931],
#     [-0.0022399072545565657,-0.002315574217027285, 0.9999948104523024,     0.11139574690677029],
#     [ 0.0,                  0.0,                   0.0,                    1.0]
# ])

# # 2. Coordinate System Adjustment: Converts Robotics Axis to CV Axis
# # (Flips Y and Z to match Computer Vision conventions)
# T_cv_robot = np.array([
#     [1,  0,  0, 0],
#     [0, -1,  0, 0],
#     [0,  0, -1, 0],
#     [0,  0,  0, 1]
# ])

SPARSE_FOLDER_NAME = r"distorted/sparse/1_manual"
COLOR_INPUT_IMAGES_FOLDER_NAME = "images"
META_INFO_FOLDER_NAME = "meta"
DEPTH_IMAGES_FOLDER_NAME = "depth"

def load_calibration_matrices() -> tuple[NDArray, NDArray]:
    """
    Reads the calibration YAML file and returns the 4x4 Homogeneous
    Transformation matrices: T_ee_cam and T_cv_robot.
    """
    calibration_folder = os.path.join(os.path.dirname(__file__), "..", "calibration")
    YAML_FILE_NAME = "handeye_result.yaml"
    YAML_FILE_PATH = os.path.join(calibration_folder, YAML_FILE_NAME)
    
    # 1. Load and parse the YAML data
    with open(YAML_FILE_PATH, 'r') as file:
        calib_data = yaml.safe_load(file)
        
    # 2. Extract the raw 4x4 nested list structure from T_end_effector_camera
    matrix_list = calib_data['T_end_effector_camera']['matrix']
    
    # Convert it into a robust 4x4 NumPy float array
    T_ee_cam = np.array(matrix_list, dtype=np.float64)
    
    # 3. Create the static Computer Vision axis realignment matrix
    # This maps: Robotics Space -> Computer Vision Space (Y-Down, Z-Forward)
    T_cv_robot = np.array([
        [1,  0,  0, 0],
        [0, -1,  0, 0],
        [0,  0, -1, 0],
        [0,  0,  0, 1]
    ], dtype=np.float64)
    
    return T_ee_cam, T_cv_robot

def convert_robot_pose_to_colmap(T_base_ee: NDArray, T_ee_cam: NDArray, T_cv_robot: NDArray) -> tuple[list[float], list[float]]:
    """
    Takes a 4x4 matrix of the Dobot's end-effector relative to the base,
    applies the Orbbec hand-eye calibration, fixes the axes, and inverts to W2C.
    """
    # Combine forward kinematics with hand-eye calibration
    T_base_cam = T_base_ee @ T_ee_cam
    
    # Adjust axes standard (Robotics space -> CV space)
    T_c2w = T_base_cam @ T_cv_robot
    
    # Invert to World-To-Camera (W2C) format for COLMAP
    T_w2c = np.linalg.inv(T_c2w)
    
    # Extract structural parameters
    rotation_matrix = T_w2c[0:3, 0:3]
    translation_vector = T_w2c[0:3, 3]
    
    # Format quaternion as [qw, qx, qy, qz]
    r = R.from_matrix(rotation_matrix)
    quat = r.as_quat() # returns [qx, qy, qz, qw]
    colmap_quat = [quat[3], quat[0], quat[1], quat[2]]
    
    return colmap_quat, translation_vector

def get_dataset_samples(folder: str) -> list:
    # dataset_samples = [
        # ("frame_001.png", T_base_ee_matrix_1),
        # ("frame_002.png", T_base_ee_matrix_2),
    # ]
    """
    Reads the dataset folder and constructs a list of tuples containing image paths and their corresponding FK matrices.
    """
    dataset_samples = []
    meta_json_paths = sorted(glob(os.path.join(folder, META_INFO_FOLDER_NAME, "meta*.json")))
    for meta_path in meta_json_paths:
        with open(meta_path, "r") as f:
            meta_data = json.load(f)
        
        img_name = os.path.join(folder, COLOR_INPUT_IMAGES_FOLDER_NAME, meta_data["color_file"])
        T_base_ee = np.array(meta_data["T_base_ee"])
        
        dataset_samples.append((img_name, T_base_ee))
    return dataset_samples

def generate_colmap_images_file(folder: str, dataset_samples: list):
    # path configs
    IMAGES_FILE_NAME = "images.txt"
    IMAGES_FILE_PATH = os.path.join(folder, SPARSE_FOLDER_NAME, IMAGES_FILE_NAME)

    T_ee_cam, T_cv_robot = load_calibration_matrices()
    with open(IMAGES_FILE_PATH, "w") as f:
        for idx, (img_name, T_base_ee) in enumerate(dataset_samples, start=1):
            q, t = convert_robot_pose_to_colmap(T_base_ee, T_ee_cam, T_cv_robot)
            
            # Line 1: Target parameters for COLMAP
            f.write(f"{idx} {q[0]} {q[1]} {q[2]} {q[3]} {t[0]} {t[1]} {t[2]} 1 {os.path.basename(img_name)}\n")
            # Line 2: Empty line strictly required by the parser
            f.write("\n")

def generate_colmap_cameras_file(folder: str) -> None:
    # Path configs
    calibration_folder = os.path.join(os.path.dirname(__file__), "..", "calibration")
    YAML_FILE_NAME = "camera_intrinsics.yaml"
    YAML_FILE_PATH = os.path.join(calibration_folder, YAML_FILE_NAME)
    OUTPUT_FILE_NAME = "cameras.txt"
    OUTPUT_FILE_PATH = os.path.join(folder, SPARSE_FOLDER_NAME, OUTPUT_FILE_NAME)
    
    # 1. Load the yaml structure
    with open(YAML_FILE_PATH, 'r') as file:
        data = yaml.safe_load(file)
        
    # 2. Extract Color profile parameters
    color_info = data['color']['intrinsics']
    dist_info = data['color']['distortion']
    
    width = color_info['width']
    height = color_info['height']
    fx = color_info['fx']
    fy = color_info['fy']
    cx = color_info['cx']
    cy = color_info['cy']
    
    k1 = dist_info['k1']
    k2 = dist_info['k2']
    p1 = dist_info['p1']
    p2 = dist_info['p2']
    # Note: COLMAP's OPENCV model ignores k3, so we drop it safely here
    
    # 3. Write out to the file
    with open(OUTPUT_FILE_PATH, 'w') as f:
        # Standard COLMAP file information headers
        f.write("# Camera list with one line of data per camera:\n")
        f.write("#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        
        # Structure payload mapping
        # 1 = CAMERA_ID (Must match the camera IDs in your images.txt file)
        f.write(f"1 OPENCV {width} {height} {fx} {fy} {cx} {cy} {k1} {k2} {p1} {p2}\n")

def generate_colmap_points3D_file(folder: str) -> None:
    # Path configs
    OUTPUT_FILE_NAME = "points3D.txt"
    OUTPUT_FILE_PATH = os.path.join(folder, SPARSE_FOLDER_NAME, OUTPUT_FILE_NAME)
    
    # Create an empty points3D.txt file for COLMAP
    with open(OUTPUT_FILE_PATH, 'w') as f:
        f.write("# 3D point list with one line of data per point:\n")
        f.write("#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[]\n")
        f.write("# Number of points: 0\n")
        

def main(folder: str):
    # 1) images.txt
    # 2) cameras.txt
    # 3) points3D.txt
    
    ## 1)
    dataset_samples = get_dataset_samples(folder)
    generate_colmap_images_file(folder, dataset_samples)
            
    ## 2)
    generate_colmap_cameras_file(folder)

    ## 3)
    generate_colmap_points3D_file(folder)

if __name__ == "__main__":
    # folder is command line argument, e.g., "dataset"
    if len(sys.argv) != 2:
        print("Usage: python poses_to_colmap.py <dataset_folder>")
        sys.exit(1) 
    folder = sys.argv[1]
    main(folder)
    
