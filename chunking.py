import re

# Minimal Document class for chunking
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

def is_heading(line):
    return bool(re.match(r"^#+ ", line.strip()))

def split_markdown_to_chunks(md):
    lines = md.strip().splitlines()
    semantic_chunks = []
    current_chunk_lines = []
    current_metadata = {}
    for line in lines:
        if is_heading(line):
            if current_chunk_lines:
                chunk_text = '\n'.join(current_chunk_lines)
                semantic_chunks.append(Document(page_content=chunk_text, metadata=current_metadata.copy()))
                current_chunk_lines = []
            header_level = line.count('#', 0, line.find(' '))
            header_text = line.strip('#').strip()
            for lvl in list(current_metadata.keys()):
                if int(lvl.split()[-1]) >= header_level:
                    del current_metadata[lvl]
            current_metadata[f'Header {header_level}'] = header_text
        current_chunk_lines.append(line)
    if current_chunk_lines:
        chunk_text = '\n'.join(current_chunk_lines)
        semantic_chunks.append(Document(page_content=chunk_text, metadata=current_metadata.copy()))
    return semantic_chunks
