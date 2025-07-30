from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class DocumentRequest(BaseModel):
    pdf_path: str
    query: str

class DocumentQuery(BaseModel):
    documents: HttpUrl
    questions: List[str]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf",
                "questions": [
                    "What is the grace period for premium payment?",
                    "What is the waiting period for pre-existing diseases?"
                ]
            }
        }
    }

class DocumentResponse(BaseModel):
    answers: List[str]

class SemanticChunk(BaseModel):
    section: str
    text: str

class ChunkMetadata(BaseModel):
    section: str
    page: int
    document_id: str
    chunk_index: int

class ProcessedChunk(BaseModel):
    text: str
    metadata: ChunkMetadata
    embedding: List[float] = None