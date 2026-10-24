from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api import logs
from app.db import get_db
from app.main import app
from app.services import log_ingestion


@pytest.fixture
def client():
    
    async def override_get_db():
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        def add_job(job):
            if job.created_at is None:
                job.created_at = datetime.now(timezone.utc)

        db.add.side_effect = add_job

        yield db


    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)



def test_upload_valid_log(tmp_path, monkeypatch, client):
    monkeypatch.setattr(log_ingestion, "UPLOAD_DIR", tmp_path)

    mock_process = AsyncMock()
    monkeypatch.setattr(
        logs,
        "process_job_in_background",
        mock_process,
    )

    response = client.post(
        "/api/v1/logs/upload",
        files={
            "file": (
                "sample.log",
                b"INFO Application started\nERROR Database timeout\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert data["status"] == "queued"
    assert data["filename"] == "sample.log"
    assert data["size_bytes"] == len(
        b"INFO Application started\nERROR Database timeout\n"
    )
    assert (tmp_path / f'{data["job_id"]}.log').exists()

    mock_process.assert_awaited_once_with(UUID(data["job_id"]))


def test_reject_unsupported_extension(client):
    response = client.post(
        "/api/v1/logs/upload",
        files={"file": ("sample.csv", b"a,b\n1,2", "text/csv")},
    )

    assert response.status_code == 400


def test_reject_empty_file(client):
    response = client.post(
        "/api/v1/logs/upload",
        files={"file": ("empty.log", b"", "text/plain")},
    )

    assert response.status_code == 400


def test_reject_oversized_file(client):
    response = client.post(
        "/api/v1/logs/upload",
        files={
            "file": (
                "large.log",
                b"x" * (log_ingestion.MAX_FILE_SIZE + 1),
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
