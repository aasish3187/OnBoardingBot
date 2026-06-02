"""
OnboardBot — RAG Chain with Out-of-Scope Detection
Custom chain that retrieves relevant context, detects out-of-scope queries,
and generates answers with source references.
"""

from typing import Dict, List, Tuple, Optional

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from src.config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    RETRIEVAL_TOP_K,
    RELEVANCE_THRESHOLD,
    SYSTEM_PROMPT,
    QA_PROMPT_TEMPLATE,
    CONDENSE_QUESTION_PROMPT_TEMPLATE,
    FOLLOW_UP_PROMPT_TEMPLATE,
    DATA_DIR,
)
from src.vector_store import similarity_search_with_scores
from src.hr_contacts import route_to_contact, format_contact_info




def get_llm(temperature: float = 0.1, num_predict: int = 512) -> OllamaLLM:
    """
    Initialize the Ollama LLM with custom parameters.
    
    Returns:
        OllamaLLM instance.
    """
    return OllamaLLM(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=num_predict,
    )


def format_source_references(docs_with_scores: List[Tuple[Document, float]]) -> str:
    """
    Format retrieved documents into source references.
    
    Args:
        docs_with_scores: List of (Document, score) tuples.
    
    Returns:
        Formatted source references string.
    """
    sources = []
    seen = set()
    
    for doc, score in docs_with_scores:
        source_name = doc.metadata.get("source_name", "Unknown Document")
        file_name = doc.metadata.get("file_name", "unknown")
        
        # Avoid duplicate source references
        if source_name not in seen:
            seen.add(source_name)
            sources.append(f"📄 **{source_name}** (`{file_name}`)")
    
    if sources:
        return "\n**Sources:**\n" + "\n".join(f"  - {s}" for s in sources)
    return ""


def format_context(docs_with_scores: List[Tuple[Document, float]]) -> str:
    """
    Combine retrieved document chunks into a context string.
    
    Args:
        docs_with_scores: List of (Document, score) tuples.
    
    Returns:
        Combined context string with source labels.
    """
    context_parts = []
    
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        source_name = doc.metadata.get("source_name", "Unknown")
        context_parts.append(
            f"[Source: {source_name}]\n{doc.page_content}"
        )
    
    return "\n\n---\n\n".join(context_parts)


def is_query_in_scope(
    docs_with_scores: List[Tuple[Document, float]],
    threshold: float = RELEVANCE_THRESHOLD,
) -> bool:
    """
    Determine if the query is within scope based on retrieval scores.
    ChromaDB uses L2 distance — lower scores mean higher similarity.
    
    Args:
        docs_with_scores: List of (Document, score) tuples.
        threshold: Maximum L2 distance for a query to be in-scope.
    
    Returns:
        True if the query is in-scope, False otherwise.
    """
    if not docs_with_scores:
        return False
    
    # Best match is the one with the lowest distance
    best_score = docs_with_scores[0][1]
    return best_score < threshold


def query_rag(
    vector_store: Chroma,
    question: str,
    llm: OllamaLLM = None,
) -> Dict:
    """
    Execute the full RAG pipeline for a question.
    
    This function:
    1. Retrieves relevant document chunks with similarity scores
    2. Checks if the query is in-scope using score thresholds
    3. If in-scope: generates an answer using the LLM with context
    4. If out-of-scope: returns a polite decline with HR contact info
    
    Args:
        vector_store: ChromaDB vector store instance.
        question: The user's question.
        llm: Optional pre-initialized LLM instance.
    
    Returns:
        Dictionary with:
        - answer: The generated answer string
        - sources: Source reference string
        - is_in_scope: Boolean indicating if query was in-scope
        - contact_info: HR contact info (if applicable)
        - retrieved_docs: Raw retrieved documents for debugging
    """
    # Step 1: Retrieve relevant chunks with scores
    docs_with_scores = similarity_search_with_scores(
        vector_store, question, k=RETRIEVAL_TOP_K
    )
    
    # Step 2: Check if query is in-scope
    in_scope = is_query_in_scope(docs_with_scores)
    
    if not in_scope:
        # Out-of-scope: return a polite decline with HR contact
        contact = route_to_contact(question)
        contact_str = format_contact_info(contact)
        
        answer = (
            "I don't have that information in our HR documents. "
            "My knowledge is limited to the HR Handbook, IT Setup Guide, "
            "and Leave & Attendance Policy.\n\n"
            "For this query, I'd recommend contacting:\n\n"
            f"{contact_str}"
        )
        
        return {
            "answer": answer,
            "sources": "",
            "is_in_scope": False,
            "contact_info": contact_str,
            "retrieved_docs": docs_with_scores,
        }
    
    # Step 3: In-scope — generate answer with LLM
    if llm is None:
        llm = get_llm()
    
    # Build context from retrieved documents
    context = format_context(docs_with_scores)
    source_refs = format_source_references(docs_with_scores)
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", QA_PROMPT_TEMPLATE),
    ])
    
    # Build the chain and invoke
    chain = prompt | llm
    
    response = chain.invoke({
        "context": context,
        "question": question,
    })
    
    # Append source references to the answer
    full_answer = response.strip()
    if source_refs:
        full_answer += "\n\n" + source_refs
    
    # Check if the LLM itself says it doesn't have the info
    # (Second layer of out-of-scope detection)
    llm_says_no_info = any(phrase in response.lower() for phrase in [
        "i don't have that information",
        "i do not have that information",
        "not available in the provided",
        "not mentioned in the",
        "no information about this",
        "cannot find any information",
    ])
    
    if llm_says_no_info:
        contact = route_to_contact(question)
        contact_str = format_contact_info(contact)
        full_answer += f"\n\n**Suggested Contact:**\n{contact_str}"
        
        return {
            "answer": full_answer,
            "sources": source_refs,
            "is_in_scope": False,
            "contact_info": contact_str,
            "retrieved_docs": docs_with_scores,
        }
    
    return {
        "answer": full_answer,
        "sources": source_refs,
        "is_in_scope": True,
        "contact_info": None,
        "retrieved_docs": docs_with_scores,
    }


