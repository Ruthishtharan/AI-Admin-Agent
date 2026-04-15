import os
from dotenv import load_dotenv

load_dotenv()

# Detect Replit environment
IS_REPLIT = bool(os.getenv("REPL_ID") or os.getenv("REPL_SLUG"))

# Anthropic (optional — only used if LLM_BACKEND=anthropic)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Groq (free, fast — used if LLM_BACKEND=groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Admin panel password (set in .env / Replit Secrets)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# LLM backend: "ollama" (default, free) | "anthropic" | "groq"
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")

# Ollama settings (free local LLM — no API key needed)
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Flask
BASE_URL   = os.getenv("BASE_URL", "http://127.0.0.1:5000")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Headless browser — always true on Replit, configurable elsewhere
_headless_env = os.getenv("HEADLESS", "").lower()
if _headless_env in ("true", "1", "yes"):
    HEADLESS = True
elif _headless_env in ("false", "0", "no"):
    HEADLESS = False
else:
    HEADLESS = IS_REPLIT  # default: headless on Replit, visible locally
