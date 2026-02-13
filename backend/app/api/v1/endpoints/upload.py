from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID, uuid4
import aiofiles
import os
from datetime import datetime
from PIL import Image as PILImage
import io

from app.db.session import get_db
from app.models.image import Image
from app.models.document import Document
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings
from app.services.audit import log_action

router = APIRouter()


class UploadedFileResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    ai_processing_queued: bool = False


class UploadResponse(BaseModel):
    uploaded: List[UploadedFileResponse]
    failed: List[dict]


@router.post("/images", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    project_id: UUID = Form(...),
    building_id: Optional[UUID] = Form(None),
    area: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload multiple images."""
    uploaded = []
    failed = []
    
    # Create project directory
    project_dir = f"{settings.STORAGE_PATH}/photos/{project_id}"
    if building_id:
        project_dir = f"{project_dir}/{building_id}"
    os.makedirs(project_dir, exist_ok=True)
    
    for file in files:
        try:
            # Validate file type
            if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
                failed.append({"filename": file.filename, "error": "Invalid file type"})
                continue
            
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            # Check file size
            if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                failed.append({"filename": file.filename, "error": "File too large"})
                continue
            
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid4()}{file_ext}"
            file_path = f"{project_dir}/{unique_filename}"
            
            # Get image dimensions
            width, height = None, None
            try:
                img = PILImage.open(io.BytesIO(content))
                width, height = img.size
            except Exception:
                pass
            
            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            # Parse tags
            tag_list = []
            if tags:
                tag_list = [t.strip() for t in tags.split(",")]
            
            # Create database record
            image = Image(
                project_id=project_id,
                building_id=building_id,
                area=area,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type,
                width=width,
                height=height,
                tags=tag_list,
                uploaded_by=current_user.id,
            )
            db.add(image)
            await db.flush()
            
            await log_action(db, current_user.id, "upload", "image", image.id, after_data={"filename": file.filename})
            
            uploaded.append(UploadedFileResponse(
                id=str(image.id),
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                width=width,
                height=height,
                ai_processing_queued=True,
            ))
            
        except Exception as e:
            failed.append({"filename": file.filename, "error": str(e)})
    
    await db.commit()
    
    # TODO: Queue images for AI processing
    
    return UploadResponse(uploaded=uploaded, failed=failed)


@router.post("/documents", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    project_id: UUID = Form(...),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload PDF documents."""
    uploaded = []
    failed = []
    
    # Create project directory
    project_dir = f"{settings.STORAGE_PATH}/pdfs/{project_id}"
    os.makedirs(project_dir, exist_ok=True)
    
    for file in files:
        try:
            # Validate file type
            if file.content_type not in settings.ALLOWED_DOCUMENT_TYPES:
                failed.append({"filename": file.filename, "error": "Invalid file type"})
                continue
            
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            # Check file size
            if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                failed.append({"filename": file.filename, "error": "File too large"})
                continue
            
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid4()}{file_ext}"
            file_path = f"{project_dir}/{unique_filename}"
            
            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            # Create database record
            document = Document(
                project_id=project_id,
                document_type=document_type,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type,
                uploaded_by=current_user.id,
            )
            db.add(document)
            await db.flush()
            
            await log_action(db, current_user.id, "upload", "document", document.id, after_data={"filename": file.filename, "type": document_type})
            
            uploaded.append(UploadedFileResponse(
                id=str(document.id),
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                ai_processing_queued=True,
            ))
            
        except Exception as e:
            failed.append({"filename": file.filename, "error": str(e)})
    
    await db.commit()
    
    # TODO: Queue documents for parsing
    
    return UploadResponse(uploaded=uploaded, failed=failed)
