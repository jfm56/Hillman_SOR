import base64
from app.services.ai.openai_client import get_openai_client
from app.core.config import settings


VISION_PROMPT = """You are analyzing a construction site photograph for a Site Observation Report.

Describe what you observe, focusing on:
1. Building identification (type, materials, construction phase)
2. Condition assessment (any damage, deterioration, or defects)
3. Safety observations (hazards, compliance issues)
4. Materials visible
5. Location clues (orientation, signage, landmarks)

Respond in JSON format:
{
  "description": "Detailed description in professional engineering language",
  "building_type": "residential|commercial|industrial|mixed_use|unknown",
  "construction_phase": "foundation|framing|exterior|interior|finishing|complete",
  "conditions": [
    {
      "category": "roof|exterior|interior|structural|mechanical|electrical|plumbing|site",
      "issue": "description of condition",
      "severity": "minor|moderate|severe|critical",
      "location": "where on the building"
    }
  ],
  "materials": ["list", "of", "materials"],
  "safety_issues": ["list of safety concerns if any"],
  "location_clues": ["visual clues about location"],
  "confidence": 0.85
}"""


async def analyze_image(file_path: str) -> dict:
    """Analyze an image using GPT-4 Vision."""
    client = get_openai_client()
    
    # Read and encode image
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Determine mime type
    if file_path.lower().endswith(".png"):
        mime_type = "image/png"
    elif file_path.lower().endswith((".jpg", ".jpeg")):
        mime_type = "image/jpeg"
    else:
        mime_type = "image/jpeg"
    
    response = await client.chat.completions.create(
        model=settings.OPENAI_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000,
        response_format={"type": "json_object"},
    )
    
    import json
    result = json.loads(response.choices[0].message.content)
    result["tokens_used"] = response.usage.total_tokens
    result["model"] = settings.OPENAI_VISION_MODEL
    
    return result
