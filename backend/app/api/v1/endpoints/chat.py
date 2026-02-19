from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.core.security import get_current_active_user

router = APIRouter()


class SessionCreate(BaseModel):
    project_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    title: Optional[str] = None


class MessageCreate(BaseModel):
    content: str
    context: Optional[dict] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tokens_used: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    project_id: Optional[str]
    report_id: Optional[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse]


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List user's chat sessions."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatSession.is_active == True)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    return [
        SessionResponse(
            id=str(s.id),
            title=s.title,
            project_id=str(s.project_id) if s.project_id else None,
            report_id=str(s.report_id) if s.report_id else None,
            is_active=s.is_active,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        project_id=session_data.project_id,
        report_id=session_data.report_id,
        title=session_data.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        project_id=str(session.project_id) if session.project_id else None,
        report_id=str(session.report_id) if session.report_id else None,
        is_active=session.is_active,
        created_at=session.created_at.isoformat(),
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get session with messages."""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = sorted(session.messages, key=lambda m: m.created_at)
    
    return SessionDetailResponse(
        id=str(session.id),
        title=session.title,
        project_id=str(session.project_id) if session.project_id else None,
        report_id=str(session.report_id) if session.report_id else None,
        is_active=session.is_active,
        created_at=session.created_at.isoformat(),
        messages=[
            MessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                tokens_used=m.tokens_used,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a chat session."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    await db.commit()
    
    return {"message": "Session deleted"}


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send a message and get AI response."""
    from app.services.ai.chat import generate_chat_response
    
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
    )
    db.add(user_message)
    await db.flush()
    
    # Get chat history
    history = [
        {"role": m.role, "content": m.content}
        for m in sorted(session.messages, key=lambda m: m.created_at)
    ]
    history.append({"role": "user", "content": message_data.content})
    
    # Generate AI response (logged for learning)
    ai_response = await generate_chat_response(
        messages=history,
        context=message_data.context,
        project_id=session.project_id,
        report_id=session.report_id,
        user_id=current_user.id,
        db=db,
    )
    
    # Save AI message
    ai_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response["content"],
        tokens_used=ai_response.get("tokens_used"),
        model_used=ai_response.get("model"),
    )
    db.add(ai_message)
    
    # Update session
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(ai_message)
    
    return MessageResponse(
        id=str(ai_message.id),
        role=ai_message.role,
        content=ai_message.content,
        tokens_used=ai_message.tokens_used,
        created_at=ai_message.created_at.isoformat(),
    )
