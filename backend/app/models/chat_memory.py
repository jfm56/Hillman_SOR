import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


class ChatMemory(Base, TimestampMixin):
    """Bounded chat memory with summarization.
    
    Instead of storing unbounded chat history, we summarize every 5 turns
    into a single paragraph and store only the summary + last 3 turns.
    """
    __tablename__ = "chat_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True)
    
    # Summarized memory (replaces old turns)
    summary_memory = Column(Text, nullable=True)
    
    # Turn counter for triggering summarization
    turn_count = Column(Integer, default=0)
    
    # Last summary turn (for tracking when to summarize again)
    last_summary_turn = Column(Integer, default=0)
