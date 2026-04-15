import sys
import threading
import time

from app import create_app
from config.settings import ANTHROPIC_API_KEY, LLM_BACKEND, OLLAMA_MODEL, FLASK_PORT


def check_ollama():
    """Verify Ollama is reachable before starting."""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


def start_flask(app):
    app.run(debug=False, port=FLASK_PORT, use_reloader=False)


def main():
    if LLM_BACKEND == "anthropic":
        if not ANTHROPIC_API_KEY:
            print("\n[ERROR] LLM_BACKEND=anthropic but ANTHROPIC_API_KEY is not set in .env")
            sys.exit(1)
    else:
        # Ollama mode — check it's running
        if not check_ollama():
            print("\n[ERROR] Ollama is not running. Start it first:")
            print("  1. Install: https://ollama.com/download")
            print(f"  2. Pull model: ollama pull {OLLAMA_MODEL}")
            print("  3. It starts automatically, or run: ollama serve\n")
            sys.exit(1)
        print(f"[OK] Ollama is running  (model: {OLLAMA_MODEL})")

    app = create_app()
    flask_thread = threading.Thread(target=start_flask, args=(app,), daemon=True)
    flask_thread.start()
    time.sleep(1.2)

    backend_label = f"Anthropic claude-sonnet-4-6" if LLM_BACKEND == "anthropic" else f"Ollama / {OLLAMA_MODEL}"

    print(f"\n{'='*54}")
    print(f"  IT Admin Panel  →  http://127.0.0.1:{FLASK_PORT}")
    print(f"  AI Chat UI      →  http://127.0.0.1:{FLASK_PORT}/chat")
    print(f"  LLM Backend     →  {backend_label}")
    print(f"{'='*54}")
    print("\nType an IT request or open the Chat UI in your browser.")
    print("Type 'quit' to exit.\n")

    from agent.agent import run_agent

    while True:
        try:
            task = input("IT request> ").strip()
            if not task:
                continue
            if task.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            print()
            run_agent(task)
            print()
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    main()
