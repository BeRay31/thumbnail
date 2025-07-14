# app/db/models.py
import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

class Job(Base):
    __tablename__ = "jobs"
    # The PK
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The current status of the job (e.g., 'processing', 'succeeded', 'failed')
    status = Column(String, nullable=False, index=True)
    # The filename of the original uploaded image
    original_filename = Column(String, nullable=True)
    # The filename of the generated thumbnail (same as the job ID)
    thumbnail_filename = Column(String, nullable=True)
    # Timestamps for creation and updates, handled automatically by the database
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())