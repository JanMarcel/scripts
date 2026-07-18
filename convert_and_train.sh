#!/bin/bash
# export CUDA_VISIBLE_DEVICES=0,2   # would hide GPU with index 1
# export CUDA_VISIBLE_DEVICES=1 # if GPU 0 is occupied
gaussian_splatting_root="/home/ja122sch/Documents/Teamprojekt/networks/gaussian-splatting"

if [[ "$2" != "--skip_colmap" ]]; then
    python $gaussian_splatting_root/convert.py -s $1 > $1/convert.log 2>&1
else
    echo "Skipping COLMAP conversion. Dataset has to be already in COLMAP format!"
fi

mkdir -p $1/output

# takes dataset in $1 and uses original image sizes (-r 1)
python $gaussian_splatting_root/train.py -s $1 -m $1/output -r 1 > $1/train.log 2>&1