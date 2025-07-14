# app/api/schemas/job.py
from pydantic import BaseModel, Field
from uuid import UUID

class JobCreateResponse(BaseModel):
    job_id: UUID = Field(..., description="The unique identifier for the created job.")

class JobStatusResponse(BaseModel):
    job_id: UUID = Field(..., description="The job's unique identifier.")
    status: str = Field(..., description="The current status of the job (e.g., 'processing', 'succeeded', 'failed').")

    class Config:
        from_attributes = True