import re
from semantic_text_splitter import TextSplitter

def detect_headings_and_chunk(md_text, chunk_size=500, chunk_overlap=50):
    lines = md_text.split("\n")
    sections = []
    current_section = {"heading": "Introduction", "content": ""}

    heading_pattern = re.compile(r"^(?:[#]+|_.*_|[*]{2}.*[*]{2}|[A-Z\s]{4,})$")  # #, _, **, ALL CAPS

    for line in lines:
        clean_line = line.strip()

        # Detect heading by pattern or short bold/italic lines
        if clean_line and heading_pattern.match(clean_line) and len(clean_line.split()) < 12:
            # Save old section if it has content
            if current_section["content"].strip():
                sections.append(current_section)
            # Start new section
            current_section = {"heading": clean_line.strip("_*# "), "content": ""}
        else:
            current_section["content"] += line + "\n"

    # Add last section
    if current_section["content"].strip():
        sections.append(current_section)

    # Now split each section semantically
    splitter = TextSplitter(capacity=chunk_size, overlap=chunk_overlap)
    chunks = []
    for sec in sections:
        for sc in splitter.chunks(sec["content"]):
            chunks.append({
                "section": sec["heading"],
                "text": sc
            })

    return chunks
