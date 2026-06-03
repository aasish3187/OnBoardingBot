import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update [data-theme="dark"] accent color
content = re.sub(
    r'(--shadow-glow:\s*0\s*0\s*28px\s*0\s*rgba\(0,\s*122,\s*255,\s*0\.2\);.*?--accent:\s*)#3b82f6(;)',
    r'--shadow-glow: 0 0 28px 0 rgba(16, 185, 129, 0.2);\n            --accent: #10b981;',
    content,
    flags=re.DOTALL
)

# 2. Update [data-theme="light"] to white and green
light_theme_new = """[data-theme="light"] {
            --bg-wallpaper: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: rgba(15, 23, 42, 0.75);
            --text-dim: rgba(15, 23, 42, 0.45);
            --border: rgba(15, 23, 42, 0.08);
            --glass-bg: rgba(255, 255, 255, 0.85);
            --glass-blur: 24px;
            --glass-border-top: rgba(255, 255, 255, 1);
            --glass-border: rgba(15, 23, 42, 0.05);
            --bg-card: #f8fafc;
            --bg-deep: #f1f5f9;
            --shadow-sm: 0 2px 4px rgba(15, 23, 42, 0.02);
            --shadow-md: 0 10px 20px -3px rgba(15, 23, 42, 0.04), 0 4px 6px -2px rgba(15, 23, 42, 0.02);
            --shadow-lg: 0 20px 25px -5px rgba(15, 23, 42, 0.08);
            --shadow-glow: 0 0 24px 0 rgba(16, 185, 129, 0.15);
            --accent: #10b981;
        }"""
        
content = re.sub(
    r'\[data-theme="light"\]\s*\{[^}]+\}',
    light_theme_new,
    content
)

# 3. Update :root base accent glows (used for focus rings etc)
content = re.sub(
    r'--accent-soft:\s*rgba\(0,\s*122,\s*255,\s*0\.1\);',
    r'--accent-soft: rgba(16, 185, 129, 0.1);',
    content
)
content = re.sub(
    r'--accent-glow:\s*rgba\(0,\s*122,\s*255,\s*0\.25\);',
    r'--accent-glow: rgba(16, 185, 129, 0.25);',
    content
)

# 4. Force default theme to light (currently it is 'auto')
content = content.replace(
    "APP = { settings: { theme: 'auto'",
    "APP = { settings: { theme: 'light'"
)
content = content.replace(
    "theme: 'auto'",
    "theme: 'light'"
)

html_path.write_text(content, encoding="utf-8")
print("Successfully overhauled theme to White & Green!")
