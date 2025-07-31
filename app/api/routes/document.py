from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import DocumentQuery, DocumentResponse
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

router = APIRouter()

async def get_document_processor():
    return DocumentProcessor()

@router.post("/run", response_model=DocumentResponse)
async def process_document_queries(
    request: DocumentQuery,
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Process document queries and return answers
    """
    try:
        answers = await processor.process_queries(
            document_url=str(request.documents),
            questions=request.questions
        )
        return DocumentResponse(answers=answers)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "document-qa"}