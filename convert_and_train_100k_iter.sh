#!/bin/bash
# export CUDA_VISIBLE_DEVICES=0,2   # would hide GPU with index 1
# export CUDA_VISIBLE_DEVICES=1 # if GPU 0 is occupied

if [[ -z "$1" ]]; then
    echo -e "\nPlease provide the path to the root of the dataset folder.\n"
    echo -e "\tusage: bash convert_and_train.sh <dataset_root> [--skip_colmap]"
    echo ""
    echo -e "options:"
    echo -e "\t--skip_colmap: skip the convert.py step"
    echo ""
    exit 1
fi

gaussian_splatting_root="/home/ja122sch/Documents/Teamprojekt/networks/gaussian-splatting"

if [[ "$2" != "--skip_colmap" ]]; then
    python $gaussian_splatting_root/convert.py -s $1 > $1/convert.log 2>&1
else
    echo "Skipping COLMAP conversion. Dataset has to be already in COLMAP format!"
fi

mkdir -p $1/output
# takes dataset in $1 and uses original image sizes (-r 1)
python $gaussian_splatting_root/train.py -s $1 -m $1/output -r 1 --iterations 100000 --test_iterations 7000 30000 40000 50000 60000 70000 80000 90000 100000 --save_iterations 7000 30000 40000 50000 60000 70000 80000 90000 100000 > $1/train.log 2>&1