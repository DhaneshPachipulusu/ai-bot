import json
from app.config import USE_MOCK_AI, client
from app.utils.prompts import QUESTION_GENERATION_PROMPT
from app.config import USE_MOCK_AI


# =========================
# MOCK QUESTIONS (SAFE FALLBACK)
# =========================
MOCK_QUESTIONS = {
    "role": "DevOps Engineer",
    "difficulty": "Junior",
    "questions": [
        {
            "type": "skill",
            "topic": "Docker",
            "question": "What is Docker and why is it used?"
        },
        {
            "type": "skill",
            "topic": "AWS EC2",
            "question": "What is EC2 and when would you use it?"
        },
        {
            "type": "project",
            "topic": "Flames Compatibility App",
            "question": "How did you deploy your Flask app using Docker on AWS?"
        },
        {
            "type": "scenario",
            "topic": "Production Issue",
            "question": "If your deployed application stops working, what steps would you take to debug it?"
        },
        {
            "type": "behavioral",
            "topic": "Learning",
            "question": "How do you approach learning a new tool or technology?"
        }
    ]
}


# =========================
# MAIN QUESTION GENERATOR
# =========================
def generate_questions(parsed_resume: dict) -> dict:
    """
    Generates interview questions from parsed resume data.
    """

    # 🔁 MOCK MODE (NO API COST)
    if USE_MOCK_AI:
        return MOCK_QUESTIONS

    try:
        prompt = f"""
{QUESTION_GENERATION_PROMPT}

Candidate Resume Data:
{json.dumps(parsed_resume)}
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        content = response.text.strip()
        questions = json.loads(content)

        # ✅ Safety checks
        if "questions" not in questions:
            raise ValueError("Invalid question format")

        # Limit question count defensively
        questions["questions"] = questions["questions"][:8]

        return questions

    except Exception as e:
        return {
            "error": "Question generation failed",
            "reason": str(e),
            "fallback": MOCK_QUESTIONS
        }
