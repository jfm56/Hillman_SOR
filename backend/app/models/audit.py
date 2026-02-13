import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    
    object_type = Column(String(100), nullable=False)
    object_id = Column(UUID(as_uuid=True), nullable=False)
    
    before_data = Column(JSONB, nullable=True)
    after_data = Column(JSONB, nullable=True)
    
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class AIInteractionLog(Base):
    __tablename__ = "ai_interaction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    interaction_type = Column(String(100), nullable=False)
    
    # Request
    model_name = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    
    # Response
    response = Column(Text, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    # Context
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)
    
    # Status
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
