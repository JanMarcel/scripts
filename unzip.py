import argparse
import shutil
from pathlib import Path
from zipfile import ZipFile

def stream_extract_zip(zip_path, extract_to):
    """Extracts a ZIP file sequentially using a memory-efficient stream loop."""
    zip_path = Path(zip_path)
    extract_to = Path(extract_to)

    if not zip_path.exists():
        print(f"Error: The file '{zip_path}' does not exist.")
        return

    print(f"Opening archive: {zip_path.name}...")
    
    with ZipFile(zip_path, "r") as zip_ref:
        files = zip_ref.infolist()
        total_files = len(files)
        
        if total_files == 0:
            print("The ZIP file appears to be empty.")
            return

        print(f"Extracting {total_files} items sequentially...")
        
        for i, file_info in enumerate(files):
            # Resolve the intended output path
            target_path = extract_to / file_info.filename
            
            # If it's a directory entry, create it and move on
            if file_info.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue
                
            # Ensure parent directories exist for the file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Stream the data in chunks from the ZIP to the disk (low RAM footprint)
            with zip_ref.open(file_info) as source_stream:
                with open(target_path, "wb") as target_file:
                    shutil.copyfileobj(source_stream, target_file)
            
            # Print status update every 10%
            log_interval = max(1, total_files // 10)
            if i % log_interval == 0 or i == total_files - 1:
                percent = int(((i + 1) / total_files) * 100)
                print(f"Progress: {percent}% ({i + 1}/{total_files} items completed)")

    print(f"\nSuccess! All files extracted to: {extract_to.resolve()}")

def main():
    parser = argparse.ArgumentParser(
        description="Simple, single-threaded ZIP extractor with a constant memory footprint."
    )
    parser.add_argument(
        "zip_file", 
        type=str, 
        help="Path to the target ZIP archive."
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default=".", 
        help="Destination directory for extracted files. (Default: current directory)"
    )

    args = parser.parse_args()
    stream_extract_zip(zip_path=args.zip_file, extract_to=args.output)

if __name__ == "__main__":
    main()