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

# 2. Remove achievements rail section HTML
content = re.sub(r'<div class="rail-section">.*?<span class="rail-section-title">Achievements</span>.*?</div>\s*</div>', '', content, flags=re.DOTALL)

# 3. Suppress JS errors from missing achievements HTML
content = re.sub(
    r'(function updateAchievementsUI\(\)\s*\{)',
    r'\1 return; // achievements removed\n',
    content
)

# 4. Enhance Progress Ring and show percentage prominently on top
new_progress = """
                <div class="rail-section" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px 0;">
                    <div style="font-weight: 800; font-size: 1.8rem; color: var(--accent); margin-bottom: 8px;" id="onboarding-pct-display">0%</div>
                    <div class="progress-gauge-container" style="justify-content: center;">
                        <svg class="progress-ring" style="width: 60px; height: 60px;">
                            <circle class="progress-ring-circle-bg" stroke-width="4" fill="transparent" r="26" cx="30" cy="30"/>
                            <circle class="progress-ring-circle" id="onboarding-progress-circle" stroke-width="4" fill="transparent" r="26" cx="30" cy="30" stroke-dasharray="163.3" stroke-dashoffset="163.3" style="transform-origin: 30px 30px;"/>
                        </svg>
                        <div style="text-align: left;">
                            <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">Onboarding</div>
                            <div style="font-size: 0.8rem; color: var(--text-dim);" id="onboarding-count-text">0 of 7 complete</div>
                        </div>
                    </div>
                </div>
"""
content = re.sub(r'<div class="rail-section">\s*<div class="progress-gauge-container">.*?</div>\s*</div>', new_progress, content, flags=re.DOTALL)

# Update the JS that calculates the progress circle offset (circumference for r=26 is ~163.36)
content = re.sub(
    r'const offset = 113\.1 - \(113\.1 \* \(pct / 100\)\);',
    r'const offset = 163.36 - (163.36 * (pct / 100));\n            const pctDisplay = document.getElementById("onboarding-pct-display");\n            if (pctDisplay) pctDisplay.textContent = Math.round(pct) + "%";',
    content
)

# 5. Clean up any lingering question marks or emojis from before
content = content.replace('<div class="thinking-bubble-indicator">...</div>', '')
content = content.replace('??', '')

html_path.write_text(content, encoding="utf-8")
print("Successfully applied glassmorphism, removed achievements, and enhanced progress UI!")
