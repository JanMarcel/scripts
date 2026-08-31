#!/bin/bash

###############################################################################
# This script converts a dataset of pictures to COLMAP format and trains
# a Gaussian Splatting model on it.
# Usage: bash convert_and_train.sh <unzipped_pictures_folder> [--skip_colmap]
###############################################################################

if [[ -z "$1" ]]; then
    echo -e "\nPlease provide the path to the root of the unzipped pictures folder.\n"
    echo -e "\tusage: bash convert_and_train.sh <unzipped_pictures_folder> [--skip_colmap]"
    echo ""
    echo -e "options:"
    echo -e "\t--skip_colmap: skip the convert.py step"
    echo ""
    exit 1
fi

# merged subfolders folder
export MERGED_FOLDER_NAME="0000_MERGED"

# colmap root folder
export COLMAP_DATA_ROOT="$1/$MERGED_FOLDER_NAME"

# GPU Settings
# You can set the CUDA_VISIBLE_DEVICES environment variable to specify which GPUs to use. For example, if you want to use GPU 0 and GPU 2, you can set it like this:
# export CUDA_VISIBLE_DEVICES=0,2   # would hide GPU with index 1
export CUDA_VISIBLE_DEVICES=1 # if GPU 0 is occupied

## Start data preprocessing

# 1) reduce dataset
# - folders with factor 1 -> do nothing
# - pictures with factor 15
python merge_subfolders.py "$1/*Hoehenlinie*" "$1/*Gesenkt*" "$1/*Gehoben*" "$1/*Nach*"
python reduce_pictures_in_folder.py "$COLMAP_DATA_ROOT" -f 15 --execute

# 2) rotate pictures
# this is needed, because the GS interprets the rotation of images differently than normally.
# If this would not be done, the generated point cloud would be rotated by 180 degrees.
python rotate_pictures.py "$COLMAP_DATA_ROOT"

# 3) randomize order of pictures
# this way COLMAP generates better sparse point clouds
python randomize_images.py "$COLMAP_DATA_ROOT"

# 4) move pictures to the correct folder
mkdir -p "$COLMAP_DATA_ROOT/input"
mv "$COLMAP_DATA_ROOT"/*.png "$COLMAP_DATA_ROOT/input/"

## End data preprocessing

gaussian_splatting_root="/path/to/your/git-repo/gaussian-splatting" # e.g. /home/myaccount/networks/gaussian-splatting
if [ ! -d "$gaussian_splatting_root" ]; then
  echo "You have to set the gaussian_splatting_root variable to the path of the gaussian-splatting repository."
  echo "You can do this in the following file: <this_git_repo>/convert_and_train_100k_iter.sh"
  exit 1
fi

# Start COLMAP conversion

if [[ "$2" != "--skip_colmap" ]]; then
    python $gaussian_splatting_root/convert.py -s $COLMAP_DATA_ROOT > $COLMAP_DATA_ROOT/convert.log 2>&1
else
    echo "Skipping COLMAP conversion. Dataset has to be already in COLMAP format!"
fi

# End of COLMAP conversion

mkdir -p $COLMAP_DATA_ROOT/output

# Start training
# takes dataset in $COLMAP_DATA_ROOT and uses original image sizes (-r 1)
python $gaussian_splatting_root/train.py \
        -s $COLMAP_DATA_ROOT           \
        -m $COLMAP_DATA_ROOT/output    \
        -r 1            \
        --iterations 5000000 \
        --test_iterations 7000 30000 100000 500000 1000000 2000000 3000000 4000000 5000000 \
        --save_iterations 7000 30000 100000 500000 1000000 2000000 3000000 4000000 5000000 \
        --checkpoint_iterations 5000000 \
        > $COLMAP_DATA_ROOT/train.log 2>&1

# make png of training loss
python plot_loss.py $COLMAP_DATA_ROOT/train.log

# EOF