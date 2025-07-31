from chunking import detect_headings_and_chunk
from bm25_utils import query_chunks_bm25
from llm_utils import answer_from_chunks
import time
import fitz  # PyMuPDF
import camelot


def pdf_to_structured_data(pdf_path):
    """Extract structured text & tables with style info using PyMuPDF + Camelot."""
    doc = fitz.open(pdf_path)
    pages_data = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        elements = []

        for b in blocks:
            if "lines" in b:
                for line in b["lines"]:
                    # Keep numbers + heading text exactly as in PDF
                    line_text = "".join(
                        (span["text"] + " ") if not span["text"].endswith(" ") else span["text"]
                        for span in line["spans"]
                    ).strip()
                    if not line_text:
                        continue
                    avg_font_size = sum(span["size"] for span in line["spans"]) / len(line["spans"])
                    is_bold = any("Bold" in (span["font"] or "") for span in line["spans"])
                    elements.append({
                        "text": line_text,
                        "font_size": avg_font_size,
                        "is_bold": is_bold,
                        "type": "text"
                    })

        # Extract tables for this page
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_num))
            for t_i, table in enumerate(tables, start=1):
                elements.append({
                    "text": table.df.to_dict(orient="records"),
                    "font_size": 0,
                    "is_bold": False,
                    "type": "table"
                })
        except Exception:
            pass

        pages_data.append({"page": page_num, "elements": elements})

    return pages_data



def main():
    pdf_path = "./sample/Arogya Sanjeevani Policy - CIN.pdf"
    query = "my son is 26 years old can he avail coverage with this policy?"

    print("Extracting structured PDF data with font sizes & bold info...")
    structured_data = pdf_to_structured_data(pdf_path)

    print("\n--- Data Extraction Complete ---")
    semantic_chunks = detect_headings_and_chunk(structured_data, chunk_size=500, chunk_overlap=50)

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
