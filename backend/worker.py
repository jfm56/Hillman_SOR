"""Background worker for off-hours document ingestion.

Responsibilities:
- Ingest new PDFs nightly
- Extract text
- Generate embeddings
- Store in database
- Generate document summary
- Delete temporary memory objects

Web API never performs bulk ingestion - this worker handles it.
"""
import asyncio
import gc
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.document import Document
from app.services.chunking import ingest_document, MAX_PDF_PAGES
from app.services.ai.document_parser import extract_text_from_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_unprocessed_documents():
    """Find and process all unprocessed documents."""
    async with AsyncSessionLocal() as db:
        # Get unprocessed documents
        result = await db.execute(
            select(Document)
            .where(Document.is_processed == False)
            .order_by(Document.created_at.asc())
            .limit(10)  # Process in batches
        )
        documents = result.scalars().all()
        
        if not documents:
            logger.info("No unprocessed documents found")
            return 0
        
        logger.info(f"Found {len(documents)} unprocessed documents")
        processed_count = 0
        
        for doc in documents:
            try:
                await process_single_document(db, doc)
                processed_count += 1
                
                # Force garbage collection after each document
                gc.collect()
                
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}")
                continue
        
        return processed_count


async def process_single_document(db: AsyncSession, doc: Document):
    """Process a single document: extract text, chunk, embed, store."""
    logger.info(f"Processing document: {doc.filename}")
    
    # Check page limit
    if doc.page_count and doc.page_count > MAX_PDF_PAGES:
        logger.warning(f"Document {doc.filename} has {doc.page_count} pages, exceeds limit of {MAX_PDF_PAGES}")
        # Still process but truncate
    
    # Extract text if not already done
    if not doc.extracted_text:
        file_path = Path(doc.file_path)
        if file_path.exists() and file_path.suffix.lower() == '.pdf':
            text = await extract_text_from_pdf(str(file_path), max_pages=MAX_PDF_PAGES)
            doc.extracted_text = text
    
    if not doc.extracted_text:
        logger.warning(f"No text extracted from document {doc.filename}")
        return
    
    # Chunk and embed
    metadata = {
        "filename": doc.filename,
        "document_type": doc.document_type,
        "project_id": str(doc.project_id) if doc.project_id else None,
    }
    
    chunk_count = await ingest_document(
        db=db,
        document_id=doc.id,
        text=doc.extracted_text,
        metadata=metadata,
    )
    
    logger.info(f"Created {chunk_count} chunks for document {doc.filename}")
    
    # Mark as processed
    await db.execute(
        update(Document)
        .where(Document.id == doc.id)
        .values(
            is_processed=True,
            processed_at=datetime.utcnow(),
        )
    )
    await db.commit()
    
    # Clear extracted text from memory (it's now in chunks)
    doc.extracted_text = None
    gc.collect()


async def cleanup_old_temp_files():
    """Delete temporary processing files older than 24 hours."""
    temp_dir = Path("/app/storage/temp")
    if not temp_dir.exists():
        return
    
    cutoff = datetime.utcnow().timestamp() - (24 * 60 * 60)
    
    for file in temp_dir.glob("*"):
        if file.stat().st_mtime < cutoff:
            try:
                file.unlink()
                logger.info(f"Deleted temp file: {file}")
            except Exception as e:
                logger.error(f"Error deleting temp file {file}: {e}")


async def run_worker():
    """Main worker loop."""
    logger.info("Starting background worker...")
    
    while True:
        try:
            # Process documents
            processed = await process_unprocessed_documents()
            logger.info(f"Processed {processed} documents")
            
            # Cleanup temp files
            await cleanup_old_temp_files()
            
            # Force garbage collection
            gc.collect()
            
            # Sleep for 1 hour before next run
            logger.info("Sleeping for 1 hour...")
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    asyncio.run(run_worker())
