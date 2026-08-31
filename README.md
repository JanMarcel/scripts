# Scripts related to automatic COLMAP dataset creation and Gaussian splatting

## Overview

This script is the main end-to-end pipeline for the Gaussian Splatting workflow in this [https://github.com/graphdeco-inria/gaussian-splatting] repo. It prepares a raw dataset, cleans and organizes the images, converts the data for training, runs a 100k-iteration Gaussian Splatting training job, and writes the output plus loss log.

---

## Command usage

Before running the shell script, you first must declare, where you have cloned the Gaussian splatting git repo in the shell script *convert_and_train_100k_iter.sh* on line 53:

```bash
gaussian_splatting_root="/path/to/your/git-repo/gaussian-splatting" 
# e.g. /home/myaccount/networks/gaussian-splatting
```

```bash
bash convert_and_train_100k_iter.sh <unzipped_pictures_folder> [--skip_colmap]
```

Examples:

```bash
bash convert_and_train_100k_iter.sh /path/to/dataset
bash convert_and_train_100k_iter.sh /path/to/dataset --skip_colmap
```

The script expects:

- a root folder with the raw image dataset
- a local path to the Gaussian Splatting repository in the script
- optional `--skip_colmap` if the dataset is already in COLMAP format

It processes data under:

```text
<dataset_root>/0000_MERGED
```

and saves logs/output in there.

There exist also two more versions of this script:
- *convert_and_train_original*.sh: 30k iterations are trained. This is the original iterations from the Gaussian splatting repo
- *convert_and_train_5m_iter*.sh : 5 million iterations are trained. Although the results will probably not be any better.

The usage is exactly the same as with *convert_and_train_100k_iter.sh*.

---

## Common issues and fixes

### Missing Gaussian Splatting repository path

The script contains:

```bash
gaussian_splatting_root="/path/to/your/git-repo/gaussian-splatting"
```

If this path is invalid, the script stops. Set it to the actual local path of the Gaussian Splatting repo.

### No images are found

Check whether:

- the source folders match the patterns used in the script
- the dataset contains PNG files
- the merge step succeeded

### Training is very slow

This is normal for large datasets and 100k iterations. Check GPU availability, VRAM usage, and the training log.

### Scene is rotated incorrectly

The script rotates the images on purpose. If this step is skipped or the dataset is not normalized, the output reconstruction may be rotated by 180°.

---

## Processing pipeline

The script does the following in order:

1. validates the input folder
2. sets the processing folder to `0000_MERGED`
3. merges selected subfolders into one dataset
4. reduces the number of input images
5. rotates images to avoid orientation issues
6. randomizes image order
7. moves PNGs into an `input` folder
8. runs the external `convert.py` step
9. starts `train.py` with `--iterations 100000`
10. creates a loss plot from the training log

The training command is based on the external Gaussian Splatting repo and writes the output to:

```text
<dataset_root>/0000_MERGED/output
```

while the logs are stored in:

```text
<dataset_root>/0000_MERGED/train.log
```

and:

```text
<dataset_root>/0000_MERGED/convert.log
```

---

## Related helper scripts

This repo contains small helper scripts that support the main Gaussian Splatting workflow. The most relevant ones are:

- `merge_subfolders.py` — combines image folders
- `reduce_pictures_in_folder.py` — reduces dataset size
- `rotate_pictures.py` — fixes image orientation
- `randomize_images.py` — shuffles image order for better reconstruction
- `plot_loss.py` — visualizes training loss

Other scripts in the repo handle tasks like:

- converting images or datasets for COLMAP pipelines
- cleaning or filtering point clouds / PLY files
- rotating, copying, or reorganizing image folders
- preparing raw data for reconstruction or training

These scripts are mostly support utilities, while this script is the main entry point for the full training workflow.
