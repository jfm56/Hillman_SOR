from typing import List, Optional
from app.services.ai.openai_client import get_openai_client
from app.core.config import settings

# In-memory store for demo (replace with ChromaDB or pgvector in production)
_historical_sections: List[dict] = []


async def get_embedding(text: str) -> List[float]:
    """Generate embedding for text."""
    client = get_openai_client()
    
    response = await client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
    )
    
    return response.data[0].embedding


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


async def add_historical_section(
    section_type: str,
    content: str,
    metadata: Optional[dict] = None,
) -> str:
    """Add a historical section to the RAG store."""
    import uuid
    
    embedding = await get_embedding(content)
    
    section = {
        "id": str(uuid.uuid4()),
        "section_type": section_type,
        "content": content,
        "embedding": embedding,
        "metadata": metadata or {},
    }
    
    _historical_sections.append(section)
    return section["id"]


async def find_similar_sections(
    section_type: str,
    query: str,
    top_k: int = 5,
) -> List[dict]:
    """Find similar historical sections using embeddings."""
    
    # Filter by section type
    candidates = [s for s in _historical_sections if s["section_type"] == section_type]
    
    if not candidates:
        return []
    
    # Get query embedding
    query_embedding = await get_embedding(query)
    
    # Calculate similarities
    results = []
    for section in candidates:
        similarity = cosine_similarity(query_embedding, section["embedding"])
        results.append({
            "id": section["id"],
            "section_type": section["section_type"],
            "content": section["content"],
            "similarity": round(similarity, 4),
            "preview": section["content"][:200] + "..." if len(section["content"]) > 200 else section["content"],
        })
    
    # Sort by similarity and return top_k
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


async def build_rag_context(
    section_type: str,
    context: dict,
    top_k: int = 3,
) -> str:
    """Build RAG context for draft generation."""
    
    # Build query from context
    query_parts = [f"Section type: {section_type}"]
    
    if context.get("building_type"):
        query_parts.append(f"Building type: {context['building_type']}")
    
    if context.get("conditions"):
        conditions = ", ".join(c.get("issue", "") for c in context["conditions"] if c.get("issue"))
        if conditions:
            query_parts.append(f"Conditions: {conditions}")
    
    if context.get("observations"):
        query_parts.append(f"Observations: {context['observations']}")
    
    query = " ".join(query_parts)
    
    # Find similar sections
    similar = await find_similar_sections(section_type, query, top_k)
    
    if not similar:
        return ""
    
    # Build context string
    context_parts = ["EXAMPLE SECTIONS (use this style and tone):"]
    for i, section in enumerate(similar, 1):
        context_parts.append(f"\nExample {i} (similarity: {section['similarity']}):")
        context_parts.append(section["content"])
    
    return "\n".join(context_parts)


# Seed some example historical sections for demo
EXAMPLE_SECTIONS = [
    {
        "section_type": "executive_summary",
        "content": """During the February 10, 2026 site observation, work was observed to be progressing in accordance with the approved construction schedule. Building A exterior facade installation is approximately 85% complete, with remaining work concentrated on the north elevation. Building B structural framing has been completed and interior rough-in work has commenced. No significant safety concerns were observed during the site visit. The project remains on track for the anticipated completion date of September 2026."""
    },
    {
        "section_type": "building_status",
        "content": """Building B – Status Update

The structural steel framing for Building B has been completed and accepted by the structural engineer of record. Exterior metal stud framing is approximately 75% complete, with work progressing on levels 2 through 4. Window installation has commenced on the south and east elevations, with approximately 40% of units installed.

Interior work includes MEP rough-in on levels 1 and 2, with electrical conduit and plumbing risers in place. HVAC ductwork installation is ongoing on level 1.

[Evidence: IMG_045.jpg, IMG_046.jpg, IMG_047.jpg]

No significant deficiencies were observed. Minor punch list items have been documented and communicated to the general contractor."""
    },
    {
        "section_type": "budget_summary",
        "content": """As of the February 2026 payment application, the project has expended $12,450,000 against an approved budget of $18,500,000, representing 67.3% of the total contract value. This expenditure level is consistent with the reported physical completion of 65%.

Change orders approved to date total $485,000, bringing the current contract value to $18,985,000. The most recent change order (CO-012) addressed unforeseen soil conditions requiring additional foundation work.

Based on current progress and approved change orders, the project remains within budget parameters. No additional contingency draws are anticipated at this time."""
    },
]


async def seed_example_sections():
    """Seed the RAG store with example sections."""
    for section in EXAMPLE_SECTIONS:
        await add_historical_section(
            section_type=section["section_type"],
            content=section["content"],
        )
