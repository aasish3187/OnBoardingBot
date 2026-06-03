import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Enhance input bar visibility in CSS
content = content.replace(
    '.input-bar {\n            display: flex; align-items: flex-end; gap: 8px; background: var(--glass-bg);',
    '.input-bar {\n            display: flex; align-items: flex-end; gap: 8px; background: rgba(255, 255, 255, 0.15);'
)
content = content.replace(
    'border: 1px solid var(--border); border-top-color: var(--glass-border-top);',
    'border: 1px solid rgba(255, 255, 255, 0.3); border-top-color: rgba(255, 255, 255, 0.4);'
)

# 2. Insert SVGs into the input bar buttons
svg_attach = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>'
svg_mic = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>'
svg_send = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:2px; margin-top:2px;"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>'

# Replace attach btn
content = re.sub(
    r'<button class="input-bar-btn" id="attach-btn"[^>]*></button>',
    f'<button class="input-bar-btn" id="attach-btn" title="Attach file" style="font-size: 1.1rem;">\n{svg_attach}\n</button>',
    content
)

# Replace mic btn
content = re.sub(
    r'<button class="input-bar-btn" id="voice-input-btn"[^>]*></button>',
    f'<button class="input-bar-btn" id="voice-input-btn" title="Voice dictation input mic" style="font-size: 1.1rem; margin-right: 4px;">\n{svg_mic}\n</button>',
    content
)

# Replace send btn
content = re.sub(
    r'<button class="send-btn" id="send-chat-btn" disabled[^>]*></button>',
    f'<button class="send-btn" id="send-chat-btn" disabled style="display: flex; align-items: center; justify-content: center;">\n{svg_send}\n</button>',
    content
)

html_path.write_text(content, encoding="utf-8")
print("Successfully updated input bar visibility and icons!")
