"""
OnboardBot — Centralized Configuration
All configurable parameters in one place.
"""

import os
from pathlib import Path

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
# Ollama LLM model — change this to match your installed model
# Common options: "llama3.2", "llama3", "mistral", "gemma2", "phi3"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Ollama base URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# HuggingFace embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ============================================================================
# RAG CONFIGURATION
# ============================================================================
# Text splitting parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Number of retrieved chunks for each query
RETRIEVAL_TOP_K = 4

# Similarity score threshold for out-of-scope detection
# ChromaDB uses L2 distance — lower = more similar
# Threshold: if the best match distance > this value, it's out-of-scope
RELEVANCE_THRESHOLD = 1.5

# ============================================================================
# CHROMADB CONFIGURATION
# ============================================================================
COLLECTION_NAME = "onboardbot_hr_docs"

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SYSTEM_PROMPT = """You are OnboardBot, a helpful and friendly HR onboarding assistant for Nexus Technologies Pvt. Ltd. Your role is to answer new employee questions about company policies, IT setup, and leave management.

RULES YOU MUST FOLLOW:
1. ONLY answer questions based on the provided context below. Do NOT make up information.
2. If the context does not contain the answer, respond with: "I don't have that information in our HR documents."
3. Always cite your source by mentioning which document the information comes from (e.g., "According to the HR Handbook..." or "As stated in the IT Setup Guide...").
4. Be warm, professional, and welcoming — remember, you're helping a new employee!
5. If the question is about a specific HR process or contact, provide the relevant contact information from the documents.
6. Keep your answers concise but complete. Use bullet points for lists.
7. If the question is partially answerable, answer what you can and clearly state what you don't have information about.

CONTEXT FROM HR DOCUMENTS:
{context}

IMPORTANT: If the context above does not contain relevant information to answer the question, you MUST say "I don't have that information in our HR documents." and suggest contacting the appropriate HR department.
"""

QA_PROMPT_TEMPLATE = """Based on the context provided in the system message, please answer the following employee question:

Question: {question}

Remember: Only use information from the provided context. Cite your sources. If the information is not available, say so clearly and suggest the appropriate HR contact.
"""

# Prompt to rephrase follow-up questions using conversation history
CONDENSE_QUESTION_PROMPT_TEMPLATE = """Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question that can be answered using document search, in its original language.

Chat History:
{chat_history}
Follow-up Input: {question}
Standalone question:"""

# Prompt to generate 2-3 dynamic follow-up questions
FOLLOW_UP_PROMPT_TEMPLATE = """Based on the following conversation context and the latest answer, generate 2 or 3 short, relevant follow-up questions that the user might want to ask next.
Format your response as a simple bulleted list with '-' prefix and keep the questions brief, direct, and natural (under 10 words).

Chat Context:
{chat_context}

Latest Answer:
{latest_answer}

Follow-up questions:"""



# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
APP_NAME = "🤖 OnboardBot"
APP_DESCRIPTION = "Your AI-powered HR Onboarding Assistant"
APP_VERSION = "1.0.0"

# Streamlit page configuration
STREAMLIT_PAGE_TITLE = "OnboardBot — HR Onboarding Assistant"
STREAMLIT_PAGE_ICON = "🤖"
STREAMLIT_LAYOUT = "wide"
