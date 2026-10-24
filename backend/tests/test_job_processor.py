
import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services import job_processor


class FakeResult:
    def __init__(self, rowcount):
        self.rowcount = rowcount


class FakeDB:
    def __init__(self, job, fail_on_commit=None):
        self.job = job
        self.commit_count = 0
        self.refresh_count = 0
        self.rollback_count = 0
        self.fail_on_commit = fail_on_commit

    async def execute(self, statement):
        # Simulate the conditional UPDATE:
        # claim only if the job is still queued.
        if self.job is None:
            return FakeResult(0)

        if self.job.status != "queued":
            return FakeResult(0)

        self.job.status = "processing"
        self.job.error_message = None
        return FakeResult(1)

    async def get(self, model, job_id):
        if self.job and self.job.id == job_id:
            return self.job
        return None

    async def commit(self):
        self.commit_count += 1

        if self.commit_count == self.fail_on_commit:
            raise RuntimeError("Simulated database commit failure")

    async def rollback(self):
        self.rollback_count += 1

    async def refresh(self, job):
        self.refresh_count += 1


def test_process_job_success(tmp_path, monkeypatch):
    job_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        filename="sample.log",
        status="queued",
        error_message=None,
        analysis_result=None,
    )

    log_content = "INFO Application started\nERROR Database timeout\n"
    (tmp_path / f"{job_id}.log").write_text(
        log_content,
        encoding="utf-8",
    )

    monkeypatch.setattr(job_processor, "UPLOAD_DIR", tmp_path)
    db = FakeDB(job)

    result = asyncio.run(job_processor.process_job(job_id, db))

    assert result.status == "completed"
    assert result.analysis_result["total_lines"] == 2
    assert result.analysis_result["level_counts"]["INFO"] == 1
    assert result.analysis_result["level_counts"]["ERROR"] == 1
    assert result.analysis_result["error_count"] == 1
    assert result.error_message is None
    assert db.commit_count == 2
    assert db.refresh_count == 1


def test_process_job_missing_file_fails(tmp_path, monkeypatch):
    job_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        filename="missing.log",
        status="queued",
        error_message=None,
        analysis_result=None,
    )

    monkeypatch.setattr(job_processor, "UPLOAD_DIR", tmp_path)
    db = FakeDB(job)

    result = asyncio.run(job_processor.process_job(job_id, db))

    assert result.status == "failed"
    assert "Uploaded log file was not found" in result.error_message
    assert result.analysis_result is None
    assert db.commit_count == 2
    assert db.refresh_count == 1


def test_process_job_rejects_already_claimed_job():
    job_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        filename="sample.log",
        status="processing",
        error_message=None,
        analysis_result=None,
    )

    db = FakeDB(job)

    try:
        asyncio.run(job_processor.process_job(job_id, db))
        assert False, "Expected ValueError for an already claimed job"
    except ValueError as exc:
        assert "cannot be processed from status 'processing'" in str(exc)

    assert job.status == "processing"
    assert db.rollback_count == 1
    assert db.commit_count == 0


def test_process_job_rolls_back_when_final_commit_fails(
    tmp_path,
    monkeypatch,
):
    job_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        filename="sample.log",
        status="queued",
        error_message=None,
        analysis_result=None,
    )

    log_content = "INFO Application started\n"
    (tmp_path / f"{job_id}.log").write_text(
        log_content,
        encoding="utf-8",
    )

    monkeypatch.setattr(job_processor, "UPLOAD_DIR", tmp_path)

    # Commit 1 claims the job; commit 2 fails when saving the result.
    db = FakeDB(job, fail_on_commit=2)

    try:
        asyncio.run(job_processor.process_job(job_id, db))
        assert False, "Expected the simulated commit failure"
    except RuntimeError as exc:
        assert "Simulated database commit failure" in str(exc)

    assert db.commit_count == 2
    assert db.rollback_count == 1
    assert db.refresh_count == 0
