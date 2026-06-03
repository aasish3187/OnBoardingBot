import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Fully Transparent Glassmorphism (White & Green only)
glass_css = """[data-theme="light"] {
            --bg-wallpaper: linear-gradient(135deg, #f8fafc 0%, #ecfdf5 100%);
            --text-primary: #0f172a;
            --text-secondary: rgba(15, 23, 42, 0.85);
            --text-dim: rgba(15, 23, 42, 0.5);
            --border: rgba(16, 185, 129, 0.2);
            --glass-bg: rgba(255, 255, 255, 0.4);
            --glass-blur: 32px;
            --glass-border-top: rgba(255, 255, 255, 0.8);
            --glass-border: rgba(255, 255, 255, 0.4);
            --bg-card: rgba(255, 255, 255, 0.6);
            --bg-deep: rgba(255, 255, 255, 0.5);
            --shadow-sm: 0 4px 6px rgba(16, 185, 129, 0.05);
            --shadow-md: 0 10px 20px -3px rgba(16, 185, 129, 0.1), 0 4px 6px -2px rgba(16, 185, 129, 0.05);
            --shadow-lg: 0 20px 25px -5px rgba(16, 185, 129, 0.15);
            --shadow-glow: 0 0 24px 0 rgba(16, 185, 129, 0.25);
            --accent: #10b981;
        }"""
content = re.sub(r'\[data-theme="light"\]\s*\{[^}]+\}', glass_css, content)

# 2. Hide achievements safely via CSS instead of deleting HTML blocks
content = content.replace(
    '.achievements-grid {',
    '.achievements-grid { display: none !important;\n'
)
# Hide the achievements title section
content = re.sub(
    r'<div class="rail-section-header" style="margin-bottom: 4px;">\s*<span class="rail-section-title">Achievements</span>',
    r'<div class="rail-section-header" style="display:none !important;">\n                        <span class="rail-section-title">Achievements</span>',
    content
)

# 3. Enhance Progress Ring and show percentage prominently on top
new_progress = """<div style="font-weight: 800; font-size: 1.8rem; color: var(--accent); text-align: center; margin-bottom: -15px;" id="onboarding-pct-display">0%</div>
                        <svg class="progress-ring" style="width: 70px; height: 70px; margin: 0 auto; display: block; overflow: visible;">
                            <circle class="progress-ring-circle-bg" stroke-width="4" fill="transparent" r="30" cx="35" cy="35"/>
                            <circle class="progress-ring-circle" id="onboarding-progress-circle" stroke-width="4" fill="transparent" r="30" cx="35" cy="35" stroke-dasharray="188.5" stroke-dashoffset="188.5" style="transform-origin: 35px 35px;"/>
                        </svg>"""

content = re.sub(
    r'<svg class="progress-ring">.*?</svg>',
    new_progress,
    content,
    flags=re.DOTALL
)

# Replace the progress JS math
content = re.sub(
    r'const offset = 113\.1 - \(113\.1 \* \(pct / 100\)\);',
    r'const offset = 188.5 - (188.5 * (pct / 100));\n            const pctDisplay = document.getElementById("onboarding-pct-display");\n            if (pctDisplay) pctDisplay.textContent = Math.round(pct) + "%";',
    content
)

# Remove the tiny 0% text inside the SVG that used to be there if it was outside the replaced block
content = re.sub(r'<text x="50%".*?id="onboarding-pct-text".*?</text>', '', content)

# 4. Remove any residual broken emojis
content = content.replace('<div class="thinking-bubble-indicator">...</div>', '')
content = content.replace('??', '')

html_path.write_text(content, encoding="utf-8")
print("Successfully and safely applied UI updates!")
