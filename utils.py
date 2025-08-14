from fastapi import UploadFile
from pathlib import Path
from uuid import uuid4
from admin_routes import UPLOAD_DIR
import os

def save_uploaded_files(image:UploadFile)->str:
    file_ext = Path(image.filename).suffix.lower()
    unique_filename = f"{uuid4}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR,unique_filename)
     # Save file - simpler way
    with open(file_path, "wb") as f:
        f.write(image.file.read())
    return file_path

