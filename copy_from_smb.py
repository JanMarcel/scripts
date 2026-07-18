import os
import shutil
import smbclient
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

smbclient.ClientConfig(username=os.environ["USERNAME"], password=os.environ["PASSWORD"])

zip_file = r"images_360deg_heights.zip"
folder = r"Dobot_3D_Scan"
remote = os.path.join(r"\\ei-data.ei.htwg-konstanz.de\ei-alle", folder, zip_file)
local = os.path.join(".", zip_file)

with smbclient.open_file(remote, "rb") as remote_fh:
    with open(local, "wb") as local_fh:
        shutil.copyfileobj(remote_fh, local_fh)
