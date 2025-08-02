#!/usr/bin/env python3
"""
Document Management Utility
Usage: python document_manager.py <command> <document_url_or_id>

Commands:
  info <url>    - Get information about a processed document
  delete <url>  - Delete a processed document
  list          - List all document IDs (requires Pinecone query)
"""

import asyncio
import sys
import hashlib
from app.services.document_processor import DocumentProcessor
from app.services.pinecone_service import PineconeService

async def get_document_info(document_url):
    """Get document information"""
    processor = DocumentProcessor()
    document_id = hashlib.md5(document_url.encode('utf-8')).hexdigest()
    
    print(f"🔍 Checking document...")
    print(f"URL: {document_url}")
    print(f"ID: {document_id}")
    print("-" * 50)
    
    info = await processor.get_document_info(document_id)
    
    if info["status"] == "processed":
        print(f"✅ Document found")
        print(f"   Chunks: {info['chunk_count']}")
        print(f"   Status: {info['status']}")
    elif info["status"] == "not_found":
        print(f"❌ Document not found in Pinecone")
    else:
        print(f"⚠️  Error: {info.get('error', 'Unknown error')}")
    
    return info

async def delete_document(document_url):
    """Delete a document"""
    processor = DocumentProcessor()
    document_id = hashlib.md5(document_url.encode('utf-8')).hexdigest()
    
    print(f"🗑️  Deleting document...")
    print(f"URL: {document_url}")
    print(f"ID: {document_id}")
    print("-" * 50)
    
    # First check if it exists
    info = await processor.get_document_info(document_id)
    
    if info["status"] == "not_found":
        print(f"❌ Document not found - nothing to delete")
        return False
    
    if info["status"] == "error":
        print(f"⚠️  Error checking document: {info.get('error')}")
        return False
    
    print(f"📋 Found document with {info['chunk_count']} chunks")
    
    # Confirm deletion
    confirm = input("Are you sure you want to delete this document? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Deletion cancelled")
        return False
    
    # Delete the document
    success = await processor.delete_document(document_id)
    
    if success:
        print(f"✅ Successfully deleted document")
    else:
        print(f"❌ Failed to delete document")
    
    return success

async def list_documents():
    """List all documents (basic implementation)"""
    print("📋 Listing documents...")
    print("Note: This is a basic implementation that searches for common terms")
    print("-" * 50)
    
    pinecone_service = PineconeService()
    
    # Search with a dummy query to get some results
    try:
        results = await pinecone_service.search_similar_chunks("policy", "")
        
        if not results:
            print("❌ No documents found")
            return
        
        # Extract unique document IDs
        document_ids = set()
        for result in results:
            # Result format: (section, text, metadata)
            if len(result) >= 3 and isinstance(result[2], dict):
                doc_id = result[2].get('document_id')
                if doc_id:
                    document_ids.add(doc_id)
        
        if document_ids:
            print(f"Found {len(document_ids)} unique documents:")
            for i, doc_id in enumerate(sorted(document_ids), 1):
                print(f"  {i}. {doc_id}")
        else:
            print("❌ No document IDs found in metadata")
            
    except Exception as e:
        print(f"❌ Error listing documents: {e}")

def print_usage():
    """Print usage information"""
    print("""
Document Management Utility

Usage:
  python document_manager.py info <document_url>
  python document_manager.py delete <document_url>
  python document_manager.py list

Examples:
  python document_manager.py info "https://example.com/policy.pdf"
  python document_manager.py delete "https://example.com/policy.pdf"
  python document_manager.py list
""")

async def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "info":
            if len(sys.argv) != 3:
                print("❌ Error: info command requires a document URL")
                print_usage()
                return
            
            document_url = sys.argv[2]
            await get_document_info(document_url)
            
        elif command == "delete":
            if len(sys.argv) != 3:
                print("❌ Error: delete command requires a document URL")
                print_usage()
                return
            
            document_url = sys.argv[2]
            await delete_document(document_url)
            
        elif command == "list":
            await list_documents()
            
        else:
            print(f"❌ Error: Unknown command '{command}'")
            print_usage()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