_bm25_retriever_cache = None
_bm25_ids_hash = None


def get_cached_bm25_retriever(vector_store, k_val: int):
    """Get the cached BM25 retriever, refitting it only if the vector store chunks changed."""
    global _bm25_retriever_cache, _bm25_ids_hash
    try:
        store_data = vector_store.get()
        if not store_data or "ids" not in store_data or len(store_data["ids"]) == 0:
            return None
            
        # Create a hash of all document chunk IDs to detect updates/deletions
        ids_tuple = tuple(sorted(store_data["ids"]))
        current_hash = hash(ids_tuple)
        
        if _bm25_retriever_cache is None or _bm25_ids_hash != current_hash:
            print("🔄 Initializing/Refitting BM25 retriever cache (chunks changed)...")
            all_docs = []
            for i in range(len(store_data["ids"])):
                metadata = store_data["metadatas"][i] if store_data["metadatas"] else {}
                page_content = store_data["documents"][i]
                all_docs.append(Document(page_content=page_content, metadata=metadata))
            
            if all_docs:
                from langchain_community.retrievers import BM25Retriever
                _bm25_retriever_cache = BM25Retriever.from_documents(all_docs)
                _bm25_ids_hash = current_hash
                print("✅ BM25 retriever cached successfully!")
                
        if _bm25_retriever_cache is not None:
            _bm25_retriever_cache.k = k_val
        return _bm25_retriever_cache
    except Exception as e:
        print(f"Error loading cached BM25 retriever: {e}")
        return None


