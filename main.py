
from pdf_utils import is_scanned
from markdown_utils import identify_structure_and_convert_to_md
from chunking import split_markdown_to_chunks
from bm25_utils import query_chunks_bm25
from llm_utils import answer_from_chunks
import pdfplumber
from pdf2image import convert_from_path



def main():
    print("Extracting text from PDF...")
    all_text = ""
    pdf_path = "./sample/EDLHLGA23009V012223.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text()
            if is_scanned(txt):
                img = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)[0]
                img.save(f"page_{i+1}.png")  # run OCR only here
            else:
                print("Text:", txt)
                all_text += txt + "\n\n"

    print("\n--- Converting to Markdown ---")
    md = identify_structure_and_convert_to_md(all_text)
    print(md)

    print("\n--- Splitting Markdown into Semantic Chunks ---")
    semantic_chunks = split_markdown_to_chunks(md)
    print("\n--- Semantic Chunks ---")
    # for i, chunk in enumerate(semantic_chunks):
    #     print(f"\nChunk {i+1} (metadata: {chunk.metadata}):\n{chunk.page_content}\n{'-'*40}")

    print("\n--- Querying Insurance Document (Semantic Chunks) ---")
    query = "will the transfer of person to another hospital be covered"
    answers = query_chunks_bm25(semantic_chunks, query)

    if not answers:
        print("No results found for the query.")
    else:
        print(f"\nResults for query: '{query}'\n{'='*60}")
        for idx, (section, content) in enumerate(answers, 1):
            print(f"Result {idx} - Section: {section}\nAnswer: {content[:300]}\n{'-'*40}")
        print("\n--- LLM Structured Answer ---")
        answer = answer_from_chunks(query, answers)
        print(answer)

if __name__ == "__main__":
    main()
