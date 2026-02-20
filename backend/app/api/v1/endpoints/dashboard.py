from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.project import Project, ProjectStatus
from app.models.report import Report
from app.models.user import User
from app.models.audit import AuditLog
from app.core.security import get_current_active_user, require_role

router = APIRouter()


class RecentActivityItem(BaseModel):
    id: str
    action: str
    object_type: str
    object_name: Optional[str] = None
    user_name: Optional[str] = None
    created_at: str


class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    total_reports: int
    pending_reports: int
    total_users: int
    recent_activity: List[RecentActivityItem]


class ProjectActivityItem(BaseModel):
    id: str
    name: str
    client_name: str
    status: str
    created_by_name: Optional[str] = None
    created_at: str
    report_count: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get dashboard statistics and recent activity."""
    # Total projects
    total_projects_result = await db.execute(select(func.count(Project.id)))
    total_projects = total_projects_result.scalar() or 0
    
    # Active projects
    active_projects_result = await db.execute(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)
    )
    active_projects = active_projects_result.scalar() or 0
    
    # Total reports
    total_reports_result = await db.execute(select(func.count(Report.id)))
    total_reports = total_reports_result.scalar() or 0
    
    # Pending reports (draft status)
    pending_reports_result = await db.execute(
        select(func.count(Report.id)).where(Report.status == "draft")
    )
    pending_reports = pending_reports_result.scalar() or 0
    
    # Total users
    total_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_users = total_users_result.scalar() or 0
    
    # Recent activity (last 20 actions)
    activity_result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    activities = activity_result.scalars().all()
    
    recent_activity = []
    for log in activities:
        object_name = None
        if log.after_data and isinstance(log.after_data, dict):
            object_name = log.after_data.get("name") or log.after_data.get("title")
        
        recent_activity.append(RecentActivityItem(
            id=str(log.id),
            action=log.action,
            object_type=log.object_type,
            object_name=object_name,
            user_name=log.user.full_name if log.user else None,
            created_at=log.created_at.isoformat(),
        ))
    
    return DashboardStats(
        total_projects=total_projects,
        active_projects=active_projects,
        total_reports=total_reports,
        pending_reports=pending_reports,
        total_users=total_users,
        recent_activity=recent_activity,
    )


@router.get("/recent-projects", response_model=List[ProjectActivityItem])
async def get_recent_projects(
    days: int = Query(7, le=30),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get recently created/updated projects."""
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.created_by_user))
        .where(Project.created_at >= since)
        .order_by(Project.created_at.desc())
        .limit(limit)
    )
    projects = result.scalars().all()
    
    project_items = []
    for p in projects:
        # Count reports for this project
        report_count_result = await db.execute(
            select(func.count(Report.id)).where(Report.project_id == p.id)
        )
        report_count = report_count_result.scalar() or 0
        
        project_items.append(ProjectActivityItem(
            id=str(p.id),
            name=p.name,
            client_name=p.client_name,
            status=p.status.value,
            created_by_name=p.created_by_user.full_name if p.created_by_user else None,
            created_at=p.created_at.isoformat(),
            report_count=report_count,
        ))
    
    return project_items


@router.get("/user-activity", response_model=List[RecentActivityItem])
async def get_user_activity(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's recent activity."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    activities = result.scalars().all()
    
    return [
        RecentActivityItem(
            id=str(log.id),
            action=log.action,
            object_type=log.object_type,
            object_name=log.after_data.get("name") if log.after_data and isinstance(log.after_data, dict) else None,
            user_name=current_user.full_name,
            created_at=log.created_at.isoformat(),
        )
        for log in activities
    ]
