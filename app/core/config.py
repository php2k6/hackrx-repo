
from pydantic_settings import BaseSettings
from typing import Optional, List
from enum import Enum

class PineconeCloud(str, Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

class Settings(BaseSettings):
    # Pinecone Configuration
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-west1-gcp-free"
    PINECONE_INDEX_NAME: str = "hackrx-documents"
    PINECONE_CLOUD: PineconeCloud = PineconeCloud.AWS
    PINECONE_REGION: str = "us-east-1"
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "g4f.Provider.Blackbox"  # Any g4f provider string
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1000
    
    # Embedding Model Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_DEVICE: str = "cpu"
    
    # Text Processing Configuration
    MAX_CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    TOP_K_RESULTS: int = 10
    MIN_CHUNK_SIZE: int = 50
    SIMILARITY_THRESHOLD: float = 0.05
    
    # Document Processing Configuration
    SUPPORTED_FORMATS: str = "pdf,docx,txt"
    MAX_FILE_SIZE_MB: int = 50
    DOWNLOAD_TIMEOUT: int = 30
    
    # Application Settings
    APP_NAME: str = "HackRX Document Q&A"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_VERSION: str = "1.0.0"
    
    @property
    def supported_formats_list(self) -> List[str]:
        """Convert comma-separated formats to list"""
        return [fmt.strip().lower() for fmt in self.SUPPORTED_FORMATS.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    model_config = {"env_file": ".env"}

settings = Settings()