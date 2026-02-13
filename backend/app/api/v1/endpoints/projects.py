from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.audit import log_action

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    client_name: str
    client_contact: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    client_contact: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    client_name: str
    client_contact: Optional[str]
    address: Optional[str]
    description: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[ProjectStatus] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all projects with optional filtering."""
    query = select(Project).order_by(Project.created_at.desc())
    
    if status:
        query = query.where(Project.status == status)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            client_name=p.client_name,
            client_contact=p.client_contact,
            address=p.address,
            description=p.description,
            status=p.status.value,
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new project."""
    project = Project(
        name=project_data.name,
        client_name=project_data.client_name,
        client_contact=project_data.client_contact,
        address=project_data.address,
        description=project_data.description,
        created_by=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    await log_action(db, current_user.id, "create", "project", project.id, after_data=project_data.model_dump())
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        client_name=project.client_name,
        client_contact=project.client_contact,
        address=project.address,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at.isoformat(),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        client_name=project.client_name,
        client_contact=project.client_contact,
        address=project.address,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at.isoformat(),
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    before_data = {
        "name": project.name,
        "client_name": project.client_name,
        "status": project.status.value,
    }
    
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    await log_action(db, current_user.id, "update", "project", project.id, before_data=before_data, after_data=update_data)
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        client_name=project.client_name,
        client_contact=project.client_contact,
        address=project.address,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at.isoformat(),
    )


@router.delete("/{project_id}")
async def archive_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Archive a project (soft delete)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.status = ProjectStatus.ARCHIVED
    await db.commit()
    
    await log_action(db, current_user.id, "archive", "project", project.id)
    
    return {"message": "Project archived successfully"}
