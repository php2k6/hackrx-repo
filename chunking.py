import re
from semantic_text_splitter import TextSplitter

def detect_headings_and_chunk(md_text, chunk_size=500, chunk_overlap=50):
    lines = md_text.split("\n")
    sections = []
    current_section = {"heading": "", "content": ""}

    # Detect headings: markdown style (#, **bold**, _italic_), ALL CAPS
    heading_pattern = re.compile(
        r"^(?:[#]+|_.*_|[*]{2}.*[*]{2}|[A-Z\s]{4,})$"
    )

    for line in lines:
        clean_line = line.strip()

        # Detect new section heading
        if clean_line and heading_pattern.match(clean_line) and len(clean_line.split()) < 12:
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"heading": clean_line.strip("_*# "), "content": ""}
        else:
            current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    # Now chunk section-wise
    splitter = TextSplitter(capacity=chunk_size, overlap=chunk_overlap)
    chunks = []
    for sec in sections:
        section_text = sec["content"].strip()
        if not section_text:
            continue
        for sc in splitter.chunks(section_text):
            chunks.append({
                "section": sec["heading"],
                "text": sc
            })

    return chunks
