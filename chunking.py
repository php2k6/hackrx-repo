import re
from semantic_text_splitter import TextSplitter

def detect_headings_and_chunk(structured_pages, chunk_size=500, chunk_overlap=50):
    """Detect headings using font size / bold style / section number, chunk section-wise."""
    # Find body font size (most common across pages)
    font_sizes = []
    for page in structured_pages:
        for el in page["elements"]:
            if el["type"] == "text":
                font_sizes.append(el["font_size"])
    body_font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10

    # Regex for numbered section headings
    numbered_heading_pattern = re.compile(r"^\d+(\.\d+)*\s+.+$")

    sections = []
    current_section = {"heading": "Introduction", "content": ""}

    for page in structured_pages:
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
                        # Keep section number as is
                        current_section = {"heading": el["text"], "content": ""}
                else:
                    current_section["content"] += el["text"] + "\n"

            elif el["type"] == "table":
                # Attach table to current section
                current_section["content"] += f"\n[TABLE DATA]: {el['text']}\n"

    if current_section["content"].strip():
        sections.append(current_section)

    # Now chunk section-wise
    splitter = TextSplitter(capacity=chunk_size, overlap=chunk_overlap)
    chunks = []
    for sec in sections:
        for sc in splitter.chunks(sec["content"]):
            chunks.append({
                "section": sec["heading"],
                "text": sc
            })

    return chunks

