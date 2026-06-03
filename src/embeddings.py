import os
# Force offline mode to prevent network requests from hanging on Windows
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from langchain_community.embeddings import HuggingFaceEmbeddings
from src.config import EMBEDDING_MODEL

# Module-level cache for the embedding model
_embeddings_instance = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get or create the HuggingFace embedding model instance.
    Uses singleton pattern to avoid loading the model multiple times.
    
    Returns:
        HuggingFaceEmbeddings instance using the configured model.
    """
    global _embeddings_instance
    
    if _embeddings_instance is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print(f"Embedding model loaded successfully!")
    
    return _embeddings_instance


_reranker_instance = None


def get_reranker():
    """
    Get or load the singleton local Cross-Encoder reranker.
    Uses the ms-marco-MiniLM-L-6-v2 model for quick CPU-based reranking.
    """
    global _reranker_instance
    if _reranker_instance is None:
        from sentence_transformers import CrossEncoder
        print("Loading Cross-Encoder reranker (ms-marco-MiniLM-L-6-v2)...")
        _reranker_instance = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
        print("Reranker model loaded successfully!")
    return _reranker_instance

