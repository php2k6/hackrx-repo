from rank_bm25 import BM25Okapi
from typing import List

class BM25Service:
    """Fallback search service if Pinecone is unavailable"""
    def __init__(self):
        self.bm25 = None
        self.chunks = []
    
    def index_chunks(self, chunks: List[dict]):
        """Your existing BM25 logic - keep as is"""
        # Copy your existing BM25 logic from bm25_utils.py here
        pass

def query_chunks_bm25(chunks, query, top_n=3):
    tokenized_corpus = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            section_meta = chunks[idx]["section"]
            results.append({"section": section_meta, "text": chunks[idx]["text"]})

    return results