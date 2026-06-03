# 🤖 OnboardBot — New Employee Onboarding Assistant

A **RAG-powered chatbot** that answers new employee questions using company HR documents. Built with LangChain, ChromaDB, HuggingFace Embeddings, and Ollama.

> **Hackathon Project** — TRIAD ACADEMY: Agentic AI Systems & Autonomous Workflow Engineering  
> Problem #7: OnboardBot — New Employee Onboarding Assistant

---

## 🎯 Features

- **RAG Pipeline**: Retrieves relevant information from 3 HR documents and generates accurate, contextual answers
- **Source References**: Every answer cites the source document for transparency
- **Out-of-Scope Detection**: Dual-layer detection (retrieval scores + LLM verification) for questions outside the knowledge base
- **HR Contact Routing**: Automatically suggests the right HR contact when information isn't available
- **Beautiful UI**: Streamlit web interface with chat history and HR contact sidebar
- **CLI Interface**: Terminal-based chat with rich formatting

---

## 📚 Knowledge Base

| Document | Contents |
|----------|----------|
| **HR Handbook** | Company overview, values, code of conduct, dress code, performance reviews, employee benefits, grievance procedures |
| **IT Setup Guide** | Laptop setup, VPN configuration, email & Slack setup, software installation, 2FA, troubleshooting |
| **Leave Policy** | Leave types (CL/SL/EL/maternity/paternity), accrual rules, holiday calendar, carry-forward, attendance |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Orchestration** | LangChain |
| **Vector Database** | ChromaDB |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **LLM** | Ollama (llama3.2) |
| **Web UI** | Streamlit |
| **CLI** | Rich (Python) |

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **Ollama** installed and running:
   ```bash
   # Download from https://ollama.com
   # Pull a model:
   ollama pull llama3.2
   ```

### Installation

```bash
# 1. Navigate to the project directory
cd "Agentic AI Project"

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Step 1: Ingest HR documents into ChromaDB
python ingest.py

# Step 2a: Launch the Streamlit web UI
streamlit run app.py

# Step 2b: OR use the terminal interface
python cli.py

# Step 2c: Launch the Premium Auth UX Sandbox
# Simply open `auth_sandbox.html` in any browser to inspect the 11-screen gateway and design specs!

# Step 3: Run the test suite
python test_queries.py

```

---

## 📁 Project Structure

```
OnboardBot/
├── data/                          # HR documents
│   ├── hr_handbook.txt            # Company policies & benefits
│   ├── it_setup_guide.txt         # IT onboarding guide
│   └── leave_policy.txt           # Leave & attendance rules
├── chroma_db/                     # Persisted vector store (auto-generated)
├── src/
│   ├── __init__.py
│   ├── config.py                  # Centralized configuration
│   ├── document_loader.py         # Document loading & chunking
│   ├── embeddings.py              # HuggingFace embedding model
│   ├── vector_store.py            # ChromaDB operations
│   ├── rag_chain.py               # RAG pipeline with out-of-scope detection
│   ├── hr_contacts.py             # HR contact directory & routing
│   └── chatbot.py                 # High-level chatbot class
├── app.py                         # Streamlit web UI
├── cli.py                         # Terminal chat interface
├── ingest.py                      # Document ingestion script
├── test_queries.py                # Automated test suite (13 queries)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🧪 Test Queries

### In-Scope (10 queries — should answer with sources)

| # | Query | Expected Source |
|---|-------|-----------------|
| 1 | What is the company's dress code policy? | HR Handbook |
| 2 | How do I set up VPN on my laptop? | IT Setup Guide |
| 3 | How many casual leaves do I get per year? | Leave Policy |
| 4 | What is the process for annual performance reviews? | HR Handbook |
| 5 | How do I configure my email and Slack? | IT Setup Guide |
| 6 | What is the maternity leave policy? | Leave Policy |
| 7 | What are the company's core values? | HR Handbook |
| 8 | How do I set up two-factor authentication? | IT Setup Guide |
| 9 | Can I carry forward unused leaves to next year? | Leave Policy |
| 10 | What health insurance benefits does the company offer? | HR Handbook |

### Out-of-Scope (3 queries — should decline and suggest HR contact)

| # | Query | Expected |
|---|-------|----------|
| 11 | What is the company's stock price today? | Decline + suggest General HR |
| 12 | Can you book a flight for my business trip? | Decline + suggest General HR |
| 13 | What's the weather like tomorrow? | Decline gracefully |

---

## ⚙️ Configuration

Key settings in `src/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size for splitting |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `4` | Number of chunks retrieved per query |
| `RELEVANCE_THRESHOLD` | `1.5` | L2 distance threshold for out-of-scope |

You can also set `OLLAMA_MODEL` via environment variable:
```bash
set OLLAMA_MODEL=mistral   # Windows
export OLLAMA_MODEL=mistral  # macOS/Linux
```

---

## 📞 HR Contact Directory

| Department | Email | Extension |
|-----------|-------|-----------|
| General HR | hr@nexustech.com | 1001 |
| IT Helpdesk | ithelpdesk@nexustech.com | 2001 |
| Leave Desk | leave.desk@nexustech.com | 1005 |
| Payroll | payroll@nexustech.com | 1010 |
| Benefits | benefits@nexustech.com | 1011 |
| Ethics | ethics@nexustech.com | Hotline: 1800-555-ETHICS |

---

## 🏗️ Architecture

```
User Query → Embedding → ChromaDB Similarity Search
                              │
                    ┌─────────┴─────────┐
                    │                   │
            Score < Threshold    Score ≥ Threshold
            (In-Scope)           (Out-of-Scope)
                    │                   │
            LLM + Context         "I don't have
            + Source Refs         that information"
                    │                + HR Contact
                    │                   │
                    └─────────┬─────────┘
                              │
                        Final Answer
```

---

## 📝 License

This project was built for the TRIAD ACADEMY Hackathon — Agentic AI Systems & Autonomous Workflow Engineering.

---

*Built with ❤️ using LangChain, ChromaDB, HuggingFace, and Ollama*
