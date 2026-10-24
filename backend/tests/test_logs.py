
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.services import log_ingestion


async def override_get_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    yield db


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_upload_valid_log(tmp_path, monkeypatch):
    monkeypatch.setattr(log_ingestion, "UPLOAD_DIR", tmp_path)

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


def test_reject_unsupported_extension():
    response = client.post(
        "/api/v1/logs/upload",
        files={"file": ("sample.csv", b"a,b\n1,2", "text/csv")},
    )

    assert response.status_code == 400


def test_reject_empty_file():
    response = client.post(
        "/api/v1/logs/upload",
        files={"file": ("empty.log", b"", "text/plain")},
    )

    assert response.status_code == 400


def test_reject_oversized_file():
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
