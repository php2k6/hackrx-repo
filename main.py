from chunking import detect_headings_and_chunk
from bm25_utils import query_chunks_bm25
from llm_utils import answer_from_chunks
import time
import fitz  # PyMuPDF
import camelot


def pdf_to_structured_md(pdf_path):
    """Extract text & tables with structure using PyMuPDF + Camelot."""
    md_parts = []
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        md_parts.append(f"\n--- Page {page_num} ---\n")

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" in b:  # text block
                for line in b["lines"]:
                    text_line = " ".join(span["text"] for span in line["spans"]).strip()
                    if text_line:
                        md_parts.append(text_line)

        # Extract tables for this page (Camelot works with PDF coords)
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_num))
            for t_i, table in enumerate(tables, start=1):
                md_parts.append(f"\n**Table {t_i} on Page {page_num}:**\n")
                df = table.df
                header = "| " + " | ".join(df.iloc[0]) + " |"
                separator = "|" + "|".join("---" for _ in df.iloc[0]) + "|"
                md_parts.append(header)
                md_parts.append(separator)
                for idx in range(1, len(df)):
                    row_md = "| " + " | ".join(df.iloc[idx]) + " |"
                    md_parts.append(row_md)
                md_parts.append("\n")
        except Exception:
            pass

    return "\n".join(md_parts)


def main():
    pdf_path = "./sample/Arogya Sanjeevani Policy - CIN.pdf"
    # query = "time limit for Reimbursement of post hospitalisation expenses and coverage"
    query = "notice period for cancellation of policy"

    print("Extracting structured markdown from PDF...")
    md = pdf_to_structured_md(pdf_path)
    # save md
    with open("extracted_content.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("\n--- Markdown Extraction Complete ---")
    semantic_chunks = detect_headings_and_chunk(md, chunk_size=500, chunk_overlap=50)

    print("\n--- Querying Document with BM25 ---")
    answers = query_chunks_bm25(semantic_chunks, query)

    if not answers:
        print("No results found.")
    else:
        print(f"\nResults for query: '{query}'\n{'='*60}")
        print("\n--- LLM Structured Answer ---")
        answer = answer_from_chunks(query, answers)
        print(answer)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")
