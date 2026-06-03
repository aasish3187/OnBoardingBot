import re
from pathlib import Path

api_path = Path("api.py")
content = api_path.read_text(encoding="utf-8")

# Add CORS imports and middleware
cors_import = "from fastapi.middleware.cors import CORSMiddleware\n"
if "CORSMiddleware" not in content:
    # Inject right after FastAPI import
    content = content.replace('from fastapi import FastAPI, HTTPException, Request', 'from fastapi import FastAPI, HTTPException, Request\nfrom fastapi.middleware.cors import CORSMiddleware')
    
    # Inject middleware setup after app = FastAPI()
    cors_setup = """
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
    content = content.replace('app = FastAPI(title="Nexus OnboardBot API")', 'app = FastAPI(title="Nexus OnboardBot API")\n' + cors_setup)
    
    api_path.write_text(content, encoding="utf-8")
    print("Successfully added CORS to api.py!")
else:
    print("CORS already configured.")
