import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Change the color of NEXUS text from var(--text-primary) to green #10b981
content = content.replace(
    'style="color: var(--text-primary); font-size: 2.8rem; font-weight: 800; letter-spacing: 2px; margin-top: 5px; margin-bottom: 0;">NEXUS</h1>',
    'style="color: #10b981; font-size: 2.8rem; font-weight: 800; letter-spacing: 2px; margin-top: 5px; margin-bottom: 0;">NEXUS</h1>'
)

html_path.write_text(content, encoding="utf-8")
print("Successfully changed NEXUS text to green!")
