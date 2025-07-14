# app/api/schemas/job.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class JobCreateResponse(BaseModel):
    """Response schema for job creation endpoint."""
    id: UUID = Field(..., description="The unique identifier for the created job.")

    class Config:
        from_attributes = True
        
    @property
    def job_id(self) -> UUID:
        """Alias for id to maintain API consistency."""
        return self.id

class JobStatusResponse(BaseModel):
    """Response schema for job status and listing endpoints."""
    id: UUID = Field(..., description="The job's unique identifier.")
    status: str = Field(..., description="The current status of the job (e.g., 'processing', 'succeeded', 'failed').")
    original_filename: Optional[str] = Field(None, description="The original filename of the uploaded image.")
    thumbnail_filename: Optional[str] = Field(None, description="The filename of the generated thumbnail.")
    created_at: datetime = Field(..., description="When the job was created.")
    updated_at: datetime = Field(..., description="When the job was last updated.")

    class Config:
        from_attributes = True
        
    @property
    def job_id(self) -> UUID:
        """Alias for id to maintain API consistency."""
        return self.id