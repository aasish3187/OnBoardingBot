import os
import sys
# Reconfigure standard output/error to utf-8 to avoid UnicodeEncodeError on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from pathlib import Path
from langchain_ollama import OllamaLLM

from src.company_engine import CompanyKnowledgeBase
from src.config import get_dynamic_system_prompt
from src.rag_chain import query_rag_stream

app = FastAPI(title="OnboardBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

company_kb = CompanyKnowledgeBase()

# Global LLM instance (similar to app.py)
llm = OllamaLLM(model="llama3.2", temperature=0.1)

# Pydantic models
class SetCompanyRequest(BaseModel):
    company: str

class ChatRequest(BaseModel):
    company: str
    message: str
    history: Optional[List[Dict[str, str]]] = []

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Serve the onboardbot.html file
    html_path = Path(__file__).parent / "onboardbot.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: onboardbot.html not found</h1>"

@app.post("/api/set_company")
async def set_company(req: SetCompanyRequest):
    try:
        if not req.company.strip():
            raise HTTPException(status_code=400, detail="Company name cannot be empty")
            
        print(f"Building/Fetching KB for: {req.company}")
        
        # Build the vector store (this takes time if it's not cached)
        vs, info = company_kb.get_or_create(req.company)
        
        if not info or not vs:
            raise HTTPException(status_code=500, detail="Failed to build knowledge base")
            
        return {
            "status": "success", 
            "company_info": info,
            "message": f"Successfully loaded {info.get('full_name', req.company)}"
        }
    except Exception as e:
        print(f"Error in set_company: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        # Get the vector store for the company
        vs, info = company_kb.get_or_create(req.company)
        if not vs:
            raise HTTPException(status_code=500, detail="Vector store not ready")
            
        system_prompt = get_dynamic_system_prompt(info.get("full_name", req.company))
        
        is_in_scope, immediate_answer, stream_generator, retrieved_docs, raw_chroma_docs = query_rag_stream(
            vector_store=vs,
            question=req.message,
            chat_history=req.history,
            llm=llm,
            system_prompt_override=system_prompt
        )
        
        # Format citations
        citations = []
        if retrieved_docs:
            for doc, score in retrieved_docs:
                citations.append({
                    "source": doc.metadata.get("source_name", "Unknown Document"),
                    "file": doc.metadata.get("file_name", "unknown")
                })
        
        if not is_in_scope and immediate_answer:
            # Return JSON for immediate answer
            return {
                "status": "success",
                "answer": immediate_answer,
                "citations": citations,
                "in_scope": False
            }
        else:
            # For streaming, we'll return a server-sent events stream or just a string stream
            def stream_response():
                # Yield SSE format
                for chunk in stream_generator():
                    # Format as Server-Sent Events (SSE) data chunk
                    # Replace newlines so the SSE parser doesn't break
                    safe_chunk = chunk.replace("\n", "\\n")
                    yield f"data: {safe_chunk}\n\n"
                
                import json
                # Send a final event with citations
                yield f"event: citations\ndata: {json.dumps(citations)}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingResponse(stream_response(), media_type="text/event-stream")
            
    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
