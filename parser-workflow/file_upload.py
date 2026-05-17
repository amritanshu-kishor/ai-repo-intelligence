import os
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile

from config import TEMP_REPOSITORY_DIR


async def save_upload_file(file: UploadFile) -> Path:
    upload_dir = Path(TEMP_REPOSITORY_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    destination = upload_dir / safe_name

    with destination.open("wb") as buffer:
        while content := await file.read(1024 * 64):
            buffer.write(content)

    return destination
