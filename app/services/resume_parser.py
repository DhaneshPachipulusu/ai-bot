import json
from app.config import USE_MOCK_AI, client
from app.utils.prompts import RESUME_PARSE_PROMPT
from app.config import USE_MOCK_AI

MOCK_RESUME_DATA = {
    "name": "Pachipulusu Dhaneswara Rao",
    "skills": ["Python", "Docker", "AWS"]
}

def parse_resume(resume_text: str) -> dict:
    if USE_MOCK_AI:
        return MOCK_RESUME_DATA

    try:
        prompt = f"""
{RESUME_PARSE_PROMPT}

Return ONLY valid JSON.
No explanation.
Resume:
{resume_text}
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        return json.loads(response.text.strip())

    except Exception as e:
        return {
            "error": "Resume parsing failed",
            "reason": str(e),
            "fallback": MOCK_RESUME_DATA
        }
