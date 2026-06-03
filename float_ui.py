import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update Topbar to float and curve
content = content.replace(
    '#topbar {\n            position: fixed; top: 0; left: 0; right: 0; height: var(--topbar-h);',
    '#topbar {\n            position: fixed; top: 24px; left: 24px; right: 24px; height: var(--topbar-h);\n            border-radius: 36px; border: 1px solid rgba(255, 255, 255, 0.15);'
)

# 2. Update Left Rail to float, curve, and disconnect from top/bottom/left
content = content.replace(
    '#left-rail { padding-top: var(--topbar-h); height: 100vh; }',
    '#left-rail { height: calc(100vh - var(--topbar-h) - 72px); margin-top: calc(var(--topbar-h) + 48px); margin-left: 24px; margin-bottom: 24px; padding-top: 0; border-radius: 36px; border: 1px solid rgba(255, 255, 255, 0.15); }'
)

# 3. Clean up the border-right on #left-rail that was used for the docked layout
content = content.replace(
    '-webkit-backdrop-filter: blur(var(--glass-blur)); border-right: 1px solid var(--glass-border);',
    '-webkit-backdrop-filter: blur(var(--glass-blur));'
)

# 4. Adjust the main area padding so content doesn't hit the new floating topbar
content = content.replace(
    '#main-area { padding-top: var(--topbar-h); height: 100vh; }',
    '#main-area { padding-top: calc(var(--topbar-h) + 48px); height: 100vh; }'
)

# 5. Fix any internal padding in left-rail so the top isn't squished since we removed padding-top
content = content.replace(
    '#left-rail {\n            width: var(--rail-width); min-width: var(--rail-width);',
    '#left-rail {\n            width: var(--rail-width); min-width: var(--rail-width); padding-top: 16px;'
)

html_path.write_text(content, encoding="utf-8")
print("Successfully applied floating and curved glass layouts!")
