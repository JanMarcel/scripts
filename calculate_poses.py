from glob import glob
import json
from math import floor
import numpy as np
import os
import sys
import roboticstoolbox as rtb

from poses_to_colmap import META_INFO_FOLDER_NAME, DEPTH_IMAGES_FOLDER_NAME, COLOR_INPUT_IMAGES_FOLDER_NAME

def calculate_cartesian(joint_angles_degrees):
    # 1. Define the link lengths for the Dobot Magician E6 (in meters)
    # These represent the physical distances between each joint axis
    d1 = 0.101   # Height from base to joint 2 axis
    a2 = 0.160   # Length of the inner arm (Link 2)
    a3 = 0.189   # Length of the outer arm (Link 3)
    d4 = 0.065   # Offset to joint 5 axis
    d5 = 0.167   # Length to the tool flange center
    # (Adjust tool offsets if you have a custom gripper attached)

    # 2. Build the robot model using standard DH parameters
    # Replicating the 6-axis configuration of the E6
    robot = rtb.DHRobot([
        rtb.RevoluteMDH(d=d1, a=0.0, alpha=0.0),       # Joint 1
        rtb.RevoluteMDH(d=0.0, a=0.0, alpha=-np.pi/2),  # Joint 2
        rtb.RevoluteMDH(d=0.0, a=a2,  alpha=0.0),       # Joint 3
        rtb.RevoluteMDH(d=d4,  a=a3,  alpha=-np.pi/2),  # Joint 4
        rtb.RevoluteMDH(d=0.0, a=0.0, alpha=np.pi/2),   # Joint 5
        rtb.RevoluteMDH(d=d5,  a=0.0, alpha=-np.pi/2)   # Joint 6
    ], name="Dobot Magician E6")
    
    joint_angles_radians = np.radians(joint_angles_degrees)

    transformation_matrix = robot.fkine(joint_angles_radians)
    return transformation_matrix

def calculate_joint_angles_for_image(meta_data, general_config):
    # calculate direction via starting and ending position
    if general_config["starting_position"]["J1"] < general_config["ending_position"]["J1"]:
        direction = 1
    else:
        direction = -1
    
    # calculate the pose for each image
    pose = {
        "J1": general_config["starting_position"]["J1"] + (meta_data["frame_index"] - 1) * general_config["degrees_per_image"] * direction,
        "J2": general_config["starting_position"]["J2"],
        "J3": general_config["starting_position"]["J3"],
        "J4": general_config["starting_position"]["J4"],
        "J5": general_config["starting_position"]["J5"],
        "J6": general_config["starting_position"]["J6"]
    }
    
    meta_data["pose"] = pose
    return pose

def calculate_poses_for_folder(folder):
    # path configs
    GENERAL_CONFIG_FILE_NAME = "general_config.json"
    GENERAL_CONFIG_FILE_PATH = os.path.join(folder, GENERAL_CONFIG_FILE_NAME)
    
    if not os.path.exists(GENERAL_CONFIG_FILE_PATH):
        raise FileNotFoundError(f"{GENERAL_CONFIG_FILE_NAME} has to be present in dataset! Full path searched for: {GENERAL_CONFIG_FILE_PATH}")
    
    with open(GENERAL_CONFIG_FILE_PATH, "r") as f:
        general_config = json.load(f)
    
    # check that the number of images matches the number of calculated images
    total_rotation = abs(general_config["starting_position"]["J1"] - general_config["ending_position"]["J1"])
    num_images_calc = floor(total_rotation / general_config["degrees_per_image"]) + 1  # +1 because we also take the starting position into account
    metajson_paths = glob(os.path.join(folder, META_INFO_FOLDER_NAME, "meta*.json"))   # meta*.json <-- 1 -- 1 --> color*.png
    if len(metajson_paths) != num_images_calc:
        print(f"[WARN] Number of images ({len(metajson_paths)}) does not match the number of calculated images ({num_images_calc})! This may be a result of pruning the dataset.")

    for meta in metajson_paths:
        with open(meta, "r") as f:
            meta_data = json.load(f)

        joint_pose = calculate_joint_angles_for_image(meta_data, general_config)
        cart_matrix = calculate_cartesian(list(joint_pose.values()))

        # save A matrix in json format
        meta_data["T_base_ee"] = cart_matrix.A.tolist()
        
        # save the pose to the existing meta*.json file
        with open(meta, "w") as f:
            json.dump(meta_data, f, indent=4)

def main(folder):
    calculate_poses_for_folder(folder)

if __name__ == "__main__":
    # pass in the folder for which you want to calculate the poses as a command line argument
    if len(sys.argv) != 2:
        print("Usage: python calculate_poses.py <folder>")
        sys.exit(1)
    folder = sys.argv[1]
    main(folder)