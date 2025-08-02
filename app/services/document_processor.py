import os
import requests
import hashlib
from urllib.parse import urlparse
from typing import List, Tuple
from app.services.extract_service import PDFExtractor
from app.services.chunking_service import ChunkingService
from app.services.pinecone_service import PineconeService
from app.services.llm_service import LLMService
from app.services.document_validator import DocumentValidator
from app.models.schemas import ProcessedChunk
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.chunking_service = ChunkingService()
        self.vector_service = PineconeService()
        self.llm_service = LLMService()
        self.validator = DocumentValidator()
        
        logger.info("Initialized DocumentProcessor with all services")
    
    async def process_queries(self, document_url: str, questions: List[str]) -> List[str]:
        """Main processing pipeline with comprehensive validation"""
        try:
            # 1. Validate inputs
            await self._validate_inputs(document_url, questions)
            
            # 2. Generate document ID
            document_id = self._generate_document_id(document_url)
            
            # 3. Check if document is already processed
            if await self._is_document_processed(document_id):
                logger.info(f"Document {document_id} already processed, using existing data")
            else:
                # 4. Download and process document
                pdf_path = await self._download_document(document_url)
                
                try:
                    # 5. Extract text and convert to structured_data
                    structured_data = self.pdf_extractor.extract_structured_data(pdf_path)

                    # 6. Create chunks
                    processed_chunks = self.chunking_service.detect_headings_and_chunk_structured(structured_data, document_id)
                    logger.info(f"Generated {len(processed_chunks)} ProcessedChunk objects")
                    
                    # Filter chunks by minimum size
                    filtered_chunks = []
                    for chunk in processed_chunks:
                        if len(chunk.text.strip()) >= settings.MIN_CHUNK_SIZE:
                            filtered_chunks.append(chunk)
                    
                    logger.info(f"Filtered to {len(filtered_chunks)} chunks meeting minimum size requirement")
                    
                    # 7. Store in Pinecone
                    await self.vector_service.store_chunks(filtered_chunks, document_id)
                    
                    logger.info(f"Successfully processed document {document_id}")
                    
                finally:
                    # Cleanup downloaded file
                    if os.path.exists(pdf_path):
                        try:
                            # Small delay to ensure file handles are closed
                            import time
                            time.sleep(0.1)
                            os.remove(pdf_path)
                            logger.debug(f"Cleaned up temporary file: {pdf_path}")
                        except Exception as cleanup_error:
                            logger.warning(f"Could not clean up temporary file {pdf_path}: {cleanup_error}")
                            # Continue processing even if cleanup fails
            
            # 8. Answer questions
            answers = []
            for i, question in enumerate(questions):
                logger.debug(f"Processing question {i+1}/{len(questions)}")
                
                # Use enhanced search strategy for complex questions
                relevant_chunks = await self._search_for_question(question, document_id)
                
                if not relevant_chunks:
                    logger.warning(f"No relevant chunks found for question: {question[:50]}...")
                    # For complex questions, try to provide a general response based on available data
                    answer = await self._handle_complex_question(question, document_id)
                    answers.append(answer)
                    continue
                
                answer = await self.llm_service.generate_answer(question, relevant_chunks)
                answers.append(answer)
            
            logger.info(f"Successfully processed {len(questions)} questions")
            return answers
            
        except Exception as e:
            logger.error(f"Error in process_queries: {e}")
            raise
    
    async def _validate_inputs(self, document_url: str, questions: List[str]):
        """Validate inputs before processing"""
        # Validate URL
        url_valid, url_error = self.validator.validate_url(document_url)
        if not url_valid:
            raise ValueError(f"Invalid document URL: {url_error}")
        
        # Validate questions
        questions_valid, questions_error = self.validator.validate_questions(questions)
        if not questions_valid:
            raise ValueError(f"Invalid questions: {questions_error}")
    
    async def _is_document_processed(self, document_id: str) -> bool:
        """Check if document is already processed in Pinecone"""
        try:
            # Try to search for any chunk from this document
            results = await self.vector_service.search_similar_chunks("test", document_id)
            return len(results) > 0
        except Exception:
            return False
    
    async def _download_document(self, url: str) -> str:
        """Download document from URL with validation"""
        try:
            logger.info(f"Downloading document from: {url}")
            
            response = requests.get(url, timeout=settings.DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            # Generate safe filename
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename:
                original_filename = "document.pdf"
            
            # Create temporary filename with timestamp to avoid conflicts
            import time
            timestamp = int(time.time())
            filename = f"temp_{timestamp}_{original_filename}"
            
            # Write file
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            # Validate downloaded file
            file_valid, file_error = self.validator.validate_file_size(filename)
            if not file_valid:
                os.remove(filename)
                raise ValueError(f"Downloaded file validation failed: {file_error}")
            
            logger.info(f"Successfully downloaded: {filename} ({os.path.getsize(filename)} bytes)")
            return filename
            
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            raise ValueError(f"Failed to download document: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise
    
    def _generate_document_id(self, url: str) -> str:
        """Generate unique document ID from URL"""
        # Create a consistent hash from the URL
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    async def _search_for_question(self, question: str, document_id: str) -> List[tuple]:
        """Enhanced search strategy for complex questions"""
        try:
            # Strategy 1: Direct semantic search
            relevant_chunks = await self.vector_service.search_similar_chunks(question, document_id)
            
            if relevant_chunks:
                return relevant_chunks
            
            # Strategy 2: Extract key terms and search with those
            key_terms = self._extract_key_terms(question)
            for term in key_terms:
                chunks = await self.vector_service.search_similar_chunks(term, document_id)
                if chunks:
                    relevant_chunks.extend(chunks)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_chunks = []
            for chunk in relevant_chunks:
                chunk_id = f"{chunk[0]}_{chunk[1][:100]}"  # Use section + first 100 chars as identifier
                if chunk_id not in seen:
                    seen.add(chunk_id)
                    unique_chunks.append(chunk)
            
            return unique_chunks[:settings.TOP_K_RESULTS]
            
        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            return []
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract key terms from complex questions for better search"""
        # Common insurance terms that might be in the document
        key_terms = []
        
        # Extract quoted terms
        import re
        quoted_terms = re.findall(r'"([^"]*)"', question)
        key_terms.extend(quoted_terms)
        
        # Insurance-specific terms
        insurance_keywords = [
            "sum insured", "room rent", "co-payment", "waiting period", "cumulative bonus",
            "day care", "hospitalisation", "plastic surgery", "dental treatment",
            "cashless", "pre-authorization", "congenital anomaly", "osteoarthritis",
            "chemotherapy", "immunotherapy", "attendant charges", "misrepresentation",
            "fraud", "modern treatment", "migration", "policy", "claim", "coverage",
            "premium", "grace period", "floater", "bonus", "deduction", "expenses"
        ]
        
        question_lower = question.lower()
        for keyword in insurance_keywords:
            if keyword in question_lower:
                key_terms.append(keyword)
        
        # Extract numerical values and percentages
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', question)
        for num in numbers:
            if "%" in num or int(num.replace("%", "")) > 1000:  # Likely important numbers
                key_terms.append(f"amount {num}")
        
        return key_terms[:5]  # Limit to top 5 key terms
    
    async def _handle_complex_question(self, question: str, document_id: str) -> str:
        """Handle complex questions when no direct matches are found"""
        try:
            # Try to get any chunks from the document to provide context
            general_chunks = await self.vector_service.search_similar_chunks("policy terms conditions", document_id)
            
            if not general_chunks:
                # Try with other general terms
                for term in ["coverage", "benefits", "exclusions", "definitions"]:
                    general_chunks = await self.vector_service.search_similar_chunks(term, document_id)
                    if general_chunks:
                        break
            
            if general_chunks:
                # Use LLM to answer based on available context, even if not perfectly matched
                enhanced_prompt = f"""Based on the available policy document sections, please answer the following question as best as possible. If specific details mentioned in the question are not available, state what information is available and indicate what specific details are missing.

Question: {question}

Available Policy Information:"""
                
                answer = await self.llm_service.generate_answer(enhanced_prompt, general_chunks)
                return answer
            else:
                return f"I apologize, but I cannot find sufficient information in the policy document to answer this specific question: '{question[:100]}...'. Please ensure the document contains the relevant policy terms and conditions."
                
        except Exception as e:
            logger.error(f"Error handling complex question: {e}")
            return "I encountered an error while trying to answer this question. Please try rephrasing the question or contact support."
    
    async def get_document_info(self, document_id: str) -> dict:
        """Get information about a processed document"""
        try:
            # Search for chunks to get document info
            chunks = await self.vector_service.search_similar_chunks("", document_id)
            
            if not chunks:
                return {"status": "not_found", "chunk_count": 0}
            
            return {
                "status": "processed",
                "chunk_count": len(chunks),
                "document_id": document_id
            }
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return {"status": "error", "error": str(e)}
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a processed document from Pinecone"""
        try:
            await self.vector_service.delete_document(document_id)
            logger.info(f"Deleted document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False