
from pathlib import Path
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalysisJob
from app.services.log_ingestion import UPLOAD_DIR
from app.services.log_parser import parse_log


MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024


async def process_job(
    job_id: UUID,
    db: AsyncSession,
) -> AnalysisJob:
    # Atomically claim the job only if it is still queued.
    claim_statement = (
        update(AnalysisJob)
        .where(
            AnalysisJob.id == job_id,
            AnalysisJob.status == "queued",
        )
        .values(
            status="processing",
            error_message=None,
        )
    )

    claim_result = await db.execute(claim_statement)

    if claim_result.rowcount != 1:
        await db.rollback()

        job = await db.get(AnalysisJob, job_id)

        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        if job.status == "completed":
            return job

        raise ValueError(
            f"Job cannot be processed from status '{job.status}'."
        )

    await db.commit()

    job = await db.get(AnalysisJob, job_id)

    if job is None:
        raise ValueError(f"Job not found after claiming: {job_id}")

    try:
        extension = Path(job.filename).suffix.lower()
        file_path = UPLOAD_DIR / f"{job.id}{extension}"

        if not file_path.is_file():
            raise FileNotFoundError("Uploaded log file was not found.")

        if file_path.stat().st_size > MAX_LOG_SIZE_BYTES:
            raise ValueError(
                "Log file exceeds the maximum supported size."
            )

        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            raise ValueError("Log file is empty.")

        result = parse_log(content)

        job.analysis_result = result
        job.status = "completed"
        job.error_message = None

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)[:1000]
        job.analysis_result = None

    try:
        await db.commit()
        await db.refresh(job)
    except Exception:
        await db.rollback()
        raise

    return job
