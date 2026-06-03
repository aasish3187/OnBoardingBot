import re
from pathlib import Path

api_path = Path("api.py")
content = api_path.read_text(encoding="utf-8")

cors_setup = """app = FastAPI(title="OnboardBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

if "app.add_middleware" not in content:
    content = content.replace('app = FastAPI(title="OnboardBot API")', cors_setup)
    api_path.write_text(content, encoding="utf-8")
    print("Successfully added CORS!")
else:
    print("CORS already added.")
