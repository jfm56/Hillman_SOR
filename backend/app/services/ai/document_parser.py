import fitz  # PyMuPDF
import json
from app.core.config import settings


async def parse_pdf(file_path: str, document_type: str) -> dict:
    """Parse a PDF document and extract structured data."""
    
    # Extract text using PyMuPDF
    doc = fitz.open(file_path)
    text_content = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        text_content.append({
            "page": page_num + 1,
            "text": text
        })
    
    full_text = "\n\n".join([p["text"] for p in text_content])
    page_count = len(doc)
    doc.close()
    
    # Use LLM to extract structured data based on document type
    structured_data = await extract_structured_data(full_text, document_type)
    
    return {
        "text": full_text,
        "page_count": page_count,
        "structured_data": structured_data,
    }


async def extract_structured_data(text: str, document_type: str) -> dict:
    """Use LLM to extract structured data from document text."""
    
    prompts = {
        "prior_sor": """Extract the following from this Site Observation Report and return as JSON:
{
  "report_date": "YYYY-MM-DD",
  "report_number": 0,
  "project_name": "",
  "sections": {
    "executive_summary": "content...",
    "budget_summary": "content...",
    "schedule_summary": "content...",
    "building_observations": ["observation 1", "observation 2"]
  },
  "recommendations": ["rec 1", "rec 2"],
  "percent_complete": 0
}""",
        "cost_review": """Extract the following from this cost review document and return as JSON:
{
  "original_budget": 0,
  "current_budget": 0,
  "total_costs_to_date": 0,
  "percent_complete": 0,
  "change_orders": [
    {"number": "CO-001", "description": "", "amount": 0, "status": "approved|pending"}
  ],
  "line_items": [
    {"description": "", "budget": 0, "costs_to_date": 0, "percent_complete": 0}
  ]
}""",
        "plan": """Extract the following from this construction plan and return as JSON:
{
  "project_name": "",
  "buildings": ["Building A", "Building B"],
  "phases": ["Phase 1", "Phase 2"],
  "specifications": ["spec 1", "spec 2"]
}""",
        "change_order": """Extract the following from this change order and return as JSON:
{
  "co_number": "",
  "date": "YYYY-MM-DD",
  "description": "",
  "amount": 0,
  "status": "approved|pending|rejected",
  "reason": ""
}""",
    }
    
    prompt = prompts.get(document_type, """Extract key information from this document and return as JSON:
{
  "document_type": "",
  "key_points": [],
  "dates": [],
  "amounts": [],
  "names": []
}""")
    
    # Truncate text if too long
    max_chars = 10000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Document truncated...]"
    
    system_prompt = "You are a document parsing assistant. Extract structured data from construction documents. Return valid JSON only, no additional text."
    user_prompt = f"{prompt}\n\nDocument text:\n{text}"
    
    if settings.USE_LOCAL_LLM:
        from app.services.ai.local_llm import generate_completion
        response_text = await generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=2000,
        )
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])
            return {"raw_text": text[:500], "parse_error": "Could not extract JSON"}
        except json.JSONDecodeError:
            return {"raw_text": text[:500], "parse_error": "Invalid JSON response"}
    else:
        from app.services.ai.openai_client import get_openai_client
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
