import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Define crisp SVG icons for the 6 cards (24x24)
svg_policies = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'

svg_it = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>'

svg_leave = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'

svg_benefits = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"></rect><circle cx="12" cy="12" r="2"></circle><path d="M6 12h.01M18 12h.01"></path></svg>'

svg_hr = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'

svg_help = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'

# To safely replace the empty boxes or the broken ? boxes without breaking the HTML, we will find each card block based on its title and replace the <div> directly above it.
replacements = [
    (r'<div class="card-icon-badge">.*?</div>\s*<h3 class="wc-title">Company Policies</h3>', f'<div class="card-icon-badge">{svg_policies}</div>\n<h3 class="wc-title">Company Policies</h3>'),
    (r'<div class="card-icon-badge">.*?</div>\s*<h3 class="wc-title">IT Setup Guide</h3>', f'<div class="card-icon-badge">{svg_it}</div>\n<h3 class="wc-title">IT Setup Guide</h3>'),
    (r'<div class="card-icon-badge">.*?</div>\s*<h3 class="wc-title">Leave & Attendance</h3>', f'<div class="card-icon-badge">{svg_leave}</div>\n<h3 class="wc-title">Leave & Attendance</h3>'),
    (r'<div class="card-icon-badge">.*?</div>\s*<h3 class="wc-title">Benefits & Payroll</h3>', f'<div class="card-icon-badge">{svg_benefits}</div>\n<h3 class="wc-title">Benefits & Payroll</h3>'),
    (r'<div class="card-icon-badge">.*?</div>\s*<h3 class="wc-title">HR Contacts</h3>', f'<div class="card-icon-badge">{svg_hr}</div>\n<h3 class="wc-title">HR Contacts</h3>'),
    (r'<div class="card-icon-badge">.*?</div>\s*<h3 class="wc-title">Help & Commands</h3>', f'<div class="card-icon-badge">{svg_help}</div>\n<h3 class="wc-title">Help & Commands</h3>')
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

html_path.write_text(content, encoding="utf-8")
print("Successfully populated card icons with professional SVGs!")
