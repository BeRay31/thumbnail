# app/api/schemas/job.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class JobCreateResponse(BaseModel):
    id: UUID

    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    id: UUID
    status: str
    original_filename: Optional[str] = None
    thumbnail_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True