from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import document
from app.core.config import settings
from app.services.llm_service import LLMService
import logging

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title=settings.APP_NAME,
    description="Insurance Document Question Answering System with Pinecone Vector Search",
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document.router, prefix="/hackrx", tags=["document"])

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.API_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "document-qa",
        "version": settings.API_VERSION
    }

@app.get("/llm")
async def llm_query(query: str = Query(..., description="The query to send to the LLM")):
    """
    Direct LLM endpoint that takes a query and returns the LLM response.
    
    Args:
        query: The question or prompt to send to the LLM
        
    Returns:
        dict: Contains the query, response, and metadata
    """
    try:
        # Initialize LLM service
        llm_service = LLMService()
        
        # Get direct response from LLM without document context
        response = await llm_service.generate_direct_answer(query)
        
        return {
            "query": query,
            "response": response,
            "llm_provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing LLM query: {str(e)}"
        )