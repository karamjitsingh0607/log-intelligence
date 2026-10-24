from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import AnalysisJob
from app.services.job_processor import process_job

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


@router.get("/{job_id}")
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(AnalysisJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return {
        "job_id": job.id,
        "filename": job.filename,
        "size_bytes": job.size_bytes,
        "status": job.status,
        "error_message": job.error_message,
        "analysis_result": job.analysis_result,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.post("/{job_id}/process")
async def process_existing_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(AnalysisJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status != "queued":
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be processed from status '{job.status}'.",
        )

    try:
        job = await process_job(job_id, db)
    except ValueError as exc:
        # The job may have been claimed by another request
        # after the initial status check.
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "job_id": job.id,
        "status": job.status,
        "error_message": job.error_message,
        "analysis_result": job.analysis_result,
    }
