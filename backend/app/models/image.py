import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, DateTime, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True)
    area = Column(String(255), nullable=True)
    
    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # AI Analysis
    ai_description = Column(Text, nullable=True)
    ai_analysis = Column(JSONB, default={})
    ai_building_suggestion = Column(UUID(as_uuid=True), ForeignKey("buildings.id"), nullable=True)
    ai_confidence = Column(Numeric(3, 2), nullable=True)
    ai_processed_at = Column(DateTime, nullable=True)
    
    # Metadata
    exif_data = Column(JSONB, default={})
    tags = Column(ARRAY(String), default=[])
    is_featured = Column(Boolean, default=False)
    
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="images")
    site = relationship("Site", back_populates="images")
    building = relationship("Building", back_populates="images", foreign_keys=[building_id])
    uploaded_by_user = relationship("User", back_populates="images")
