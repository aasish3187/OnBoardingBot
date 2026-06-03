import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Replace the gradient logic in .welcome-brand with solid green
old_css = """        .welcome-brand {
            font-family: var(--font-ui);
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.04em;
            background: linear-gradient(135deg, var(--accent) 0%, var(--system-indigo) 50%, var(--system-purple) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 2px 10px rgba(0, 122, 255, 0.15));
        }"""

new_css = """        .welcome-brand {
            font-family: var(--font-ui);
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.04em;
            color: #10b981;
            filter: drop-shadow(0 2px 10px rgba(16, 185, 129, 0.15));
        }"""

# A safer regex replacement in case spacing is slightly different
content = re.sub(
    r'\.welcome-brand\s*\{[^}]+\}',
    new_css.strip(),
    content
)

html_path.write_text(content, encoding="utf-8")
print("Successfully removed the gradient and made the text solid green!")
