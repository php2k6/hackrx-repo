#!/usr/bin/env python3
"""
Temporary script to delete ALL records from Pinecone index
WARNING: This will permanently delete all vectors in the index!

Usage:
    python delete_all_pinecone_records.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path so we can import app modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now import from app
from app.services.pinecone_service import PineconeService
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def delete_all_records_sync():
    """Delete all records from Pinecone index - synchronous version"""
    try:
        # Initialize Pinecone service
        logger.info("Initializing Pinecone service...")
        pinecone_service = PineconeService()
        
        # Get index stats first
        stats = pinecone_service.index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        
        if total_vectors == 0:
            logger.info("No vectors found in the index.")
            return
        
        logger.info(f"Found {total_vectors} vectors in index '{settings.PINECONE_INDEX_NAME}'")
        
        # Show current namespaces if any
        namespaces = stats.get('namespaces', {})
        if namespaces:
            logger.info(f"Namespaces found: {list(namespaces.keys())}")
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will delete ALL {total_vectors} vectors from Pinecone index '{settings.PINECONE_INDEX_NAME}'")
        print("This action is IRREVERSIBLE!")
        print(f"Index details:")
        print(f"  - API Key: {settings.PINECONE_API_KEY[:8]}...{settings.PINECONE_API_KEY[-4:]}")
        print(f"  - Environment: {settings.PINECONE_ENVIRONMENT}")
        print(f"  - Region: {settings.PINECONE_REGION}")
        
        confirm = input("\nType 'DELETE ALL' to confirm (anything else to cancel): ")
        
        if confirm != "DELETE ALL":
            logger.info("Operation cancelled by user.")
            return
        
        logger.info("Starting deletion process...")
        
        # Method 1: Try delete_all (most efficient)
        try:
            logger.info("Attempting to delete all vectors using delete_all method...")
            
            # Delete all vectors in the default namespace
            pinecone_service.index.delete(delete_all=True)
            logger.info("Successfully used delete_all method")
            
            # If there are namespaces, delete from each
            if namespaces:
                for namespace in namespaces.keys():
                    if namespace and namespace != '':  # Skip empty namespace (already deleted)
                        logger.info(f"Deleting all vectors in namespace: {namespace}")
                        pinecone_service.index.delete(delete_all=True, namespace=namespace)
                        
        except Exception as e:
            logger.warning(f"delete_all method failed: {e}")
            logger.info("Trying query and delete method...")
            
            # Method 2: Query for IDs and delete in batches
            try:
                # Create a dummy vector for querying
                dummy_vector = [0.0] * settings.EMBEDDING_DIMENSION
                
                # Query to get all vector IDs
                logger.info("Querying for vector IDs...")
                results = pinecone_service.index.query(
                    vector=dummy_vector,
                    top_k=10000,  # Maximum allowed
                    include_metadata=False,
                    include_values=False
                )
                
                matches = results.get('matches', [])
                vector_ids = [match['id'] for match in matches]
                
                logger.info(f"Found {len(vector_ids)} vector IDs to delete")
                
                if vector_ids:
                    # Delete in batches
                    batch_size = 1000
                    total_deleted = 0
                    
                    for i in range(0, len(vector_ids), batch_size):
                        batch = vector_ids[i:i + batch_size]
                        
                        logger.info(f"Deleting batch {i//batch_size + 1}: {len(batch)} vectors")
                        pinecone_service.index.delete(ids=batch)
                        
                        total_deleted += len(batch)
                        logger.info(f"Progress: {total_deleted}/{len(vector_ids)} vectors deleted")
                
                logger.info(f"Batch deletion completed: {total_deleted} vectors deleted")
                
            except Exception as e2:
                logger.error(f"Query and delete method also failed: {e2}")
                raise
        
        # Wait a moment for deletion to process
        import time
        logger.info("Waiting for deletion to complete...")
        time.sleep(3)
        
        # Verify deletion
        try:
            final_stats = pinecone_service.index.describe_index_stats()
            remaining_vectors = final_stats.get('total_vector_count', 0)
            
            if remaining_vectors == 0:
                logger.info("✅ All vectors successfully deleted!")
                print("\n🎉 SUCCESS: All Pinecone records have been deleted!")
            else:
                logger.warning(f"⚠️ {remaining_vectors} vectors still remain in the index")
                print(f"\n⚠️ WARNING: {remaining_vectors} vectors still remain - you may need to run this again")
                
        except Exception as e:
            logger.warning(f"Could not verify deletion: {e}")
        
    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        print(f"\n❌ ERROR: {e}")
        raise

def main():
    """Main function"""
    print("🗑️  Pinecone Record Deletion Script")
    print("=" * 50)
    print(f"Target Index: {settings.PINECONE_INDEX_NAME}")
    print(f"Environment: {settings.PINECONE_ENVIRONMENT}")
    print("=" * 50)
    
    try:
        delete_all_records_sync()
        print("\n✅ Script completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user (Ctrl+C)")
        logger.info("Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
