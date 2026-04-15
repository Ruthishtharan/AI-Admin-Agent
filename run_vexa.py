"""
Run the Vexa AI agent app on port 5000.
Make sure run_admin.py is already running (port 5001) before using Vexa.

Usage:
    python run_vexa.py
"""
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import GROQ_API_KEY, LLM_BACKEND, FLASK_PORT

def main():
    if LLM_BACKEND == "groq" and not GROQ_API_KEY:
        print("\n[ERROR] LLM_BACKEND=groq but GROQ_API_KEY is not set in .env\n")
        sys.exit(1)

    print(f"\n{'='*56}")
    print(f"  Vexa AI Agent   →  http://127.0.0.1:{FLASK_PORT}")
    print(f"  Admin Panel     →  http://127.0.0.1:5001  (run separately)")
    print(f"  LLM Backend     →  {LLM_BACKEND}")
    print(f"{'='*56}")
    print("\n  Start the admin panel first:  python run_admin.py")
    print(f"  Then open Vexa at:            http://127.0.0.1:{FLASK_PORT}/chat\n")

    from app import create_app
    vexa_app = create_app()
    vexa_app.run(host="127.0.0.1", port=FLASK_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
