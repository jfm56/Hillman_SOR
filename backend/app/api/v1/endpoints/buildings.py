from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.models.building import Building
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.audit import log_action

router = APIRouter()


class BuildingCreate(BaseModel):
    site_id: UUID
    name: str
    building_type: Optional[str] = None
    floors: Optional[int] = None
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    description: Optional[str] = None


class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    building_type: Optional[str] = None
    floors: Optional[int] = None
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    description: Optional[str] = None


class BuildingResponse(BaseModel):
    id: str
    site_id: str
    name: str
    building_type: Optional[str]
    floors: Optional[int]
    year_built: Optional[int]
    square_footage: Optional[int]
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[BuildingResponse])
async def list_buildings(
    site_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all buildings with optional site filtering."""
    query = select(Building).order_by(Building.name)
    if site_id:
        query = query.where(Building.site_id == site_id)
    
    result = await db.execute(query)
    buildings = result.scalars().all()
    
    return [
        BuildingResponse(
            id=str(b.id),
            site_id=str(b.site_id),
            name=b.name,
            building_type=b.building_type,
            floors=b.floors,
            year_built=b.year_built,
            square_footage=b.square_footage,
            description=b.description,
            created_at=b.created_at.isoformat(),
        )
        for b in buildings
    ]


@router.post("", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    building_data: BuildingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new building."""
    building = Building(**building_data.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    
    await log_action(db, current_user.id, "create", "building", building.id, after_data=building_data.model_dump(mode="json"))
    
    return BuildingResponse(
        id=str(building.id),
        site_id=str(building.site_id),
        name=building.name,
        building_type=building.building_type,
        floors=building.floors,
        year_built=building.year_built,
        square_footage=building.square_footage,
        description=building.description,
        created_at=building.created_at.isoformat(),
    )


@router.get("/{building_id}", response_model=BuildingResponse)
async def get_building(
    building_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get building details."""
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    return BuildingResponse(
        id=str(building.id),
        site_id=str(building.site_id),
        name=building.name,
        building_type=building.building_type,
        floors=building.floors,
        year_built=building.year_built,
        square_footage=building.square_footage,
        description=building.description,
        created_at=building.created_at.isoformat(),
    )


@router.put("/{building_id}", response_model=BuildingResponse)
async def update_building(
    building_id: UUID,
    building_data: BuildingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a building."""
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    update_data = building_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(building, field, value)
    
    await db.commit()
    await db.refresh(building)
    
    await log_action(db, current_user.id, "update", "building", building.id, after_data=update_data)
    
    return BuildingResponse(
        id=str(building.id),
        site_id=str(building.site_id),
        name=building.name,
        building_type=building.building_type,
        floors=building.floors,
        year_built=building.year_built,
        square_footage=building.square_footage,
        description=building.description,
        created_at=building.created_at.isoformat(),
    )


@router.delete("/{building_id}")
async def delete_building(
    building_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a building."""
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    await log_action(db, current_user.id, "delete", "building", building.id)
    await db.delete(building)
    await db.commit()
    
    return {"message": "Building deleted successfully"}
