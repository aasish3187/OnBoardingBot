import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update the Dark Theme for True High-Contrast Glassmorphism
dark_glass_css = """[data-theme="dark"] {
            --bg-wallpaper: #0b0f19;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --text-dim: rgba(255, 255, 255, 0.5);
            --border: rgba(255, 255, 255, 0.15);
            --glass-bg: rgba(255, 255, 255, 0.08);
            --glass-blur: 30px;
            --glass-border-top: rgba(255, 255, 255, 0.2);
            --glass-border: rgba(255, 255, 255, 0.1);
            --bg-card: rgba(255, 255, 255, 0.05);
            --bg-deep: rgba(0, 0, 0, 0.2);
            --shadow-sm: 0 4px 6px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 10px 20px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
            --shadow-glow: 0 0 24px 0 rgba(16, 185, 129, 0.4);
            --accent: #10b981;
        }"""
content = re.sub(r'\[data-theme="dark"\]\s*\{[^}]+\}', dark_glass_css, content)

# 2. Force Dark Theme Default
# In the previous script I set it to 'light', so let's set it to 'dark'
content = content.replace(
    "APP = { settings: { theme: 'light'",
    "APP = { settings: { theme: 'dark'"
)
content = content.replace(
    "theme: 'light'",
    "theme: 'dark'"
)

# 3. Update Ambient Spheres to Nexus Green Colors and Increase Intensity
content = re.sub(
    r'\.ambient-sphere\s*\{[^}]+\}',
    r'.ambient-sphere { position: absolute; border-radius: 50%; filter: blur(140px); opacity: 0.6; pointer-events: none; mix-blend-mode: screen; transition: transform 1.2s ease-out; }',
    content
)
content = content.replace('background: var(--system-blue);', 'background: #10b981;')  # Nexus Green
content = content.replace('background: var(--system-purple);', 'background: #059669;') # Deeper Green
content = content.replace('background: var(--system-teal);', 'background: #34d399;')   # Lighter Green

# 4. Enhance Text Visibility
# Since the background is dark and the glass is translucent white, we want all text to be crisp white.
# Some hardcoded text colors like style="color: var(--text-primary);" are already fine, but we need to ensure the nexus SVG text is white in dark mode.
# I'll update the SVG NEXUS text injected earlier to use var(--text-primary) if it doesn't already.
content = content.replace('<span style="letter-spacing: 1px; font-weight: 800;">NEXUS</span>', '<span style="letter-spacing: 1px; font-weight: 800; color: var(--text-primary);">NEXUS</span>')

html_path.write_text(content, encoding="utf-8")
print("Successfully applied high-contrast dark green glassmorphism!")
