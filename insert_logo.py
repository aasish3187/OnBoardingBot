import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Nexus SVG Logo (Small for Topbar/Sidebar)
nexus_svg_small = """
<svg width="24" height="24" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: inline-block; vertical-align: middle;">
  <path d="M 20 50 Q 35 15, 50 50 T 80 50" stroke="#10b981" stroke-width="12" stroke-linecap="round" fill="none"/>
  <circle cx="20" cy="50" r="10" fill="#10b981" />
  <circle cx="80" cy="50" r="10" fill="#10b981" />
</svg>
<span style="letter-spacing: 1px; font-weight: 800;">NEXUS</span>
"""

# Nexus SVG Logo (Large for Welcome Screen)
nexus_svg_large = """
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 15px;">
    <svg width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 4px 6px rgba(16, 185, 129, 0.2));">
      <path d="M 15 50 Q 32.5 10, 50 50 T 85 50" stroke="#10b981" stroke-width="12" stroke-linecap="round" fill="none"/>
      <circle cx="15" cy="50" r="10" fill="#10b981" />
      <circle cx="85" cy="50" r="10" fill="#10b981" />
    </svg>
    <h1 class="welcome-brand" style="color: var(--text-primary); font-size: 2.8rem; font-weight: 800; letter-spacing: 2px; margin-top: 5px; margin-bottom: 0;">NEXUS</h1>
</div>
"""

# 1. Replace topbar brand
content = re.sub(
    r'<span class="brand-title">OnboardBot</span>',
    nexus_svg_small.strip(),
    content
)

# 2. Replace welcome screens h1
content = re.sub(
    r'<h1 class="welcome-brand"[^>]*>OnboardBot</h1>',
    nexus_svg_large.strip(),
    content
)

# 3. Replace text references to OnboardBot
content = content.replace("OnboardBot v2.0   Nexus Technologies", "Nexus System v2.0")

html_path.write_text(content, encoding="utf-8")
print("Successfully injected Nexus Logo!")
