"""
OnboardBot — Document Loader
Handles loading and splitting of HR documents from the data directory.
Supports .txt and .pdf file formats.
"""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP


# Mapping of friendly document names for source references
DOCUMENT_NAMES = {
    "hr_handbook": "HR Handbook",
    "it_setup_guide": "IT Setup Guide",
    "leave_policy": "Leave & Attendance Policy",
}


def get_document_display_name(filename: str) -> str:
    """Convert a filename to a friendly display name."""
    stem = Path(filename).stem
    return DOCUMENT_NAMES.get(stem, stem.replace("_", " ").title())


def load_single_document(file_path: Path) -> List[Document]:
    """
    Load a single document file (TXT or PDF).
    
    Args:
        file_path: Path to the document file.
    
    Returns:
        List of Document objects with metadata.
    """
    suffix = file_path.suffix.lower()
    
    if suffix == ".txt":
        loader = TextLoader(str(file_path), encoding="utf-8")
    elif suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
    else:
        print(f"⚠️  Skipping unsupported file format: {file_path.name}")
        return []
    
    docs = loader.load()
    
    # Enrich metadata with friendly source name
    display_name = get_document_display_name(file_path.name)
    for doc in docs:
        doc.metadata["source_name"] = display_name
        doc.metadata["file_name"] = file_path.name
    
    return docs


def load_all_documents() -> List[Document]:
    """
    Load all supported documents from the data directory.
    
    Returns:
        List of all Document objects from all files.
    """
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Data directory not found: {DATA_DIR}\n"
            f"Please create the directory and add HR documents."
        )
    
    all_docs = []
    supported_extensions = {".txt", ".pdf"}
    
    files = sorted([
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ])
    
    if not files:
        raise FileNotFoundError(
            f"No supported documents found in {DATA_DIR}\n"
            f"Supported formats: {', '.join(supported_extensions)}"
        )
    
    print(f"\n📂 Loading documents from: {DATA_DIR}")
    print(f"{'─' * 50}")
    
    for file_path in files:
        try:
            docs = load_single_document(file_path)
            all_docs.extend(docs)
            print(f"  ✅ Loaded: {file_path.name} ({len(docs)} page(s))")
        except Exception as e:
            print(f"  ❌ Error loading {file_path.name}: {e}")
    
    print(f"{'─' * 50}")
    print(f"📄 Total documents loaded: {len(all_docs)}")
    
    return all_docs


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for embedding.
    
    Args:
        documents: List of full Document objects.
    
    Returns:
        List of chunked Document objects.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=[
            "\n================",  # Major section breaks
            "\n\n",               # Paragraph breaks
            "\n",                 # Line breaks
            ". ",                 # Sentence breaks
            " ",                  # Word breaks
            "",                   # Character breaks
        ],
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_documents(documents)
    
    # Add chunk index to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    
    print(f"✂️  Split into {len(chunks)} chunks "
          f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    
    return chunks


def load_and_split_documents() -> List[Document]:
    """
    Complete pipeline: load all documents and split into chunks.
    
    Returns:
        List of chunked Document objects ready for embedding.
    """
    documents = load_all_documents()
    chunks = split_documents(documents)
    return chunks
