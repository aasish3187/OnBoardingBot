"""
OnboardBot — Terminal Chat Interface
Color-coded REPL loop for quick testing and interaction.

Usage:
    python cli.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from src.chatbot import OnboardBot


console = Console()


def display_welcome(bot: OnboardBot):
    """Display the welcome panel."""
    welcome = bot.get_welcome_message()
    # Convert markdown bold to rich markup
    welcome_text = welcome.replace("**", "")
    
    console.print(Panel(
        welcome_text,
        title="🤖 OnboardBot",
        subtitle="Type 'quit' to exit | 'contacts' for HR directory | 'clear' to reset",
        border_style="cyan",
        padding=(1, 2),
    ))


def display_answer(result: dict):
    """Display the chatbot's answer with formatting."""
    if result["is_in_scope"]:
        style = "green"
        icon = "✅"
    else:
        style = "yellow"
        icon = "⚠️"
    
    console.print()
    console.print(Panel(
        Markdown(result["answer"]),
        title=f"{icon} OnboardBot",
        border_style=style,
        padding=(1, 2),
    ))


def main():
    """Run the CLI chat loop."""
    console.print()
    
    # Initialize the bot
    try:
        bot = OnboardBot()
    except FileNotFoundError as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print("[yellow]Run 'python ingest.py' first to set up the vector store.[/yellow]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error initializing OnboardBot: {e}[/red]")
        console.print("[yellow]Make sure Ollama is running: 'ollama serve'[/yellow]\n")
        sys.exit(1)
    
    # Display welcome message
    display_welcome(bot)
    
    # Chat loop
    while True:
        try:
            console.print()
            question = console.input("[bold cyan]You:[/bold cyan] ").strip()
            
            if not question:
                continue
            
            # Handle special commands
            if question.lower() in ("quit", "exit", "bye", "q"):
                console.print("\n[cyan]👋 Goodbye! Have a great day at Nexus Technologies![/cyan]\n")
                break
            
            if question.lower() == "contacts":
                contacts = bot.get_all_contacts()
                console.print(Panel(
                    Markdown(contacts),
                    title="📞 HR Contact Directory",
                    border_style="blue",
                    padding=(1, 2),
                ))
                continue
            
            if question.lower() == "clear":
                bot.clear_history()
                console.print("[dim]🗑️  Conversation history cleared.[/dim]")
                continue
            
            if question.lower() == "stats":
                stats = bot.get_stats()
                stats_text = "\n".join(f"  {k}: {v}" for k, v in stats.items())
                console.print(Panel(
                    stats_text,
                    title="📊 Bot Statistics",
                    border_style="magenta",
                    padding=(1, 1),
                ))
                continue
            
            if question.lower() == "help":
                console.print(Panel(
                    "Available commands:\n"
                    "  contacts  — Show all HR contacts\n"
                    "  stats     — Show bot statistics\n"
                    "  clear     — Clear conversation history\n"
                    "  help      — Show this help message\n"
                    "  quit      — Exit the chat",
                    title="❓ Help",
                    border_style="cyan",
                    padding=(1, 2),
                ))
                continue
            
            # Process the question
            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                result = bot.ask(question)
            
            display_answer(result)
            
        except KeyboardInterrupt:
            console.print("\n\n[cyan]👋 Goodbye![/cyan]\n")
            break
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            console.print("[dim]Please try again or type 'quit' to exit.[/dim]")


if __name__ == "__main__":
    main()
