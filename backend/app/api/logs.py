
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import AnalysisJob
from app.schemas.log import LogUploadResponse
from app.services.log_ingestion import save_log_file

router = APIRouter(
    prefix="/api/v1/logs",
    tags=["Logs"],
)


@router.post(
    "/upload",
    response_model=LogUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_log(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    job_id = uuid4()

    try:
        filename, size_bytes = await save_log_file(
            file,
            job_id,
        )
    finally:
        await file.close()

    job = AnalysisJob(
        id=job_id,
        filename=filename,
        size_bytes=size_bytes,
        status="queued",
    )

    db.add(job)
    await db.commit()

    return LogUploadResponse(
        job_id=job.id,
        status="queued",
        filename=job.filename,
        size_bytes=job.size_bytes,
        uploaded_at=job.created_at,
    )
