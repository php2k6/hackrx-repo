from rank_bm25 import BM25Okapi

def query_chunks_bm25(chunks, query, top_n=3):
    # Extract all page texts
    tokenized_corpus = [c["text"].lower().split() for c in chunks]

    # Initialize BM25
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Get top N results
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            section_meta = chunks[idx]["section"]
            results.append((section_meta, chunks[idx]["text"]))

    # Debug info
    print(f"BM25 scores: {scores}")
    print("Relevant chunks:")
    for section, content in results:
        print(f"Section: {section}\nContent: {content[:200]}...\n")

    return results
