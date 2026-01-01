"""
Application Configuration

Environment variables and settings management.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # CORS Settings
    ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:5173,http://localhost:3000,http://localhost:8000"
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Database Settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/codebase_db"
    
    # Vector Store Settings
    VECTOR_STORE_PATH: str = "./data/faiss_index"
    
    # Embedding Settings
    EMBEDDING_PROVIDER: str = "huggingface"  # "openai" or "huggingface"
    OPENAI_API_KEY: str = ""  # Only needed if using OpenAI embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # HuggingFace: all-MiniLM-L6-v2, OpenAI: text-embedding-ada-002
    
    # LLM Settings (Groq - Free)
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.1-70b-versatile"  # or mixtral-8x7b-32768
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2000
    
    # Repository Settings
    REPO_CLONE_PATH: str = "./data/repositories"
    MAX_FILE_SIZE_MB: int = 10
    SUPPORTED_LANGUAGES: List[str] = ["python", "javascript", "typescript"]
    
    # Retrieval Settings
    TOP_K_RESULTS: int = 10
    MAX_FLOW_DEPTH: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
