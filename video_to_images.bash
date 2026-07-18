abspath_input=$(realpath $1)
folder_path=${abspath_input%.*}
folder_path_with_suffix="$folder_path"_images
mkdir -p $folder_path_with_suffix
ffmpeg -i $1 -qscale:v 1 -qmin 1 -vf fps=5 $folder_path_with_suffix/%04d.jpg