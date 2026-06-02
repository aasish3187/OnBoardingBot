"""
OnboardBot — Main Chatbot Logic
High-level chatbot class that wraps the RAG chain and manages state.
"""

from typing import Dict, List, Optional

from src.config import APP_NAME, APP_DESCRIPTION, OLLAMA_MODEL
from src.vector_store import load_vector_store, get_vector_store_stats
from src.rag_chain import get_llm, query_rag
from src.hr_contacts import get_all_contacts_formatted


class OnboardBot:
    """
    OnboardBot chatbot class.
    Manages the vector store connection, LLM, and conversation history.
    """
    
    def __init__(self):
        """Initialize OnboardBot with vector store and LLM."""
        self.name = APP_NAME
        self.description = APP_DESCRIPTION
        self.conversation_history: List[Dict[str, str]] = []
        
        # Load components
        print(f"\n{'═' * 60}")
        print(f"  {self.name} — {self.description}")
        print(f"{'═' * 60}")
        print(f"\n🚀 Initializing OnboardBot...")
        
        # Load vector store
        print(f"\n📦 Loading vector store...")
        self.vector_store = load_vector_store()
        
        # Initialize LLM
        print(f"\n🤖 Connecting to Ollama ({OLLAMA_MODEL})...")
        self.llm = get_llm()
        
        print(f"\n✅ OnboardBot is ready! Ask me anything about:")
        print(f"   📋 HR Handbook — Policies, values, benefits, conduct")
        print(f"   💻 IT Setup — Laptop, VPN, email, software, 2FA")
        print(f"   🏖️  Leave Policy — Leave types, holidays, attendance")
        print(f"\n{'═' * 60}\n")
    
    def ask(self, question: str) -> Dict:
        """
        Ask OnboardBot a question.
        
        Args:
            question: The user's question string.
        
        Returns:
            Dictionary with answer, sources, and metadata.
        """
        # Store the question in history
        self.conversation_history.append({
            "role": "user",
            "content": question,
        })
        
        # Query the RAG chain
        result = query_rag(
            vector_store=self.vector_store,
            question=question,
            llm=self.llm,
        )
        
        # Store the answer in history
        self.conversation_history.append({
            "role": "assistant",
            "content": result["answer"],
        })
        
        return result
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
    
    def get_stats(self) -> Dict:
        """Get chatbot statistics."""
        vs_stats = get_vector_store_stats(self.vector_store)
        return {
            "model": OLLAMA_MODEL,
            "conversation_turns": len(self.conversation_history) // 2,
            **vs_stats,
        }
    
    def get_all_contacts(self) -> str:
        """Get all HR contacts formatted for display."""
        return get_all_contacts_formatted()
    
    def get_welcome_message(self) -> str:
        """Get the welcome message for new users."""
        return (
            f"👋 **Welcome to {self.name}!**\n\n"
            f"I'm your AI-powered onboarding assistant for **Nexus Technologies**. "
            f"I can help you with questions about:\n\n"
            f"- 📋 **Company policies** — dress code, conduct, values, reviews\n"
            f"- 💻 **IT setup** — laptop, VPN, email, Slack, software, 2FA\n"
            f"- 🏖️ **Leave & attendance** — leave types, holidays, applications\n"
            f"- 💰 **Benefits** — insurance, PF, wellness programs\n\n"
            f"Just type your question below and I'll find the answer from our "
            f"official HR documents! 🚀\n\n"
            f"_If I can't find the answer, I'll direct you to the right HR contact._"
        )
