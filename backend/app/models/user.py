import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """
    ADMIN: IT / system control - full access to all features
    MANAGER: Review & approve reports - can approve/reject reports
    INSPECTOR: Upload photos & write narratives - create and edit reports
    """
    ADMIN = "admin"
    MANAGER = "manager"
    INSPECTOR = "inspector"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.INSPECTOR, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="created_by_user")
    reports = relationship("Report", back_populates="created_by_user", foreign_keys="Report.created_by")
    images = relationship("Image", back_populates="uploaded_by_user")
    documents = relationship("Document", back_populates="uploaded_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
