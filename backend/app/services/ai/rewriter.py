from typing import Optional
from app.services.ai.openai_client import get_openai_client
from app.core.config import settings


STYLE_PROMPTS = {
    "formal_sor": """You are a professional construction consultant writing Site Observation Reports for Hillmann Consulting.

Rewrite the following text using:
- Formal, technical language appropriate for engineering reports
- Passive voice for observations ("It was observed that...")
- Specific, measurable descriptions
- Professional terminology
- No speculation - only state what can be directly observed

Maintain the original meaning while improving clarity and professionalism.""",

    "concise": """Rewrite the following text to be more concise while maintaining all key information.
Remove unnecessary words and redundant phrases.
Use active voice where appropriate.""",

    "detailed": """Expand the following text with more detail and technical specificity.
Add professional construction terminology.
Include potential implications or recommendations where appropriate.""",
}


async def rewrite_in_style(
    text: str,
    style: str = "formal_sor",
    context: Optional[dict] = None,
) -> str:
    """Rewrite text in the specified style."""
    client = get_openai_client()
    
    system_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["formal_sor"])
    
    # Add context if provided
    if context:
        if context.get("section_type"):
            system_prompt += f"\n\nThis text is for a {context['section_type'].replace('_', ' ')} section."
        if context.get("building_name"):
            system_prompt += f"\nBuilding: {context['building_name']}"
    
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Rewrite this text:\n\n{text}"}
        ],
        max_tokens=1000,
        temperature=0.3,
    )
    
    return response.choices[0].message.content.strip()
