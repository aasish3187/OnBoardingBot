"""
OnboardBot — Premium Obsidian & Gold Web UI
Sleek, modern, and award-winning enterprise conversational interface
integrating advanced Hugging Face Inference pipelines.

Usage:
    streamlit run app.py
"""

import sys
import uuid
import threading
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from src.config import (
    STREAMLIT_PAGE_TITLE,
    STREAMLIT_PAGE_ICON,
    STREAMLIT_LAYOUT,
    OLLAMA_MODEL,
    EMBEDDING_MODEL,
    APP_NAME,
    APP_VERSION,
    DATA_DIR,
)
from src.vector_store import load_vector_store, get_vector_store_stats
from src.rag_chain import (
    get_llm,
    query_rag,
    query_rag_stream,
    query_hybrid_search,
    generate_follow_up_questions,
    get_unique_documents,
    delete_document_from_store,
)
from src.hr_contacts import HR_CONTACTS, get_all_contacts_formatted

# Import Hugging Face Client Layer
from src.hf_client import (
    classify_intent,
    summarize_text,
    translate_text,
    rephrase_text,
    calculate_query_similarity,
    add_query_to_history,
)

# ============================================================================
# SELF-HEALING AUTOMATIC ICON & SHORTCUT GENERATOR
# ============================================================================
import os
import subprocess

def generate_icon_and_shortcut():
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if not os.path.exists(icon_path):
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([30, 220, 226, 245], fill=(0, 0, 0, 80))
            for i in range(10):
                offset = 190 + i
                draw.ellipse([20, 20 + i, 236, offset + i], fill=(140, 88, 25, 255))
            draw.ellipse([20, 20, 236, 236], fill=(232, 168, 56, 255))
            draw.ellipse([25, 25, 231, 231], outline=(245, 200, 66, 255), width=6)
            draw.ellipse([80, 100, 110, 130], fill=(15, 15, 20, 255))
            draw.ellipse([98, 104, 106, 112], fill=(255, 255, 255, 255))
            draw.ellipse([146, 100, 176, 130], fill=(15, 15, 20, 255))
            draw.ellipse([164, 104, 172, 112], fill=(255, 255, 255, 255))
            draw.arc([105, 125, 151, 155], start=0, end=180, fill=(15, 15, 20, 255), width=5)
            draw.polygon([(190, 50), (195, 60), (205, 65), (195, 70), (190, 80), (185, 70), (175, 65), (185, 60)], fill=(255, 255, 255, 255))
            img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            
        vbs_path = os.path.join(os.path.dirname(__file__), "create_shortcut.vbs")
        if os.path.exists(vbs_path):
            subprocess.run(["cscript.exe", "//NoLogo", vbs_path], capture_output=True)
    except Exception as e:
        print(f"Error in automatic icon/shortcut generator: {e}")

generate_icon_and_shortcut()

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title=STREAMLIT_PAGE_TITLE,
    page_icon=STREAMLIT_PAGE_ICON,
    layout=STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "bot_ready" not in st.session_state:
    st.session_state.bot_ready = False
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "llm" not in st.session_state:
    st.session_state.llm = None
if "follow_ups" not in st.session_state:
    st.session_state.follow_ups = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "temp_files" not in st.session_state:
    st.session_state.temp_files = []
if "memory_vault" not in st.session_state:
    st.session_state.memory_vault = [
        "Prefers direct structured policies",
        "Exploring employee insurance plans",
    ]
if "duplicate_alert" not in st.session_state:
    st.session_state.duplicate_alert = None

# New cockpit states
if "specialist_persona" not in st.session_state:
    st.session_state.specialist_persona = "Nexus Guide"
if "excluded_docs" not in st.session_state:
    st.session_state.excluded_docs = []
if "last_retrieved_docs" not in st.session_state:
    st.session_state.last_retrieved_docs = []
if "last_raw_chroma_docs" not in st.session_state:
    st.session_state.last_raw_chroma_docs = []
if "selected_workspace" not in st.session_state:
    st.session_state.selected_workspace = "Nexus Onboarding Vault"

# Accessibility States
if "dyslexia_mode" not in st.session_state:
    st.session_state.dyslexia_mode = False
if "high_contrast_mode" not in st.session_state:
    st.session_state.high_contrast_mode = False
if "font_scale" not in st.session_state:
    st.session_state.font_scale = 1.0
if "reduced_motion" not in st.session_state:
    st.session_state.reduced_motion = False


# ============================================================================
# INITIALIZATION & MODEL BACKGROUND PRELOADING
# ============================================================================
@st.cache_resource(show_spinner=False)
def init_vector_store():
    return load_vector_store()

@st.cache_resource(show_spinner=False)
def init_llm(temperature=0.1, num_predict=512):
    return get_llm(temperature=temperature, num_predict=num_predict)

def ensure_bot_ready(temperature=0.1, max_tokens=512):
    try:
        if not st.session_state.vector_store:
            st.session_state.vector_store = init_vector_store()
        st.session_state.llm = init_llm(temperature=temperature, num_predict=max_tokens)
        st.session_state.bot_ready = True
    except FileNotFoundError:
        st.error("❌ **Vector store not found!** Run `python ingest.py` first.")
        st.stop()
    except Exception as e:
        st.error(f"❌ **Error initializing local AI models:** {e}")
        st.stop()

# Eagerly preload vector store and CrossEncoder reranker
try:
    if not st.session_state.vector_store:
        st.session_state.vector_store = init_vector_store()
    
    # Warm up CrossEncoder reranker model asynchronously to avoid blocking UI load
    def preload_reranker():
        try:
            from src.embeddings import get_reranker
            get_reranker()
        except Exception:
            pass
    threading.Thread(target=preload_reranker, daemon=True).start()
except Exception:
    pass


# ============================================================================
# AUDIT LOGGING
# ============================================================================
AUDIT_LOG_FILE = Path("audit_log.csv")

def write_audit_log(username, query, answer, threshold, temperature, chroma_score, rerank_score, rating=0, comment=""):
    file_exists = AUDIT_LOG_FILE.exists()
    try:
        import csv
        with open(AUDIT_LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Timestamp", "User", "Query", "Answer", 
                    "Threshold", "Temperature", "Best_Chroma_Score", 
                    "Best_Rerank_Score", "Feedback_Rating", "Comment"
                ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                username, query, answer, threshold, temperature,
                chroma_score, rerank_score, rating, comment
            ])
    except Exception as e:
        print(f"Error writing audit log: {e}")

def update_last_audit_log_feedback(rating_val):
    if not AUDIT_LOG_FILE.exists():
        return
    try:
        import pandas as pd
        df = pd.read_csv(AUDIT_LOG_FILE)
        if not df.empty:
            df.iloc[-1, df.columns.get_loc("Feedback_Rating")] = rating_val
            df.to_csv(AUDIT_LOG_FILE, index=False)
    except Exception as e:
        print(f"Error updating feedback in audit log: {e}")


# ============================================================================
# DYNAMIC WORKSPACE THEME SYSTEM (HSL CSS INJECTIONS)
# ============================================================================
workspace = st.session_state.get("selected_workspace", "Nexus Onboarding Vault")

if workspace == "Nexus Onboarding Vault":
    primary_hsl = "210, 100%, 50%"  # iOS Blue
    secondary_hsl = "240, 70%, 60%" # iOS Indigo
    ambient_glow = "rgba(0, 122, 255, 0.15)"
    accent_gradient = "linear-gradient(135deg, #007AFF 0%, #5856D6 100%)"
    user_bubble_gradient = "linear-gradient(135deg, #007AFF 0%, #5856D6 100%)"
    bg_mesh = """
        radial-gradient(ellipse at 15% 10%, rgba(0, 122, 255, 0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 85% 90%, rgba(88, 86, 214, 0.06) 0%, transparent 60%)
    """
elif workspace == "IT Support Desk":
    primary_hsl = "120, 60%, 49%"  # iOS Green
    secondary_hsl = "180, 85%, 40%" # iOS Teal
    ambient_glow = "rgba(52, 199, 89, 0.15)"
    accent_gradient = "linear-gradient(135deg, #34C759 0%, #30B0C7 100%)"
    user_bubble_gradient = "linear-gradient(135deg, #34C759 0%, #30B0C7 100%)"
    bg_mesh = """
        radial-gradient(ellipse at 15% 10%, rgba(52, 199, 89, 0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 85% 90%, rgba(48, 176, 199, 0.06) 0%, transparent 60%)
    """
else: # Benefits Desk
    primary_hsl = "275, 75%, 55%"  # iOS Purple
    secondary_hsl = "300, 70%, 55%" # iOS Pink
    ambient_glow = "rgba(175, 82, 222, 0.15)"
    accent_gradient = "linear-gradient(135deg, #AF52DE 0%, #FF2D55 100%)"
    user_bubble_gradient = "linear-gradient(135deg, #AF52DE 0%, #FF2D55 100%)"
    bg_mesh = """
        radial-gradient(ellipse at 15% 10%, rgba(175, 82, 222, 0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 85% 90%, rgba(255, 45, 85, 0.06) 0%, transparent 60%)
    """

SVG_LOGO = """
<svg viewBox="0 0 40 40" class="bot-avatar-svg" style="width: 100%; height: 100%; max-width: 44px; max-height: 44px; display: inline-block; vertical-align: middle;" aria-hidden="true">
    <defs>
      <linearGradient id="app-grad-rail" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#e8a838"/>
        <stop offset="100%" style="stop-color:#c4873a"/>
      </linearGradient>
    </defs>
    <ellipse cx="20" cy="36.5" rx="14" ry="1.2" fill="rgba(0,0,0,0.4)"/>
    <g class="circle-back">
      <circle cx="20" cy="20" r="16" fill="#8c5819" stroke="#663e0e" stroke-width="1.2" transform="translate(0, 1.8)"/>
    </g>
    <g class="circle-front">
      <circle cx="20" cy="20" r="16" fill="url(#app-grad-rail)" stroke="#f5c842" stroke-width="1.2"/>
      <path d="M 8,12 A 16,16 0 0,1 32,12" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="0.8" stroke-linecap="round"/>
      <g class="geodesic-sphere"></g>
      <circle cx="15" cy="17" r="2.2" fill="#0f0d0a" class="avatar-eye avatar-eye-blink" style="transform-origin:15px 17px"/>
      <circle cx="25" cy="17" r="2.2" fill="#0f0d0a" class="avatar-eye avatar-eye-blink" style="transform-origin:25px 17px"/>
      <path d="M14 25 Q20 30 26 25" stroke="#0f0d0a" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    </g>
</svg>
"""

