import os
import argparse
from glob import glob
from concurrent.futures import ThreadPoolExecutor

import cv2


class ArgumentError(Exception):
    pass


def rotate_image(input_path, output_dir=None):
    try:
        image_name = os.path.basename(input_path)

        # If no output directory is provided, overwrite the original file
        if output_dir:
            output_path = os.path.join(output_dir, image_name)
        else:
            output_path = input_path
            temp_path = input_path + ".tmp.png"

        # Load image
        img = cv2.imread(input_path)
        if img is None:
            print(f"Could not read {input_path}")
            return

        # Rotate 180 degrees
        rotated = cv2.rotate(img, cv2.ROTATE_180)

        # Save image
        if output_dir:
            cv2.imwrite(output_path, rotated)
        else:
            # Safer overwrite: write temp file, then replace original
            cv2.imwrite(temp_path, rotated)
            os.replace(temp_path, input_path)

    except Exception as e:
        print(f"Error processing {input_path}: {e}")


def batch_rotate(images, output_dir=None):
    valid_extensions = ('.jpg', '.jpeg', '.png')
    image_files = [
        f for f in images
        if f.lower().endswith(valid_extensions)
    ]

    with ThreadPoolExecutor() as executor:
        executor.map(
            lambda img: rotate_image(img, output_dir),
            image_files
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rotate images 180 degrees."
    )

    parser.add_argument(
        "-s",
        "--source",
        required=True,
        help="Source folder or glob pattern containing images "
             "(e.g. './images/*.png')"
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Optional output folder. If omitted, images are replaced in place."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not args.source.endswith(".png"):
        source_pattern = os.path.join(args.source, "*.png")
    else:
        source_pattern = args.source

    images = glob(source_pattern, recursive=True)

    if not images:
        raise ArgumentError(f"No images found for: {args.source}")

    if args.output:
        os.makedirs(args.output, exist_ok=True)

    print(f"Starting image rotation for {len(images)} images...")

    if args.output:
        print(f"Output directory: {args.output}")
    else:
        print("Replacing original images in place")

    batch_rotate(images, args.output)

    print("Process finished!")