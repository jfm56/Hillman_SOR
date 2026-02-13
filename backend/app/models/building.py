import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Building(Base, TimestampMixin):
    __tablename__ = "buildings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    building_type = Column(String(100), nullable=True)
    floors = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    square_footage = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    extra_data = Column(JSONB, default={})

    # Relationships
    site = relationship("Site", back_populates="buildings")
    images = relationship("Image", back_populates="building")
