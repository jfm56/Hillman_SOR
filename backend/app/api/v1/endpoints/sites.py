from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

from app.db.session import get_db
from app.models.site import Site
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.audit import log_action

router = APIRouter()


class SiteCreate(BaseModel):
    project_id: UUID
    name: str
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None


class SiteResponse(BaseModel):
    id: str
    project_id: str
    name: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[SiteResponse])
async def list_sites(
    project_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all sites with optional project filtering."""
    query = select(Site).order_by(Site.created_at.desc())
    if project_id:
        query = query.where(Site.project_id == project_id)
    
    result = await db.execute(query)
    sites = result.scalars().all()
    
    return [
        SiteResponse(
            id=str(s.id),
            project_id=str(s.project_id),
            name=s.name,
            address=s.address,
            latitude=float(s.latitude) if s.latitude else None,
            longitude=float(s.longitude) if s.longitude else None,
            description=s.description,
            created_at=s.created_at.isoformat(),
        )
        for s in sites
    ]


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new site."""
    site = Site(**site_data.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    
    await log_action(db, current_user.id, "create", "site", site.id, after_data=site_data.model_dump(mode="json"))
    
    return SiteResponse(
        id=str(site.id),
        project_id=str(site.project_id),
        name=site.name,
        address=site.address,
        latitude=float(site.latitude) if site.latitude else None,
        longitude=float(site.longitude) if site.longitude else None,
        description=site.description,
        created_at=site.created_at.isoformat(),
    )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get site details."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return SiteResponse(
        id=str(site.id),
        project_id=str(site.project_id),
        name=site.name,
        address=site.address,
        latitude=float(site.latitude) if site.latitude else None,
        longitude=float(site.longitude) if site.longitude else None,
        description=site.description,
        created_at=site.created_at.isoformat(),
    )


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: UUID,
    site_data: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a site."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = site_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)
    
    await db.commit()
    await db.refresh(site)
    
    await log_action(db, current_user.id, "update", "site", site.id, after_data=update_data)
    
    return SiteResponse(
        id=str(site.id),
        project_id=str(site.project_id),
        name=site.name,
        address=site.address,
        latitude=float(site.latitude) if site.latitude else None,
        longitude=float(site.longitude) if site.longitude else None,
        description=site.description,
        created_at=site.created_at.isoformat(),
    )


@router.delete("/{site_id}")
async def delete_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a site."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    await log_action(db, current_user.id, "delete", "site", site.id)
    await db.delete(site)
    await db.commit()
    
    return {"message": "Site deleted successfully"}
