import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Add width: 100%; height: 100%; to .bot-avatar-svg
content = content.replace(
    ".bot-avatar-svg { animation",
    ".bot-avatar-svg { width: 100%; height: 100%; animation"
)

html_path.write_text(content, encoding="utf-8")
print("Successfully patched bot-avatar-svg size!")
