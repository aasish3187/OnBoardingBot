"""
OnboardBot — ChromaDB Vector Store Operations
Handles creating, persisting, and querying the vector store.
"""

from typing import List, Optional, Tuple

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from src.config import CHROMA_DB_DIR, COLLECTION_NAME, RETRIEVAL_TOP_K
from src.embeddings import get_embeddings


def create_vector_store(documents: List[Document]) -> Chroma:
    """
    Create a new ChromaDB vector store from document chunks.
    Persists the store to disk for future use.
    
    Args:
        documents: List of chunked Document objects to embed and store.
    
    Returns:
        Chroma vector store instance.
    """
    embeddings = get_embeddings()
    
    print(f"\n[Vector Store] Creating vector store with {len(documents)} chunks...")
    print(f"   Persist directory: {CHROMA_DB_DIR}")
    print(f"   Collection name: {COLLECTION_NAME}")
    
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_DB_DIR),
        collection_name=COLLECTION_NAME,
    )
    
    # Get collection stats
    collection = vector_store._collection
    count = collection.count()
    
    print(f"Vector store created successfully!")
    print(f"   Total vectors stored: {count}")
    
    return vector_store


def load_vector_store() -> Chroma:
    """
    Load an existing ChromaDB vector store from disk.
    
    Returns:
        Chroma vector store instance.
    
    Raises:
        FileNotFoundError: If the vector store directory doesn't exist.
    """
    if not CHROMA_DB_DIR.exists():
        raise FileNotFoundError(
            f"Vector store not found at: {CHROMA_DB_DIR}\n"
            f"Please run 'python ingest.py' first to create the vector store."
        )
    
    embeddings = get_embeddings()
    
    vector_store = Chroma(
        persist_directory=str(CHROMA_DB_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    
    count = vector_store._collection.count()
    print(f"Vector store loaded: {count} vectors in collection '{COLLECTION_NAME}'")
    
    return vector_store


def get_retriever(vector_store: Chroma):
    """
    Create a retriever from the vector store.
    
    Args:
        vector_store: Chroma vector store instance.
    
    Returns:
        Retriever configured with top-K search.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVAL_TOP_K},
    )


def similarity_search_with_scores(
    vector_store: Chroma,
    query: str,
    k: int = RETRIEVAL_TOP_K,
) -> List[Tuple[Document, float]]:
    """
    Search the vector store and return results with similarity scores.
    Useful for out-of-scope detection based on score thresholds.
    
    Args:
        vector_store: Chroma vector store instance.
        query: The search query string.
        k: Number of results to return.
    
    Returns:
        List of (Document, score) tuples, sorted by relevance.
    """
    results = vector_store.similarity_search_with_score(query, k=k)
    return results


def get_vector_store_stats(vector_store: Chroma) -> dict:
    """
    Get statistics about the vector store.
    
    Returns:
        Dictionary with collection stats.
    """
    collection = vector_store._collection
    count = collection.count()
    
    return {
        "collection_name": COLLECTION_NAME,
        "total_vectors": count,
        "persist_directory": str(CHROMA_DB_DIR),
    }
