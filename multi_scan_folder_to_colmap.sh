#!/usr/bin/env bash

colmap_dataset_abspath=$(realpath $1)
dataset_train_root=$colmap_dataset_abspath/undistorted_colmap

if [[ "$2" != "--skip_colmap" ]]; then
    # ## Step 1: tranform dataset into COLMAP dataset
    # # store original files in a subfolder
    # mkdir -p $1/original
    # cp $1/* $1/original

    # # move depth images to depth folder
    # mkdir -p $1/depth
    # mv $1/depth*.png $1/depth

    # # move meta*.json to meta folder
    # mkdir -p $1/meta
    # mv $1/meta*.json $1/meta

    # # move images to images folder
    # mkdir -p $1/images
    # mv $1/color*.png $1/images

    # create sparse folders for COLMAP
    mkdir -p $1/distorted/sparse/1_manual           # -> first stage; manual images.txt etc.
    mkdir -p $1/distorted/sparse/2_triangulated     # -> second stage; COLMAP triangulated points
    mkdir -p $dataset_train_root                    # -> third stage; acts as input root folder for GS

    # this script calculates first the joint angles, converts them to cartesian coordinates and stores them in meta*.json
    # python calculate_poses.py $1

    # this script takes the meta information of the folder and makes it COLMAP ready
    python poses_to_colmap.py $1

    ## Step 2: COLMAP feature extraction, matching and sparse reconstruction
    # mkdir -p $1/sparse/0
    python colmap_caller.py $1 > $1/colmap.log 2>&1

    # Step 3: put the *.bin files into correct folder
    mkdir -p $dataset_train_root/sparse/0
    mv $dataset_train_root/sparse/*.bin $dataset_train_root/sparse/0
else
    echo "Skipping COLMAP processing"
fi

## Step 3: train neural network with COLMAP dataset
cd ../../../../networks/gaussian-splatting

mkdir -p $dataset_train_root/output
python train.py -s $dataset_train_root -m $dataset_train_root/output > $colmap_dataset_abspath/train.log 2>&1