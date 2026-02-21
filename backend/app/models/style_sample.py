"""Style Sample model for persistent storage of learned writing styles."""
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class StyleSample(Base):
    """Stores extracted sections from uploaded reports for style learning."""
    __tablename__ = "style_samples"

    id = Column(String(36), primary_key=True)
    sample_id = Column(String(36), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=True)
    section_type = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    style_characteristics = Column(JSON, nullable=True)
    common_phrases = Column(JSON, nullable=True)
    terminology = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
