#!/usr/bin/env python3
"""
Check Pinecone index status and record count
"""

import sys
from pathlib import Path

# Add current directory to path  
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pinecone_service import PineconeService
from app.core.config import settings

def check_pinecone_status():
    """Check current Pinecone index status"""
    print("🔍 Pinecone Index Status Check")
    print("=" * 40)
    
    try:
        # Initialize service
        print("Connecting to Pinecone...")
        service = PineconeService()
        
        print(f"✅ Connected to index: {settings.PINECONE_INDEX_NAME}")
        print(f"Environment: {settings.PINECONE_ENVIRONMENT}")
        print(f"Region: {settings.PINECONE_REGION}")
        
        # Get detailed stats
        stats = service.index.describe_index_stats()
        
        print("\n📊 Index Statistics:")
        print(f"Total Vectors: {stats.get('total_vector_count', 0):,}")
        print(f"Index Fullness: {stats.get('index_fullness', 0):.2%}")
        print(f"Dimension: {stats.get('dimension', 'N/A')}")
        
        # Check namespaces
        namespaces = stats.get('namespaces', {})
        if namespaces:
            print(f"\n📂 Namespaces ({len(namespaces)}):")
            for ns_name, ns_stats in namespaces.items():
                ns_display = ns_name if ns_name else "[default]"
                vector_count = ns_stats.get('vector_count', 0)
                print(f"  - {ns_display}: {vector_count:,} vectors")
        else:
            print("\n📂 Namespaces: Using default namespace only")
        
        # Sample some vector IDs if any exist
        total_vectors = stats.get('total_vector_count', 0)
        if total_vectors > 0:
            print(f"\n🔬 Sample Vector IDs:")
            try:
                # Query for a few sample vectors
                dummy_vector = [0.0] * settings.EMBEDDING_DIMENSION
                results = service.index.query(
                    vector=dummy_vector,
                    top_k=5,
                    include_metadata=True,
                    include_values=False
                )
                
                for i, match in enumerate(results.get('matches', []), 1):
                    vector_id = match.get('id', 'N/A')
                    score = match.get('score', 0)
                    metadata = match.get('metadata', {})
                    
                    print(f"  {i}. ID: {vector_id}")
                    print(f"     Score: {score:.4f}")
                    if metadata:
                        doc_id = metadata.get('document_id', 'N/A')
                        chunk_idx = metadata.get('chunk_index', 'N/A')
                        text_preview = metadata.get('text', '')[:100] + '...' if len(metadata.get('text', '')) > 100 else metadata.get('text', '')
                        print(f"     Document: {doc_id}, Chunk: {chunk_idx}")
                        print(f"     Text: {text_preview}")
                    print()
                    
            except Exception as e:
                print(f"  Could not sample vectors: {e}")
        
        print("\n" + "=" * 40)
        
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        print(f"Check your configuration:")
        print(f"  - API Key: {settings.PINECONE_API_KEY[:8] if settings.PINECONE_API_KEY else 'Not set'}...")
        print(f"  - Index Name: {settings.PINECONE_INDEX_NAME}")
        print(f"  - Environment: {settings.PINECONE_ENVIRONMENT}")

if __name__ == "__main__":
    check_pinecone_status()
