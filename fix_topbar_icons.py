import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Make light theme MORE transparent for the glass effect
content = content.replace(
    '--glass-bg: rgba(255, 255, 255, 0.4);',
    '--glass-bg: rgba(255, 255, 255, 0.15);'
)
content = content.replace(
    '--bg-card: rgba(255, 255, 255, 0.6);',
    '--bg-card: rgba(255, 255, 255, 0.25);'
)
content = content.replace(
    '--bg-deep: rgba(255, 255, 255, 0.5);',
    '--bg-deep: rgba(255, 255, 255, 0.2);'
)

# 2. SVGs for the topbar buttons
svg_phone = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'
svg_keyboard = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6" y2="8"></line><line x1="10" y1="8" x2="10" y2="8"></line><line x1="14" y1="8" x2="14" y2="8"></line><line x1="18" y1="8" x2="18" y2="8"></line><line x1="6" y1="12" x2="6" y2="12"></line><line x1="10" y1="12" x2="10" y2="12"></line><line x1="14" y1="12" x2="14" y2="12"></line><line x1="18" y1="12" x2="18" y2="12"></line><line x1="8" y1="16" x2="16" y2="16"></line></svg>'
svg_mic = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>'

# Replace HR Contact button
content = re.sub(
    r'<button class="topbar-icon-action" id="topbar-hr-btn"[^>]*>.*?</button>',
    f'<button class="topbar-icon-action" id="topbar-hr-btn" style="color: var(--accent); background: rgba(16, 185, 129, 0.15); border-radius: 50%; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;" title="HR Contact Numbers">{svg_phone}</button>',
    content,
    flags=re.DOTALL
)

# Replace Keyboard button
content = re.sub(
    r'<button class="topbar-icon-action" id="topbar-keyboard-btn"[^>]*>.*?</button>',
    f'<button class="topbar-icon-action" id="topbar-keyboard-btn" style="margin-left: 8px; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;" title="View Keyboard Shortcuts">{svg_keyboard}</button>',
    content,
    flags=re.DOTALL
)

# Replace Mic button
content = re.sub(
    r'<button class="topbar-icon-action" id="topbar-mic-btn"[^>]*>.*?</button>',
    f'<button class="topbar-icon-action" id="topbar-mic-btn" style="margin-left: 4px; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;" title="Voice Assistant dictation">{svg_mic}</button>',
    content,
    flags=re.DOTALL
)

html_path.write_text(content, encoding="utf-8")
print("Successfully fixed topbar icons and made the theme more transparent!")
