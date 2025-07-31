
from markdown_utils import identify_structure_and_convert_to_md
from bm25_utils import query_chunks_bm25
from llm_utils import answer_from_chunks
import time
from chunking import detect_headings_and_chunk
import pdfplumber


def pdf_to_markdown(pdf_path):
    """Extract text and tables using pdfplumber only"""
    md_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            md_parts.append(f"\n--- Page {page_num} ---\n")
            
            # Extract text with column tolerance
            text = page.extract_text(x_tolerance=1)
            if text:
                md_parts.append(text)
            
            # Extract tables
            tables = page.extract_tables()
            if tables:
                for table_num, table in enumerate(tables, 1):
                    md_parts.append(f"\n**Table {table_num} on Page {page_num}:**\n")
                    
                    # Convert table to markdown format
                    if table and len(table) > 0:
                        # Header row
                        if table[0]:
                            header = "| " + " | ".join(str(cell or "") for cell in table[0]) + " |"
                            separator = "|" + "|".join("---" for _ in table[0]) + "|"
                            md_parts.append(header)
                            md_parts.append(separator)
                        
                        # Data rows
                        for row in table[1:]:
                            if row:
                                row_md = "| " + " | ".join(str(cell or "") for cell in row) + " |"
                                md_parts.append(row_md)
                    
                    md_parts.append("\n")
    
    return "\n".join(md_parts)

def main():
    print("Extracting text from PDF...")
    pdf_path = "./sample/Arogya Sanjeevani Policy - CIN.pdf"

    # query = "how much is the coverage for Cataract Treatment"
    query = "time limit for Reimbursement of post hospitalisation expenses"
    md = pdf_to_markdown(pdf_path)
    print("\n--- Markdown Conversion Complete ---")
    print(md)

    semantic_chunks = detect_headings_and_chunk(md, chunk_size=500, chunk_overlap=50)
    # print("Sementic chunks created:",semantic_chunks)
    print("\n--- Querying Insurance Document (Semantic Chunks) ---")
    answers = query_chunks_bm25(semantic_chunks, query)

    if not answers:
        print("No results found for the query.")
    else:
        print(f"\nResults for query: '{query}'\n{'='*60}")
        print("\n--- LLM Structured Answer ---")
        answer = answer_from_chunks(query, answers)
        print(answer)

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
