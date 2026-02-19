"""
AI Learning Service - Learn from past AI interactions to improve report generation.
Stores all AI prompts/responses and uses them to enhance future drafts.
"""
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert

from app.models.audit import AIInteractionLog
from app.core.config import settings


async def log_ai_interaction(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    interaction_type: str,
    model_name: str,
    prompt: str,
    response: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int = 0,
    project_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    status: str = "success",
    error_message: Optional[str] = None,
) -> AIInteractionLog:
    """Log an AI interaction to the database for learning."""
    log_entry = AIInteractionLog(
        user_id=user_id,
        interaction_type=interaction_type,
        model_name=model_name,
        prompt=prompt,
        response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        project_id=project_id,
        report_id=report_id,
        status=status,
        error_message=error_message,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry


async def get_similar_interactions(
    db: AsyncSession,
    interaction_type: str,
    context_keywords: List[str],
    limit: int = 5,
) -> List[dict]:
    """
    Retrieve past successful AI interactions similar to the current request.
    Uses keyword matching for now; can be upgraded to embedding similarity.
    """
    # Get recent successful interactions of same type
    query = (
        select(AIInteractionLog)
        .where(AIInteractionLog.interaction_type == interaction_type)
        .where(AIInteractionLog.status == "success")
        .where(AIInteractionLog.response.isnot(None))
        .order_by(desc(AIInteractionLog.created_at))
        .limit(100)  # Get last 100 to filter
    )
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    if not interactions:
        return []
    
    # Score by keyword relevance
    scored = []
    keywords_lower = [k.lower() for k in context_keywords if k]
    
    for interaction in interactions:
        score = 0
        prompt_lower = interaction.prompt.lower()
        response_lower = (interaction.response or "").lower()
        
        for keyword in keywords_lower:
            if keyword in prompt_lower:
                score += 2
            if keyword in response_lower:
                score += 1
        
        if score > 0:
            scored.append({
                "id": str(interaction.id),
                "prompt": interaction.prompt[:500],  # Truncate for context
                "response": interaction.response[:1000] if interaction.response else "",
                "score": score,
                "created_at": interaction.created_at.isoformat(),
            })
    
    # Sort by score and return top results
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


async def get_section_examples_from_logs(
    db: AsyncSession,
    section_type: str,
    building_type: Optional[str] = None,
    limit: int = 3,
) -> List[dict]:
    """Get past successful draft generations for a section type."""
    keywords = [section_type.replace("_", " ")]
    if building_type:
        keywords.append(building_type)
    
    # Look for draft generation interactions
    interactions = await get_similar_interactions(
        db=db,
        interaction_type="draft_generation",
        context_keywords=keywords,
        limit=limit,
    )
    
    return interactions


async def build_learning_context(
    db: AsyncSession,
    section_type: str,
    context: dict,
) -> str:
    """
    Build context from past AI interactions to improve draft generation.
    Returns formatted examples from successful past generations.
    """
    # Extract keywords from context
    keywords = [section_type.replace("_", " ")]
    
    if context.get("building_type"):
        keywords.append(context["building_type"])
    if context.get("conditions"):
        keywords.extend(context["conditions"][:5])  # Top 5 conditions
    
    # Get similar past interactions
    examples = await get_section_examples_from_logs(
        db=db,
        section_type=section_type,
        building_type=context.get("building_type"),
        limit=3,
    )
    
    if not examples:
        return ""
    
    # Format as learning context
    parts = [
        "\n--- LEARNED EXAMPLES (from past successful reports) ---",
    ]
    
    for i, ex in enumerate(examples, 1):
        parts.append(f"\nExample {i}:")
        parts.append(ex["response"][:800])  # Truncate long responses
    
    parts.append("\n--- END LEARNED EXAMPLES ---\n")
    parts.append("Use these examples as reference for style, structure, and terminology.")
    
    return "\n".join(parts)


async def get_learning_stats(db: AsyncSession) -> dict:
    """Get statistics about learned AI interactions."""
    # Count by interaction type
    query = select(AIInteractionLog).where(AIInteractionLog.status == "success")
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    stats = {
        "total_interactions": len(interactions),
        "by_type": {},
        "recent_count": 0,
    }
    
    now = datetime.utcnow()
    for interaction in interactions:
        # Count by type
        itype = interaction.interaction_type
        stats["by_type"][itype] = stats["by_type"].get(itype, 0) + 1
        
        # Count recent (last 7 days)
        if (now - interaction.created_at).days < 7:
            stats["recent_count"] += 1
    
    return stats
