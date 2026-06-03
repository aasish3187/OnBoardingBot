import re
from pathlib import Path

rag_path = Path("src/rag_chain.py")
content = rag_path.read_text(encoding="utf-8")

# Force in_scope to True for query_rag
content = content.replace(
    'in_scope = is_query_in_scope(docs_with_scores, threshold=relevance_threshold)',
    'in_scope = is_query_in_scope(docs_with_scores, threshold=relevance_threshold)\n    in_scope = True  # OVERRIDE: Allow LLM to answer all questions'
)

# Force in_scope to True for query_rag_stream
content = content.replace(
    'in_scope = is_query_in_scope(raw_chroma_docs, threshold=relevance_threshold)',
    'in_scope = is_query_in_scope(raw_chroma_docs, threshold=relevance_threshold)\n    in_scope = True  # OVERRIDE: Allow LLM to answer all questions'
)

# Also update the system prompt slightly to let it answer outside context if needed
# (Optional, but let's check if SYSTEM_PROMPT restricts it heavily)
# We will just patch the strict guardrail first.

rag_path.write_text(content, encoding="utf-8")
print("Successfully disabled out-of-scope guardrails!")
