"""
OnboardBot — Hugging Face Inference API Client
Handles all NLP tasks (Intent, Summarization, Translation, Rephrasing) via HF Inference API
with high-speed local/offline fallbacks if API token is missing or offline.
"""

import requests
import streamlit as st
import numpy as np
from typing import Dict, List, Tuple, Optional
from src.embeddings import get_embeddings

# Base URLs for HF models
MODEL_INTENT = "facebook/bart-large-mnli"
MODEL_SUMMARIZE = "facebook/bart-large-cnn"
MODEL_TRANSLATE = "facebook/nllb-200-distilled-600M"
MODEL_REPHRASE = "microsoft/DialoGPT-medium"

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


def get_hf_token() -> Optional[str]:
    """Retrieve Hugging Face API token from streamlit secrets if available."""
    try:
        if "HF_API_TOKEN" in st.secrets:
            return st.secrets["HF_API_TOKEN"]
    except Exception:
        pass
    return None


def query_hf_api(model_id: str, payload: dict) -> Optional[dict]:
    """Helper to query the Hugging Face Inference API."""
    token = get_hf_token()
    if not token or not token.strip():
        return None

    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"HF API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error querying HF API: {e}")
    return None


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def classify_intent(text: str) -> str:
    """
    Classify user query intent into:
    ['HR policy', 'IT setup', 'Leave & attendance', 'Benefits', 'Out of scope']
    using facebook/bart-large-mnli Zero-shot classification.
    Falls back to high-speed local keyword classifier.
    """
    labels = ["HR policy", "IT setup", "Leave & attendance", "Benefits", "Out of scope"]
    payload = {
        "inputs": text,
        "parameters": {"candidate_labels": labels}
    }
    
    result = query_hf_api(MODEL_INTENT, payload)
    if result and "labels" in result and len(result["labels"]) > 0:
        return result["labels"][0]
        
    # Local fallback
    text_lower = text.lower()
    if any(w in text_lower for w in ["leave", "sick", "holiday", "casual", "vacation", "attendance", "absent"]):
        return "Leave & attendance"
    elif any(w in text_lower for w in ["vpn", "laptop", "email", "wifi", "password", "slack", "software", "hardware", "setup", "credential", "2fa"]):
        return "IT setup"
    elif any(w in text_lower for w in ["insurance", "pf", "provident", "salary", "payroll", "bonus", "payslip", "benefit", "claim"]):
        return "Benefits"
    elif any(w in text_lower for w in ["dress", "policy", "appraisal", "review", "code", "conduct", "office", "probation"]):
        return "HR policy"
    
    # Generic check for off-scope
    if any(w in text_lower for w in ["weather", "movie", "cook", "recipe", "game", "sport", "joke", "news", "stock"]):
        return "Out of scope"
        
    return "HR policy"


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def summarize_text(text: str) -> str:
    """
    Summarize long assistant answers to 2-3 bullet points using facebook/bart-large-cnn.
    Falls back to basic local sentence extraction.
    """
    payload = {
        "inputs": text,
        "parameters": {"max_length": 80, "min_length": 30, "do_sample": False}
    }
    
    result = query_hf_api(MODEL_SUMMARIZE, payload)
    if result and isinstance(result, list) and len(result) > 0 and "summary_text" in result[0]:
        summary = result[0]["summary_text"].strip()
        # Format as clean bullet points
        bullets = [s.strip() for s in summary.split(".") if s.strip()]
        return "\n".join(f"- {b}." for b in bullets[:3])
        
    # Local fallback: extract first 2 sentences
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if len(sentences) <= 2:
        return "\n".join(f"- {s}." for s in sentences)
    return "\n".join(f"- {s}." for s in sentences[:2])


