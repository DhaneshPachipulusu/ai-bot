import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

USE_MOCK_AI = False
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(GEMINI_API_KEY)
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

# ✅ NEW CLIENT (v1, not v1beta)
client = genai.Client(api_key=GEMINI_API_KEY)
