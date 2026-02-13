"""Style Learning API endpoints - Upload reports to learn writing style."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import os
import uuid

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings
from app.services.ai.style_learner import (
    process_sample_report,
    get_all_samples,
    delete_sample,
    get_style_examples,
)
from app.services.ai.document_parser import parse_pdf

router = APIRouter()


class StyleSampleResponse(BaseModel):
    id: str
    source_name: str
    created_at: str
    sections: List[dict]


class ProcessedSampleResponse(BaseModel):
    sample_id: str
    source_name: str
    sections_extracted: int
    sections: List[dict]
    style_characteristics: dict
    common_phrases: List[str]
    terminology: List[str]


class TextUploadRequest(BaseModel):
    content: str
    source_name: str
    report_type: str = "sor"


@router.post("/upload-text", response_model=ProcessedSampleResponse)
async def upload_text_sample(
    request: TextUploadRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Upload report text directly to learn style patterns."""
    if len(request.content) < 100:
        raise HTTPException(
            status_code=400,
            detail="Report content must be at least 100 characters"
        )
    
    result = await process_sample_report(
        content=request.content,
        source_name=request.source_name,
        report_type=request.report_type,
    )
    
    return ProcessedSampleResponse(**result)


@router.post("/upload-file", response_model=ProcessedSampleResponse)
async def upload_file_sample(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a PDF report file to learn style patterns."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file temporarily
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Parse PDF
        parsed = await parse_pdf(temp_path, "prior_sor")
        text_content = parsed.get("text", "")
        
        if len(text_content) < 100:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from PDF"
            )
        
        # Process for style learning
        result = await process_sample_report(
            content=text_content,
            source_name=source_name or file.filename,
            report_type="sor",
        )
        
        return ProcessedSampleResponse(**result)
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/samples", response_model=List[StyleSampleResponse])
async def list_style_samples(
    current_user: User = Depends(get_current_active_user),
):
    """List all uploaded style samples."""
    samples = get_all_samples()
    return [StyleSampleResponse(**s) for s in samples]


@router.delete("/samples/{sample_id}")
async def delete_style_sample(
    sample_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a style sample."""
    if delete_sample(sample_id):
        return {"message": "Sample deleted successfully"}
    raise HTTPException(status_code=404, detail="Sample not found")


@router.get("/examples/{section_type}")
async def get_section_examples(
    section_type: str,
    context: Optional[str] = None,
    top_k: int = 3,
    current_user: User = Depends(get_current_active_user),
):
    """Get style examples for a specific section type."""
    examples = await get_style_examples(
        section_type=section_type,
        context=context or "",
        top_k=top_k,
    )
    return {
        "section_type": section_type,
        "examples": examples,
        "count": len(examples),
    }
