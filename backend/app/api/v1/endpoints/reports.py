from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime

from app.db.session import get_db
from app.models.report import Report, ReportSection, ReportStatus
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.audit import log_action

router = APIRouter()


class ReportCreate(BaseModel):
    project_id: UUID
    site_id: Optional[UUID] = None
    report_number: int
    report_date: date
    inspection_date: date
    weather_conditions: Optional[str] = None
    personnel_on_site: Optional[str] = None


class ReportUpdate(BaseModel):
    report_date: Optional[date] = None
    inspection_date: Optional[date] = None
    weather_conditions: Optional[str] = None
    personnel_on_site: Optional[str] = None
    executive_summary: Optional[str] = None
    status: Optional[ReportStatus] = None


class SectionResponse(BaseModel):
    id: str
    section_type: str
    section_order: int
    title: Optional[str]
    ai_draft: Optional[str]
    human_content: Optional[str]
    final_content: Optional[str]
    is_approved: bool

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: str
    project_id: str
    site_id: Optional[str]
    report_number: int
    report_date: str
    inspection_date: str
    status: str
    version: int
    weather_conditions: Optional[str]
    personnel_on_site: Optional[str]
    executive_summary: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    sections: List[SectionResponse]


class GenerateRequest(BaseModel):
    sections: List[str]
    options: Optional[dict] = None


class SectionUpdate(BaseModel):
    human_content: Optional[str] = None
    final_content: Optional[str] = None
    is_final: bool = False


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    project_id: Optional[UUID] = None,
    status: Optional[ReportStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all reports."""
    query = select(Report).order_by(Report.created_at.desc())
    if project_id:
        query = query.where(Report.project_id == project_id)
    if status:
        query = query.where(Report.status == status)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return [
        ReportResponse(
            id=str(r.id),
            project_id=str(r.project_id),
            site_id=str(r.site_id) if r.site_id else None,
            report_number=r.report_number,
            report_date=r.report_date.isoformat(),
            inspection_date=r.inspection_date.isoformat(),
            status=r.status.value,
            version=r.version,
            weather_conditions=r.weather_conditions,
            personnel_on_site=r.personnel_on_site,
            executive_summary=r.executive_summary,
            created_at=r.created_at.isoformat(),
        )
        for r in reports
    ]


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new report."""
    report = Report(
        **report_data.model_dump(),
        created_by=current_user.id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    await log_action(db, current_user.id, "create", "report", report.id, after_data=report_data.model_dump(mode="json"))
    
    return ReportResponse(
        id=str(report.id),
        project_id=str(report.project_id),
        site_id=str(report.site_id) if report.site_id else None,
        report_number=report.report_number,
        report_date=report.report_date.isoformat(),
        inspection_date=report.inspection_date.isoformat(),
        status=report.status.value,
        version=report.version,
        weather_conditions=report.weather_conditions,
        personnel_on_site=report.personnel_on_site,
        executive_summary=report.executive_summary,
        created_at=report.created_at.isoformat(),
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get report with sections."""
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.sections))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    sections = sorted(report.sections, key=lambda s: s.section_order)
    
    return ReportDetailResponse(
        id=str(report.id),
        project_id=str(report.project_id),
        site_id=str(report.site_id) if report.site_id else None,
        report_number=report.report_number,
        report_date=report.report_date.isoformat(),
        inspection_date=report.inspection_date.isoformat(),
        status=report.status.value,
        version=report.version,
        weather_conditions=report.weather_conditions,
        personnel_on_site=report.personnel_on_site,
        executive_summary=report.executive_summary,
        created_at=report.created_at.isoformat(),
        sections=[
            SectionResponse(
                id=str(s.id),
                section_type=s.section_type,
                section_order=s.section_order,
                title=s.title,
                ai_draft=s.ai_draft,
                human_content=s.human_content,
                final_content=s.final_content,
                is_approved=s.is_approved,
            )
            for s in sections
        ],
    )


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    report_data: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a report."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    update_data = report_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    await db.commit()
    await db.refresh(report)
    
    await log_action(db, current_user.id, "update", "report", report.id, after_data=update_data)
    
    return ReportResponse(
        id=str(report.id),
        project_id=str(report.project_id),
        site_id=str(report.site_id) if report.site_id else None,
        report_number=report.report_number,
        report_date=report.report_date.isoformat(),
        inspection_date=report.inspection_date.isoformat(),
        status=report.status.value,
        version=report.version,
        weather_conditions=report.weather_conditions,
        personnel_on_site=report.personnel_on_site,
        executive_summary=report.executive_summary,
        created_at=report.created_at.isoformat(),
    )


@router.post("/{report_id}/generate")
async def generate_report_drafts(
    report_id: UUID,
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate AI drafts for report sections."""
    from app.services.ai.draft_generator import generate_section_draft
    
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    generated_sections = []
    
    for idx, section_type in enumerate(request.sections):
        # Check if section exists
        section_result = await db.execute(
            select(ReportSection)
            .where(ReportSection.report_id == report_id)
            .where(ReportSection.section_type == section_type)
        )
        section = section_result.scalar_one_or_none()
        
        if not section:
            section = ReportSection(
                report_id=report_id,
                section_type=section_type,
                section_order=idx + 1,
                title=section_type.replace("_", " ").title(),
            )
            db.add(section)
            await db.flush()
        
        # Generate draft
        draft = await generate_section_draft(
            db=db,
            report=report,
            section_type=section_type,
            options=request.options or {},
        )
        
        section.ai_draft = draft["content"]
        section.ai_generated_at = datetime.utcnow()
        section.evidence_references = draft.get("evidence_references", [])
        
        generated_sections.append({
            "section_type": section_type,
            "status": "completed",
            "draft_preview": draft["content"][:200] + "..." if len(draft["content"]) > 200 else draft["content"],
        })
    
    report.ai_generated_at = datetime.utcnow()
    await db.commit()
    
    await log_action(db, current_user.id, "generate_ai", "report", report.id, after_data={"sections": request.sections})
    
    return {
        "report_id": str(report_id),
        "sections_generated": len(generated_sections),
        "sections": generated_sections,
    }


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Approve a report."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = ReportStatus.APPROVED
    report.approved_by = current_user.id
    report.approved_at = datetime.utcnow()
    
    await db.commit()
    
    await log_action(db, current_user.id, "approve", "report", report.id)
    
    return {"message": "Report approved successfully"}


@router.put("/{report_id}/sections/{section_id}")
async def update_section(
    report_id: UUID,
    section_id: UUID,
    section_data: SectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a report section."""
    result = await db.execute(
        select(ReportSection)
        .where(ReportSection.id == section_id)
        .where(ReportSection.report_id == report_id)
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    if section_data.human_content is not None:
        section.human_content = section_data.human_content
        section.human_edited_by = current_user.id
        section.human_edited_at = datetime.utcnow()
    
    if section_data.final_content is not None:
        section.final_content = section_data.final_content
    
    if section_data.is_final:
        section.is_approved = True
        section.approved_by = current_user.id
        section.approved_at = datetime.utcnow()
    
    await db.commit()
    
    await log_action(db, current_user.id, "update", "report_section", section.id)
    
    return {"message": "Section updated successfully"}
