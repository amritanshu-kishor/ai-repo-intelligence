from pathlib import Path
import uuid

from fastapi import UploadFile

from config import TEMP_REPOSITORY_DIR


async def save_repository_upload(file: UploadFile) -> tuple[str, str]:
    upload_dir = Path(TEMP_REPOSITORY_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    repository_id = str(uuid.uuid4())
    safe_name = Path(file.filename).name
    destination = upload_dir / f"{repository_id}_{safe_name}"
    content = await file.read()
    destination.write_bytes(content)

    return repository_id, str(destination)
