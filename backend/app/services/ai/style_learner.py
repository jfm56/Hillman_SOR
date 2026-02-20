"""
Style Learning Service - Learn writing patterns from uploaded reports.
Supports both local LLM (Ollama) and OpenAI for processing.
Uses database for persistent storage.
"""
import uuid
import json
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.style_sample import StyleSample


async def get_embedding_local_or_remote(text: str) -> List[float]:
    """Get embedding using local or remote model."""
    if settings.USE_LOCAL_LLM:
        from app.services.ai.local_llm import generate_embedding
        return await generate_embedding(text)
    else:
        from app.services.ai.rag import get_embedding
        return await get_embedding(text)


async def process_sample_report(
    content: str,
    source_name: str,
    report_type: str = "sor",
) -> dict:
    """Process an uploaded report to extract style patterns."""
    
    # Simplified prompt for faster processing
    system_prompt = """Extract sections from this construction report. Return only valid JSON:
{"sections":[{"type":"summary","content":"..."}],"style":{"voice":"passive","tone":"formal"},"phrases":[],"terms":[]}"""

    # Limit text to 5000 chars for faster processing
    user_prompt = f"Extract sections from this report:\n\n{content[:5000]}"
    
    # Use local LLM or OpenAI
    if settings.USE_LOCAL_LLM:
        from app.services.ai.local_llm import generate_completion
        response_text = await generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=settings.LOCAL_FAST_MODEL,  # Use fast model for style analysis
            max_tokens=1000,
        )
        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                analysis = json.loads(response_text[json_start:json_end])
            else:
                analysis = {"sections": [], "style_characteristics": {}, "common_phrases": [], "terminology": []}
        except (json.JSONDecodeError, ValueError):
            analysis = {"sections": [], "style_characteristics": {}, "common_phrases": [], "terminology": []}
    else:
        from app.services.ai.openai_client import get_openai_client
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            response_format={"type": "json_object"},
        )
        analysis = json.loads(response.choices[0].message.content)
    
    # Store each section with embeddings in database
    sample_id = str(uuid.uuid4())
    stored_sections = []
    
    async with AsyncSessionLocal() as db:
        for section in analysis.get("sections", []):
            if section.get("content"):
                embedding = await get_embedding_local_or_remote(section["content"])
                
                style_sample = StyleSample(
                    id=str(uuid.uuid4()),
                    sample_id=sample_id,
                    source_name=source_name,
                    section_type=section["type"],
                    content=section["content"],
                    embedding=embedding,
                    style_characteristics=analysis.get("style_characteristics", {}),
                    common_phrases=analysis.get("common_phrases", []),
                    terminology=analysis.get("terminology", []),
                )
                db.add(style_sample)
                
                stored_sections.append({
                    "type": section["type"],
                    "preview": section["content"][:200] + "..." if len(section["content"]) > 200 else section["content"]
                })
        
        await db.commit()
    
    return {
        "sample_id": sample_id,
        "source_name": source_name,
        "sections_extracted": len(stored_sections),
        "sections": stored_sections,
        "style_characteristics": analysis.get("style_characteristics", {}),
        "common_phrases": analysis.get("common_phrases", []),
        "terminology": analysis.get("terminology", []),
    }


async def get_style_examples(
    section_type: str,
    context: str = "",
    top_k: int = 3,
) -> List[dict]:
    """Get style examples for a section type, optionally matching context."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(StyleSample).where(StyleSample.section_type == section_type)
        )
        candidates = result.scalars().all()
        
        if not candidates:
            return []
        
        if context:
            query_embedding = await get_embedding_local_or_remote(context)
            from app.services.ai.rag import cosine_similarity
            results = []
            for sample in candidates:
                if sample.embedding:
                    similarity = cosine_similarity(query_embedding, list(sample.embedding))
                    results.append({
                        "content": sample.content,
                        "source": sample.source_name,
                        "similarity": round(similarity, 4),
                    })
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        else:
            return [
                {
                    "content": s.content,
                    "source": s.source_name,
                    "similarity": 1.0,
                }
                for s in candidates[:top_k]
            ]


async def build_style_prompt(section_type: str, context: str = "") -> str:
    """Build a prompt section with style examples for draft generation."""
    examples = await get_style_examples(section_type, context)
    
    if not examples:
        return ""
    
    parts = [
        "\n--- STYLE REFERENCE ---",
        "Use the following examples as reference for writing style, tone, and terminology:",
    ]
    
    for i, ex in enumerate(examples, 1):
        parts.append(f"\nExample {i} (from {ex['source']}):")
        parts.append(ex["content"])
    
    parts.append("\n--- END STYLE REFERENCE ---\n")
    
    return "\n".join(parts)


async def get_all_samples() -> List[dict]:
    """Get all stored style samples (grouped by sample_id)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(StyleSample).order_by(StyleSample.created_at.desc()))
        all_sections = result.scalars().all()
        
        samples_by_id = {}
        for section in all_sections:
            sample_id = section.sample_id
            if sample_id not in samples_by_id:
                samples_by_id[sample_id] = {
                    "id": sample_id,
                    "source_name": section.source_name,
                    "created_at": section.created_at.isoformat() if section.created_at else "",
                    "sections": [],
                }
            samples_by_id[sample_id]["sections"].append({
                "type": section.section_type,
                "preview": section.content[:100] + "..." if len(section.content) > 100 else section.content,
            })
        
        return list(samples_by_id.values())


async def delete_sample(sample_id: str) -> bool:
    """Delete a style sample and all its sections."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(StyleSample).where(StyleSample.sample_id == sample_id)
        )
        await db.commit()
        return result.rowcount > 0
