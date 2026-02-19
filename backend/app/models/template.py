import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ReportTemplate(Base, TimestampMixin):
    """Store report templates for formatting reference."""
    __tablename__ = "report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(100), default="sor")  # sor, photo_log, inspection, progress
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # File info
    filename = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)
    
    # Parsed structure - sections, formatting, layout
    structure = Column(JSONB, default={})
    # Example: {
    #   "sections": ["header", "executive_summary", "observations", "recommendations"],
    #   "formatting": {"font": "Times New Roman", "margins": {...}},
    #   "header_template": "Site Observation Report No. {report_number}",
    #   "section_templates": {...}
    # }
    
    # Style characteristics extracted from template
    style_guide = Column(JSONB, default={})
    # Example: {
    #   "tone": "formal",
    #   "tense": "past",
    #   "person": "third",
    #   "common_phrases": [...],
    #   "terminology": [...]
    # }
    
    processed_at = Column(DateTime, nullable=True)
