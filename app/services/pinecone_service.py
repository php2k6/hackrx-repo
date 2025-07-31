import pinecone
from typing import List
from app.models.schemas import ProcessedChunk
from app.core.config import settings
from app.services.embedder import embedding_service
from pinecone import Pinecone, ServerlessSpec
import logging

logger = logging.getLogger(__name__)

class PineconeService:
    def __init__(self):
        # Initialize Pinecone (new SDK)
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Use custom embedding service
        self.embedding_service = embedding_service
        
        # Create or connect to index
        self._ensure_index_exists()
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        
        logger.info(f"Initialized Pinecone service with custom BGE embedder: {settings.EMBEDDING_MODEL}")
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if settings.PINECONE_INDEX_NAME not in index_names:
                # Create index with configurable dimensions and cloud settings
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=settings.EMBEDDING_DIMENSION,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud=settings.PINECONE_CLOUD.value,
                        region=settings.PINECONE_REGION
                    )
                )
                logger.info(f"Created new index: {settings.PINECONE_INDEX_NAME}")
            else:
                logger.info(f"Using existing index: {settings.PINECONE_INDEX_NAME}")
                
        except Exception as e:
            logger.error(f"Error with index: {e}")
            raise
    
    async def store_chunks(self, chunks: List[ProcessedChunk], document_id: str):
        """Store document chunks in Pinecone"""
        if not chunks:
            logger.warning("No chunks to store")
            return
            
        vectors = []
        
        # Prepare texts for batch embedding
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings in batch
        embeddings = self.embedding_service.embed(texts)
        
        for i, chunk in enumerate(chunks):
            # Create vector with metadata
            vector = {
                "id": f"{document_id}_{chunk.metadata.chunk_index}",
                "values": embeddings[i],
                "metadata": {
                    "text": chunk.text[:1000],  # Pinecone metadata size limit
                    "section": chunk.metadata.section,
                    "document_id": document_id,
                    "chunk_index": chunk.metadata.chunk_index
                }
            }
            vectors.append(vector)
        
        # Upsert to Pinecone in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                logger.debug(f"Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error upserting batch: {e}")
                raise
        
        logger.info(f"Stored {len(vectors)} chunks for document {document_id}")
    
    async def search_similar_chunks(self, query: str, document_id: str) -> List[tuple]:
        """Search for similar chunks using vector similarity"""
        try:
            # Generate query embedding using custom embedder
            query_embeddings = self.embedding_service.embed([query])
            query_embedding = query_embeddings[0]
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=settings.TOP_K_RESULTS,
                filter={"document_id": document_id},
                include_metadata=True
            )
            
            # Format results similar to BM25 output
            formatted_results = []
            for match in results.get('matches', []):
                if 'metadata' in match:
                    section = match['metadata'].get('section', 'Unknown')
                    text = match['metadata'].get('text', '')
                    score = match.get('score', 0.0)
                    
                    # Only include results above similarity threshold
                    if score >= settings.SIMILARITY_THRESHOLD:
                        formatted_results.append((section, text))
            
            logger.debug(f"Found {len(formatted_results)} relevant chunks for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []
    
    async def delete_document(self, document_id: str):
        """Delete all chunks for a document"""
        try:
            # Search for all vectors with this document_id
            results = self.index.query(
                vector=[0.0] * settings.EMBEDDING_DIMENSION,  # Dummy vector
                top_k=10000,  # Large number to get all
                filter={"document_id": document_id},
                include_metadata=False
            )
            
            # Extract vector IDs
            vector_ids = [match['id'] for match in results.get('matches', [])]
            
            if vector_ids:
                # Delete in batches
                batch_size = 1000
                for i in range(0, len(vector_ids), batch_size):
                    batch = vector_ids[i:i + batch_size]
                    self.index.delete(ids=batch)
                
                logger.info(f"Deleted {len(vector_ids)} vectors for document {document_id}")
            else:
                logger.info(f"No vectors found for document {document_id}")
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise