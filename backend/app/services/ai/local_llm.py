"""
Local LLM Service using Ollama - keeps all data on-premises.
No data is sent to external APIs.
"""
import httpx
from typing import List, Optional, AsyncGenerator
from app.core.config import settings


async def check_ollama_connection() -> dict:
    """Check if Ollama is running and accessible."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "status": "connected",
                    "models": models,
                    "has_required_model": settings.LOCAL_MODEL in models,
                }
            return {"status": "error", "message": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "disconnected", "message": str(e)}


async def pull_model(model_name: str) -> bool:
    """Pull a model from Ollama registry."""
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/pull",
                json={"name": model_name},
            )
            return response.status_code == 200
    except Exception:
        return False


async def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """Generate a completion using local Ollama model."""
    model = model or settings.LOCAL_MODEL
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.text}")
        
        data = response.json()
        return data.get("message", {}).get("content", "")


async def generate_chat_completion(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    """Generate a chat completion from message history."""
    model = model or settings.LOCAL_MODEL
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            },
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.text}")
        
        data = response.json()
        return data.get("message", {}).get("content", "")


async def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """Generate embedding using local Ollama model."""
    model = model or settings.LOCAL_EMBEDDING_MODEL
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_HOST}/api/embeddings",
            json={
                "model": model,
                "prompt": text,
            },
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama embedding error: {response.text}")
        
        data = response.json()
        return data.get("embedding", [])


async def generate_embeddings_batch(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    embeddings = []
    for text in texts:
        embedding = await generate_embedding(text, model)
        embeddings.append(embedding)
    return embeddings


# System prompts for different tasks
SYSTEM_PROMPTS = {
    "chat": """You are an AI assistant for Hillmann Consulting, helping with Site Observation Reports (SORs).
You have access to historical reports and can help write, review, and improve construction observation reports.
Be professional, technical, and concise. Use construction industry terminology appropriately.
All conversations are private and data stays on-premises.""",

    "draft_generator": """You are an expert construction report writer for Hillmann Consulting.
Generate professional Site Observation Report sections based on the provided context.
Use formal, technical language appropriate for construction documentation.
Include specific observations, measurements, and professional assessments.
Reference evidence (photos, documents) when available.""",

    "style_analyzer": """You are an expert at analyzing technical writing style.
Extract writing patterns, common phrases, terminology, and structural elements from construction reports.
Identify the tone, voice, and formatting conventions used.""",
}


async def chat_with_context(
    user_message: str,
    context: str = "",
    history: List[dict] = None,
) -> str:
    """Chat with optional RAG context from learned reports."""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS["chat"]}]
    
    if context:
        messages.append({
            "role": "system",
            "content": f"Relevant context from historical reports:\n{context}"
        })
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_message})
    
    return await generate_chat_completion(messages)


async def generate_section_draft(
    section_type: str,
    context: dict,
    style_examples: str = "",
) -> str:
    """Generate a report section draft using local LLM."""
    system = SYSTEM_PROMPTS["draft_generator"]
    
    if style_examples:
        system += f"\n\nUse the following examples as style reference:\n{style_examples}"
    
    prompt = f"""Generate a {section_type.replace('_', ' ')} section for a Site Observation Report.

Context:
- Project: {context.get('project_name', 'N/A')}
- Date: {context.get('inspection_date', 'N/A')}
- Building: {context.get('building_type', 'N/A')}
- Observations: {context.get('observations', 'No specific observations provided')}

Generate a professional, detailed section appropriate for the report."""

    return await generate_completion(prompt, system_prompt=system)
