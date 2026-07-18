from glob import glob
import os
import shutil

def main():
    output_foldername = "different_heights"
    output_folder = os.path.join(".", "output", output_foldername)
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
        os.mkdir(os.path.join(output_folder, "input"))
    
    source_folder = "./scan_360_images_different_heights/scan_360_images/**/color*.png"
    images = glob(source_folder, recursive=True)
    
    for idx, path in enumerate(images):
        # name = path.rsplit("/", 1)[1]
        new_name = f"color_{idx}.png"
        shutil.copy(path, f"./output/{output_foldername}/input/{new_name}")
        print(f"mv {path} {new_name}")

if __name__ == "__main__":
    
    main()