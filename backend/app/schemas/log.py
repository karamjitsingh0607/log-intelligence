from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from uuid import UUID


class LogUploadResponse(BaseModel):
    job_id: UUID
    status: Literal["queued"]
    filename: str
    size_bytes: int
    uploaded_at: datetime
