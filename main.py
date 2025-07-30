from markdown_utils import identify_structure_and_convert_to_md
from bm25_utils import query_chunks_bm25
from llm_utils import answer_from_chunks
import time
# from extract_text import extract_text_from_pdf
import pymupdf4llm
from chunking import detect_headings_and_chunk


def main():

    print("Extracting text from PDF...")
    pdf_path = "./sample/BAJHLIP23020V012223.pdf"

    query = "46M, knee surgery, Pune, 3-month policy"
    # print("\n--- Extracting Text from PDF ---")
    # extracted_text = extract_text_from_pdf(pdf_path)
    # print(extracted_text)
    # # save the extracted text to a file
    # with open("extracted_text.txt", "w", encoding="utf-8") as f:
    #     f.write(extracted_text)

    # print("\n--- Converting to Markdown ---")
    # md = identify_structure_and_convert_to_md(extracted_text)
    # print(md)
    md = pymupdf4llm.to_markdown(pdf_path)
    print("\n--- Markdown Conversion Complete ---")
    # print(md)  # Print first 500 characters for brevity

    semantic_chunks = detect_headings_and_chunk(md, chunk_size=500, chunk_overlap=50)
    # print("\n--- Splitting Markdown into Semantic Chunks ---")
    # semantic_chunks = split_markdown_to_chunks(md)
    # print("\n--- Semantic Chunks ---")
    # for i, chunk in enumerate(semantic_chunks):
    #     print(f"\nChunk {i+1} (metadata: {chunk.metadata}):\n{chunk.page_content}\n{'-'*40}")
    print("Sementic chunks created:",semantic_chunks)
    print("\n--- Querying Insurance Document (Semantic Chunks) ---")
    answers = query_chunks_bm25(semantic_chunks, query)

    if not answers:
        print("No results found for the query.")
    else:
        print(f"\nResults for query: '{query}'\n{'='*60}")
        # for idx, (section, content) in enumerate(answers, 1):
        #     print(f"Result {idx} - Section: {section}\nAnswer: {content}\n{'-'*40}")
        print("\n--- LLM Structured Answer ---")
        answer = answer_from_chunks(query, answers)
        print(answer)

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
