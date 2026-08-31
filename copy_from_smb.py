import os
import sys
import shutil
import smbclient
import time
from pathlib import Path
from dotenv import load_dotenv
import traceback


def main():
    load_dotenv()
    
    try:
        username = os.environ["USERNAME"]
        password = os.environ["PASSWORD"]

    except KeyError as e:
        traceback.print_exc()
        print("USERNAME and PASSWORD must be set in file called .env!")
        sys.exit(1)
            
    smbclient.ClientConfig(username=username, password=password)

    zip_file = r"images_360deg_poses.zip"
    folder = r"Dobot_3D_Scan"
    remote = os.path.join(r"\\ei-data.ei.htwg-konstanz.de\ei-alle", folder, zip_file)
    local = os.path.join(".", zip_file)

    with smbclient.open_file(remote, "rb") as remote_fh:
        with open(local, "wb") as local_fh:
            shutil.copyfileobj(remote_fh, local_fh)

if __name__ == '__main__':
    main()

