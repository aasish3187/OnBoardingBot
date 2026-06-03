import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Hide the old smiley face avatar on the welcome screen
content = content.replace(
    ".welcome-avatar-wrap {",
    ".welcome-avatar-wrap { display: none !important; "
)

html_path.write_text(content, encoding="utf-8")
print("Successfully hid the welcome avatar wrap!")
