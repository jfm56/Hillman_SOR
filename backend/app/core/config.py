from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Hillmann AI System"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sor_ai"
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # File Storage
    STORAGE_PATH: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/heic"]
    ALLOWED_DOCUMENT_TYPES: List[str] = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    # OpenAI (optional - only if USE_LOCAL_LLM=false)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_VISION_MODEL: str = "gpt-4-vision-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Local LLM Settings (Ollama)
    USE_LOCAL_LLM: bool = True
    OLLAMA_HOST: str = "http://localhost:11434"
    LOCAL_MODEL: str = "llama3.2"
    LOCAL_EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # RAG Settings
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure storage directories exist
os.makedirs(f"{settings.STORAGE_PATH}/photos", exist_ok=True)
os.makedirs(f"{settings.STORAGE_PATH}/pdfs", exist_ok=True)
os.makedirs(f"{settings.STORAGE_PATH}/reports", exist_ok=True)
os.makedirs(f"{settings.STORAGE_PATH}/exports", exist_ok=True)