def query_hybrid_search(
    vector_store: Chroma,
    question: str,
    k: int = RETRIEVAL_TOP_K,
    excluded_files: Optional[List[str]] = None,
) -> Tuple[List[Tuple[Document, float]], List[Tuple[Document, float]]]:
    """
    Perform hybrid search using local ChromaDB (dense) and BM25 (sparse),
    followed by local Cross-Encoder reranking for maximum factual precision.
    
    Returns:
        tuple: (reranked_results_with_scores, raw_chroma_results_with_scores)
    """
    # 1. Semantic search (ChromaDB) - fetch 2x k for reranking candidates
    chroma_results = vector_store.similarity_search_with_score(question, k=k * 2)
    
    # 2. Keyword search (BM25) - fetch 2x k for reranking candidates using cached retriever
    bm25_results = []
    bm25_retriever = get_cached_bm25_retriever(vector_store, k * 2)
    if bm25_retriever:
        try:
            bm25_docs = bm25_retriever.invoke(question)
            bm25_results = [(doc, 1.0) for doc in bm25_docs]
        except Exception as e:
            print(f"Error executing BM25 keyword search: {e}")

    # Exclude files if specified
    if excluded_files:
        chroma_results = [
            (doc, score) for doc, score in chroma_results
            if doc.metadata.get("file_name") not in excluded_files
            and doc.metadata.get("source_name") not in excluded_files
        ]
        bm25_results = [
            (doc, score) for doc, score in bm25_results
            if doc.metadata.get("file_name") not in excluded_files
            and doc.metadata.get("source_name") not in excluded_files
        ]
        
    # Combine results, removing duplicates based on exact content match
    seen_contents = set()
    combined_results = []
    
    # Add Chroma results first
    for doc, score in chroma_results:
        content_clean = doc.page_content.strip()
        if content_clean not in seen_contents:
            seen_contents.add(content_clean)
            combined_results.append((doc, score))
            
    # Add BM25 results
    for doc, score in bm25_results:
        content_clean = doc.page_content.strip()
        if content_clean not in seen_contents:
            seen_contents.add(content_clean)
            combined_results.append((doc, score))
            
    # Apply Cross-Encoder Reranking
    if combined_results:
        try:
            from src.embeddings import get_reranker
            reranker = get_reranker()
            
            # Predict scores for pairs [question, document_text]
            pairs = [[question, doc.page_content] for doc, _ in combined_results]
            rerank_scores = reranker.predict(pairs)
            
            # Reassemble with new Cross-Encoder relevance score
            reranked_results = []
            for i, (doc, old_score) in enumerate(combined_results):
                reranked_results.append((doc, float(rerank_scores[i])))
                
            # Sort by rerank score descending (higher is more relevant)
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k reranked results, along with raw chroma results for scope checking
            return reranked_results[:k], chroma_results[:k]
        except Exception as e:
            print(f"Error during Cross-Encoder reranking: {e}")
            
    # Fallback to standard top-k hybrid if reranker fails
    return combined_results[:k], chroma_results[:k]



def condense_question(
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    llm: OllamaLLM = None,
) -> str:
    """
    Condense follow-up questions using chat history into a standalone query.
    """
    if not chat_history or len(chat_history) < 2:
        return question
        
    # Speed Optimization: Bypass LLM condensation if the question is standalone/long and has no reference pronouns
    q_lower = question.lower()
    pronouns = {"it", "that", "this", "them", "those", "they", "he", "she", "him", "her", "his", "hers", "their", "theirs", "what about", "how to"}
    words = q_lower.split()
    
    # If the question has 6 or more words and doesn't contain reference pronouns, it is likely already standalone.
    # Bypassing the second LLM call saves 3-8 seconds of latency.
    has_pronoun = any(w in pronouns for w in words)
    if len(words) >= 6 and not has_pronoun:
        return question
        
    if llm is None:
        llm = get_llm()
        
    # Format the last 6 messages (3 turns)
    formatted_turns = []
    for msg in chat_history[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_turns.append(f"{role}: {msg['content']}")
    history_str = "\n".join(formatted_turns)
    
    from langchain_core.prompts import PromptTemplate
    prompt = PromptTemplate.from_template(CONDENSE_QUESTION_PROMPT_TEMPLATE)
    chain = prompt | llm
    
    try:
        standalone = chain.invoke({
            "chat_history": history_str,
            "question": question
        }).strip()
        
        # Clean up common prefixes
        for prefix in ["standalone question:", "standalone:", "rephrased question:", "rephrased:"]:
            if standalone.lower().startswith(prefix):
                standalone = standalone[len(prefix):].strip()
                
        # If response is empty or too short, fallback to original
        if not standalone or len(standalone) < 2:
            return question
            
        return standalone
    except Exception as e:
        print(f"Error condensing follow-up question: {e}")
        return question


def query_rag_stream(
    vector_store: Chroma,
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    relevance_threshold: float = RELEVANCE_THRESHOLD,
    llm: OllamaLLM = None,
    system_prompt_override: Optional[str] = None,
    excluded_files: Optional[List[str]] = None,
) -> Tuple[bool, str, any, List[Tuple[Document, float]], List[Tuple[Document, float]]]:
    """
    Execute the hybrid RAG pipeline and return a generator for streaming the response.
    
    This version includes memory condensation, hybrid search, and custom settings.
    
    Returns:
        Tuple of (is_in_scope, immediate_answer_if_out_of_scope, generator_func, retrieved_docs, raw_chroma_docs)
    """
    if llm is None:
        llm = get_llm()
        
    # Step 1: Condense question if history is present
    standalone_question = condense_question(question, chat_history, llm)
    
    # Step 2: Retrieve relevant chunks using hybrid search
    combined_docs, raw_chroma_docs = query_hybrid_search(
        vector_store, standalone_question, k=RETRIEVAL_TOP_K, excluded_files=excluded_files
    )
    
    # Step 3: Check if query is in-scope based on semantic (ChromaDB) scores using dynamic threshold
    in_scope = is_query_in_scope(raw_chroma_docs, threshold=relevance_threshold)
    
    if not in_scope:
        # Out-of-scope: return immediate answer
        contact = route_to_contact(question)
        contact_str = format_contact_info(contact)
        answer = (
            "I don't have that information in our HR documents. "
            "My knowledge is limited to the HR Handbook, IT Setup Guide, "
            "and Leave & Attendance Policy.\n\n"
            "For this query, I'd recommend contacting:\n\n"
            f"{contact_str}"
        )
        return False, answer, None, raw_chroma_docs, raw_chroma_docs
        
    # In-scope: prepare stream context
    context = format_context(combined_docs)
    source_refs = format_source_references(combined_docs)
    
    sys_prompt = system_prompt_override if system_prompt_override else SYSTEM_PROMPT
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_prompt),
        ("human", QA_PROMPT_TEMPLATE),
    ])
    
    chain = prompt | llm
    
    def generator():
        full_response = ""
        # Stream from LangChain chain using the condensed question for search context
        for chunk in chain.stream({"context": context, "question": standalone_question}):
            full_response += chunk
            yield chunk
            
        # Second-layer out-of-scope check
        llm_says_no_info = any(phrase in full_response.lower() for phrase in [
            "i don't have that information",
            "i do not have that information",
            "not available in the provided",
            "not mentioned in the",
            "no information about this",
            "cannot find any information",
        ])
        
        if llm_says_no_info:
            contact = route_to_contact(question)
            contact_str = format_contact_info(contact)
            extra = f"\n\n**Suggested Contact:**\n{contact_str}"
            yield extra
            
        elif source_refs:
            yield "\n\n" + source_refs
            
    return True, None, generator, combined_docs, raw_chroma_docs



