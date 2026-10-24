
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MiB
ALLOWED_EXTENSIONS = {".log", ".txt"}

UPLOAD_DIR = Path("data/uploads")


async def save_log_file(
    file: UploadFile,
    job_id: UUID,
) -> tuple[str, int]:
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .log and .txt files are supported.",
        )

    # Read at most one byte beyond the limit.
    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MiB upload limit.",
        )

    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The file must contain valid UTF-8 text.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Generate the storage name ourselves; never trust the supplied path.
    storage_path = UPLOAD_DIR / f"{job_id}{extension}"
    storage_path.write_bytes(content)

    return original_name, len(content)
