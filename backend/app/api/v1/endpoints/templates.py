"""Report Template API endpoints - Upload and manage report templates."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
import aiofiles

from app.db.session import get_db
from app.models.template import ReportTemplate
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings
from app.services.ai.document_parser import parse_pdf

router = APIRouter()


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    template_type: str
    is_active: bool
    is_default: bool
    original_filename: Optional[str]
    file_size: Optional[int]
    structure: dict
    style_guide: dict
    created_at: str
    processed_at: Optional[str]


class TemplateCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    template_type: str = "sor"


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    structure: Optional[dict] = None
    style_guide: Optional[dict] = None


@router.post("/upload", response_model=TemplateResponse)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    template_type: str = Form("sor"),
    set_as_default: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a report template file (PDF or Word doc)."""
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and Word documents are supported"
        )
    
    # Create templates directory
    templates_dir = f"{settings.STORAGE_PATH}/templates"
    os.makedirs(templates_dir, exist_ok=True)
    
    # Read and save file
    content = await file.read()
    file_size = len(content)
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"{templates_dir}/{unique_filename}"
    
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # Parse document to extract text and structure
    extracted_text = ""
    structure = {}
    style_guide = {}
    
    try:
        if file.content_type == "application/pdf":
            parsed = await parse_pdf(file_path, "template")
            extracted_text = parsed.get("text", "")
            
            # Extract basic structure from parsed content
            structure = extract_template_structure(extracted_text)
            style_guide = analyze_style(extracted_text)
    except Exception as e:
        print(f"Template parsing error: {e}")
    
    # If setting as default, unset any existing default
    if set_as_default:
        await db.execute(
            update(ReportTemplate)
            .where(ReportTemplate.template_type == template_type)
            .where(ReportTemplate.is_default == True)
            .values(is_default=False)
        )
    
    # Create template record
    template = ReportTemplate(
        name=name,
        description=description,
        template_type=template_type,
        is_default=set_as_default,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        extracted_text=extracted_text,
        structure=structure,
        style_guide=style_guide,
        processed_at=datetime.utcnow(),
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        template_type=template.template_type,
        is_active=template.is_active,
        is_default=template.is_default,
        original_filename=template.original_filename,
        file_size=template.file_size,
        structure=template.structure or {},
        style_guide=template.style_guide or {},
        created_at=template.created_at.isoformat(),
        processed_at=template.processed_at.isoformat() if template.processed_at else None,
    )


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    template_type: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all report templates."""
    query = select(ReportTemplate)
    
    if template_type:
        query = query.where(ReportTemplate.template_type == template_type)
    if active_only:
        query = query.where(ReportTemplate.is_active == True)
    
    query = query.order_by(ReportTemplate.is_default.desc(), ReportTemplate.created_at.desc())
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        TemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            template_type=t.template_type,
            is_active=t.is_active,
            is_default=t.is_default,
            original_filename=t.original_filename,
            file_size=t.file_size,
            structure=t.structure or {},
            style_guide=t.style_guide or {},
            created_at=t.created_at.isoformat(),
            processed_at=t.processed_at.isoformat() if t.processed_at else None,
        )
        for t in templates
    ]


@router.get("/default")
async def get_default_template(
    template_type: str = "sor",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the default template for a given type."""
    query = (
        select(ReportTemplate)
        .where(ReportTemplate.template_type == template_type)
        .where(ReportTemplate.is_default == True)
        .where(ReportTemplate.is_active == True)
    )
    
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        return {"message": "No default template set", "template": None}
    
    return {
        "template": TemplateResponse(
            id=str(template.id),
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            is_active=template.is_active,
            is_default=template.is_default,
            original_filename=template.original_filename,
            file_size=template.file_size,
            structure=template.structure or {},
            style_guide=template.style_guide or {},
            created_at=template.created_at.isoformat(),
            processed_at=template.processed_at.isoformat() if template.processed_at else None,
        )
    }


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific template by ID."""
    query = select(ReportTemplate).where(ReportTemplate.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        template_type=template.template_type,
        is_active=template.is_active,
        is_default=template.is_default,
        original_filename=template.original_filename,
        file_size=template.file_size,
        structure=template.structure or {},
        style_guide=template.style_guide or {},
        created_at=template.created_at.isoformat(),
        processed_at=template.processed_at.isoformat() if template.processed_at else None,
    )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a template's metadata."""
    query = select(ReportTemplate).where(ReportTemplate.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # If setting as default, unset other defaults
    if request.is_default:
        await db.execute(
            update(ReportTemplate)
            .where(ReportTemplate.template_type == template.template_type)
            .where(ReportTemplate.is_default == True)
            .where(ReportTemplate.id != template_id)
            .values(is_default=False)
        )
    
    # Update fields
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.is_active is not None:
        template.is_active = request.is_active
    if request.is_default is not None:
        template.is_default = request.is_default
    if request.structure is not None:
        template.structure = request.structure
    if request.style_guide is not None:
        template.style_guide = request.style_guide
    
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        template_type=template.template_type,
        is_active=template.is_active,
        is_default=template.is_default,
        original_filename=template.original_filename,
        file_size=template.file_size,
        structure=template.structure or {},
        style_guide=template.style_guide or {},
        created_at=template.created_at.isoformat(),
        processed_at=template.processed_at.isoformat() if template.processed_at else None,
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a template."""
    query = select(ReportTemplate).where(ReportTemplate.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Delete file if exists
    if template.file_path and os.path.exists(template.file_path):
        os.remove(template.file_path)
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "Template deleted successfully"}


def extract_template_structure(text: str) -> dict:
    """Extract section structure from template text."""
    structure = {
        "sections": [],
        "detected_headings": [],
        "required_fields": [],
    }
    
    # Common SOR section patterns
    section_patterns = [
        "executive summary",
        "introduction",
        "project information",
        "site observations",
        "observations",
        "findings",
        "recommendations",
        "conclusion",
        "appendix",
        "photographs",
        "photo log",
        "plan and cost review",
        "requisition",
        "submittal log",
        "change order",
        "soft cost",
        "construction schedule",
    ]
    
    text_lower = text.lower()
    for pattern in section_patterns:
        if pattern in text_lower:
            structure["sections"].append(pattern.replace(" ", "_"))
            structure["detected_headings"].append(pattern.title())
    
    # SOR Required Fields per Hillmann Guidelines
    sor_required_fields = [
        {"field": "remaining_items", "label": "Remaining Items from Plan and Cost Review", "frequency": "monthly"},
        {"field": "notice_to_proceed", "label": "Notice-to-Proceed and Building Permits", "frequency": "first_draw"},
        {"field": "requisition", "label": "Monthly Requisition (AIA G702/703)", "frequency": "monthly"},
        {"field": "waiver_of_lien", "label": "Waiver of Lien", "frequency": "monthly"},
        {"field": "submittal_log", "label": "Submittal Log with Approval Status", "frequency": "monthly"},
        {"field": "change_order_log", "label": "Change Order Log (Executed & Potential)", "frequency": "monthly"},
        {"field": "soft_cost_tracking", "label": "Soft Cost Tracking (Sources & Uses Budget)", "frequency": "monthly"},
        {"field": "new_change_orders", "label": "New Change Orders with Pricing Backup", "frequency": "as_required"},
        {"field": "construction_schedule", "label": "Updated Construction Schedule", "frequency": "when_changed"},
        {"field": "percent_complete", "label": "Project Percent Complete", "frequency": "monthly"},
        {"field": "budget_status", "label": "Current Budget Status", "frequency": "monthly"},
    ]
    
    structure["required_fields"] = sor_required_fields
    
    return structure


def analyze_style(text: str) -> dict:
    """Analyze writing style from template text."""
    style = {
        "tone": "formal",
        "estimated_length": len(text),
        "common_phrases": [],
        "terminology": [],
    }
    
    # Extract common professional phrases
    phrases = [
        "it was observed that",
        "upon inspection",
        "the contractor",
        "construction progress",
        "in accordance with",
        "as noted",
        "field observations",
        "site visit",
        "percent complete",
        "work in progress",
    ]
    
    text_lower = text.lower()
    for phrase in phrases:
        if phrase in text_lower:
            style["common_phrases"].append(phrase)
    
    # Extract terminology
    terms = [
        "RFI", "change order", "punch list", "substantial completion",
        "deficiency", "remediation", "specification", "drawings",
        "submittal", "schedule", "milestone", "phase",
    ]
    
    for term in terms:
        if term.lower() in text_lower:
            style["terminology"].append(term)
    
    return style
