from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.jobs import get_db
from app.main import app


class FakeDB:
    def __init__(self, job):
        self.job = job

    async def get(self, model, job_id):
        if self.job and self.job.id == job_id:
            return self.job
        return None


def test_processing_completed_job_returns_409():
    job_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        filename="sample.log",
        status="completed",
        error_message=None,
        analysis_result={"overall_severity": "LOW"},
    )

    async def override_get_db():
        yield FakeDB(job)

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/jobs/{job_id}/process"
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 409
    assert "completed" in response.json()["detail"]


def test_get_unknown_job_returns_404():
    async def override_get_db():
        yield FakeDB(None)

    app.dependency_overrides[get_db] = override_get_db
    unknown_job_id = uuid4()

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/jobs/{unknown_job_id}"
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
