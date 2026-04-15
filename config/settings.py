import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic (optional — only used if LLM_BACKEND=anthropic)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# LLM backend: "ollama" (default, free) or "anthropic"
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")

# Ollama settings (free local LLM — no API key needed)
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Flask
BASE_URL   = os.getenv("BASE_URL", "http://127.0.0.1:5000")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
HEADLESS   = os.getenv("HEADLESS", "false").lower() == "true"
