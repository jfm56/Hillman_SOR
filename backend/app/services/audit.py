from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: Optional[UUID],
    action: str,
    object_type: str,
    object_id: UUID,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log an audit action."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        before_data=before_data,
        after_data=after_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    await db.flush()
