import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Hide the scrollbar for the left-rail so it doesn't poke out of the rounded borders
css_to_inject = """
        /* Hide scrollbar for the sidebar */
        #left-rail::-webkit-scrollbar {
            display: none;
        }
        #left-rail {
            -ms-overflow-style: none;  /* IE and Edge */
            scrollbar-width: none;  /* Firefox */
        }
"""

# Insert right after the #left-rail class definition starts or just append it after the scrollbar general definitions
content = content.replace(
    '::-webkit-scrollbar-thumb:hover { background: var(--accent); }',
    '::-webkit-scrollbar-thumb:hover { background: var(--accent); }' + css_to_inject
)

html_path.write_text(content, encoding="utf-8")
print("Successfully hidden the sidebar scrollbar!")