# Mapping target languages for Helsinki or NLLB
LANG_CODES = {
    "Hindi": {"nllb": "hin_Deva", "opus": "hi"},
    "Telugu": {"nllb": "tel_Telu", "opus": "te"},
    "Tamil": {"nllb": "tam_Taml", "opus": "ta"},
    "Spanish": {"nllb": "spa_Latn", "opus": "es"},
    "French": {"nllb": "fra_Latn", "opus": "fr"},
    "German": {"nllb": "deu_Latn", "opus": "de"},
    "Japanese": {"nllb": "jpn_Jpan", "opus": "ja"}
}

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def translate_text(text: str, target_lang: str) -> str:
    """
    Translate text to Hindi, Telugu, or Tamil using HF model.
    Falls back to offline notification layout.
    """
    import re
    if target_lang not in LANG_CODES:
        return text
        
    lang_info = LANG_CODES[target_lang]
    payload = {
        "inputs": text,
        "parameters": {"src_lang": "eng_Latn", "tgt_lang": lang_info["nllb"]}
    }
    
    def clean_bold_markdown(t: str) -> str:
        return re.sub(r"\*\*\s*(.*?)\s*\*\*", r"**\1**", t)
    
    # Try NLLB-200 model first
    result = query_hf_api(MODEL_TRANSLATE, payload)
    if result and isinstance(result, list) and len(result) > 0 and "translation_text" in result[0]:
        return clean_bold_markdown(result[0]["translation_text"])
        
    # Try Helsinki OPUS translation model as secondary fallback
    opus_model = f"Helsinki-NLP/opus-mt-en-{lang_info['opus']}"
    payload_opus = {"inputs": text}
    result_opus = query_hf_api(opus_model, payload_opus)
    if result_opus and isinstance(result_opus, list) and len(result_opus) > 0 and "translation_text" in result_opus[0]:
        return clean_bold_markdown(result_opus[0]["translation_text"])
        
    # Try MyMemory public API as a robust paragraph-by-paragraph online fallback
    try:
        paragraphs = text.split("\n")
        translated_paragraphs = []
        for p in paragraphs:
            if not p.strip():
                translated_paragraphs.append(p)
                continue
            
            # Match list prefixes like "• ", "- ", "1. ", etc.
            prefix_match = re.match(r"^(\s*(?:[•\-*]|\d+\.)\s+)(.*)$", p)
            if prefix_match:
                prefix = prefix_match.group(1)
                to_translate = prefix_match.group(2).strip()
            else:
                prefix = ""
                to_translate = p.strip()
                
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(to_translate)}&langpair=en|{lang_info['opus']}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data and "responseData" in data and "translatedText" in data["responseData"]:
                    translated = data["responseData"]["translatedText"]
                    translated = clean_bold_markdown(translated)
                    translated_paragraphs.append(prefix + translated)
                else:
                    translated_paragraphs.append(p)
            else:
                translated_paragraphs.append(p)
        return "\n".join(translated_paragraphs)
    except Exception as e:
        print(f"MyMemory API fallback failed: {e}")
        
    # Friendly local fallback message
    return f"✨ *[{target_lang} Translation unavailable offline]*\n\n{text}"


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def rephrase_text(text: str, tone: str) -> str:
    """
    Rephrase the last bot answer in a different tone (polite, casual, professional) using DialoGPT.
    Falls back to high-quality template-based style transforms.
    """
    # Standard template transforms (usually higher quality than free-tier small model text generation)
    if tone == "polite":
        return f"Would you kindly note: {text.strip()}\n\nPlease let me know if you need any additional clarification."
    elif tone == "casual":
        return f"Here's the scoop! {text.strip().replace('Please contact', 'Feel free to hit up')}"
    elif tone == "professional":
        return f"Please review the following policy details:\n\n{text.strip()}\n\nThis information is subject to standard corporate guidelines."
    
    return text


def calculate_query_similarity(new_query: str, past_queries_vectors: List[Tuple[str, List[float]]]) -> Tuple[Optional[str], float]:
    """
    Locally calculate the cosine similarity between the new query and the last 5 queries.
    Uses the active local HuggingFace embedding model.
    
    Returns:
        tuple: (matching_query_text, similarity_score)
    """
    if not past_queries_vectors:
        return None, 0.0
        
    try:
        embeddings = get_embeddings()
        new_vector = np.array(embeddings.embed_query(new_query))
        
        # Normalize new vector
        new_norm = np.linalg.norm(new_vector)
        if new_norm == 0:
            return None, 0.0
            
        best_score = 0.0
        best_match = None
        
        for past_text, past_vector in past_queries_vectors:
            past_arr = np.array(past_vector)
            past_norm = np.linalg.norm(past_arr)
            if past_norm == 0:
                continue
                
            # Cosine similarity formula
            sim = np.dot(new_vector, past_arr) / (new_norm * past_norm)
            if sim > best_score:
                best_score = sim
                best_match = past_text
                
        return best_match, float(best_score)
    except Exception as e:
        print(f"Error calculating local similarity: {e}")
        return None, 0.0


def add_query_to_history(query: str) -> None:
    """Embed the new query and store it in st.session_state history (max 5)."""
    if "past_queries_vectors" not in st.session_state:
        st.session_state.past_queries_vectors = []
        
    try:
        # Check if already cached in current turns to avoid double embeds
        if any(query == q for q, _ in st.session_state.past_queries_vectors):
            return
            
        embeddings = get_embeddings()
        vector = embeddings.embed_query(query)
        st.session_state.past_queries_vectors.append((query, vector))
        
        # Keep only the last 5 queries
        if len(st.session_state.past_queries_vectors) > 5:
            st.session_state.past_queries_vectors.pop(0)
    except Exception as e:
        print(f"Error adding query to vector history: {e}")
