import os
import subprocess
import sys
import traceback

def colmap(command: str):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while calling COLMAP: {e}")
        traceback.print_exc()
        sys.exit(1)

def main(folder: str):
    # feature extraction
    print("Extracting features...")
    command = ['colmap', 'feature_extractor',
               '--database_path', f'{folder}/distorted/database.db',
               '--image_path', f'{folder}/images',
               '--ImageReader.camera_model', 'OPENCV',
               '--ImageReader.single_camera', '1',
               '--FeatureExtraction.use_gpu', '1',
               '--SiftExtraction.max_num_features', f'{2**15}'  # 2**15 = 32768
               ]
    colmap(command)
    
    # feature mapping
    print("Matching features...")
    command = [
        'colmap', 'exhaustive_matcher',
        '--database_path', f'{folder}/distorted/database.db',
        '--ExhaustiveMatching.block_size', '180',
        '--FeatureMatching.num_threads', '-1',
        '--FeatureMatching.use_gpu', '1',
        # '--FeatureMatching.skip_geometric_verification', '1',
        # '--FeatureMatching.skip_image_pairs_in_same_frame', '1',
    ]
    colmap(command)
    
    print("Triangulating points...")
    manual_folder = f"{folder}/distorted/sparse/1_manual"
    triangulated_folder = f"{folder}/distorted/sparse/2_triangulated"
    os.makedirs(manual_folder, exist_ok=True)
    os.makedirs(triangulated_folder, exist_ok=True)
    gpu_idx = os.environ.get("CUDA_VISIBLE_DEVICES", 0)
    command = [
        'colmap', 'point_triangulator',
        '--database_path', f'{folder}/distorted/database.db',
        '--image_path', f'{folder}/images',
        '--input_path', manual_folder,
        '--output_path', triangulated_folder,
        '--Mapper.ba_use_gpu', "1",
        '--Mapper.ba_gpu_index', str(gpu_idx),
        '--Mapper.tri_ignore_two_view_tracks', '1',          # Restrict to robust 3+ view tracks
        '--Mapper.tri_merge_max_reproj_error', '2.0',        # Strict merge threshold (in pixels)
        '--Mapper.tri_complete_max_reproj_error', '2.0',     # Strict completion threshold (in pixels)
        '--Mapper.tri_min_angle', '3.0'                      # Avoid shallow, uncertain depth vectors
    ]
    colmap(command)
    
    print("Filtering outlier points...")
    filtered_dir = f"{folder}/distorted/sparse/3_filtered"
    os.makedirs(filtered_dir, exist_ok=True)
    command = [
        'colmap', 'point_filtering',
        '--input_path', triangulated_folder,        # triangulated intermediate triangulation
        '--output_path', filtered_dir,
        '--min_track_len', '4',                     # CRITICAL: Drops all weak 2-view matches
        '--max_reproj_error', '2.51',               # Lower = stricter alignment rule
        '--min_tri_angle', '4.5'                    # Drops shallow depth estimation errors
    ]
    colmap(command)
    
    print("Undistorting images to PINHOLE format for Gaussian Splatting...")
    undistorted_folder = f"{folder}/undistorted_colmap/"
    os.makedirs(undistorted_folder, exist_ok=True)
    command = [
        'colmap', 'image_undistorter',
        '--image_path', f'{folder}/images',
        '--input_path', filtered_dir,  # Reads your manual configuration layout
        '--output_path', undistorted_folder,
        '--output_type', 'COLMAP'
    ]
    colmap(command)


if __name__ == '__main__':
    # pass in the folder for which you want to calculate the poses as a command line argument
    if len(sys.argv) != 2:
        print("Usage: python colmap_caller.py <folder>")
        sys.exit(1)
    folder = sys.argv[1]
    main(folder)