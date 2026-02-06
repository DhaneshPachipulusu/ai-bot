"""
Config - API Keys and Settings
==============================
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# AI Configuration
# ==========================================

USE_MOCK_AI = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not set - AI features disabled")
    USE_MOCK_AI = True

# Model to use
GEMINI_MODEL = "gemini-2.0-flash"

# ==========================================
# Initialize Gemini Client (NEW SDK)
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
# Interview Settings
# ==========================================

DEFAULT_MAX_QUESTIONS = 10
DEFAULT_MAX_DURATION_MINS = 25

# ==========================================
# Database
# ==========================================

DATABASE_PATH = "interview_bot.db"