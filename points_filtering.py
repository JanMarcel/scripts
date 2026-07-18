import argparse
import os
import subprocess
import sys
import traceback

def colmap(command: str) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while calling COLMAP: {e}")
        traceback.print_exc()
        sys.exit(1)

def frange(start: float, step:float, stop:float):
    while start < stop:
        yield start
        start += step

def do_colmap_steps(image_folder: str,
                    sparse_folder: str, 
                    output_folder: str, 
                    min_track_len: int = 2, 
                    max_reproj_error: float = 4, 
                    min_tri_angle: float = 1.5
    ) -> None:

    os.makedirs(output_folder, exist_ok=True)
    log_dir = os.path.join(output_folder, 'log')
    os.makedirs(log_dir, exist_ok=True)
    command = [
        'colmap', 'point_filtering',
        '--input_path',         sparse_folder,               # triangulated intermediate triangulation
        '--output_path',        output_folder,
        '--log_path',           log_dir,
        '--min_track_len',      f'{min_track_len}',          # CRITICAL: Drops all weak 2-view matches
        '--max_reproj_error',   f'{max_reproj_error}',       # Lower = stricter alignment rule
        '--min_tri_angle',      f'{min_tri_angle}'           # Drops shallow depth estimation errors
    ]
    colmap(command)
    
    undistorted_folder = f"{output_folder}/undistorted_colmap/"
    os.makedirs(undistorted_folder, exist_ok=True)
    command = [
        'colmap', 'image_undistorter',
        '--image_path',     f'{image_folder}',
        '--input_path',     output_folder,  # Reads your manual configuration layout
        '--output_path',    undistorted_folder,
        '--output_type',    'COLMAP'
    ]
    colmap(command)
    
    point_cloud_folder = os.path.join(output_folder, "point_cloud")
    os.makedirs(point_cloud_folder)
    command = [
        'colmap', 'model_converter',
        '--input_path', output_folder,
        '--output_path', f'{point_cloud_folder}/points3D.ply',
        '--output_type', 'PLY'
    ]
    colmap(command)

def main(image_folder: str, mapped_folder: str):
    output_folder_template = os.path.join(mapped_folder, "..", "{}")

    # variate min_track_len
    OPTS_min_track_len = [i for i in range(3, 15)]
    # Tested 3 - 15: we can go quite high, >6..15
    # for mtl in OPTS_min_track_len:
    #     output_folder = output_folder_template.format(f"mtl_{mtl}")
    #     do_colmap_steps(
    #         image_folder,
    #         mapped_folder,
    #         output_folder,
    #         min_track_len=mtl
    #     )
        
    # variate max_reproj_error
    OPTS_max_reproj_error = [f for f in frange(0.5, 0.25, 4)]
    # Tested until 2.0: 0.5 looks good enough for now, 
    # maybe a bit higher, but relatively low seems good
    # for mre in OPTS_max_reproj_error:
    #     output_folder = output_folder_template.format(f"mre_{round(mre, 2)}".replace(".", "p"))
    #     do_colmap_steps(
    #         image_folder,
    #         mapped_folder,
    #         output_folder,
    #         max_reproj_error=mre
    #     )
        
    # variate min_tri_angle
    OPTS_min_tri_angle = [f for f in frange(1.5, 0.25, 15)]
    for mta in OPTS_min_tri_angle:
        output_folder = output_folder_template.format(f"mta_{round(mta, 2)}".replace(".", "p"))
        do_colmap_steps(
            image_folder,
            mapped_folder,
            output_folder,
            min_tri_angle=mta
        )
        
def make_output_folder_name(mapped_folder: str, mtl: int, mre: float, mta: float) -> str:
    suffix = f'mtl_{mtl}__mre_{round(mre, 2)}__mta_{round(mta, 2)}'.replace(".", "p")
    return os.path.join(mapped_folder, "..", suffix)
        
def filter_points(image_folder: str, mapped_folder: str):
    mtl = 6
    mre = 1.0
    mta = 10
    
    output_folder = make_output_folder_name(mapped_folder, mtl, mre, mta)
    do_colmap_steps(
        image_folder,
        mapped_folder,
        output_folder,
        min_track_len=mtl,
        max_reproj_error=mre,
        min_tri_angle=mta
    )
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test out different parameters from matched and mapped dataset"
    )
    
    parser.add_argument(
        "-img", "--image_folder", 
        type=str, 
        help="Folder to input images"
    )
    
    parser.add_argument(
        "-m", "--mapped_folder", 
        type=str, 
        help="Folder to mapped configuration"
    )
    
    args = parser.parse_args()
    # main(args.image_folder, args.mapped_folder)
    filter_points(args.image_folder, args.mapped_folder)