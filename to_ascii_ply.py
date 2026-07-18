import argparse
import os
import plyfile

def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Convert a PLY file (binary or ASCII) to an ASCII formatted file."
    )
    
    # Expect the input file as a required argument
    parser.add_argument(
        "input_file", 
        type=str, 
        help="Path to the input PLY file."
    )
    
    # Optional output file argument
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        help="Path to the output file. If omitted, defaults to <input_file>_ascii.txt"
    )

    args = parser.parse_args()

    # Determine the output filename if not explicitly provided
    if args.output:
        output_file = args.output
    else:
        # Split the extension to safely insert '_ascii.txt'
        base_path, _ = os.path.splitext(args.input_file)
        output_file = f"{base_path}_ascii.ply"

    # Read and convert the data
    try:
        # 1. Read the original PLY file with all metadata structures fully intact
        data = plyfile.PlyData.read(args.input_file)
        
        # 2. Mutate the existing object in-place.
        # This forces the library to switch the target formatting strategy to ASCII 
        # without touching, decoupling, or dropping any global or element-specific metadata.
        data.text = True
        
        # 3. Stream the exact, modified object to the output path
        data.write(output_file)
        print(f"Successfully converted to ASCII PLY: {output_file}")
        
    except Exception as e:
        print(f"Error processing PLY file: {e}")

if __name__ == "__main__":
    main()