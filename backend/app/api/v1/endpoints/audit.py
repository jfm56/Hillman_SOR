from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date

from app.db.session import get_db
from app.models.audit import AuditLog, AIInteractionLog
from app.models.user import User
from app.core.security import get_current_active_user, require_role

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    object_type: str
    object_id: str
    before_data: Optional[dict]
    after_data: Optional[dict]
    ip_address: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AILogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    interaction_type: str
    model_name: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: Optional[int]
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    user_id: Optional[UUID] = None,
    object_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """List audit logs (admin/manager only)."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if object_type:
        query = query.where(AuditLog.object_type == object_type)
    if action:
        query = query.where(AuditLog.action == action)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            action=log.action,
            object_type=log.object_type,
            object_id=str(log.object_id),
            before_data=log.before_data,
            after_data=log.after_data,
            ip_address=str(log.ip_address) if log.ip_address else None,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


@router.get("/logs/{object_type}/{object_id}", response_model=List[AuditLogResponse])
async def get_object_logs(
    object_type: str,
    object_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get audit logs for a specific object."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.object_type == object_type)
        .where(AuditLog.object_id == object_id)
        .order_by(AuditLog.created_at.desc())
    )
    logs = result.scalars().all()
    
    return [
        AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            action=log.action,
            object_type=log.object_type,
            object_id=str(log.object_id),
            before_data=log.before_data,
            after_data=log.after_data,
            ip_address=str(log.ip_address) if log.ip_address else None,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


@router.get("/ai-logs", response_model=List[AILogResponse])
async def list_ai_logs(
    interaction_type: Optional[str] = None,
    project_id: Optional[UUID] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """List AI interaction logs (admin/manager only)."""
    query = select(AIInteractionLog).order_by(AIInteractionLog.created_at.desc())
    
    if interaction_type:
        query = query.where(AIInteractionLog.interaction_type == interaction_type)
    if project_id:
        query = query.where(AIInteractionLog.project_id == project_id)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        AILogResponse(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            interaction_type=log.interaction_type,
            model_name=log.model_name,
            input_tokens=log.input_tokens,
            output_tokens=log.output_tokens,
            latency_ms=log.latency_ms,
            status=log.status,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]
