import json
from app.config import USE_MOCK_AI, client

# ---------------- MOCKS ----------------

MOCK_ANSWER_ANALYSIS = {
    "fluency": 5,
    "grammar": 5,
    "technical_depth": 5,
    "confidence": 5,
    "clarity": 5
}

MOCK_FINAL_ANALYSIS = {
    "overall_score": 6,
    "fluency": 5,
    "grammar": 5,
    "technical_depth": 5,
    "confidence": 6,
    "clarity": 5,
    "response_pace": 5,
    "strengths": ["Understands basics"],
    "weaknesses": ["Needs more depth"],
    "recommendations": ["Practice explanations"],
    "job_readiness": "Junior – Needs Improvement"
}

# ==================================================
# 1️⃣ QUICK PER-ANSWER ANALYSIS (FOR CONVERSATION)
# ==================================================
def analyze_answer(answer: str) -> dict:
    """
    Lightweight analysis used DURING the interview
    (for deciding follow-ups).
    """

    if USE_MOCK_AI:
        return MOCK_ANSWER_ANALYSIS

    try:
        prompt = f"""
You are an interviewer analyzing a SINGLE spoken answer.

Return ONLY valid JSON.

Score each from 0 to 10:
- fluency
- grammar
- technical_depth
- confidence
- clarity

Answer:
{answer}
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        return json.loads(response.text.strip())

    except Exception:
        # Fallback keeps interview moving
        return MOCK_ANSWER_ANALYSIS


# ==================================================
# 2️⃣ FULL INTERVIEW ANALYSIS (FINAL REPORT)
# ==================================================
def analyze_interview(interview_file_path: str) -> dict:
    if USE_MOCK_AI:
        return MOCK_FINAL_ANALYSIS

    with open(interview_file_path) as f:
        interview_data = json.load(f)

    try:
        prompt = f"""
You are an expert interviewer.

Analyze the full interview and return ONLY JSON.

FIELDS:
- overall_score
- fluency
- grammar
- technical_depth
- confidence
- clarity
- response_pace
- strengths (array)
- weaknesses (array)
- recommendations (array)
- job_readiness (string)

Interview data:
{json.dumps(interview_data)}
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        return json.loads(response.text.strip())

    except Exception:
        return MOCK_FINAL_ANALYSIS
