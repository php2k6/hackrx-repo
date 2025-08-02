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

        logger.info(
            f"Initialized chunking service - Size: {self.chunk_size}, Overlap: {self.chunk_overlap}"
        )

    def create_chunks(self, data: Union[str, List], document_id: str = "") -> List[ProcessedChunk]:
        """Create chunks from text or structured data with enhanced processing"""
        if isinstance(data, str):
            if not data.strip():
                logger.warning("Empty text provided")
                return []
        else:
            if not data:
                logger.warning("Empty structured data provided")
                return []

        chunks = self.detect_headings_and_chunk_structured(data, document_id)

        if not chunks:
            logger.warning("No chunks created from data")
            return []

        logger.info(
            f"Successfully created {len(chunks)} ProcessedChunk objects")
        return chunks

    def detect_headings_and_chunk_structured(
        self, data: Union[str, List[dict]], document_id: str = ""
    ) -> List[ProcessedChunk]:
        """Detect headings using font size / bold style / section number, chunk section-wise."""

        structured_pages = data
        logger.info(
            f"Starting structured chunking for {len(structured_pages)} pages (document: {document_id})"
        )

        # Find body font size
        font_sizes = [
            el["font_size"]
            for page in structured_pages
            for el in page["elements"]
            if el["type"] == "text"
        ]
        body_font_size = max(
            set(font_sizes), key=font_sizes.count) if font_sizes else 10
        logger.info(f"Detected body font size: {body_font_size}")

        # Patterns
        level1_pattern = re.compile(r"^\d+(\s+|\.)(?!\d).+")  # 1 Intro
        numbered_heading_pattern = re.compile(
            r"^\d+(\.\d+)*\s+.+$")  # 1.1 Subheading

        sections = []
        current_level1 = "Introduction"
        current_section = {
            "heading": "Introduction",
            "content": "",
            "page": 1,
            "level1": current_level1
        }
        headings_detected = 0

        for page in structured_pages:
            page_num = page.get("page", 1)
            logger.debug(
                f"Processing page {page_num} with {len(page['elements'])} elements")
            for el in page["elements"]:
                if el["type"] == "text":
                    is_numbered_heading = (
                        el["is_bold"] and numbered_heading_pattern.match(
                            el["text"])
                    )

                    if (
                        el["font_size"] > body_font_size + 0.5
                        or el["is_bold"]
                        or is_numbered_heading
                    ):
                        if level1_pattern.match(el["text"]):
                            current_level1 = el["text"].strip()

                        if current_section["content"].strip():
                            sections.append(current_section)

                        current_section = {
                            "heading": el["text"].strip(),
                            "content": "",
                            "page": page_num,
                            "level1": current_level1
                        }
                        headings_detected += 1
                        logger.debug(
                            f"Detected heading: '{el['text'][:50]}...' "
                            f"(font: {el['font_size']}, bold: {el['is_bold']}, page: {page_num})"
                        )
                    else:
                        current_section["content"] += el["text"] + "\n"

                elif el["type"] == "table":
                    current_section["content"] += f"\n[TABLE DATA]: {el['text']}\n"
                    logger.debug(
                        f"Added table data to section '{current_section['heading']}' on page {page_num}"
                    )

        if current_section["content"].strip():
            sections.append(current_section)

        logger.info(
            f"Detected {headings_detected} headings, created {len(sections)} sections")

        # Chunk section-wise
        splitter = TextSplitter(capacity=self.chunk_size,
                                overlap=self.chunk_overlap)
        processed_chunks = []
        chunk_index = 0

        for sec in sections:
            section_chunks = list(splitter.chunks(sec["content"]))
            logger.debug(
                f"Section '{sec['heading'][:30]}...' split into {len(section_chunks)} chunks"
            )

            for chunk_text in section_chunks:
                if len(chunk_text.strip()) < self.min_chunk_size:
                    continue

                # Prepend headings for LLM context
                chunk_with_context = (
                    f"This section is under : {sec['level1']}\n"
                    f"This sub section is : {sec['heading']}\n\n"
                    f"{chunk_text}"
                )

                metadata = ChunkMetadata(
                    section=sec["level1"],        # Top-level section
                    sub_section=sec["heading"],   # Current sub-section
                    page=sec["page"],
                    document_id=document_id,
                    chunk_index=chunk_index
                )

                processed_chunk = ProcessedChunk(
                    text=chunk_with_context,
                    metadata=metadata
                )

                processed_chunks.append(processed_chunk)
                chunk_index += 1

        logger.info(
            f"Created {len(processed_chunks)} ProcessedChunk objects from structured data "
            f"(document: {document_id})"
            # print all chunks for debugging
        )
        for chunk in processed_chunks:
            logger.info(
                f"ProcessedChunk (document: {document_id}, index: {chunk.metadata.chunk_index}): {chunk.text[:500]}...")

        return processed_chunks
