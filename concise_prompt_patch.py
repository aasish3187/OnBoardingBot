import re
from pathlib import Path

config_path = Path("src/config.py")
content = config_path.read_text(encoding="utf-8")

# Add a rule to SYSTEM_PROMPT
content = content.replace(
    '6. Keep your answers concise but complete. Use bullet points for lists.',
    '6. Be extremely DIRECT and CONCISE. If the user asks about one specific thing, ONLY answer about that specific thing. Do not dump the entire document context. Think critically and synthesize the exact answer on your own. Use bullet points for lists if necessary.'
)

# Replace in QA_PROMPT_TEMPLATE as well to reinforce the behavior
content = content.replace(
    'Question: {question}',
    'Question: {question}\n\nCRITICAL INSTRUCTION: Analyze the question carefully. Answer ONLY the specific question asked. Do not provide unrelated information from the context. Be direct and concise.'
)

config_path.write_text(content, encoding="utf-8")
print("Successfully updated the prompts for concise answering!")
