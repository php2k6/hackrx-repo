from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.models.schemas import DocumentQuery, DocumentResponse, WebhookQuery, WebhookResponse
from app.services.document_processor import DocumentProcessor
from app.services.auth_service import get_api_key_dependency
from app.core.config import settings
import requests
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_document_processor():
    return DocumentProcessor()

@router.post("/run", response_model=DocumentResponse)
async def process_document_queries(
    request: DocumentQuery,
    processor: DocumentProcessor = Depends(get_document_processor),
    api_key: str = get_api_key_dependency()
):
    """
    Process document queries and return answers (Synchronous API)
    Requires valid API key in Authorization header: Bearer <api_key>
    """
    try:
        logger.info(f"Processing document queries with API key: {api_key[:10] if api_key != 'disabled' else 'disabled'}...")
        
        answers = await processor.process_queries(
            document_url=str(request.documents),
            questions=request.questions
        )
        return DocumentResponse(answers=answers)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/webhook", response_model=WebhookResponse)
async def webhook_process_document(
    request: WebhookQuery,
    background_tasks: BackgroundTasks,
    processor: DocumentProcessor = Depends(get_document_processor),
    api_key: str = get_api_key_dependency()
):
    """
    Webhook-style document processing with optional callback
    Processes in background and optionally calls back with results
    Requires valid API key in Authorization header: Bearer <api_key>
    """
    try:
        logger.info(f"Processing webhook request with API key: {api_key[:10] if api_key != 'disabled' else 'disabled'}...")
        
        if request.callback_url:
            # Process in background and send results to callback URL
            background_tasks.add_task(
                process_and_callback,
                processor,
                str(request.documents),
                request.questions,
                str(request.callback_url)
            )
            return WebhookResponse(
                status="accepted",
                message="Processing started. Results will be sent to callback URL.",
                callback_url=str(request.callback_url)
            )
        else:
            # Process in background but return immediate response
            background_tasks.add_task(
                process_in_background,
                processor,
                str(request.documents),
                request.questions
            )
            return WebhookResponse(
                status="accepted",
                message="Processing started in background.",
                note="Use /run endpoint for synchronous processing with immediate results"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook setup failed: {str(e)}")

async def process_and_callback(
    processor: DocumentProcessor,
    document_url: str,
    questions: list,
    callback_url: str
):
    """Background task to process document and send results to callback URL"""
    try:
        logger.info(f"Starting background processing for webhook callback to {callback_url}")
        
        # Process the document
        answers = await processor.process_queries(document_url, questions)
        
        # Prepare callback payload
        callback_data = {
            "status": "completed",
            "document_url": document_url,
            "questions": questions,
            "answers": answers,
            "timestamp": "2025-08-02T12:00:00Z"  # You might want to use actual timestamp
        }
        
        # Send results to callback URL
        response = requests.post(
            callback_url,
            json=callback_data,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent results to callback URL: {callback_url}")
        else:
            logger.error(f"Callback failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"Error in webhook callback processing: {e}")
        
        # Send error callback
        try:
            error_data = {
                "status": "error",
                "document_url": document_url,
                "questions": questions,
                "error": str(e),
                "timestamp": "2025-08-02T12:00:00Z"
            }
            requests.post(callback_url, json=error_data, timeout=10)
        except:
            logger.error(f"Failed to send error callback to {callback_url}")

async def process_in_background(
    processor: DocumentProcessor,
    document_url: str,
    questions: list
):
    """Background task to process document without callback"""
    try:
        logger.info(f"Starting background processing (no callback)")
        answers = await processor.process_queries(document_url, questions)
        logger.info(f"Background processing completed. Processed {len(questions)} questions.")
        # Results are processed but not sent anywhere (fire-and-forget)
        
    except Exception as e:
        logger.error(f"Error in background processing: {e}")

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "document-qa"}