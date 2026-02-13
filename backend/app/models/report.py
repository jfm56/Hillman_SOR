import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, DateTime, Date, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base, TimestampMixin


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    FINAL = "final"
    ARCHIVED = "archived"


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    
    report_number = Column(Integer, nullable=False)
    report_date = Column(Date, nullable=False)
    inspection_date = Column(Date, nullable=False)
    
    # Status and versioning
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)
    
    # Summary fields
    weather_conditions = Column(Text, nullable=True)
    personnel_on_site = Column(Text, nullable=True)
    executive_summary = Column(Text, nullable=True)
    
    # AI tracking
    ai_generated_at = Column(DateTime, nullable=True)
    ai_model_used = Column(String(100), nullable=True)
    
    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="reports")
    site = relationship("Site", back_populates="reports")
    created_by_user = relationship("User", back_populates="reports", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan")


class ReportSection(Base, TimestampMixin):
    __tablename__ = "report_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    
    section_type = Column(String(100), nullable=False)
    section_order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    
    # Content versions
    ai_draft = Column(Text, nullable=True)
    ai_generated_at = Column(DateTime, nullable=True)
    ai_prompt_used = Column(Text, nullable=True)
    
    human_content = Column(Text, nullable=True)
    human_edited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    human_edited_at = Column(DateTime, nullable=True)
    
    # Final content
    final_content = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Related data
    related_images = Column(ARRAY(UUID(as_uuid=True)), default=[])
    related_documents = Column(ARRAY(UUID(as_uuid=True)), default=[])
    evidence_references = Column(JSONB, default=[])

    # Relationships
    report = relationship("Report", back_populates="sections")
