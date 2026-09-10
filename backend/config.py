"""
Config - Single source of truth for app settings.
=================================================
All important values are read from environment variables HERE (with safe
defaults), and every other module imports them from this file. No other module
should call os.getenv directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ------------------------------------------------------------------
# Small helpers for typed env parsing
# ------------------------------------------------------------------

def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_list(name: str, default: list) -> list:
    """Comma-separated env value -> list of trimmed strings."""
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


# ==========================================
# App
# ==========================================

APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# ==========================================
# AI / LLM Configuration
# ==========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model to use. gemini-2.0-flash was retired and 404s; 2.5-flash is the current
# fast tier. Override per-environment with the GEMINI_MODEL env var.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Allow forcing mock mode via env; also auto-enabled below if no key/SDK.
USE_MOCK_AI = _get_bool("USE_MOCK_AI", False)

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not set - AI features disabled")
    USE_MOCK_AI = True

# ==========================================
# Initialize Gemini Client (google-genai SDK)
# ==========================================

client = None

if GEMINI_API_KEY and not USE_MOCK_AI:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini AI client initialized (google-genai SDK)")
    except ImportError:
        print("⚠️ google-genai not installed. Run: pip install google-genai")
        USE_MOCK_AI = True
    except Exception as e:
        print(f"⚠️ Failed to initialize Gemini: {e}")
        USE_MOCK_AI = True

# ==========================================
# CORS
# ==========================================

# Comma-separated list in env, e.g.
# ALLOWED_ORIGINS=https://app.college.edu,https://staging.college.edu
ALLOWED_ORIGINS = _get_list(
    "ALLOWED_ORIGINS",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-bot-8xzr.vercel.app",
    ],
)

# ==========================================
# Interview Settings
# ==========================================

DEFAULT_MAX_QUESTIONS = _get_int("DEFAULT_MAX_QUESTIONS", 10)
DEFAULT_MAX_DURATION_MINS = _get_int("DEFAULT_MAX_DURATION_MINS", 25)

# ==========================================
# Database
# ==========================================

DATABASE_PATH = os.getenv("DATABASE_PATH", "interview_bot.db")
