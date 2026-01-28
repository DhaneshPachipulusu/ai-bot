"""
Utility Prompts
===============
Prompts for resume parsing and question generation.
"""

RESUME_PARSE_PROMPT = """
You MUST return only valid JSON.
Do NOT add explanations, markdown, or text.

Extract:
- name
- total_experience_years (number)
- skills (array)
- tools_and_technologies (array)
- projects (array of {name, description, tech_stack})
- role_type (backend | frontend | fullstack | devops | data | mobile)
- seniority_level (beginner | intermediate | advanced)

Resume text:
"""

QUESTION_GENERATION_PROMPT = """
You are an experienced technical interviewer.

Your task is to generate interview questions based on the candidate's resume data.

RULES (VERY IMPORTANT):
- Generate ONLY JSON
- No explanation
- No markdown
- No extra text

GUIDELINES:
- Candidate level is Junior / Beginner
- Questions should be clear and realistic
- Prefer resume-based questions
- Avoid overly theoretical or senior-level questions
- Mix different types of questions

QUESTION TYPES REQUIRED:
- skill (from skills / tools)
- project (from projects)
- scenario (real-world problem)
- behavioral (communication / teamwork)

STRUCTURE:
{
  "role": "<inferred role>",
  "difficulty": "<beginner | junior | intermediate>",
  "questions": [
    {
      "type": "skill | project | scenario | behavioral",
      "topic": "<skill or project name>",
      "question": "<question text>"
    }
  ]
}

NUMBER OF QUESTIONS:
- Minimum: 5
- Maximum: 8

FOCUS AREAS:
- Docker, Kubernetes, AWS (if present)
- Projects deployment & decisions
- Problem-solving thinking
- Basic DevOps understanding
"""