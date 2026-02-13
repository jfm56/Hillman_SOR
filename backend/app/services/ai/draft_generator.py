from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.report import Report
from app.models.image import Image
from app.models.document import Document
from app.services.ai.openai_client import get_openai_client
from app.services.ai.rag import build_rag_context
from app.core.config import settings


SYSTEM_PROMPT = """You are a professional construction consultant writing a Site Observation Report for Hillmann Consulting.

Your writing must:
1. Use formal, technical language appropriate for engineering reports
2. Reference specific evidence (photos, documents) with citations like [Evidence: filename]
3. Avoid speculation - only state what was directly observed
4. Use passive voice for observations ("It was observed that...")
5. Include specific dates and locations when available
6. Follow the exact structure of the example sections provided

CRITICAL RULES:
- Never fabricate observations not supported by the input data
- Always cite the source of each observation
- Flag any uncertainty with "appears to" or "further investigation recommended"
- Use standard construction terminology"""


async def generate_section_draft(
    db: AsyncSession,
    report: Report,
    section_type: str,
    options: dict,
) -> dict:
    """Generate an AI draft for a report section."""
    client = get_openai_client()
    
    # Gather context data
    context_parts = []
    evidence_references = []
    
    # 1. Get project images with AI analysis
    if options.get("include_images", True):
        image_result = await db.execute(
            select(Image)
            .where(Image.project_id == report.project_id)
            .where(Image.ai_description.isnot(None))
        )
        images = image_result.scalars().all()
        
        if images:
            image_descriptions = []
            for img in images[:10]:  # Limit to 10 images
                desc = f"- {img.original_filename}: {img.ai_description}"
                if img.building:
                    desc = f"- {img.original_filename} ({img.building.name}): {img.ai_description}"
                image_descriptions.append(desc)
                evidence_references.append({
                    "type": "image",
                    "id": str(img.id),
                    "filename": img.original_filename,
                })
            
            context_parts.append("PHOTO OBSERVATIONS:\n" + "\n".join(image_descriptions))
    
    # 2. Get parsed documents
    if options.get("include_documents", True):
        doc_result = await db.execute(
            select(Document)
            .where(Document.project_id == report.project_id)
            .where(Document.is_processed == True)
        )
        documents = doc_result.scalars().all()
        
        if documents:
            doc_summaries = []
            for doc in documents:
                if doc.parsed_data:
                    summary = f"- {doc.original_filename} ({doc.document_type}): "
                    if doc.document_type == "prior_sor":
                        summary += f"Prior report from {doc.parsed_data.get('report_date', 'unknown date')}"
                    elif doc.document_type == "cost_review":
                        summary += f"Budget: ${doc.parsed_data.get('current_budget', 0):,}, {doc.parsed_data.get('percent_complete', 0)}% complete"
                    else:
                        summary += "Parsed successfully"
                    doc_summaries.append(summary)
                    evidence_references.append({
                        "type": "document",
                        "id": str(doc.id),
                        "filename": doc.original_filename,
                        "document_type": doc.document_type,
                    })
            
            if doc_summaries:
                context_parts.append("DOCUMENT DATA:\n" + "\n".join(doc_summaries))
    
    # 3. Get RAG examples
    rag_context = ""
    if options.get("use_rag", True):
        # Build context from image analyses
        image_context = {}
        if images:
            for img in images:
                if img.ai_analysis:
                    if img.ai_analysis.get("conditions"):
                        image_context.setdefault("conditions", []).extend(img.ai_analysis["conditions"])
                    if img.ai_analysis.get("building_type"):
                        image_context["building_type"] = img.ai_analysis["building_type"]
        
        rag_context = await build_rag_context(section_type, image_context)
    
    # 4. Build the prompt
    user_prompt = f"""Generate the {section_type.replace('_', ' ').title()} section for this Site Observation Report.

PROJECT CONTEXT:
- Report Number: {report.report_number}
- Inspection Date: {report.inspection_date}
- Report Date: {report.report_date}
{f'- Weather: {report.weather_conditions}' if report.weather_conditions else ''}
{f'- Personnel: {report.personnel_on_site}' if report.personnel_on_site else ''}

{chr(10).join(context_parts)}

{rag_context}

Generate the {section_type.replace('_', ' ').title()} section following the exact style of the examples.
Include [Evidence: filename] citations for all observations.
Return only the section content, no additional formatting."""

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000,
        temperature=0.3,
    )
    
    content = response.choices[0].message.content
    
    return {
        "content": content,
        "evidence_references": evidence_references,
        "tokens_used": response.usage.total_tokens,
        "model": settings.OPENAI_MODEL,
    }
