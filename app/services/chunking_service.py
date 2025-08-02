import re
from typing import List, Union
from semantic_text_splitter import TextSplitter
from app.models.schemas import ProcessedChunk, ChunkMetadata
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ChunkingService:
    def __init__(self):
        self.chunk_size = settings.MAX_CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.min_chunk_size = settings.MIN_CHUNK_SIZE
        
        logger.info(f"Initialized chunking service - Size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
    
    def create_chunks(self, data: Union[str, List], document_id: str = "") -> List[ProcessedChunk]:
        """Create chunks from text or structured data with enhanced processing"""
        if isinstance(data, str):
            # Handle plain text/markdown
            if not data.strip():
                logger.warning("Empty text provided")
                return []
        else:
            # Handle structured data
            if not data:
                logger.warning("Empty structured data provided")
                return []
        
        # Use the same function for both text and structured data
        chunks = self.detect_headings_and_chunk_structured(data, document_id)
        
        if not chunks:
            logger.warning("No chunks created from data")
            return []
        
        logger.info(f"Successfully created {len(chunks)} ProcessedChunk objects")
        return chunks

    def detect_headings_and_chunk_structured(self, data: Union[str, List[dict]], document_id: str = "") -> List[ProcessedChunk]:
        """Detect headings using font size / bold style / section number, chunk section-wise."""
        
        
        # Handle structured data
        structured_pages = data
        logger.info(f"Starting structured chunking for {len(structured_pages)} pages (document: {document_id})")
        
        # Find body font size (most common across pages)
        font_sizes = []
        for page in structured_pages:
            for el in page["elements"]:
                if el["type"] == "text":
                    font_sizes.append(el["font_size"])
        body_font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10
        logger.info(f"Detected body font size: {body_font_size}")

        # Regex for numbered section headings
        numbered_heading_pattern = re.compile(r"^\d+(\.\d+)*\s+.+$")

        sections = []
        current_section = {"heading": "Introduction", "content": "", "page": 1}
        headings_detected = 0

        for page in structured_pages:
            page_num = page.get('page', 1)
            logger.debug(f"Processing page {page_num} with {len(page['elements'])} elements")
            for el in page["elements"]:
                if el["type"] == "text":
                    is_numbered_heading = (
                        el["is_bold"] and numbered_heading_pattern.match(el["text"])
                    )

                    # Heading detection: larger font OR bold OR numbered heading
                    if (
                        el["font_size"] > body_font_size + 0.5
                        or el["is_bold"]
                        or is_numbered_heading
                    ):
                        # Force accept if it's a numbered heading
                        if is_numbered_heading or (el["font_size"] > body_font_size + 0.5 or el["is_bold"]):
                            if current_section["content"].strip():
                                sections.append(current_section)
                            # Keep section number as is and track page
                            current_section = {"heading": el["text"], "content": "", "page": page_num}
                            headings_detected += 1
                            logger.debug(f"Detected heading: '{el['text'][:50]}...' (font: {el['font_size']}, bold: {el['is_bold']}, page: {page_num})")
                    else:
                        current_section["content"] += el["text"] + "\n"

                elif el["type"] == "table":
                    # Attach table to current section
                    current_section["content"] += f"\n[TABLE DATA]: {el['text']}\n"
                    logger.debug(f"Added table data to section '{current_section['heading']}' on page {page_num}")

        if current_section["content"].strip():
            sections.append(current_section)

        logger.info(f"Detected {headings_detected} headings, created {len(sections)} sections")

        # Now chunk section-wise and create ProcessedChunk objects
        splitter = TextSplitter(capacity=self.chunk_size, overlap=self.chunk_overlap)
        processed_chunks = []
        chunk_index = 0
        
        for sec in sections:
            section_chunks = list(splitter.chunks(sec["content"]))
            logger.debug(f"Section '{sec['heading'][:30]}...' split into {len(section_chunks)} chunks")
            
            for chunk_text in section_chunks:
                # Skip chunks that are too small
                if len(chunk_text.strip()) < self.min_chunk_size:
                    continue
                    
                metadata = ChunkMetadata(
                    section=sec["heading"],
                    page=sec["page"],
                    document_id=document_id,
                    chunk_index=chunk_index
                )
                
                processed_chunk = ProcessedChunk(
                    text=chunk_text,
                    metadata=metadata
                )
                
                processed_chunks.append(processed_chunk)
                chunk_index += 1

        logger.info(f"Created {len(processed_chunks)} ProcessedChunk objects from structured data (document: {document_id})")
        return processed_chunks

        