import re
from typing import List
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
    
    def create_chunks(self, markdown_text: str, document_id: str = "") -> List[ProcessedChunk]:
        """Create chunks from markdown text with enhanced processing"""
        if not markdown_text.strip():
            logger.warning("Empty markdown text provided")
            return []
        
        # Use enhanced chunking logic
        raw_chunks = self._detect_headings_and_chunk(markdown_text)
        
        if not raw_chunks:
            logger.warning("No chunks created from markdown text")
            return []
        
        processed_chunks = []
        for i, chunk in enumerate(raw_chunks):
            # Skip chunks that are too small
            if len(chunk["text"].strip()) < self.min_chunk_size:
                continue
                
            metadata = ChunkMetadata(
                section=chunk["section"],
                page=chunk.get("page", 1),
                document_id=document_id,
                chunk_index=i
            )
            
            processed_chunks.append(ProcessedChunk(
                text=chunk["text"],
                metadata=metadata
            ))
        
        logger.info(f"Created {len(processed_chunks)} chunks from {len(raw_chunks)} raw chunks")
        return processed_chunks
    
    def _detect_headings_and_chunk(self, md_text: str) -> List[dict]:
        """Your existing chunking logic - keep as is"""
        lines = md_text.split("\n")
        sections = []
        current_section = {"heading": "Introduction", "content": ""}

        heading_pattern = re.compile(r"^\s*#{1,6}\s+.+")

        for line in lines:
            clean_line = line.strip()

            if clean_line and heading_pattern.match(clean_line) and len(clean_line.split()) < 12:
                if current_section["content"].strip():
                    sections.append(current_section)
                current_section = {"heading": clean_line.strip("_*# "), "content": ""}
            else:
                current_section["content"] += line + "\n"

        if current_section["content"].strip():
            sections.append(current_section)

        splitter = TextSplitter(capacity=self.chunk_size, overlap=self.chunk_overlap)
        chunks = []
        for sec in sections:
            for sc in splitter.chunks(sec["content"]):
                chunks.append({
                    "section": sec["heading"],
                    "text": sc
                })

        return chunks