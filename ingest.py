"""
OnboardBot — Document Ingestion Script
Loads HR documents, splits them into chunks, and stores in ChromaDB.
Run this once before using the chatbot.

Usage:
    python ingest.py
"""

import sys
# Reconfigure standard output/error to utf-8 to avoid UnicodeEncodeError on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import CHROMA_DB_DIR, COLLECTION_NAME
from src.document_loader import load_and_split_documents
from src.vector_store import create_vector_store, get_vector_store_stats


def main():
    """Run the full document ingestion pipeline."""
    print("\n" + "=" * 60)
    print("  [Ingestion] OnboardBot - Document Ingestion Pipeline")
    print("=" * 60)
    
    # Step 0: Clear existing vector store if present
    if CHROMA_DB_DIR.exists():
        print(f"\n[Ingestion] Clearing existing vector store at: {CHROMA_DB_DIR}")
        shutil.rmtree(CHROMA_DB_DIR)
        print(f"   Done!")
    
    # Step 1: Load and split documents
    print(f"\n{'-' * 60}")
    print(f"  STEP 1: Loading & Splitting Documents")
    print(f"{'-' * 60}")
    
    chunks = load_and_split_documents()
    
    # Step 2: Create vector store
    print(f"\n{'-' * 60}")
    print(f"  STEP 2: Creating Vector Store (ChromaDB)")
    print(f"{'-' * 60}")
    
    vector_store = create_vector_store(chunks)
    
    # Step 3: Verify
    print(f"\n{'-' * 60}")
    print(f"  STEP 3: Verification")
    print(f"{'-' * 60}")
    
    stats = get_vector_store_stats(vector_store)
    
    print(f"\n  Ingestion Complete!")
    print(f"     Collection: {stats['collection_name']}")
    print(f"     Total vectors: {stats['total_vectors']}")
    print(f"     Stored at: {stats['persist_directory']}")
    
    # Step 4: Quick test query
    print(f"\n{'-' * 60}")
    print(f"  STEP 4: Quick Test Query")
    print(f"{'-' * 60}")
    
    test_query = "What is the company dress code?"
    results = vector_store.similarity_search_with_score(test_query, k=2)
    
    print(f"\n  Query: \"{test_query}\"")
    for i, (doc, score) in enumerate(results):
        source = doc.metadata.get("source_name", "Unknown")
        snippet = doc.page_content[:100].replace("\n", " ")
        print(f"\n  Result {i+1} (distance: {score:.4f}):")
        print(f"    Source: {source}")
        print(f"    Snippet: {snippet}...")
    
    print(f"\n{'=' * 60}")
    print(f"  Ready! Run 'python cli.py' or 'streamlit run app.py'")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
