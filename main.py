import os
import sys
import threading
import time

from app import create_app
from config.settings import ANTHROPIC_API_KEY, GROQ_API_KEY, LLM_BACKEND, OLLAMA_MODEL, FLASK_PORT

# Detect if running on Replit
IS_REPLIT = bool(os.getenv("REPL_ID") or os.getenv("REPL_SLUG"))


def check_ollama():
    """Verify Ollama is reachable before starting."""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


def start_flask(app, host="127.0.0.1"):
    app.run(debug=False, host=host, port=FLASK_PORT, use_reloader=False)


def main():
    # ── LLM backend check ──────────────────────────────────────
    if LLM_BACKEND == "anthropic":
        if not ANTHROPIC_API_KEY:
            print("\n[ERROR] LLM_BACKEND=anthropic but ANTHROPIC_API_KEY is not set.")
            if IS_REPLIT:
                print("  → Add it in Replit Secrets: ANTHROPIC_API_KEY = sk-ant-...")
            else:
                print("  → Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-...")
            sys.exit(1)
        print("[OK] Anthropic API key loaded  (model: claude-sonnet-4-6)")
    elif LLM_BACKEND == "groq":
        if not GROQ_API_KEY:
            print("\n[ERROR] LLM_BACKEND=groq but GROQ_API_KEY is not set.")
            if IS_REPLIT:
                print("  → Add it in Replit Secrets: GROQ_API_KEY = gsk_...")
            else:
                print("  → Add it to your .env file: GROQ_API_KEY=gsk_...")
            sys.exit(1)
        print("[OK] Groq API key loaded  (model: llama-3.3-70b-versatile)")
    elif not IS_REPLIT:
        # Ollama mode — only check locally (Ollama can't run on Replit)
        if not check_ollama():
            print("\n[ERROR] Ollama is not running. Start it first:")
            print("  1. Install: https://ollama.com/download")
            print(f"  2. Pull model: ollama pull {OLLAMA_MODEL}")
            print("  3. It starts automatically, or run: ollama serve\n")
            sys.exit(1)
        print(f"[OK] Ollama is running  (model: {OLLAMA_MODEL})")
    else:
        # On Replit with Ollama backend — warn and continue (chat UI still works)
        print("[WARN] Ollama backend selected but Ollama cannot run on Replit.")
        print("  → Set LLM_BACKEND=anthropic and ANTHROPIC_API_KEY in Replit Secrets.")
        print("  → The admin panel UI will still load; AI tasks will fail until key is set.\n")

    # ── Start Flask ─────────────────────────────────────────────
    app = create_app()

    # Bind to 0.0.0.0 on Replit so it's reachable publicly
    flask_host = "0.0.0.0" if IS_REPLIT else "127.0.0.1"
    flask_thread = threading.Thread(
        target=start_flask, args=(app, flask_host), daemon=True
    )
    flask_thread.start()
    time.sleep(1.2)

    if LLM_BACKEND == "anthropic":
        backend_label = "Anthropic claude-sonnet-4-6"
    elif LLM_BACKEND == "groq":
        backend_label = "Groq (llama-3.3-70b-versatile)"
    else:
        backend_label = f"Ollama / {OLLAMA_MODEL}"

    if IS_REPLIT:
        print(f"\n{'='*54}")
        print(f"  IT Admin Panel  →  Your Replit public URL")
        print(f"  AI Chat UI      →  Your Replit public URL/chat")
        print(f"  LLM Backend     →  {backend_label}")
        print(f"{'='*54}")
        print("\nServer is running. Use the Web Chat UI at /chat")
        print("Press Ctrl+C to stop.\n")
        # On Replit — keep alive without a blocking CLI loop
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nGoodbye.")
    else:
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
