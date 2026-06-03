import re
from pathlib import Path

# 1. Update config.py prompts to allow general knowledge
config_path = Path("src/config.py")
config_content = config_path.read_text(encoding="utf-8")

# Replace strict rules in SYSTEM_PROMPT
config_content = re.sub(
    r'1\. ONLY answer questions based on the provided context below\. Do NOT make up information\.',
    '1. Use the provided context below first. If the context does not contain the answer, you may use your general knowledge to assist the user as an AI.',
    config_content
)
config_content = re.sub(
    r'2\. If the context does not contain the answer, respond with: "I don\'t have that information in our HR documents\."',
    '2. If the context does not contain the answer, you can answer from your own knowledge, but clarify it is not from the official HR documents if it pertains to specific company policies.',
    config_content
)
config_content = re.sub(
    r'IMPORTANT: If the context above does not contain relevant information to answer the question, you MUST say "I don\'t have that information in our HR documents." and suggest contacting the appropriate HR department[^.]*\.',
    'IMPORTANT: If the context above does not contain relevant information, feel free to assist the user with your general LLM capabilities.',
    config_content
)
config_content = re.sub(
    r'Remember: Only use information from the provided context\. Cite your sources\. If the information is not available, say so clearly and suggest the appropriate HR contact\.',
    'Remember: Use information from the provided context if available, and cite sources. If not available, answer using your general knowledge and capabilities.',
    config_content
)

config_path.write_text(config_content, encoding="utf-8")

# 2. Disable the second-layer guardrail in rag_chain.py
rag_path = Path("src/rag_chain.py")
rag_content = rag_path.read_text(encoding="utf-8")

# Just clear the list of phrases that trigger the block
rag_content = re.sub(
    r'llm_says_no_info = any\(phrase in full_response\.lower\(\) for phrase in \[[^\]]+\]\)',
    'llm_says_no_info = False  # Disabled strict guardrail to allow general LLM answers',
    rag_content
)

rag_path.write_text(rag_content, encoding="utf-8")
print("Successfully made the LLM permissive and disabled second-layer guardrails!")
