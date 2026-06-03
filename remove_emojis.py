import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Regex to remove emojis from common unicode blocks
emoji_pattern = re.compile(
    r'['
    r'\U0001F600-\U0001F64F'  # Emoticons
    r'\U0001F300-\U0001F5FF'  # Misc Symbols and Pictographs
    r'\U0001F680-\U0001F6FF'  # Transport and Map
    r'\U0001F700-\U0001F77F'  # Alchemical Symbols
    r'\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
    r'\U0001F800-\U0001F8FF'  # Supplemental Arrows-C
    r'\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
    r'\U0001FA00-\U0001FA6F'  # Chess Symbols
    r'\U0001FA70-\U0001FAFF'  # Symbols and Pictographs Extended-A
    r'\u2600-\u26FF'          # Misc symbols
    r'\u2700-\u27BF'          # Dingbats
    r']+',
    flags=re.UNICODE
)

new_content = emoji_pattern.sub('', content)

# Clean up any literal " ??" that got messed up in previous edits
new_content = new_content.replace('Good morning! ?? Ready to tackle', 'Good morning! Ready to tackle')
new_content = new_content.replace('<div class="thinking-bubble-indicator">??</div>', '<div class="thinking-bubble-indicator">...</div>')

# In the user screenshot there was a moon emoji that might be matched by \u2600-\u26FF or similar.
# Just to be safe:
new_content = re.sub(r'Good evening!.*?(?:Burning the midnight oil\?)', 'Good evening! Burning the midnight oil?', new_content)
new_content = re.sub(r'Good afternoon!.*?(?:Keeping the momentum going\?)', 'Good afternoon! Keeping the momentum going?', new_content)

html_path.write_text(new_content, encoding="utf-8")
print("Successfully removed emojis to make it professional!")
