from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.models.image import Image
from app.models.document import Document
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.audit import log_action

router = APIRouter()


class ImageAnalysisRequest(BaseModel):
    image_id: UUID


class ImageAnalysisResponse(BaseModel):
    image_id: str
    analysis: dict
    tokens_used: int
    model: str


class DocumentParseRequest(BaseModel):
    document_id: UUID


class DocumentParseResponse(BaseModel):
    document_id: str
    parsed_data: dict
    page_count: int


class BuildingClassifyRequest(BaseModel):
    image_id: UUID
    project_id: UUID


class RewriteRequest(BaseModel):
    text: str
    style: str = "formal_sor"
    context: Optional[dict] = None


class RewriteResponse(BaseModel):
    original: str
    rewritten: str


class SimilarSectionsRequest(BaseModel):
    section_type: str
    query: str
    top_k: int = 5


@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Analyze a single image using vision model."""
    from app.services.ai.vision import analyze_image as vision_analyze
    
    result = await db.execute(select(Image).where(Image.id == request.image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    analysis = await vision_analyze(image.file_path)
    
    # Update image record
    image.ai_description = analysis.get("description", "")
    image.ai_analysis = analysis
    image.ai_confidence = analysis.get("confidence", 0.0)
    from datetime import datetime
    image.ai_processed_at = datetime.utcnow()
    
    await db.commit()
    
    await log_action(db, current_user.id, "analyze_image", "image", image.id)
    
    return ImageAnalysisResponse(
        image_id=str(image.id),
        analysis=analysis,
        tokens_used=analysis.get("tokens_used", 0),
        model=analysis.get("model", "gpt-4-vision"),
    )


@router.post("/analyze-images")
async def analyze_images_batch(
    image_ids: List[UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch analyze multiple images."""
    results = []
    
    for image_id in image_ids:
        try:
            result = await analyze_image(
                ImageAnalysisRequest(image_id=image_id),
                db=db,
                current_user=current_user,
            )
            results.append({"image_id": str(image_id), "status": "success", "analysis": result.analysis})
        except Exception as e:
            results.append({"image_id": str(image_id), "status": "error", "error": str(e)})
    
    return {"results": results}


@router.post("/parse-document", response_model=DocumentParseResponse)
async def parse_document(
    request: DocumentParseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Parse a PDF document."""
    from app.services.ai.document_parser import parse_pdf
    
    result = await db.execute(select(Document).where(Document.id == request.document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    parsed = await parse_pdf(document.file_path, document.document_type)
    
    # Update document record
    document.extracted_text = parsed.get("text", "")
    document.parsed_data = parsed.get("structured_data", {})
    document.page_count = parsed.get("page_count", 0)
    document.is_processed = True
    from datetime import datetime
    document.processed_at = datetime.utcnow()
    
    await db.commit()
    
    await log_action(db, current_user.id, "parse_document", "document", document.id)
    
    return DocumentParseResponse(
        document_id=str(document.id),
        parsed_data=parsed.get("structured_data", {}),
        page_count=parsed.get("page_count", 0),
    )


@router.post("/classify-building")
async def classify_building(
    request: BuildingClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Suggest which building an image belongs to."""
    from app.services.ai.building_classifier import classify_image_building
    
    result = await db.execute(select(Image).where(Image.id == request.image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    classification = await classify_image_building(
        db=db,
        image=image,
        project_id=request.project_id,
    )
    
    if classification.get("suggested_building_id"):
        image.ai_building_suggestion = classification["suggested_building_id"]
        image.ai_confidence = classification.get("confidence", 0.0)
        await db.commit()
    
    return classification


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_text(
    request: RewriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Rewrite text in Hillmann SOR style."""
    from app.services.ai.rewriter import rewrite_in_style
    
    rewritten = await rewrite_in_style(
        text=request.text,
        style=request.style,
        context=request.context,
    )
    
    return RewriteResponse(
        original=request.text,
        rewritten=rewritten,
    )


@router.post("/similar-sections")
async def find_similar_sections(
    request: SimilarSectionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Find similar historical SOR sections for RAG."""
    from app.services.ai.rag import find_similar_sections as rag_search
    
    results = await rag_search(
        section_type=request.section_type,
        query=request.query,
        top_k=request.top_k,
    )
    
    return {"sections": results}
