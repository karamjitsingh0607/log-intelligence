from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, get_db
from app.models import AnalysisJob
from app.schemas.log import LogUploadResponse
from app.services.job_processor import process_job
from app.services.log_ingestion import save_log_file

router = APIRouter(
    prefix="/api/v1/logs",
    tags=["Logs"],
)


async def process_job_in_background(job_id):
    async with SessionLocal() as db:
        await process_job(job_id, db)


@router.post(
    "/upload",
    response_model=LogUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_log(
    background_tasks: BackgroundTasks,
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
    await db.refresh(job)

    background_tasks.add_task(
        process_job_in_background,
        job_id,
    )

    return LogUploadResponse(
        job_id=job.id,
        status="queued",
        filename=job.filename,
        size_bytes=job.size_bytes,
        uploaded_at=job.created_at,
    )