def generate_follow_up_questions(
    question: str,
    answer: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    llm: OllamaLLM = None,
) -> List[str]:
    """
    Generate 2-3 dynamic follow-up suggestions based on the conversation context.
    """
    if llm is None:
        llm = get_llm()
        
    # Format context
    history_turns = []
    if chat_history:
        for msg in chat_history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_turns.append(f"{role}: {msg['content']}")
    history_turns.append(f"User: {question}")
    context_str = "\n".join(history_turns)
    
    from langchain_core.prompts import PromptTemplate
    prompt = PromptTemplate.from_template(FOLLOW_UP_PROMPT_TEMPLATE)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "chat_context": context_str,
            "latest_answer": answer
        }).strip()
        
        # Parse lines into list of clean questions
        questions = []
        for line in response.split("\n"):
            line = line.strip()
            # Remove bullets
            if line.startswith("-") or line.startswith("*"):
                line = line[1:].strip()
            elif line and line[0].isdigit() and len(line) > 1 and line[1] == ".":
                line = line[2:].strip()
            
            # Remove quotes
            line = line.replace('"', '').replace("'", "")
            
            if line and line.endswith("?") and len(line) > 5 and len(line) < 100:
                questions.append(line)
                
        return questions[:3]
    except Exception as e:
        print(f"Error generating follow-ups: {e}")
        return []


def get_unique_documents(vector_store: Chroma) -> List[Dict]:
    """Get list of unique documents loaded in ChromaDB with metadata and chunk count."""
    try:
        data = vector_store.get()
        if not data or "metadatas" not in data or not data["metadatas"]:
            return []
            
        docs_summary = {}
        for i, meta in enumerate(data["metadatas"]):
            file_name = meta.get("file_name", "unknown")
            source_name = meta.get("source_name", "Unknown Source")
            
            if file_name not in docs_summary:
                docs_summary[file_name] = {
                    "file_name": file_name,
                    "source_name": source_name,
                    "chunks": 0
                }
            docs_summary[file_name]["chunks"] += 1
            
        return list(docs_summary.values())
    except Exception as e:
        print(f"Error listing documents: {e}")
        return []


def delete_document_from_store(vector_store: Chroma, file_name: str) -> bool:
    """Delete all chunks belonging to a specific file from ChromaDB."""
    try:
        import os
        from src.config import DATA_DIR
        
        # Get all IDs matching the file_name
        data = vector_store.get(where={"file_name": file_name})
        if data and "ids" in data and data["ids"]:
            vector_store.delete(ids=data["ids"])
            
            # Also delete from DATA_DIR if the physical file exists
            file_path = DATA_DIR / file_name
            if file_path.exists():
                os.remove(file_path)
                
            return True
        return False
    except Exception as e:
        print(f"Error deleting document: {e}")
        return False


