from rank_bm25 import BM25Okapi

def query_chunks_bm25(chunks, query):
    corpus = [chunk.page_content for chunk in chunks]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    top_n = 3
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            section = " > ".join([f"{k}: {v}" for k, v in chunks[idx].metadata.items()])
            results.append((section, chunks[idx].page_content))
    print(f"BM25 scores: {scores}")
    print("Relevant chunks:")
    for section, content in results:
        print(f"Section: {section}\nContent: {content[:100]}...\n")
    return results
