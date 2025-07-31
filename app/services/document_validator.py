import os
import requests
from urllib.parse import urlparse
from typing import Tuple, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentValidator:
    """Service to validate documents before processing"""
    
    def __init__(self):
        self.supported_formats = settings.supported_formats_list
        self.max_file_size = settings.max_file_size_bytes
        self.download_timeout = settings.DOWNLOAD_TIMEOUT
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate if URL is accessible and points to supported format"""
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            # Check file extension
            path = parsed.path.lower()
            file_extension = path.split('.')[-1] if '.' in path else ''
            
            if file_extension not in self.supported_formats:
                return False, f"Unsupported format: {file_extension}. Supported: {', '.join(self.supported_formats)}"
            
            # Check if URL is accessible (HEAD request)
            try:
                response = requests.head(url, timeout=self.download_timeout)
                if response.status_code >= 400:
                    return False, f"URL not accessible: HTTP {response.status_code}"
                
                # Check content length if available
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_file_size:
                    return False, f"File too large: {int(content_length) / 1024 / 1024:.1f}MB (max: {settings.MAX_FILE_SIZE_MB}MB)"
                
            except requests.RequestException as e:
                return False, f"URL accessibility check failed: {str(e)}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False, f"URL validation failed: {str(e)}"
    
    def validate_file_size(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate downloaded file size"""
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False, f"File too large: {file_size / 1024 / 1024:.1f}MB (max: {settings.MAX_FILE_SIZE_MB}MB)"
            
            if file_size == 0:
                return False, "File is empty"
            
            return True, None
            
        except Exception as e:
            logger.error(f"File size validation error: {e}")
            return False, f"File size validation failed: {str(e)}"
    
    def validate_questions(self, questions: list) -> Tuple[bool, Optional[str]]:
        """Validate questions list"""
        if not questions:
            return False, "No questions provided"
        
        if not isinstance(questions, list):
            return False, "Questions must be a list"
        
        if len(questions) > 50:  # Reasonable limit
            return False, "Too many questions (max: 50)"
        
        for i, question in enumerate(questions):
            if not isinstance(question, str):
                return False, f"Question {i+1} must be a string, got {type(question)}"
            
            if not question.strip():
                return False, f"Question {i+1} is empty"
            
            if len(question) > 1000:  # Reasonable limit
                return False, f"Question {i+1} too long (max: 1000 characters)"
        
        return True, None
