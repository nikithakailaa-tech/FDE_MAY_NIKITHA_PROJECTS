"""
Configuration
=============
Central place for API keys, model names, and constants.
In production these come from environment variables / secrets manager.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY")
OPENROUTER_API_KEY   = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL  = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL     = "meta-llama/llama-3.3-70b-instruct:free"
LLM_MODEL            = "gpt-4o-mini"

# ── External APIs ─────────────────────────────────────────────────────────
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_WEATHER_KEY")
SERPER_API_KEY      = os.getenv("SERPER_API_KEY", "")
GOOGLE_MAPS_KEY     = os.getenv("GOOGLE_MAPS_KEY", "YOUR_MAPS_KEY")
GOOGLE_PLACES_KEY   = os.getenv("GOOGLE_PLACES_KEY", "YOUR_PLACES_KEY")

# ── App settings ──────────────────────────────────────────────────────────
MAX_RETRIES         = 3
OUTPUT_DIR          = "output"

# ── Memory ────────────────────────────────────────────────────────────────
MEMORY_FILE         = "memory/user_memory.json"   # simple JSON store (demo)