st.markdown(f"""
<style>
    /* Google Fonts Import for Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono&display=swap');

    :root {{
        --obsidian-bg: #202336;
        --slate-card: rgba(15, 18, 32, 0.52);
        --accent-primary: hsl({primary_hsl});
        --accent-secondary: hsl({secondary_hsl});
        --accent-glow: {ambient_glow};
        --concierge-white: #FFFFFF;
        --concierge-silver: rgba(255, 255, 255, 0.75);
        --bronze-gold: #e8a838;
        --bg-deep: rgba(5, 5, 8, 0.50);
        --glass-bg: rgba(15, 18, 32, 0.65);
        --glass-blur: 35px;
        --glass-border: rgba(255, 255, 255, 0.12);
        --glass-border-top: rgba(255, 255, 255, 0.32);
        --glow-gold: 0 4px 20px rgba(0, 0, 0, 0.2);
        --glow-indigo: 0 4px 12px rgba(0, 122, 255, 0.15);
        --success: #34C759;
        --error: #FF3B30;
    }}

    @media (prefers-color-scheme: light) {{
        :root {{
            --obsidian-bg: #f5f5f7;
            --slate-card: rgba(255, 255, 255, 0.68);
            --accent-glow: rgba(0, 122, 255, 0.1);
            --concierge-white: #1c1c1e;
            --concierge-silver: #2c2c2e;
            --bronze-gold: #b47b2c;
            --bg-deep: rgba(0, 0, 0, 0.06);
            --glass-bg: rgba(255, 255, 255, 0.65);
            --glass-border: rgba(0, 0, 0, 0.12);
            --glass-border-top: rgba(255, 255, 255, 0.98);
            --glow-gold: 0 4px 20px rgba(0, 0, 0, 0.04);
            --glow-indigo: 0 4px 12px rgba(0, 122, 255, 0.06);
        }}
        /* User message text color fix */
        div[data-testid="stChatMessage"][class*="user"],
        div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"] {
            color: #FFFFFF !important;
            background: {user_bubble_gradient} !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.35) !important;
        }
        div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"] p,
        div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"] li,
        div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"] span,
        div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"] strong {
            color: #FFFFFF !important;
        }
        /* Form background & border override */
        div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.55) !important;
            border: 1px solid rgba(0, 0, 0, 0.06) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06), var(--glow-indigo) !important;
        }}
        /* Caption text color override */
        .stCaption {{
            color: var(--concierge-silver) !important;
        }}
        /* Card header bottom border override */
        .royal-card h4 {{
            border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
        }}
        .stApp {{
            background: {bg_mesh}, linear-gradient(135deg, #e0f2fe, #f3e8ff, #fce7f3, #f5f3ff, #e0f2fe) !important;
            background-size: 400% 400% !important;
            animation: ios-wallpaper-flow 25s ease infinite !important;
        }}
        /* Input overrides for light mode */
        .stTextInput input, .stTextArea textarea, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
            background-color: rgba(255, 255, 255, 0.7) !important;
            border-bottom: 2px solid rgba(0, 0, 0, 0.06) !important;
            color: #1D1D1F !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus, [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{
            background-color: #FFFFFF !important;
            border-bottom: 2px solid var(--accent-primary) !important;
        }}
        div[data-testid="stSidebar"] {{
            background-color: rgba(255, 255, 255, 0.5) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
        }}
        div[data-testid="stSidebar"] * {{
            color: #1D1D1F !important;
        }}
        /* Checkbox labels in light mode */
        .stCheckbox label, .stCheckbox span, [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p {{
            color: #1D1D1F !important;
        }}
        /* Tab list override */
        div[data-testid="stTabBar"], [class*="stTabBar"], [role="tablist"] {{
            background: rgba(255, 255, 255, 0.6) !important;
            border: 1px solid rgba(0, 0, 0, 0.06) !important;
        }}
        button[data-baseweb="tab"] {{
            color: #424245 !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"], [role="tab"][aria-selected="true"], [role="tab"][class*="active"] {{
            color: var(--accent-primary) !important;
            font-weight: 600 !important;
        }}
        /* Selectbox and dropdowns in light mode */
        div[data-baseweb="popover"], div[data-baseweb="listbox"], ul[role="listbox"] {{
            background-color: #FFFFFF !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }}
        div[data-baseweb="popover"] [data-baseweb="menu-item"], [role="option"], li[role="option"] {{
            color: #1D1D1F !important;
            background-color: transparent !important;
        }}
        div[data-baseweb="popover"] [data-baseweb="menu-item"]:hover, [role="option"]:hover, li[role="option"]:hover {{
            background-color: rgba(0, 122, 255, 0.08) !important;
            color: var(--accent-primary) !important;
        }}
        div[data-baseweb="select"] div {{
            color: #1D1D1F !important;
        }}
        /* Expanders */
        [data-testid="stExpander"] details > summary {{
            color: #1D1D1F !important;
        }}
        /* Debug Trace */
        .citation-bubble-card {{
            background: rgba(255, 255, 255, 0.85) !important;
            border: 1px solid rgba(0, 0, 0, 0.06) !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05) !important;
        }}
        /* Assistant message capsule */
        div[data-testid="stChatMessage"][class*="assistant"] {{
            background: rgba(255, 255, 255, 0.6) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.5) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.5) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.5) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06) !important;
        }}
    }}

    @keyframes ios-wallpaper-flow {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    /* Global styling */
    .stApp {{
        background: {bg_mesh}, linear-gradient(135deg, #202336, #2d3150, #22253f, #3b4060, #202336) !important;
        background-size: 400% 400% !important;
        animation: ios-wallpaper-flow 25s ease infinite !important;
        color: var(--concierge-white) !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif !important;
    }}

    /* Typography */
    h1, h2, h3, h4, .logo-title, .concierge-card-title, button, label, span:not(.message-content-serif) {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", sans-serif !important;
        letter-spacing: -0.02em !important;
    }}
    
    p, .stTextInput input, .stTextArea textarea, select {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif !important;
    }}

    /* Assistant chat font override to Inter */
    div[data-testid="stChatMessage"][class*="assistant"] p,
    div[data-testid="stChatMessage"][class*="assistant"] li,
    div[data-testid="stChatMessage"][class*="assistant"] ul,
    div[data-testid="stChatMessage"][class*="assistant"] ol {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif !important;
        font-size: 0.96rem !important;
        line-height: 1.6 !important;
    }}
    
    /* Code styling */
    code, .source-ref {{
        font-family: 'JetBrains Mono', monospace !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 4px;
        padding: 0.15rem 0.4rem;
        color: var(--accent-primary) !important;
    }}

    /* Scrollbars */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--obsidian-bg);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--slate-card);
        border: 2px solid var(--obsidian-bg);
        border-radius: 99px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--accent-primary);
    }}

    /* Sidebar */
    div[data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 15, 0.5) !important;
        backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }}

    /* Card styling */
    .royal-card {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        border: 1px solid var(--glass-border) !important;
        border-top: 1px solid var(--glass-border-top) !important;
        border-radius: 14px !important;
        padding: 1.3rem !important;
        margin-bottom: 1.2rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    .royal-card:hover {{
        transform: translateY(-2px) !important;
        border-color: var(--accent-primary) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25), var(--glow-indigo) !important;
    }}
    .royal-card h4 {{
        margin-top: 0;
        color: var(--accent-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", sans-serif !important;
        font-size: 1.05rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.4rem;
        margin-bottom: 0.8rem;
    }}

    /* Tech Spinner node */
    .tech-logo-node {{
        width: 80px;
        height: 80px;
        margin: 0 auto 1.5rem;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.03) 0%, transparent 70%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px dashed rgba(255, 255, 255, 0.15);
        animation: spinNode 12s linear infinite;
        position: relative;
    }}
    @keyframes spinNode {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    .tech-logo-inner {{
        font-size: 2.20rem;
        animation: pulseLogo 3s ease-in-out infinite alternate;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    @keyframes pulseLogo {{
        from {{ transform: scale(0.93); opacity: 0.85; filter: drop-shadow(0 0 2px rgba(255, 255, 255, 0.15)); }}
        to {{ transform: scale(1.07); opacity: 1; filter: drop-shadow(0 0 12px var(--accent-primary)); }}
    }}
    
    /* 3D stacked circle style classes */
    .bot-avatar-svg {{
        transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.3s ease;
        transform-style: preserve-3d;
        perspective: 1000px;
    }}
    .bot-avatar-svg:hover {{
        transform: scale(1.08) rotateY(10deg) rotateX(-5deg);
        filter: drop-shadow(0 6px 12px rgba(232, 168, 56, 0.25)) !important;
    }}
    .circle-front, .circle-back {{
        transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    .bot-avatar-svg:hover .circle-front {{
        transform: translate(-1px, -1px);
    }}
    .bot-avatar-svg:hover .circle-back {{
        transform: translate(1px, 1.5px);
    }}
    .avatar-eye-blink {{
        animation: blink 4s ease-in-out infinite;
    }}
    @keyframes blink {{
        0%, 90%, 100% {{ transform: scaleY(1); }}
        95% {{ transform: scaleY(0.1); }}
    }}

    /* Header styling with premium glassmorphism */
    .royal-header {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        border: 1px solid var(--glass-border) !important;
        border-top: 1px solid var(--glass-border-top) !important;
        border-radius: 14px !important;
        padding: 1.2rem 2rem !important;
        margin-bottom: 2rem !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
    }}

    /* Status dot */
    .pulse-dot {{
        width: 8px;
        height: 8px;
        background-color: var(--success);
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: statusPulse 2s infinite;
        vertical-align: middle;
        margin-right: 0.35rem;
    }}
    @keyframes statusPulse {{
        0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
        70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
        100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}

    /* Confidence bar */
    .confidence-meter-container {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        background: rgba(255, 255, 255, 0.02);
        padding: 0.35rem 0.9rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .confidence-bar-outer {{
        width: 100px;
        height: 6px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 99px;
        overflow: hidden;
        position: relative;
    }}
    .confidence-bar-inner {{
        height: 100%;
        background: {accent_gradient};
        border-radius: 99px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    /* Message Meta Info */
    .bubble-meta {{
        font-size: 0.72rem;
        opacity: 0.65;
        margin-top: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.8rem;
    }}

    /* User Message - colourful gradient bubble */
    div[data-testid="stChatMessage"][class*="user"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"] {
        background: {user_bubble_gradient} !important;
        border-radius: 24px 24px 4px 24px !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25), var(--glow-indigo) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.35) !important;
        padding: 1.1rem 1.4rem !important;
        transition: all 0.3s ease !important;
        display: inline-block !important;
        width: auto !important;
        max-width: 100% !important;
    }
    div[data-testid="stChatMessage"][class*="user"] [data-testid="stChatMessageContent"]:hover {
        transform: scale(1.01);
    }

    /* Assistant Message - Glassmorphic */
    div[data-testid="stChatMessage"][class*="assistant"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    div[data-testid="stChatMessage"][class*="assistant"] [data-testid="stChatMessageContent"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        border-left: 4px solid var(--accent-primary) !important;
        border-radius: 24px 24px 24px 4px !important;
        color: var(--concierge-white) !important;
        border-top: 1px solid var(--glass-border-top) !important;
        border-right: 1px solid var(--glass-border) !important;
        border-bottom: 1px solid var(--glass-border) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
        padding: 1.1rem 1.4rem !important;
        transition: all 0.3s ease !important;
        display: inline-block !important;
        width: auto !important;
        max-width: 100% !important;
    }
    div[data-testid="stChatMessage"][class*="assistant"] [data-testid="stChatMessageContent"]:hover {
        transform: scale(1.01);
    }

    /* Citation Hover Slide In */
    .citation-wrapper {{
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: rotateX(-15deg);
        transform-origin: top;
        transition: all 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}
    div[data-testid="stChatMessage"][class*="assistant"]:hover .citation-wrapper {{
        max-height: 800px;
        opacity: 1;
        transform: rotateX(0deg);
        margin-top: 0.9rem;
    }}
    .citation-bubble-card {{
        background: rgba(7, 9, 19, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-left: 3px solid var(--accent-primary) !important;
        border-radius: 12px !important;
        padding: 0.9rem 1.1rem !important;
        margin-bottom: 0.6rem !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
    }}

    /* Summarize & Translate toolbars */
    .tool-bar {{
        display: flex;
        gap: 0.5rem;
        margin-top: 0.6rem;
        align-items: center;
    }}
    .summarize-btn-container .stButton > button {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        color: var(--accent-primary) !important;
        font-size: 0.72rem !important;
        padding: 0.2rem 0.6rem !important;
        border-radius: 8px !important;
    }}
    .summarize-btn-container .stButton > button:hover {{
        background: var(--accent-gradient) !important;
        color: #070913 !important;
        border-color: var(--accent-primary) !important;
        box-shadow: var(--glow-gold) !important;
    }}

    /* Tab Layout */
    div[data-testid="stTabBar"], [class*="stTabBar"], [role="tablist"] {{
        background: rgba(7, 9, 19, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 30px !important;
        padding: 0.25rem !important;
        margin-bottom: 1.5rem !important;
        display: flex !important;
        justify-content: space-around !important;
    }}
    button[data-baseweb="tab"], [role="tab"] {{
        color: var(--concierge-silver) !important;
        font-weight: 500 !important;
        background: transparent !important;
        border: none !important;
        padding: 0.45rem 1.2rem !important;
        border-radius: 20px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-size: 0.85rem !important;
        flex-grow: 1 !important;
        text-align: center !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"], [role="tab"][aria-selected="true"], [role="tab"][class*="active"] {{
        color: #070913 !important;
        background: var(--accent-gradient) !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px var(--accent-glow) !important;
    }}

    /* Inputs borderless bottom line highlight */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {{
        border: none !important;
        background-color: transparent !important;
    }}
    .stTextInput input, .stTextArea textarea, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
        background-color: rgba(7, 9, 19, 0.6) !important;
        border: none !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 0px !important;
        color: var(--concierge-white) !important;
        transition: all 0.3s ease !important;
        padding: 0.6rem 0.4rem !important;
        box-shadow: none !important;
        width: 100% !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus, [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{
        background-color: rgba(7, 9, 19, 0.8) !important;
        border-bottom: 2px solid var(--accent-primary) !important;
        box-shadow: none !important;
    }}

    /* Buttons */
    .stButton>button {{
        border-radius: 12px !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #0F1224, #1B203E) !important;
        color: var(--accent-primary) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25) !important;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        padding: 0.5rem 1rem !important;
    }}
    .stButton>button:hover {{
        background: var(--accent-gradient) !important;
        color: #070913 !important;
        border-color: var(--accent-primary) !important;
        box-shadow: 0 8px 25px var(--accent-glow) !important;
        transform: translateY(-2px) scale(1.02);
    }}
    .stButton>button:active {{
        transform: translateY(1px) scale(0.97);
    }}

    /* Custom CSS chevron arrow for st.expander */
    [data-testid="stExpander"] details > summary svg,
    [data-testid="stExpander"] details > summary span[data-testid^="stIcon"],
    [data-testid="stExpander"] details > summary span[class*="Icon"],
    [data-testid="stExpander"] details > summary span[class*="material"] {{
        display: none !important;
    }}
    [data-testid="stExpander"] details > summary {{
        padding-left: 2.2rem !important;
        position: relative !important;
        background: transparent !important;
        color: var(--concierge-white) !important;
        font-weight: 500 !important;
    }}
    [data-testid="stExpander"] details > summary::before {{
        content: '▶' !important;
        position: absolute !important;
        left: 0.9rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 0.75rem !important;
        color: var(--accent-primary) !important;
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: inline-block !important;
    }}
    [data-testid="stExpander"] details[open] > summary::before {{
        transform: translateY(-50%) rotate(90deg) !important;
    }}

    /* Form boundary rules */
    div[data-testid="stForm"] {{
        background: var(--slate-card) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 24px !important;
        padding: 1.8rem !important;
        box-shadow: var(--glow-gold) !important;
    }}

    /* Chat Input Floating Box */
    div[data-testid="stChatInput"] {{
        background-color: var(--glass-bg) !important;
        backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(190%) !important;
        border: 1px solid var(--glass-border) !important;
        border-top: 1px solid var(--glass-border-top) !important;
        border-radius: 24px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25) !important;
        padding: 0.35rem 0.8rem !important;
        position: relative !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), var(--glow-indigo) !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        background: transparent !important;
        color: var(--concierge-white) !important;
        font-size: 0.95rem !important;
        border: none !important;
        box-shadow: none !important;
        resize: none !important;
    }}

    .custom-input-tool-btn {{
        background: transparent !important;
        border: none !important;
        font-size: 1.25rem !important;
        cursor: pointer !important;
        padding: 0.2rem !important;
        margin: 0 0.35rem !important;
        opacity: 0.65 !important;
        transition: all 0.2s ease !important;
        vertical-align: middle;
        display: inline-block;
        color: var(--accent-primary) !important;
    }}
    .custom-input-tool-btn:hover {{
        opacity: 1 !important;
        transform: scale(1.15) !important;
    }}
    .custom-input-tool-btn.recording {{
        color: var(--error) !important;
        animation: recordingFlash 1s infinite alternate !important;
        opacity: 1 !important;
    }}
    @keyframes recordingFlash {{
        from {{ transform: scale(1); filter: drop-shadow(0 0 2px var(--error)); }}
        to {{ transform: scale(1.2); filter: drop-shadow(0 0 10px var(--error)); }}
    }}

    .custom-char-counter {{
        position: absolute !important;
        right: 4.8rem !important;
        bottom: -1.3rem !important;
        font-size: 0.72rem !important;
        color: var(--concierge-silver) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* Voice Waveform */
    .voice-waveform {{
        display: none;
        align-items: center;
        justify-content: center;
        gap: 4px;
        padding: 0.5rem 1rem !important;
        margin-bottom: 0.6rem !important;
        background: rgba(15, 18, 36, 0.92) !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 12px !important;
        box-shadow: var(--glow-gold) !important;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }}
    .wave-bar {{
        width: 3px;
        height: 10px;
        background-color: var(--accent-primary);
        border-radius: 2px;
        animation: waveBounce 0.8s ease-in-out infinite alternate;
    }}
    .wave-bar:nth-child(2) {{ animation-delay: 0.15s; height: 16px; }}
    .wave-bar:nth-child(3) {{ animation-delay: 0.3s; height: 22px; }}
    .wave-bar:nth-child(4) {{ animation-delay: 0.45s; height: 14px; }}
    .wave-bar:nth-child(5) {{ animation-delay: 0.6s; height: 8px; }}
    @keyframes waveBounce {{
        from {{ transform: scaleY(0.4); }}
        to {{ transform: scaleY(1.3); }}
    }}

    /* Emoji Picker */
    .custom-emoji-picker {{
        display: none;
        grid-template-columns: repeat(6, 1fr);
        gap: 8px;
        padding: 10px !important;
        background: var(--slate-card) !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 12px !important;
        position: absolute !important;
        bottom: 3.8rem !important;
        right: 1.5rem !important;
        z-index: 1000 !important;
        box-shadow: var(--glow-gold) !important;
        width: 220px !important;
    }}
    .custom-emoji-picker span {{
        font-size: 1.25rem !important;
        text-align: center !important;
        transition: transform 0.15s ease !important;
        user-select: none;
    }}
    .custom-emoji-picker span:hover {{
        transform: scale(1.25) !important;
    }}

    /* Suggestions */
    .suggestion-pills-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.8rem;
    }}
    .suggestion-pill {{
        background: rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: var(--accent-primary) !important;
        border-radius: 99px !important;
        font-size: 0.78rem !important;
        padding: 0.35rem 0.9rem !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    .suggestion-pill:hover {{
        background: var(--accent-gradient) !important;
        border-color: var(--accent-primary) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), var(--glow-indigo) !important;
        transform: translateY(-1px) scale(1.02);
    }}

    /* Duplicate query banner */
    .duplicate-alert-banner {{
        background: linear-gradient(90deg, rgba(255, 255, 255, 0.02), rgba(15, 18, 36, 0.9)) !important;
        border-left: 4px solid var(--accent-primary) !important;
        border-radius: 12px !important;
        padding: 0.8rem 1.2rem !important;
        margin-bottom: 1rem !important;
        border-top: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important;
    }}

    [data-testid="stHeaderDeployButton"] {{ display: none !important; }}

    /* Document Graph Match Bar */
    .rag-match-bar-outer {{
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 99px;
        overflow: hidden;
        margin-top: 4px;
        position: relative;
    }}
    .rag-match-bar-inner {{
        height: 100%;
        border-radius: 99px;
    }}
    .rag-match-bar-green {{
        background: linear-gradient(90deg, #10B981, #34D399);
    }}
    .rag-match-bar-amber {{
        background: linear-gradient(90deg, #F59E0B, #FBBF24);
    }}
    .rag-match-bar-rose {{
        background: linear-gradient(90deg, #EF4444, #F87171);
    }}

    /* RAG Metrics latency badge */
    .latency-badge {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        color: var(--concierge-silver);
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 0.68rem;
        font-family: 'JetBrains Mono', monospace;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    .latency-badge-fast {{
        border-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
    }}
    .latency-badge-normal {{
        border-color: rgba(255, 184, 0, 0.2);
        color: #FFB800;
    }}

    /* Persona Selector Cards */
    .persona-card {{
        border: 1.5px solid rgba(255, 255, 255, 0.04);
        background: rgba(255, 255, 255, 0.01);
        border-radius: 14px;
        padding: 0.8rem;
        text-align: center;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .persona-card:hover {{
        border-color: var(--accent-primary);
        box-shadow: 0 4px 12px var(--accent-glow);
    }}
    .persona-card-active {{
        background: rgba(255, 255, 255, 0.04) !important;
        border-color: var(--accent-primary) !important;
        box-shadow: var(--glow-gold) !important;
    }}

    /* Responsive Floating Chat Input for AI Cockpit Grid */
    @media (min-width: 992px) {{
        div[data-testid="stChatInput"] {{
            max-width: 53% !important;
            position: fixed !important;
            bottom: 1.5rem !important;
            left: 21% !important;
            z-index: 999 !important;
        }}
    }}
    div[data-testid="stChatMessageContainer"] {{
        padding-bottom: 120px !important;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DYNAMIC ISLAND DOM INJECTION
# ============================================================================
dynamic_island_injection_js = f"""
<script>
(function() {{
    const doc = window.parent.document || document;
    
    // Set reduced motion state on parent window
    window.parent.streamlitReducedMotion = {str(st.session_state.reduced_motion).lower()};
    
    if (!doc.getElementById('dynamic-island-container')) {{
        // Create CSS style element
        const style = doc.createElement('style');
        style.innerHTML = `
            #dynamic-island-container {{
              position: fixed;
              top: 14px;
              left: 50%;
              transform: translateX(-50%);
              z-index: 10000;
              pointer-events: none;
              display: flex;
              justify-content: center;
            }}
            #dynamic-island {{
              background: #000000;
              color: #FFFFFF;
              border-radius: 20px;
              padding: 0 16px;
              height: 32px;
              min-width: 130px;
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 8px;
              box-shadow: 0 8px 30px rgba(0,0,0,0.6);
              transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
              font-size: 11px;
              font-weight: 600;
              overflow: hidden;
              border: 1px solid rgba(255, 255, 255, 0.12);
              font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
              pointer-events: auto;
            }}
            #dynamic-island.speaking {{
              height: 42px;
              min-width: 260px;
              border-radius: 21px;
              background: #09090b;
              border-color: rgba(0, 122, 255, 0.35);
              box-shadow: 0 8px 30px rgba(0, 122, 255, 0.15);
            }}
            #dynamic-island.thinking {{
              height: 42px;
              min-width: 220px;
              border-radius: 21px;
              background: #09090b;
              border-color: rgba(232, 168, 56, 0.35);
              box-shadow: 0 8px 30px rgba(232, 168, 56, 0.15);
            }}
            #dynamic-island.listening {{
              height: 42px;
              min-width: 200px;
              border-radius: 21px;
              background: #09090b;
              border-color: rgba(255, 59, 48, 0.35);
              box-shadow: 0 8px 30px rgba(255, 59, 48, 0.15);
            }}
            #dynamic-island.achievement {{
              height: 48px;
              min-width: 290px;
              border-radius: 24px;
              background: #000000;
              border-color: #f5c842;
              box-shadow: 0 8px 30px rgba(245, 200, 66, 0.25);
            }}
            .di-content {{
              display: flex;
              align-items: center;
              gap: 8px;
              white-space: nowrap;
              animation: di-fade-in 0.25s ease-out;
            }}
            @keyframes di-fade-in {{
              from {{ opacity: 0; transform: scale(0.95); }}
              to {{ opacity: 1; transform: scale(1); }}
            }}
            .di-dot {{
              width: 7px; height: 7px;
              border-radius: 50%;
              background: #34C759;
            }}
            .di-dot.listening-dot {{
              background: #FF3B30;
              animation: di-pulse-mic 1s infinite alternate;
            }}
            @keyframes di-pulse-mic {{
              from {{ opacity: 0.4; transform: scale(0.8); }}
              to {{ opacity: 1; transform: scale(1.1); }}
            }}
            .di-waveform {{
              display: flex;
              gap: 2.5px;
              align-items: center;
            }}
            .di-wave-bar {{
              width: 2px;
              height: 6px;
              background-color: #007AFF;
              border-radius: 1px;
              animation: di-bounce 0.6s ease-in-out infinite alternate;
            }}
            .di-wave-bar:nth-child(2) {{ animation-delay: 0.1s; height: 12px; }}
            .di-wave-bar:nth-child(3) {{ animation-delay: 0.2s; height: 8px; }}
            .di-wave-bar:nth-child(4) {{ animation-delay: 0.3s; height: 14px; }}
            .di-wave-bar:nth-child(5) {{ animation-delay: 0.4s; height: 6px; }}
            @keyframes di-bounce {{
              from {{ transform: scaleY(0.4); }}
              to {{ transform: scaleY(1.3); }}
            }}
            @keyframes di-spin {{
              from {{ transform: rotate(0deg); }}
              to {{ transform: rotate(360deg); }}
            }}
            @keyframes di-pulse-gold {{
              from {{ filter: drop-shadow(0 0 2px rgba(245, 200, 66, 0.4)); }}
              to {{ filter: drop-shadow(0 0 8px rgba(245, 200, 66, 0.9)); }}
            }}
        `;
        doc.head.appendChild(style);

        // Create Container
        const container = doc.createElement('div');
        container.id = 'dynamic-island-container';
        container.innerHTML = `
            <div id="dynamic-island">
              <div class="di-content">
                <div class="di-dot"></div>
                <span>OnboardBot</span>
              </div>
            </div>
        `;
        doc.body.appendChild(container);
    }}

    // Expose updateDynamicIsland globally on parent window
    window.parent.updateDynamicIsland = function(state, text, duration = null) {{
        if (window.parent.streamlitReducedMotion) {{ return; }}
        const island = doc.getElementById('dynamic-island');
        if (!island) {{ return; }}
        
        island.className = '';
        island.classList.add(state);
        
        let html = '';
        if (state === 'thinking') {{
            html = '<div class="di-content"><span style="font-size: 13px; animation: di-spin 2s linear infinite; display: inline-block;">🔍</span><span>' + (text || 'Thinking...') + '</span></div>';
        }} else if (state === 'listening') {{
            html = '<div class="di-content"><div class="di-dot listening-dot"></div><span>' + (text || 'Listening...') + '</span></div>';
        }} else if (state === 'speaking') {{
            html = '<div class="di-content"><div class="di-waveform"><div class="di-wave-bar"></div><div class="di-wave-bar"></div><div class="di-wave-bar"></div><div class="di-wave-bar"></div><div class="di-wave-bar"></div></div><span>' + (text || 'Reading Aloud...') + '</span></div>';
        }} else if (state === 'achievement') {{
            html = '<div class="di-content" style="color: #f5c842; font-weight: bold; animation: di-pulse-gold 1.5s infinite alternate;"><span>🏆</span><span>' + (text || 'Achievement Unlocked!') + '</span></div>';
        }} else {{ // default / idle
            html = '<div class="di-content"><div class="di-dot" style="background: #34C759;"></div><span>OnboardBot</span></div>';
        }}
        
        island.innerHTML = html;
        
        if (duration) {{
            if (window.parent.diTimeout) {{ clearTimeout(window.parent.diTimeout); }}
            window.parent.diTimeout = setTimeout(() => {{
                if (island.classList.contains(state)) {{
                    window.parent.updateDynamicIsland('idle');
                }}
            }}, duration);
        }}
    }};
    
    // Set to idle initially
    window.parent.updateDynamicIsland('idle');
}})();
</script>
"""
st.markdown(dynamic_island_injection_js, unsafe_allow_html=True)


# ============================================================================
# ACCESSIBILITY STYLE INJECTIONS (WCAG & Accessibility)
# ============================================================================
accessibility_css = "<style>"
if st.session_state.high_contrast_mode:
    accessibility_css += """
    .stApp {
        background-color: #000000 !important;
        background-image: none !important;
        color: #ffffff !important;
    }
    .royal-card, .royal-header, div[data-testid="stChatMessage"] {
        background-color: #000000 !important;
        border: 2px solid #ffffff !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }
    * {
        border-color: #ffffff !important;
    }
    p, span, label, textarea, input, h1, h2, h3, a {
        color: #ffffff !important;
    }
    """

if st.session_state.dyslexia_mode:
    accessibility_css += """
    body, p, button, input, textarea, label, span, div, h1, h2, h3, h4 {
        font-family: 'Comic Sans MS', 'Chalkboard SE', 'Comic Neue', sans-serif !important;
        letter-spacing: 0.05em !important;
        line-height: 1.85 !important;
    }
    """

if st.session_state.font_scale != 1.0:
    accessibility_css += f"""
    html, body, p, span, label, textarea, input, button, h4, code {{
        font-size: {st.session_state.font_scale * 0.95}rem !important;
    }}
    h1 {{ font-size: {st.session_state.font_scale * 2.2}rem !important; }}
    h2 {{ font-size: {st.session_state.font_scale * 1.8}rem !important; }}
    h3 {{ font-size: {st.session_state.font_scale * 1.4}rem !important; }}
    """

if st.session_state.reduced_motion:
    accessibility_css += """
    * {
        animation: none !important;
        transition: none !important;
    }
    """
accessibility_css += "</style>"
st.markdown(accessibility_css, unsafe_allow_html=True)


# ============================================================================
# LOGIN PORTAL (Obsidian Shimmer Card - No Crowns)
# ============================================================================
if not st.session_state.logged_in:
    # Inject page centering and no-scroll layout CSS
    st.markdown("""
    <style>
        /* Force no-scroll vertical and horizontal centering for login only */
        html, body, [data-testid="stAppViewContainer"] {
            height: 100vh !important;
            overflow: hidden !important;
            background: linear-gradient(135deg, #0a0a0c, #1a1a24, #0d0f1a, #161823, #0a0a0c) !important;
            background-size: 400% 400% !important;
            animation: ios-wallpaper-flow 25s ease infinite !important;
        }
        
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        div.block-container {
            max-width: 440px !important;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            margin: auto !important;
            height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            box-sizing: border-box !important;
        }
        
        .tech-logo-node {
            width: 60px !important;
            height: 60px !important;
            margin: 0 auto 0.6rem !important;
            border: 1.5px dashed var(--accent-primary) !important;
            animation: spinNode 12s linear infinite;
        }
        .tech-logo-inner {
            font-size: 1.6rem !important;
        }
        
        div[data-testid="stForm"] {
            padding: 1.2rem 1.6rem !important;
            border-radius: 14px !important;
            margin-top: 0.2rem !important;
            background: rgba(255, 255, 255, 0.06) !important;
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25), var(--glow-indigo) !important;
        }
        
        .stTextInput, .stTextInput > div {
            margin-bottom: 0.4rem !important;
        }
        
        .stCaption {
            margin-bottom: 0.6rem !important;
            font-size: 0.75rem !important;
            color: rgba(255, 255, 255, 0.7) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Tech Concierge Login Card (Compact, spinning dashed logo outer ring)
    st.markdown(f"""
    <div class="royal-card" style="text-align: center; border-top: 3.5px solid var(--accent-primary); padding: 1.1rem 1.4rem !important; margin-bottom: 0.6rem !important;">
        <div class="tech-logo-node">
            <div class="tech-logo-inner" style="width: 50px; height: 50px; margin: auto;">{SVG_LOGO}</div>
        </div>
        <h2 style='margin: 0; font-size: 1.75rem; font-family: "Space Grotesk", sans-serif; color: var(--concierge-white);'>
            OnboardBot
        </h2>
        <p style='color: var(--concierge-silver); font-size: 0.8rem; margin-top: 0.25rem; margin-bottom: 0; letter-spacing: 0.04em;'>
            Enterprise Concierge • Nexus Technologies
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🤖 Employee Access", "⚙️ Admin Portal"])
    
    with tab1:
        with st.form("employee_login_form"):
            st.caption("Sign in using corporate access key")
            emp_name = st.text_input("Full Name", placeholder="e.g. Elizabeth Bennet")
            emp_pass = st.text_input("Access Key", type="password", placeholder="Enter access key")
            submitted_emp = st.form_submit_button("Authenticate Access", use_container_width=True)
            
            if submitted_emp:
                if emp_pass == "nexuspass" and len(emp_name.strip()) >= 2:
                    st.session_state.logged_in = True
                    st.session_state.username = emp_name.strip().title()
                    st.session_state.role = "employee"
                    st.rerun()
                else:
                    st.error("Authentication failed. (Password: nexuspass)")
                    
    with tab2:
        with st.form("admin_login_form"):
            st.caption("Sign in using system manager credentials")
            admin_user = st.text_input("Admin Username", placeholder="admin")
            admin_pass = st.text_input("Security Password", type="password", placeholder="Enter admin password")
            submitted_admin = st.form_submit_button("Authenticate Admin", use_container_width=True)
            
            if submitted_admin:
                if admin_user.lower() == "admin" and admin_pass == "adminpass":
                    st.session_state.logged_in = True
                    st.session_state.username = "Admin Manager"
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error("Authentication failed. (Hint: admin / adminpass)")
    
    st.markdown("""
    <div style='text-align: center; color: var(--concierge-silver); font-size: 0.68rem; margin-top: 0.8rem;'>
        🔒 Secure audit-logged enterprise access compliance gateway.
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ============================================================================
# TEMPORARY FILE UPLOADS CLEANER ON LOGOUT
# ============================================================================
def perform_logout():
    # Clean up any session-temporary document embeddings from Chroma
    if st.session_state.temp_files and st.session_state.vector_store:
        for temp_fname in st.session_state.temp_files:
            try:
                delete_document_from_store(st.session_state.vector_store, temp_fname)
            except Exception:
                pass
    
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.messages = []
    st.session_state.follow_ups = []
    st.session_state.temp_files = []
    st.session_state.past_queries_vectors = []
    st.session_state.duplicate_alert = None
    st.rerun()


# ============================================================================
# SIDEBAR — INTELLIGENT CONCIERGE PANEL
# ============================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 0.5rem 0 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 1rem; text-align: center; display: flex; flex-direction: column; align-items: center;">
        <div style="width: 44px; height: 44px; margin: 0 auto 0.5rem; filter: drop-shadow(0 0 8px var(--accent-primary));">{SVG_LOGO}</div>
        <h3 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; color: var(--concierge-white);">OnboardBot</h3>
        <p style="margin: 0; font-size: 0.72rem; color: var(--accent-primary); font-weight: 700; letter-spacing: 0.05em;">EXECUTIVE PORTAL</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Workspace selector (Chatbot UI Style)
    st.markdown("<span style='font-size: 0.75rem; color: var(--concierge-silver); font-weight: 600; letter-spacing: 0.05em;'>WORKSPACE</span>", unsafe_allow_html=True)
    st.selectbox("Workspace Selector", ["Nexus Onboarding Vault", "IT Support Desk", "Benefits Desk"], key="selected_workspace", label_visibility="collapsed")
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # New Conversation button
    if st.button("➕ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.follow_ups = []
        st.session_state.duplicate_alert = None
        st.rerun()
        
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # Search history (Chatbot UI Style)
    st.markdown("<span style='font-size: 0.75rem; color: var(--concierge-silver); font-weight: 600; letter-spacing: 0.05em;'>SEARCH CHATS</span>", unsafe_allow_html=True)
    search_q = st.text_input("Search chats...", placeholder="Search conversations...", label_visibility="collapsed")
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Conversation List
    st.markdown("<span style='font-size: 0.75rem; color: var(--concierge-silver); font-weight: 600; letter-spacing: 0.05em;'>RECENT CONVERSATIONS</span>", unsafe_allow_html=True)
    
    if st.session_state.messages:
        # Show first user query
        first_q = st.session_state.messages[0]["content"]
        if search_q.strip() == "" or search_q.lower() in first_q.lower():
            short_q = first_q[:24] + "..." if len(first_q) > 24 else first_q
            st.markdown(f"""
            <div class="royal-card" style="padding: 0.6rem !important; border-left: 2px solid var(--bronze-gold); background: rgba(212, 175, 55, 0.05) !important; margin-bottom: 0.5rem !important;">
                <span style="font-size: 0.8rem; color: var(--concierge-white); font-weight: 600;">💬 {short_q}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 0.8rem; font-style: italic; color: var(--concierge-silver); padding: 0.5rem;'>No matching conversations.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 0.8rem; font-style: italic; color: var(--concierge-silver); padding: 0.5rem;'>No recent chats.</div>", unsafe_allow_html=True)
        
    # Spacer
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    
    # User Profile card at bottom
    role_color = "var(--accent-primary)"
    initials = "".join([n[0] for n in st.session_state.username.split()[:2]]).upper() if st.session_state.username else "?"
    
    st.markdown(f"""
    <div class="royal-card" style="border-left: 3.5px solid {role_color}; padding: 0.8rem !important; margin-bottom: 0.8rem !important;">
        <div style="display: flex; align-items: center; gap: 0.8rem;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: var(--accent-gradient); border: 1px solid var(--accent-primary); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; color: #070913;">{initials}</div>
            <div style="overflow: hidden; width: 100%;">
                <p style="font-size: 0.82rem; font-weight: 600; margin: 0; color: var(--concierge-white); white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{st.session_state.username}</p>
                <p style="font-size: 0.68rem; color: var(--concierge-silver); margin: 0; text-transform: uppercase;">{st.session_state.role}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Export & Logout
    col_c, col_e = st.columns(2)
    with col_c:
        if st.button("🗑️ Clear", use_container_width=True, help="Clear active chat history"):
            st.session_state.messages = []
            st.session_state.follow_ups = []
            st.session_state.duplicate_alert = None
            st.rerun()
    with col_e:
        if st.button("🚪 Logout", use_container_width=True, help="Exit portal & clear temp session files"):
            perform_logout()


# ============================================================================
# MAIN AREA LAYOUT (Double Sidebar AI Cockpit)
# ============================================================================

# Calculate dynamic RAG params and intent classifications first
latest_intent = "HR policy"
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    latest_intent = classify_intent(st.session_state.messages[-1]["content"])
elif st.session_state.messages and len(st.session_state.messages) > 1 and st.session_state.messages[-2]["role"] == "user":
    latest_intent = classify_intent(st.session_state.messages[-2]["content"])
    
contact_mapping = {
    "HR policy": "general_hr",
    "IT setup": "it_helpdesk",
    "Leave & attendance": "leave_desk",
    "Benefits": "benefits",
    "Out of scope": "ethics"
}
contact_key = contact_mapping.get(latest_intent, "general_hr")
contact = HR_CONTACTS.get(contact_key, HR_CONTACTS["general_hr"])

# Bind admin settings to state
if st.session_state.role == "admin":
    threshold_val = st.session_state.get("admin_threshold", 1.5)
    temperature_val = st.session_state.get("admin_temperature", 0.1)
    max_tokens_val = st.session_state.get("admin_max_tokens", 512)
else:
    threshold_val = 1.5
    temperature_val = 0.1
    max_tokens_val = 512

# Create columns for layout
chat_col, console_col = st.columns([3.0, 1.25])

with chat_col:
    # Concierge dynamic Header with animated gradient border and real-time confidence bar
    last_best_score = None
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_best_score = st.session_state.messages[-1].get("best_rerank_score")

    confidence_pct = 95
    if last_best_score is not None:
        confidence_pct = int((last_best_score + 1) * 50) if last_best_score > 0 else 90
        confidence_pct = min(max(confidence_pct, 75), 98)

    st.markdown(f"""
    <div class="royal-header fade-up-header">
        <div style="display: flex; align-items: center; gap: 0.8rem;">
            <div style="width: 44px; height: 44px; filter: drop-shadow(0 0 6px var(--bronze-gold));">{SVG_LOGO}</div>
            <div>
                <h1 style="margin: 0; font-size: 1.6rem; color: var(--concierge-white); font-family: 'Space Grotesk', sans-serif;">OnboardBot</h1>
                <span style="background: rgba(212,175,55,0.12); color: var(--bronze-gold); padding: 0.1rem 0.4rem; border-radius: 6px; font-size: 0.55rem; font-weight: 700; letter-spacing: 0.05em;">PREMIUM</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <div style="font-size: 0.85rem; color: var(--concierge-silver);">
                <span class="pulse-dot"></span> Concierge Online
            </div>
            <div class="confidence-meter-container">
                <span style="font-size: 0.78rem; color: var(--bronze-gold); font-weight: 600; font-family: 'Space Grotesk', sans-serif;">Confidence: {confidence_pct}%</span>
                <div class="confidence-bar-outer">
                    <div class="confidence-bar-inner" style="width: {confidence_pct}%;"></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Duplicate Query similarity banner alert
    if st.session_state.duplicate_alert:
        match_q = st.session_state.duplicate_alert["query"]
        match_a = st.session_state.duplicate_alert["answer"]
        
        col_al, col_cl = st.columns([12, 1])
        with col_al:
            st.markdown(f"""
            <div class="duplicate-alert-banner">
                <h5 style="margin:0 0 0.3rem 0; color:var(--bronze-gold); font-family:'Space Grotesk', sans-serif; font-size:0.95rem;">💡 You asked something very similar before:</h5>
                <p style="margin:0 0 0.5rem 0; font-size:0.82rem; color:var(--concierge-white); font-style:italic;">"{match_q}"</p>
                <div style="background:rgba(9,10,15,0.7); padding:0.6rem 0.8rem; border-radius:8px; border:1px solid rgba(212,175,55,0.15); font-size:0.8rem; color:var(--concierge-silver); max-height:150px; overflow-y:auto;">
                    {match_a}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_cl:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("✖", key="dismiss_dup_alert", help="Dismiss Alert"):
                st.session_state.duplicate_alert = None
                st.rerun()

    # Welcome Block
    if not st.session_state.messages:
        greeting_name = st.session_state.username if st.session_state.username else "esteemed guest"
        hour = datetime.now().hour
        time_greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        
        st.markdown(f"""
        <div class="royal-card fade-up-chat" style="padding: 2.2rem !important; border-top: 3px solid var(--accent-primary);">
            <h3 style='margin-top: 0; font-family: "Space Grotesk", sans-serif; font-size: 1.8rem; font-weight: 500; color: var(--concierge-white);'>
                👋 {time_greeting}, {greeting_name}!
            </h3>
            <p style='color: var(--concierge-silver); font-size: 0.95rem; line-height: 1.7; margin: 0.6rem 0 0;'>
                Welcome to the premium concierge service at <strong>Nexus Technologies</strong>. As your dedicated digital assistant, 
                I am prepared to guide you through our corporate policy frameworks, IT setups, and insurance schemes. 
                All insights are verified directly from our official document knowledge vault.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2x2 Grid Columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="royal-card fade-up-chat">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">📋</div>
                <h4 style="margin:0 0 0.4rem; color:var(--accent-primary); font-size:1.1rem; font-family:'Space Grotesk', sans-serif;">Company Policies</h4>
                <p style="margin:0; color:var(--concierge-silver); font-size:0.85rem; line-height:1.5;">Dress code parameters, behavioral conduct guides, appraisal structures, and workplace guidelines.</p>
            </div>
            <div style="height: 10px;"></div>
            <div class="royal-card fade-up-chat">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🏖️</div>
                <h4 style="margin:0 0 0.4rem; color:var(--accent-primary); font-size:1.1rem; font-family:'Space Grotesk', sans-serif;">Leave & Attendance</h4>
                <p style="margin:0; color:var(--concierge-silver); font-size:0.85rem; line-height:1.5;">Casual leaves allotments, medical declarations, carry-forward options, and leave request processes.</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="royal-card fade-up-chat">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">💻</div>
                <h4 style="margin:0 0 0.4rem; color:var(--accent-primary); font-size:1.1rem; font-family:'Space Grotesk', sans-serif;">IT Setup & Infrastructure</h4>
                <p style="margin:0; color:var(--concierge-silver); font-size:0.85rem; line-height:1.5;">Secure VPN laptop configuration, corporate email registrations, 2FA credentials, and Slack channels.</p>
            </div>
            <div style="height: 10px;"></div>
            <div class="royal-card fade-up-chat">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">💰</div>
                <h4 style="margin:0 0 0.4rem; color:var(--accent-primary); font-size:1.1rem; font-family:'Space Grotesk', sans-serif;">Employee Benefits</h4>
                <p style="margin:0; color:var(--concierge-silver); font-size:0.85rem; line-height:1.5;">Star Health Insurance limits, Provident Fund (PF) allocations, and training budgets details.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Quick Starter Queries
        st.markdown("<h4 style='color:var(--accent-primary); font-family:\"Space Grotesk\", sans-serif; margin-bottom:0.4rem;'>💡 Concierge Starter Queries</h4>", unsafe_allow_html=True)
        sample_queries = [
            "What is the company's dress code policy?",
            "How do I set up VPN on my laptop?",
            "How many casual leaves do I get per year?",
            "What health insurance benefits are offered?"
        ]
        
        st.markdown('<div class="suggestion-pills-container">', unsafe_allow_html=True)
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            if st.button(f"💬 {sample_queries[0]}", key="sample_q0", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": sample_queries[0],
                    "intent": "HR policy",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
            if st.button(f"💬 {sample_queries[1]}", key="sample_q1", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": sample_queries[1],
                    "intent": "IT setup",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
        with col_q2:
            if st.button(f"💬 {sample_queries[2]}", key="sample_q2", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": sample_queries[2],
                    "intent": "Leave & attendance",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
            if st.button(f"💬 {sample_queries[3]}", key="sample_q3", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": sample_queries[3],
                    "intent": "Benefits",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Render Messages Loop
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "✨"):
            # User message
            if message["role"] == "user":
                intent_val = message.get("intent", "Query")
                intent_class = "intent-badge-hr"
                if intent_val == "IT setup":
                    intent_class = "intent-badge-it"
                elif intent_val == "Leave & attendance":
                    intent_class = "intent-badge-leave"
                elif intent_val == "Benefits":
                    intent_class = "intent-badge-benefits"
                elif intent_val == "Out of scope":
                    intent_class = "intent-badge-scope"
                    
                intent_tag = f"<span class='intent-badge {intent_class}'>{intent_val}</span>"
                st.markdown(f"""
                <div style="font-size:0.95rem; line-height:1.65; color:var(--concierge-white); font-weight: 500;">
                    {message['content']}
                </div>
                <div class="bubble-meta">
                    {intent_tag} <span style="font-family:'JetBrains Mono',monospace;">{message.get('timestamp', '')} ✔✔</span>
                </div>
                """, unsafe_allow_html=True)
                
            # Assistant message
            else:
                word_count = len(message["content"].split())
                
                # Conditionally render summary if toggled
                if message.get("show_summary", False):
                    st.markdown(f"✨ **Summarised TL;DR:**\n\n{message.get('summary', '')}")
                else:
                    st.markdown(message["content"])
                    
                latency_str = ""
                if "latency" in message:
                    l_val = message["latency"]
                    if l_val < 0.2:
                        latency_str = f"""<span class="latency-badge latency-badge-fast">⚡ Cached match · {l_val:.2f}s</span>"""
                    else:
                        latency_str = f"""<span class="latency-badge latency-badge-normal">⚡ Response speed · {l_val:.2f}s</span>"""
                
                persona_tag = ""
                if "persona" in message:
                    persona_tag = f"""<span class="latency-badge">👤 Specialist: {message['persona']}</span>"""
                
                st.markdown(f"""
                <div class="bubble-meta">
                    <span style="font-family:'JetBrains Mono',monospace; color:var(--concierge-silver);">{message.get('timestamp', '')}</span>
                    <div style="display:flex; gap:0.5rem; align-items:center;">
                        {persona_tag}
                        {latency_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Interactive toolbar: Summarize and Voice Read Aloud
                st.markdown("<div class='tool-bar summarize-btn-container'>", unsafe_allow_html=True)
                col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 6])
                
                with col_b1:
                    if word_count > 150:
                        sum_key = f"sum_toggle_{idx}"
                        if not message.get("show_summary", False):
                            if st.button("✨ Summarise", key=sum_key, help="Provide dynamic TL;DR Summary"):
                                if "summary" not in message:
                                    with st.spinner("Generating TL;DR..."):
                                        message["summary"] = summarize_text(message["content"])
                                message["show_summary"] = True
                                st.rerun()
                        else:
                            if st.button("✨ Show Full", key=sum_key, help="Show full answer details"):
                                message["show_summary"] = False
                                st.rerun()
                with col_b2:
                    voice_key = f"voice_play_{idx}"
                    if st.button("🔊 Read Aloud", key=voice_key, help="Listen to answer (Web Speech API)"):
                        speak_text = message["content"].replace("\n", " ").replace('"', '\\"').replace("'", "\\'")
                        st.components.v1.html(f"""
                        <script>
                            if (window.parent.updateDynamicIsland) {{
                                window.parent.updateDynamicIsland('speaking', 'Reading Aloud...');
                            }}
                            const utterance = new window.parent.SpeechSynthesisUtterance("{speak_text}");
                            utterance.lang = "en-US";
                            utterance.rate = 1.05;
                            utterance.onend = () => {{
                                if (window.parent.updateDynamicIsland) {{
                                    window.parent.updateDynamicIsland('idle');
                                }}
                            }};
                            utterance.onerror = () => {{
                                if (window.parent.updateDynamicIsland) {{
                                    window.parent.updateDynamicIsland('idle');
                                }}
                            }};
                            window.parent.speechSynthesis.speak(utterance);
                        </script>
                        """, height=0, width=0)
                st.markdown("</div>", unsafe_allow_html=True)

                # Slide-in Verbatim Citation Cards
                if "citations" in message and message["citations"]:
                    st.markdown("<div class='citation-wrapper'>", unsafe_allow_html=True)
                    for s_idx, cite in enumerate(message["citations"], 1):
                        st.markdown(f"""
                        <div class="citation-bubble-card">
                            <div style="font-size:0.75rem; font-family:'JetBrains Mono',monospace; color:var(--bronze-gold); font-weight:600; margin-bottom:0.3rem;">
                                📄 Source {s_idx}: {cite['source']} <span style="color:var(--concierge-silver); font-weight:normal;">({cite['file']})</span>
                            </div>
                            <div style="font-size:0.82rem; line-height:1.5; color:var(--concierge-silver); font-style:italic;">
                                "{cite['text'].strip()}"
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    # Suggested Follow-ups
    if st.session_state.follow_ups and st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.8rem; color:var(--accent-primary); font-weight:600; font-family:\"Space Grotesk\", sans-serif;'>✨ Concierge suggestions for you:</span>", unsafe_allow_html=True)
        cols = st.columns(len(st.session_state.follow_ups))
        for f_idx, q in enumerate(st.session_state.follow_ups):
            with cols[f_idx]:
                if st.button(f"💬 {q}", key=f"fup_btn_{f_idx}", use_container_width=True):
                    fup_intent = classify_intent(q)
                    st.session_state.messages.append({
                        "role": "user",
                        "content": q,
                        "intent": fup_intent,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    st.session_state.follow_ups = []
                    st.rerun()

    # Response Generation RAG Processor
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_msg = st.session_state.messages[-1]
        prompt = user_msg["content"]
        
        # Trigger Dynamic Island thinking state
        st.markdown("""
        <script>
            if (window.parent && window.parent.updateDynamicIsland) {
                window.parent.updateDynamicIsland('thinking', 'Consulting Documents...');
            }
        </script>
        """, unsafe_allow_html=True)
        
        # 1. Cosine similarity duplicate check
        best_match_q, max_similarity = calculate_query_similarity(prompt, st.session_state.get("past_queries_vectors", []))
        if max_similarity > 0.85 and best_match_q:
            for m_idx, msg in enumerate(st.session_state.messages):
                if msg["role"] == "user" and msg["content"] == best_match_q:
                    if m_idx + 1 < len(st.session_state.messages) and st.session_state.messages[m_idx + 1]["role"] == "assistant":
                        st.session_state.duplicate_alert = {
                            "query": best_match_q,
                            "answer": st.session_state.messages[m_idx + 1]["content"]
                        }
                        break

        with st.chat_message("assistant", avatar="✨"):
            # Waveform loader
            loader = st.empty()
            loader.markdown("""
            <div class="voice-waveform" style="display:flex;">
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <span style="color:var(--accent-primary); font-size:0.8rem; margin-left:0.5rem; font-family:'Space Grotesk',sans-serif;">Consulting corporate documents...</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Ingest and initialize vector store & LLM
            ensure_bot_ready(temperature=temperature_val, max_tokens=max_tokens_val)
            
            # Specialist System Prompt override
            persona = st.session_state.get("specialist_persona", "Nexus Guide")
            sys_prompt_override = None
            if persona == "HR Policy Expert":
                sys_prompt_override = SYSTEM_PROMPT + "\n\n" + (
                    "You are in 'HR Policy Expert' mode. Answer with extreme precision, citing exact document names and guidelines. "
                    "Be formal, structured, and thorough. Present policy details clearly and exhaustively."
                )
            elif persona == "Tech Ninja":
                sys_prompt_override = SYSTEM_PROMPT + "\n\n" + (
                    "You are in 'Tech Ninja' mode. Keep answers extremely brief, concise, and direct. Focus purely on technical setups, "
                    "commands, links, and step-by-step action items. Use bullet points and bold keywords for maximum speed of reading."
                )
            elif persona == "Empathetic Guide":
                sys_prompt_override = SYSTEM_PROMPT + "\n\n" + (
                    "You are in 'Empathetic Guide' mode. Speak with a warm, welcoming, and highly supportive tone. Encourage the new hire, "
                    "explain details gently, and show empathy for the onboarding process."
                )
                
            # Execute query and measure latency
            import time
            start_time = time.time()
            
            is_in_scope, immediate_answer, stream_generator, retrieved_docs, raw_chroma_docs = query_rag_stream(
                vector_store=st.session_state.vector_store,
                question=prompt,
                chat_history=st.session_state.messages[:-1],
                relevance_threshold=threshold_val,
                llm=st.session_state.llm,
                system_prompt_override=sys_prompt_override,
                excluded_files=st.session_state.get("excluded_docs", []),
            )
            
            best_chroma_score = raw_chroma_docs[0][1] if raw_chroma_docs else None
            best_rerank_score = retrieved_docs[0][1] if retrieved_docs else None
            
            loader.empty()
            
            if not is_in_scope and immediate_answer:
                st.markdown(immediate_answer)
                st.warning("⚠️ Query routing: Outside the scope of HR policy parameters.")
                answer = immediate_answer
                citations = None
                follow_ups = []
                elapsed_time = time.time() - start_time
            else:
                answer = st.write_stream(stream_generator())
                st.success("✅ Information verified from HR Documents.")
                elapsed_time = time.time() - start_time
                
                citations = []
                if retrieved_docs:
                    for idx, (doc, score) in enumerate(retrieved_docs, 1):
                        citations.append({
                            "source": doc.metadata.get("source_name", "Unknown Document"),
                            "file": doc.metadata.get("file_name", "unknown"),
                            "text": doc.page_content
                        })
                        
                follow_ups = generate_follow_up_questions(
                    question=prompt,
                    answer=answer,
                    chat_history=st.session_state.messages[:-1],
                    llm=st.session_state.llm
                )
                
        # Append response to chat logs
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "citations": citations,
            "best_chroma_score": best_chroma_score,
            "best_rerank_score": best_rerank_score,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "latency": elapsed_time,
            "persona": persona,
        })
        
        # Save cache for RAG graph
        st.session_state.last_retrieved_docs = retrieved_docs if retrieved_docs else []
        st.session_state.last_raw_chroma_docs = raw_chroma_docs if raw_chroma_docs else []
        
        # Store query embedding
        add_query_to_history(prompt)
        
        # Log audit
        write_audit_log(
            username=st.session_state.username,
            query=prompt,
            answer=answer,
            threshold=threshold_val,
            temperature=temperature_val,
            chroma_score=best_chroma_score,
            rerank_score=best_rerank_score
        )
        
        st.session_state.follow_ups = follow_ups
        st.rerun()

    # Chat Input Box
    user_prompt = st.chat_input("Ask anything about Nexus Technologies onboarding...")
    if user_prompt:
        prompt_intent = classify_intent(user_prompt)
        st.session_state.messages.append({
            "role": "user",
            "content": user_prompt,
            "intent": prompt_intent,
            "timestamp": datetime.now().strftime("%I:%M %p")
        })
        st.rerun()

with console_col:
    st.markdown("<h4 style='color:var(--accent-primary); font-family:\"Space Grotesk\", sans-serif; margin-bottom:0.8rem; margin-top:0.4rem;'>🎛️ AI Cockpit Console</h4>", unsafe_allow_html=True)
    
    # Specialist Selector
    st.markdown("<span style='font-size:0.75rem; color:var(--concierge-silver); font-weight:600; letter-spacing:0.05em;'>AI SPECIALIST COCKPIT</span>", unsafe_allow_html=True)
    active_p = st.session_state.get("specialist_persona", "Nexus Guide")
    
    # Render beautiful custom specialist cards
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(f"""
        <div class="persona-card {'persona-card-active' if active_p == 'Nexus Guide' else ''}">
            <span style="font-size:1.3rem;">🤖</span>
            <div style="font-size:0.78rem; font-weight:600; margin-top:2px; color:var(--concierge-white);">Nexus Guide</div>
            <div style="font-size:0.62rem; color:var(--concierge-silver);">Standard Agent</div>
        </div>
        <div style="height:8px;"></div>
        <div class="persona-card {'persona-card-active' if active_p == 'HR Policy Expert' else ''}">
            <span style="font-size:1.3rem;">⚖️</span>
            <div style="font-size:0.78rem; font-weight:600; margin-top:2px; color:var(--concierge-white);">HR Expert</div>
            <div style="font-size:0.62rem; color:var(--concierge-silver);">Detailed Policies</div>
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown(f"""
        <div class="persona-card {'persona-card-active' if active_p == 'Tech Ninja' else ''}">
            <span style="font-size:1.3rem;">💻</span>
            <div style="font-size:0.78rem; font-weight:600; margin-top:2px; color:var(--concierge-white);">Tech Ninja</div>
            <div style="font-size:0.62rem; color:var(--concierge-silver);">Short Guides</div>
        </div>
        <div style="height:8px;"></div>
        <div class="persona-card {'persona-card-active' if active_p == 'Empathetic Guide' else ''}">
            <span style="font-size:1.3rem;">🌟</span>
            <div style="font-size:0.78rem; font-weight:600; margin-top:2px; color:var(--concierge-white);">Empathy Host</div>
            <div style="font-size:0.62rem; color:var(--concierge-silver);">Warm & Supportive</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    
    # Interactive selection list below cards
    selected_p = st.selectbox(
        "Active Specialist Persona",
        ["Nexus Guide", "HR Policy Expert", "Tech Ninja", "Empathetic Guide"],
        key="specialist_persona_selector_key",
        index=["Nexus Guide", "HR Policy Expert", "Tech Ninja", "Empathetic Guide"].index(active_p),
        label_visibility="collapsed"
    )
    if selected_p != active_p:
        st.session_state.specialist_persona = selected_p
        st.rerun()
        
    st.markdown("<div style='height:15px; border-bottom:1px solid rgba(255,255,255,0.05); margin-bottom:15px;'></div>", unsafe_allow_html=True)
    
    # Render Hugging Face Tools if assistant generated a response last
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_answer = st.session_state.messages[-1]["content"]
        with st.expander("🤖 Assistant Analysis Tools", expanded=True):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                if st.button("🧒 ELI5", help="Explain like I'm 5", use_container_width=True):
                    st.markdown("""<script>if (window.parent && window.parent.updateDynamicIsland) { window.parent.updateDynamicIsland('thinking', 'Simplifying context...'); }</script>""", unsafe_allow_html=True)
                    with st.spinner("Analyzing..."):
                        ensure_bot_ready()
                        prompt = f"Explain the following HR context in extremely simple terms, as if explaining to a 5 year old child:\n\n{last_answer}"
                        eli5_ans = st.session_state.llm.invoke(prompt)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"🧒 **Explain Like I'm 5:**\n\n{eli5_ans.strip()}",
                            "best_rerank_score": st.session_state.messages[-1].get("best_rerank_score"),
                            "citations": st.session_state.messages[-1].get("citations")
                        })
                        st.rerun()
                
                rephrase_tone = st.selectbox("Rephrase:", ["Tone...", "polite", "casual", "professional"], key="rephrase_select_box", label_visibility="collapsed")
                if rephrase_tone != "Tone...":
                    st.markdown(f"""<script>if (window.parent && window.parent.updateDynamicIsland) {{ window.parent.updateDynamicIsland('thinking', 'Rephrasing...'); }}</script>""", unsafe_allow_html=True)
                    with st.spinner("Rephrasing..."):
                        rephrased = rephrase_text(last_answer, rephrase_tone)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"🤗 **Rephrased ({rephrase_tone}):**\n\n{rephrased}",
                            "best_rerank_score": st.session_state.messages[-1].get("best_rerank_score"),
                            "citations": st.session_state.messages[-1].get("citations")
                        })
                        st.rerun()
                        
            with col_t2:
                if st.button("📋 Actions", help="Extract Action Items", use_container_width=True):
                    st.markdown("""<script>if (window.parent && window.parent.updateDynamicIsland) { window.parent.updateDynamicIsland('thinking', 'Extracting actions...'); }</script>""", unsafe_allow_html=True)
                    with st.spinner("Extracting..."):
                        ensure_bot_ready()
                        prompt = f"Identify and extract a brief bulleted list of actual action items or direct next steps from this onboarding details:\n\n{last_answer}"
                        actions = st.session_state.llm.invoke(prompt)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"📋 **Action Items & Next Steps:**\n\n{actions.strip()}",
                            "best_rerank_score": st.session_state.messages[-1].get("best_rerank_score"),
                            "citations": st.session_state.messages[-1].get("citations")
                        })
                        st.rerun()
                
                trans_lang = st.selectbox("Translate:", ["Language...", "Hindi", "Telugu", "Tamil", "Spanish", "French", "German", "Japanese"], key="translate_select_box", label_visibility="collapsed")
                if trans_lang != "Language...":
                    st.markdown(f"""<script>if (window.parent && window.parent.updateDynamicIsland) {{ window.parent.updateDynamicIsland('thinking', 'Translating...'); }}</script>""", unsafe_allow_html=True)
                    with st.spinner("Translating..."):
                        translated = translate_text(last_answer, trans_lang)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"🌐 **Translated to {trans_lang}:**\n\n{translated}",
                            "best_rerank_score": st.session_state.messages[-1].get("best_rerank_score"),
                            "citations": st.session_state.messages[-1].get("citations")
                        })
                        st.rerun()

    # Segmented tabs for console widgets
    if st.session_state.role == "admin":
        tab_names = ["📎 Context", "📊 RAG Graph", "🧠 Memory", "♿ Adjust", "⚙️ Tuning"]
    else:
        tab_names = ["📎 Context", "📊 RAG Graph", "🧠 Memory", "♿ Adjust"]
        
    console_tabs = st.tabs(tab_names)
    
    # Tab 1: Context & HR
    with console_tabs[0]:
        # Live Contact Card
        st.markdown(f"""
        <div class="royal-card" style="border-right: 3px solid var(--accent-primary); margin-bottom: 0.8rem !important; padding: 1rem !important;">
            <h4 style="margin-top:0; font-size:0.95rem;">Live HR Contact</h4>
            <div style="font-size:0.65rem; color:var(--accent-primary); font-weight:700; margin-bottom:0.3rem; text-transform:uppercase; letter-spacing:0.05em;">Intent: {latest_intent}</div>
            <p style="font-size:0.82rem; font-weight:600; margin:0; color:var(--concierge-white);">{contact['name']}</p>
            <p style="font-size:0.7rem; color:var(--concierge-silver); margin:0.1rem 0 0.4rem 0;">{contact['description']}</p>
            <p style="font-size:0.7rem; margin:0; color:var(--concierge-silver);">
                📧 <code>{contact.get('email', 'N/A')}</code><br>
                📞 {contact.get('phone', 'N/A')} (Ext {contact.get('extension', 'N/A')})
            </p>
            <div style="margin-top:0.6rem;">
                <a href="mailto:{contact.get('email', '')}?subject=HR Onboarding Query" style="text-decoration:none;">
                    <button class="stButton" style="width:100%; border:1px solid var(--accent-primary); background:rgba(255,255,255,0.02); color:var(--accent-primary); border-radius:6px; font-size:0.7rem; padding:0.25rem; cursor:pointer;">📧 Send email</button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Temporary uploads
        st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>📎 Session Documents</h4>", unsafe_allow_html=True)
        temp_uploader = st.file_uploader(
            "Upload PDF/TXT (Temp Context)",
            type=["pdf", "txt"],
            help="Upload context valid only for your current chat session.",
            key="temp_file_workspace",
            label_visibility="collapsed"
        )
        if temp_uploader is not None:
            temp_fname = f"temp_{st.session_state.session_id}_{temp_uploader.name}"
            if temp_fname not in st.session_state.temp_files:
                with st.spinner("Embedding..."):
                    try:
                        ensure_bot_ready()
                        import os
                        os.makedirs(DATA_DIR, exist_ok=True)
                        save_path = DATA_DIR / temp_fname
                        with open(save_path, "wb") as f:
                            f.write(temp_uploader.getbuffer())
                            
                        from src.document_loader import load_single_document, split_documents
                        docs = load_single_document(save_path)
                        chunks = split_documents(docs)
                        
                        if chunks:
                            for chunk in chunks:
                                chunk.metadata["temp"] = True
                                chunk.metadata["file_name"] = temp_fname
                                chunk.metadata["source_name"] = f"Temp: {temp_uploader.name}"
                                
                            st.session_state.vector_store.add_documents(chunks)
                            st.session_state.temp_files.append(temp_fname)
                            st.success(f"Loaded: {temp_uploader.name}")
                            st.rerun()
                        else:
                            st.error("Empty document.")
                    except Exception as ex:
                        st.error(f"Error: {ex}")
                        
        if st.session_state.temp_files:
            st.caption("Active Session Documents:")
            for temp_f in st.session_state.temp_files:
                clean_name = temp_f.split("_", 2)[-1]
                st.markdown(f"📄 `{clean_name}`")
            if st.button("Clear Temp Files", use_container_width=True):
                with st.spinner("Deleting..."):
                    for temp_f in st.session_state.temp_files:
                        try:
                            delete_document_from_store(st.session_state.vector_store, temp_f)
                        except Exception:
                            pass
                    st.session_state.temp_files = []
                    st.success("Cleaned!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Tab 2: RAG Graph
    with console_tabs[1]:
        st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>📊 RAG Graph & Context Filter</h4>", unsafe_allow_html=True)
        
        last_docs = st.session_state.get("last_retrieved_docs", [])
        
        if not last_docs:
            st.caption("Ask a query first to analyze document retrieval scores.")
        else:
            st.markdown("<span style='font-size:0.75rem; color:var(--concierge-silver); font-weight:600;'>RETRIEVED CHUNKS</span>", unsafe_allow_html=True)
            
            excluded_set = set(st.session_state.get("excluded_docs", []))
            
            for idx, (doc, score) in enumerate(last_docs):
                source_name = doc.metadata.get("source_name", "Unknown Document")
                file_name = doc.metadata.get("file_name", "unknown")
                
                # ChromaDB L2 score conversion
                match_pct = max(0, min(100, int((1.8 - score) / 1.8 * 100)))
                
                if match_pct >= 70:
                    color_class = "rag-match-bar-green"
                    badge_style = "color: #10B981; border: 1px solid rgba(16,185,129,0.2); background: rgba(16,185,129,0.05);"
                elif match_pct >= 50:
                    color_class = "rag-match-bar-amber"
                    badge_style = "color: #F59E0B; border: 1px solid rgba(245,158,11,0.2); background: rgba(245,158,11,0.05);"
                else:
                    color_class = "rag-match-bar-rose"
                    badge_style = "color: #EF4444; border: 1px solid rgba(239,68,68,0.2); background: rgba(239,68,68,0.05);"
                
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                    <span style="font-size:0.78rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:70%; color:var(--concierge-white);">📄 {source_name}</span>
                    <span style="font-size:0.68rem; font-family:'JetBrains Mono',monospace; padding:1px 4px; border-radius:4px; {badge_style}">{match_pct}% Match</span>
                </div>
                <div class="rag-match-bar-outer">
                    <div class="rag-match-bar-inner {color_class}" style="width: {match_pct}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<span style='font-size:0.65rem; color:var(--concierge-silver); font-family:\"JetBrains Mono\",monospace;'>File: {file_name}</span>", unsafe_allow_html=True)
                
                with st.expander(f"Inspect Text Chunk {idx+1}", expanded=False):
                    st.markdown(f"<p style='font-size:0.75rem; font-style:italic; line-height:1.4;'>\"{doc.page_content.strip()}\"</p>", unsafe_allow_html=True)
                
                exclude_key = f"exclude_check_{file_name}_{idx}"
                is_excluded = file_name in excluded_set
                check_val = st.checkbox("Exclude file from next search", key=exclude_key, value=is_excluded)
                
                if check_val:
                    excluded_set.add(file_name)
                else:
                    excluded_set.discard(file_name)
                    
                st.markdown("<div style='height:8px; border-bottom:1px solid rgba(255,255,255,0.03);'></div>", unsafe_allow_html=True)
            
            st.session_state.excluded_docs = list(excluded_set)
            
            if st.session_state.excluded_docs:
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                st.warning(f"⚠️ {len(st.session_state.excluded_docs)} documents excluded from search context.")
                
                if st.button("🔄 Re-run Query with Filters", use_container_width=True):
                    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                        last_user_prompt = None
                        for msg in reversed(st.session_state.messages):
                            if msg["role"] == "user":
                                last_user_prompt = msg["content"]
                                break
                        
                        if last_user_prompt:
                            st.session_state.messages.pop()
                            st.session_state.messages.append({
                                "role": "user",
                                "content": last_user_prompt,
                                "intent": classify_intent(last_user_prompt),
                                "timestamp": datetime.now().strftime("%I:%M %p")
                            })
                            st.session_state.follow_ups = []
                            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Tab 3: Memory Vault
    with console_tabs[2]:
        st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>Memory Vault</h4>", unsafe_allow_html=True)
        if not st.session_state.memory_vault:
            st.caption("No user facts stored yet.")
        else:
            for idx, fact in enumerate(st.session_state.memory_vault):
                col_f, col_d = st.columns([5, 1.2])
                with col_f:
                    st.markdown(f"<span style='font-size:0.72rem; color:var(--concierge-white);'>📌 {fact}</span>", unsafe_allow_html=True)
                with col_d:
                    if st.button("🗑️", key=f"del_fact_{idx}", help="Delete Fact"):
                        st.session_state.memory_vault.pop(idx)
                        st.rerun()
                        
        with st.form("add_memory_fact_form"):
            new_fact = st.text_input("Add Preference Fact", placeholder="e.g. Prefers email follow-ups", label_visibility="collapsed")
            if st.form_submit_button("Store Fact", use_container_width=True) and new_fact.strip():
                st.session_state.memory_vault.append(new_fact.strip())
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Tab 4: Accessibility
    with console_tabs[3]:
        st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>♿ Adjustments</h4>", unsafe_allow_html=True)
        dys_val = st.toggle("Dyslexia Font", value=st.session_state.dyslexia_mode)
        if dys_val != st.session_state.dyslexia_mode:
            st.session_state.dyslexia_mode = dys_val
            st.rerun()
            
        hc_val = st.toggle("High Contrast", value=st.session_state.high_contrast_mode)
        if hc_val != st.session_state.high_contrast_mode:
            st.session_state.high_contrast_mode = hc_val
            st.rerun()
            
        font_scale_val = st.slider("Font Scale", 0.8, 1.4, st.session_state.font_scale, 0.05)
        if font_scale_val != st.session_state.font_scale:
            st.session_state.font_scale = font_scale_val
            st.rerun()
            
        motion_val = st.toggle("Reduce Motion", value=st.session_state.reduced_motion)
        if motion_val != st.session_state.reduced_motion:
            st.session_state.reduced_motion = motion_val
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Tab 4: Tuning (Admin only)
    if st.session_state.role == "admin":
        with console_tabs[4]:
            st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>⚙️ Tuning Params</h4>", unsafe_allow_html=True)
            st.slider("Similarity Threshold", 0.5, 2.5, threshold_val, 0.1, key="admin_threshold")
            st.slider("LLM Temperature", 0.0, 1.0, temperature_val, 0.05, key="admin_temperature")
            st.number_input("Max Output Tokens", 64, 2048, max_tokens_val, 64, key="admin_max_tokens")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>📁 Doc Manager</h4>", unsafe_allow_html=True)
            admin_uploader = st.file_uploader("Upload Policy (PDF/TXT)", type=["pdf", "txt"], key="admin_doc_loader", label_visibility="collapsed")
            if admin_uploader is not None:
                doc_name_input = st.text_input("Citation Name", value=Path(admin_uploader.name).stem.replace("_", " ").title())
                if st.button("📥 Ingest File", use_container_width=True):
                    with st.spinner("Ingesting..."):
                        try:
                            ensure_bot_ready()
                            save_path = DATA_DIR / admin_uploader.name
                            with open(save_path, "wb") as f:
                                f.write(admin_uploader.getbuffer())
                            from src.document_loader import DOCUMENT_NAMES, load_single_document, split_documents
                            DOCUMENT_NAMES[Path(admin_uploader.name).stem] = doc_name_input
                            docs = load_single_document(save_path)
                            chunks = split_documents(docs)
                            if chunks:
                                st.session_state.vector_store.add_documents(chunks)
                                st.success("Added permanently!")
                                st.rerun()
                        except Exception as ex:
                            st.error(f"Error: {ex}")
            st.markdown("---")
            if st.session_state.vector_store:
                unique_docs = get_unique_documents(st.session_state.vector_store)
            else:
                unique_docs = []
            for d in unique_docs:
                f_name = d["file_name"]
                col_n, col_x = st.columns([4, 1.2])
                with col_n:
                    st.markdown(f"📄 `{f_name}`")
                with col_x:
                    if st.button("🗑️", key=f"del_admin_{f_name}"):
                        ensure_bot_ready()
                        delete_document_from_store(st.session_state.vector_store, f_name)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="royal-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:0.95rem;'>📊 Audit Logs</h4>", unsafe_allow_html=True)
            if AUDIT_LOG_FILE.exists():
                import pandas as pd
                st.dataframe(pd.read_csv(AUDIT_LOG_FILE), use_container_width=True)
                if st.button("Clear Logs", use_container_width=True):
                    import os
                    os.remove(AUDIT_LOG_FILE)
                    st.rerun()
            else:
                st.caption("No logs.")
            st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# CUSTOM JAVASCRIPT INJECTOR (Microphone, Emoji, Char Counter, Key bindings)
# ============================================================================
st.components.v1.html("""
<script>
    const doc = window.parent.document;

    // Injected stylesheet with waveform and picker layouts
    if (!doc.getElementById('royal-theme-injections')) {
        const style = doc.createElement('style');
        style.id = 'royal-theme-injections';
        style.innerHTML = `
            .custom-input-tool-btn {
                background: transparent !important;
                border: none !important;
                font-size: 1.25rem !important;
                cursor: pointer !important;
                padding: 0.2rem !important;
                margin: 0 0.35rem !important;
                opacity: 0.65 !important;
                transition: all 0.2s ease !important;
                color: #D4AF37 !important;
                vertical-align: middle;
            }
            .custom-input-tool-btn:hover {
                opacity: 1 !important;
                transform: scale(1.15) !important;
            }
            .custom-input-tool-btn.recording {
                color: #EF4444 !important;
                animation: recordingFlash 1s infinite alternate !important;
                opacity: 1 !important;
            }
            @keyframes recordingFlash {
                from { transform: scale(1); filter: drop-shadow(0 0 2px #EF4444); }
                to { transform: scale(1.2); filter: drop-shadow(0 0 10px #EF4444); }
            }
            .custom-char-counter {
                position: absolute !important;
                right: 4.8rem !important;
                bottom: -1.3rem !important;
                font-size: 0.72rem !important;
                color: #8E9AAF !important;
                font-family: 'JetBrains Mono', monospace !important;
            }
            .voice-waveform {
                display: none;
                align-items: center;
                justify-content: center;
                gap: 4px;
                padding: 0.5rem 1rem !important;
                margin-bottom: 0.6rem !important;
                background: rgba(18, 20, 28, 0.92) !important;
                border: 1px solid #D4AF37 !important;
                border-radius: 12px !important;
                box-shadow: 0 0 15px rgba(212,175,55,0.2) !important;
                width: fit-content;
                margin-left: auto;
                margin-right: auto;
                animation: fadeIn 0.3s ease !important;
            }
            .wave-bar {
                width: 3px;
                height: 10px;
                background-color: #D4AF37;
                border-radius: 2px;
                animation: waveBounce 0.8s ease-in-out infinite alternate;
            }
            .wave-bar:nth-child(2) { animation-delay: 0.15s; height: 16px; }
            .wave-bar:nth-child(3) { animation-delay: 0.3s; height: 22px; }
            .wave-bar:nth-child(4) { animation-delay: 0.45s; height: 14px; }
            .wave-bar:nth-child(5) { animation-delay: 0.6s; height: 8px; }
            @keyframes waveBounce {
                from { transform: scaleY(0.4); }
                to { transform: scaleY(1.3); }
            }
            .custom-emoji-picker {
                display: none;
                grid-template-columns: repeat(6, 1fr);
                gap: 8px;
                padding: 10px !important;
                background: #12141C !important;
                border: 1px solid #D4AF37 !important;
                border-radius: 12px !important;
                position: absolute !important;
                bottom: 3.8rem !important;
                right: 1.5rem !important;
                z-index: 1000 !important;
                box-shadow: 0 0 18px rgba(212,175,55,0.2) !important;
                width: 220px !important;
            }
            .custom-emoji-picker span {
                font-size: 1.25rem !important;
                text-align: center !important;
                transition: transform 0.15s ease !important;
                user-select: none;
            }
            .custom-emoji-picker span:hover {
                transform: scale(1.25) !important;
            }
        `;
        doc.head.appendChild(style);
    }

    // SetInterval checks if the chat textarea container is loaded in DOM
    const injectInterval = setInterval(() => {
        const textarea = doc.querySelector('div[data-testid="stChatInput"] textarea');
        if (textarea) {
            if (!doc.getElementById('voice-input-btn')) {
                augmentChatInput(textarea, doc);
            }
        }
    }, 1000);

    function augmentChatInput(textarea, doc) {
        const wrapper = textarea.parentNode;
        wrapper.style.position = 'relative';
        
        // Mic Button
        const micBtn = doc.createElement('button');
        micBtn.id = 'voice-input-btn';
        micBtn.innerHTML = '🎤';
        micBtn.className = 'custom-input-tool-btn';
        micBtn.title = 'Voice Input';
        micBtn.type = 'button';
        
        // Emoji picker
        const emojiBtn = doc.createElement('button');
        emojiBtn.id = 'emoji-picker-btn';
        emojiBtn.innerHTML = '😊';
        emojiBtn.className = 'custom-input-tool-btn';
        emojiBtn.title = 'Insert Emoji';
        emojiBtn.type = 'button';
        
        // Counter
        const charCounter = doc.createElement('div');
        charCounter.id = 'custom-char-counter';
        charCounter.className = 'custom-char-counter';
        charCounter.innerText = textarea.value.length + ' / 1000';
        
        // Insert custom tool widgets next to textarea
        wrapper.appendChild(emojiBtn);
        wrapper.appendChild(micBtn);
        wrapper.appendChild(charCounter);
        
        // Bind updates on change
        textarea.addEventListener('input', () => {
            const len = textarea.value.length;
            charCounter.innerText = len + ' / 1000';
            if (len >= 950) {
                charCounter.style.color = '#EF4444';
            } else if (len >= 800) {
                charCounter.style.color = '#E8A317';
            } else {
                charCounter.style.color = '#8E9AAF';
            }
        });
        
        // Bind Ctrl+Enter keyboard submission
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                const submitBtn = wrapper.querySelector('button[data-testid="stChatInputSubmitButton"]');
                if (submitBtn) submitBtn.click();
            }
        });
        
        // Voice recognition setup
        let recognition;
        let isRecording = false;
        
        micBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (!recognition) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("Browser speech recognition not supported.");
                    return;
                }
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                
                recognition.onstart = () => {
                    isRecording = true;
                    micBtn.innerHTML = '🛑';
                    micBtn.classList.add('recording');
                    showWaveform();
                    if (window.parent && window.parent.updateDynamicIsland) {
                        window.parent.updateDynamicIsland('listening', 'Listening...');
                    }
                };
                
                recognition.onend = () => {
                    isRecording = false;
                    micBtn.innerHTML = '🎤';
                    micBtn.classList.remove('recording');
                    hideWaveform();
                    if (window.parent && window.parent.updateDynamicIsland) {
                        window.parent.updateDynamicIsland('idle');
                    }
                };
                
                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    textarea.value = textarea.value ? textarea.value + " " + transcript : transcript;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    
                    // Auto submit on speech complete
                    setTimeout(() => {
                        const submitBtn = wrapper.querySelector('button[data-testid="stChatInputSubmitButton"]');
                        if (submitBtn) submitBtn.click();
                    }, 500);
                };
                
                recognition.onerror = (e) => {
                    console.error("SpeechRecognition error:", e.error);
                    recognition.stop();
                    if (window.parent && window.parent.updateDynamicIsland) {
                        window.parent.updateDynamicIsland('idle');
                    }
                };
            }
            
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
        
        function showWaveform() {
            let wave = doc.getElementById('voice-waveform');
            if (!wave) {
                wave = doc.createElement('div');
                wave.id = 'voice-waveform';
                wave.className = 'voice-waveform';
                wave.innerHTML = `
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <span style="color:#D4AF37; font-size:0.75rem; margin-left:0.5rem; font-family:'Inter',sans-serif;">Listening...</span>
                `;
                const container = doc.querySelector('div[data-testid="stChatInput"]');
                container.parentNode.insertBefore(wave, container);
            }
            wave.style.display = 'flex';
        }
        
        function hideWaveform() {
            const wave = doc.getElementById('voice-waveform');
            if (wave) wave.style.display = 'none';
        }
        
        // Emoji panel toggle
        emojiBtn.addEventListener('click', (e) => {
            e.preventDefault();
            let picker = doc.getElementById('custom-emoji-picker');
            if (!picker) {
                picker = doc.createElement('div');
                picker.id = 'custom-emoji-picker';
                picker.className = 'custom-emoji-picker';
                const emojis = ['😊', '👍', '🎉', '❤️', '💻', '🏖️', '📄', '📞', '📧', '💡', '🌿', '✨', '🚀', '🤖', '🚪', '❓', '✅', '⚠️'];
                emojis.forEach(emo => {
                    const span = doc.createElement('span');
                    span.innerText = emo;
                    span.style.cursor = 'pointer';
                    span.addEventListener('click', () => {
                        textarea.value = textarea.value + emo;
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        picker.style.display = 'none';
                        textarea.focus();
                    });
                    picker.appendChild(span);
                });
                wrapper.appendChild(picker);
            }
            picker.style.display = picker.style.display === 'none' ? 'grid' : 'none';
        });
    }

    // ═══════════════════════════════════════════════════════════
    // 3D GEODESIC WIREFRAME SPHERE ENGINE
    // ═══════════════════════════════════════════════════════════
    if (!doc.sphereMouseOffset) {
        doc.sphereMouseOffset = { x: 0, y: 0 };
        doc.addEventListener('mousemove', (e) => {
            doc.sphereMouseOffset.x = ((e.clientX / window.parent.innerWidth) - 0.5) * 2 * Math.PI;
            doc.sphereMouseOffset.y = ((e.clientY / window.parent.innerHeight) - 0.5) * 2 * Math.PI;
        });
    }

    let appAutoRotX = 0;
    let appAutoRotY = 0;

    function updateAppAvatarSpheres(rotX, rotY) {
        const t = (1.0 + Math.sqrt(5.0)) / 2.0;
        const vertices = [
            [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
            [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
            [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
        ];
        
        const R = 15.5;
        const len = Math.sqrt(1 + t*t);
        const normalizedVertices = vertices.map(v => [
            (v[0] / len) * R,
            (v[1] / len) * R,
            (v[2] / len) * R
        ]);
        
        const faces = [
            [0, 1, 5], [0, 5, 11], [0, 11, 10], [0, 10, 7], [0, 7, 1],
            [1, 9, 5], [5, 9, 4], [5, 4, 11], [11, 4, 2], [11, 2, 10],
            [10, 2, 6], [10, 6, 7], [7, 6, 8], [7, 8, 1], [1, 8, 9],
            [3, 9, 8], [3, 4, 9], [3, 2, 4], [3, 6, 2], [3, 8, 6]
        ];
        
        const cosX = Math.cos(rotX);
        const sinX = Math.sin(rotX);
        const cosY = Math.cos(rotY);
        const sinY = Math.sin(rotY);
        
        const rotated = normalizedVertices.map(v => {
            let x1 = v[0] * cosY - v[2] * sinY;
            let z1 = v[0] * sinY + v[2] * cosY;
            let y2 = v[1] * cosX - z1 * sinX;
            let z2 = v[1] * sinX + z1 * cosX;
            return [x1, y2, z2];
        });
        
        const centerX = 20;
        const centerY = 20;
        const d = 100;
        
        const projected = rotated.map(r => {
            const x = r[0];
            const y = r[1];
            const z = r[2];
            const scale = d / (d + z);
            return [x * scale + centerX, y * scale + centerY, z];
        });
        
        const facesData = [];
        const lightSource = [0.436, 0.436, 0.784];
        
        faces.forEach(face => {
            const vA = rotated[face[0]];
            const vB = rotated[face[1]];
            const vC = rotated[face[2]];
            
            const ux = vB[0] - vA[0];
            const uy = vB[1] - vA[1];
            const uz = vB[2] - vA[2];
            
            const vx = vC[0] - vA[0];
            const vy = vC[1] - vA[1];
            const vz = vC[2] - vA[2];
            
            let nx = uy * vz - uz * vy;
            let ny = uz * vx - ux * vz;
            let nz = ux * vy - uy * vx;
            
            const nLen = Math.sqrt(nx*nx + ny*ny + nz*nz);
            if (nLen > 0) {
                nx /= nLen;
                ny /= nLen;
                nz /= nLen;
            }
            
            const dot = nx * lightSource[0] + ny * lightSource[1] + nz * lightSource[2];
            const brightness = Math.max(0.15, dot);
            const avgZ = (vA[2] + vB[2] + vC[2]) / 3;
            
            facesData.push({
                pA: projected[face[0]],
                pB: projected[face[1]],
                pC: projected[face[2]],
                avgZ: avgZ,
                brightness: brightness
            });
        });
        
        facesData.sort((a, b) => b.avgZ - a.avgZ);
        
        const avatars = doc.querySelectorAll('.bot-avatar-svg');
        avatars.forEach(avatar => {
            let sphereGroup = avatar.querySelector('.geodesic-sphere');
            if (!sphereGroup) return;
            
            let polys = sphereGroup.querySelectorAll('polygon');
            if (polys.length !== 20) {
                sphereGroup.innerHTML = '';
                for (let i = 0; i < 20; i++) {
                    const poly = doc.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                    sphereGroup.appendChild(poly);
                }
                polys = sphereGroup.querySelectorAll('polygon');
            }
            
            facesData.forEach((f, idx) => {
                const poly = polys[idx];
                const pointsStr = `${f.pA[0].toFixed(2)},${f.pA[1].toFixed(2)} ${f.pB[0].toFixed(2)},${f.pB[1].toFixed(2)} ${f.pC[0].toFixed(2)},${f.pC[1].toFixed(2)}`;
                poly.setAttribute('points', pointsStr);
                
                const lightness = Math.round(25 + f.brightness * 42);
                poly.setAttribute('fill', `hsl(35, 75%, ${lightness}%)`);
                
                poly.setAttribute('stroke', '#f5c842');
                poly.setAttribute('stroke-width', '0.25');
                
                if (avatar.matches(':hover')) {
                    poly.setAttribute('fill-opacity', '0.92');
                    poly.setAttribute('stroke-opacity', '0.7');
                } else {
                    poly.setAttribute('fill-opacity', '0.8');
                    poly.setAttribute('stroke-opacity', '0.45');
                }
            });
        });
    }

    function animateAppSphere() {
        let reduced = false;
        doc.querySelectorAll('[data-testid="stCheckbox"] label').forEach(lbl => {
            if (lbl.innerText.includes("Reduce Motion")) {
                const btn = lbl.parentNode.querySelector('button[aria-checked="true"]');
                if (btn) reduced = true;
            }
        });
        
        if (!reduced) {
            appAutoRotX += 0.003;
            appAutoRotY += 0.005;
            
            const finalRotX = appAutoRotX + doc.sphereMouseOffset.y;
            const finalRotY = appAutoRotY + doc.sphereMouseOffset.x;
            
            updateAppAvatarSpheres(finalRotX, finalRotY);
        }
        
        window.parent.activeSphereLoopId = window.parent.requestAnimationFrame(animateAppSphere);
    }

    if (window.parent.activeSphereLoopId) {
        window.parent.cancelAnimationFrame(window.parent.activeSphereLoopId);
    }
    animateAppSphere();
</script>
""", height=0, width=0)


# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem 0; margin-top: 3rem; border-top: 1px solid rgba(212, 175, 55, 0.15);">
    <p style="font-size: 0.72rem; color: var(--concierge-silver); line-height: 1.6;">
        Powered by <strong>LangChain</strong> · <strong>ChromaDB</strong> · 
        <strong>Hugging Face Inference API</strong> · <strong>Ollama (Llama 3.2)</strong> · <strong>Streamlit</strong><br>
        OnboardBot v1.0.0 — Custom hand-crafted premium Obsidian & Gold interface for Nexus Technologies Pvt. Ltd.
    </p>
</div>
""", unsafe_allow_html=True)
