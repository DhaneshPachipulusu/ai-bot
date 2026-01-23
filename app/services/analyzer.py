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

MOCK_RESUME_ANALYSIS = {
    "ats_score": 72,
    "keyword_score": 75,
    "format_score": 70,
    "content_score": 68,
    "sections": [
        {"name": "Contact Info", "score": 60, "status": "weak", "feedback": "Missing phone or LinkedIn"},
        {"name": "Summary", "score": 0, "status": "missing", "feedback": "Add a professional summary"},
        {"name": "Experience", "score": 65, "status": "weak", "feedback": "Add measurable achievements"},
        {"name": "Education", "score": 80, "status": "good", "feedback": "Clear and complete"},
        {"name": "Skills", "score": 85, "status": "excellent", "feedback": "Good variety of skills"},
        {"name": "Projects", "score": 90, "status": "excellent", "feedback": "Strong project descriptions"},
    ],
    "ats_checks": [
        {"name": "Contact Information", "passed": True, "message": "", "priority": "critical"},
        {"name": "Standard Section Headings", "passed": True, "message": "", "priority": "critical"},
        {"name": "No Tables/Graphics", "passed": True, "message": "", "priority": "critical"},
        {"name": "Professional Summary", "passed": False, "message": "Add 2-3 sentence summary at top", "priority": "warning"},
        {"name": "Measurable Achievements", "passed": False, "message": "Add numbers: %, $, time saved", "priority": "warning"},
        {"name": "Action Verbs", "passed": True, "message": "", "priority": "info"},
        {"name": "Consistent Date Format", "passed": True, "message": "", "priority": "info"},
        {"name": "Appropriate Length", "passed": True, "message": "", "priority": "info"},
    ],
    "skills_found": ["Python", "JavaScript", "SQL", "FastAPI", "React", "Docker"],
    "missing_skills": ["AWS", "CI/CD", "Unit Testing"],
    "strengths": [
        "Strong technical skills in modern technologies",
        "Relevant project experience with metrics",
        "Clear education background"
    ],
    "critical_issues": [
        "Missing professional summary section",
        "Work experience lacks quantifiable achievements"
    ],
    "improvements": [
        "Add 2-3 line professional summary",
        "Include metrics in experience (%, $, time)",
        "Add LinkedIn profile URL"
    ],
    "experience_level": "Entry Level (0-2 years)"
}


# ==================================================
# 1️⃣ QUICK PER-ANSWER ANALYSIS (FOR CONVERSATION)
# ==================================================
def analyze_answer(answer: str) -> dict:
    if USE_MOCK_AI:
        return MOCK_ANSWER_ANALYSIS

    try:
        prompt = f"""
You are an interviewer analyzing a SINGLE spoken answer.
Return ONLY valid JSON. Score each from 0 to 10:
- fluency
- grammar
- technical_depth
- confidence
- clarity

Answer: {answer}
"""
        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )
        return json.loads(response.text.strip())
    except Exception:
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
- overall_score, fluency, grammar, technical_depth, confidence, clarity, response_pace
- strengths (array), weaknesses (array), recommendations (array)
- job_readiness (string)

Interview data: {json.dumps(interview_data)}
"""
        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )
        return json.loads(response.text.strip())
    except Exception:
        return MOCK_FINAL_ANALYSIS


# ==================================================
# 3️⃣ ATS RESUME ANALYSIS
# ==================================================
def analyze_resume(parsed_resume: dict, job_description: str = None) -> dict:
    """
    Analyze resume like a real ATS system.
    Scoring: Keywords (40%) + Format (35%) + Content (25%)
    """
    
    if USE_MOCK_AI:
        mock = MOCK_RESUME_ANALYSIS.copy()
        if "skills" in parsed_resume and parsed_resume["skills"]:
            mock["skills_found"] = parsed_resume["skills"][:15]
        return mock

    try:
        jd_context = f"\nJob Description to match against:\n{job_description}" if job_description else ""
        
        prompt = f"""You are an ATS (Applicant Tracking System) resume analyzer.
Analyze this resume and return a detailed JSON report.

SCORING BREAKDOWN:
- keyword_score (40%): Relevant skills/keywords found
- format_score (35%): ATS-readable formatting
- content_score (25%): Quality of content, achievements

Return ONLY valid JSON with this exact structure:
{{
    "ats_score": <0-100 weighted average>,
    "keyword_score": <0-100>,
    "format_score": <0-100>,
    "content_score": <0-100>,
    "sections": [
        {{"name": "Contact Info", "score": <0-100>, "status": "<missing|weak|good|excellent>", "feedback": "<10 words max>"}},
        {{"name": "Summary", "score": <0-100>, "status": "<missing|weak|good|excellent>", "feedback": "<10 words max>"}},
        {{"name": "Experience", "score": <0-100>, "status": "<missing|weak|good|excellent>", "feedback": "<10 words max>"}},
        {{"name": "Education", "score": <0-100>, "status": "<missing|weak|good|excellent>", "feedback": "<10 words max>"}},
        {{"name": "Skills", "score": <0-100>, "status": "<missing|weak|good|excellent>", "feedback": "<10 words max>"}},
        {{"name": "Projects", "score": <0-100>, "status": "<missing|weak|good|excellent>", "feedback": "<10 words max>"}}
    ],
    "ats_checks": [
        {{"name": "Contact Information Complete", "passed": <true|false>, "message": "<fix if failed, empty if passed>", "priority": "critical"}},
        {{"name": "Standard Section Headings", "passed": <true|false>, "message": "", "priority": "critical"}},
        {{"name": "No Complex Formatting", "passed": <true|false>, "message": "", "priority": "critical"}},
        {{"name": "Professional Summary", "passed": <true|false>, "message": "", "priority": "warning"}},
        {{"name": "Measurable Achievements", "passed": <true|false>, "message": "", "priority": "warning"}},
        {{"name": "Action Verbs Used", "passed": <true|false>, "message": "", "priority": "info"}},
        {{"name": "Consistent Date Format", "passed": <true|false>, "message": "", "priority": "info"}},
        {{"name": "Appropriate Length", "passed": <true|false>, "message": "", "priority": "info"}}
    ],
    "skills_found": ["skill1", "skill2", ...],
    "missing_skills": ["recommended1", "recommended2", ...],
    "strengths": ["<1 line each, max 4>"],
    "critical_issues": ["<urgent fixes needed, 1 line each>"],
    "improvements": ["<quick wins, 1 line each>"],
    "experience_level": "<Entry Level (0-2 years) | Mid Level (3-5 years) | Senior (5+ years)>"
}}

RULES:
- Score 80+ = likely to pass ATS
- Score 60-79 = may get filtered out
- Score <60 = will likely be rejected
- Keep all feedback SHORT and ACTIONABLE
- critical_issues = things that WILL get resume rejected
- improvements = nice-to-have fixes
{jd_context}

Resume data:
{json.dumps(parsed_resume)}
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        # Clean and parse response
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())

    except Exception as e:
        print(f"Resume analysis error: {e}")
        # Return enhanced mock as fallback
        mock = MOCK_RESUME_ANALYSIS.copy()
        if "skills" in parsed_resume and parsed_resume["skills"]:
            mock["skills_found"] = parsed_resume["skills"][:15]
        return mock