"""
Interview V2 Routes - AI Powered
================================
Uses Gemini AI (google-genai SDK) for dynamic questions and follow-ups.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
import json
import os
import random
from datetime import datetime

router = APIRouter()

# Create data directories
os.makedirs("data/interviews", exist_ok=True)
os.makedirs("data/conversations", exist_ok=True)

# ==========================================
# AI Setup - Using google-genai SDK
# ==========================================

AI_AVAILABLE = False
client = None
GEMINI_MODEL = "gemini-2.5-flash"

try:
    from app.config import client as gemini_client, USE_MOCK_AI, GEMINI_MODEL as MODEL
    GEMINI_MODEL = MODEL
    
    if gemini_client and not USE_MOCK_AI:
        client = gemini_client
        AI_AVAILABLE = True
        print("✅ Gemini AI available for interviews")
    else:
        print("⚠️ AI disabled - using fallback questions")
except Exception as e:
    print(f"⚠️ Gemini import failed: {e}")


def call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini API using google-genai SDK."""
    if not client:
        return None
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return None


# ==========================================
# Request/Response Models
# ==========================================

class StartInterviewRequest(BaseModel):
    user_id: int
    mode: str = "resume"
    parsed_resume: Optional[dict] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = "fresher"
    difficulty: Optional[str] = "auto"
    max_questions: Optional[int] = 10
    max_duration_mins: Optional[int] = 25


class RespondRequest(BaseModel):
    interview_id: str
    user_id: int
    answer: str
    answer_duration_seconds: Optional[int] = None


class EndInterviewRequest(BaseModel):
    interview_id: str
    user_id: int
    reason: Optional[str] = "user_ended"


# ==========================================
# In-memory storage
# ==========================================

active_interviews = {}


# ==========================================
# AI Functions
# ==========================================

# Interview stages for natural flow
INTERVIEW_STAGES = [
    "greeting",
    "self_intro", 
    "background",
    "skills_interest",
    "technical",
    "project",
    "behavioral",
    "closing"
]


def get_time_greeting(candidate_name: str) -> str:
    """Generate contextual greeting based on time of day."""
    hour = datetime.now().hour
    
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    # Clean up name
    name = candidate_name.split()[0] if candidate_name and candidate_name != "Candidate" else "there"
    
    greetings = [
        f"{time_greeting}, {name}! I'm your interviewer today. This will be a relaxed, conversational session. How are you doing today?",
        f"{time_greeting}, {name}! Thanks for joining. Before we dive in, how's your day going so far?",
        f"{time_greeting}! Great to meet you, {name}. Let's keep this casual. How are you feeling today?",
    ]
    
    return random.choice(greetings)


def flatten_skills(skills) -> list:
    """Normalize skills into a flat list of strings.

    Skills can arrive as a flat list (from /upload-resume) or as a nested dict
    (from the resume-builder schema: {languages: [...], databases: [...], ...}).
    Without this, dict-shaped skills silently break the keyword logic downstream.
    """
    if isinstance(skills, dict):
        flat = []
        for value in skills.values():
            if isinstance(value, list):
                flat.extend(str(v) for v in value if v)
            elif value:
                flat.append(str(value))
        return flat
    if isinstance(skills, list):
        return [str(s) for s in skills if s]
    return []


def build_resume_context(interview: dict) -> str:
    """Build a compact summary of the candidate's actual resume.

    This is what makes the interview genuinely resume-based: the model can ask
    about *their* projects/experience by name instead of generic placeholders.
    """
    resume = interview.get("parsed_resume") or {}
    parts = []

    # Experience / internships
    exp_lines = []
    for exp in (resume.get("experience") or [])[:3]:
        if not isinstance(exp, dict):
            continue
        title = exp.get("title") or exp.get("role") or ""
        company = exp.get("company") or ""
        date = exp.get("date") or ""
        header = " | ".join(p for p in [title, company, date] if p)
        bullets = exp.get("responsibilities") or exp.get("bullets") or []
        if isinstance(bullets, str):
            bullets = [bullets]
        line = f"- {header}" if header else "-"
        if bullets:
            line += ": " + "; ".join(b for b in bullets[:2] if b)
        elif exp.get("description"):
            line += ": " + str(exp["description"])[:160]
        if line.strip("- "):
            exp_lines.append(line)
    if exp_lines:
        parts.append("EXPERIENCE / INTERNSHIPS:\n" + "\n".join(exp_lines))

    # Projects
    proj_lines = []
    for proj in (resume.get("projects") or [])[:3]:
        if not isinstance(proj, dict):
            continue
        name = proj.get("name") or proj.get("title") or ""
        tech = proj.get("technologies") or proj.get("tech") or ""
        desc = proj.get("description") or ""
        if not desc and isinstance(proj.get("bullets"), list):
            desc = "; ".join(str(b) for b in proj["bullets"][:2] if b)
        line = f"- {name}" if name else "-"
        if tech:
            line += f" (tech: {tech})"
        if desc:
            line += f": {str(desc)[:160]}"
        if line.strip("- "):
            proj_lines.append(line)
    if proj_lines:
        parts.append("PROJECTS:\n" + "\n".join(proj_lines))

    # Education
    edu_lines = []
    for edu in (resume.get("education") or [])[:2]:
        if not isinstance(edu, dict):
            continue
        degree = edu.get("degree") or ""
        inst = edu.get("institution") or ""
        score = edu.get("score") or edu.get("cgpa") or ""
        bits = [b for b in [degree, inst, score] if b]
        line = "- " + (" | ".join(bits) if bits else str(edu.get("description") or "")[:120])
        if line.strip("- "):
            edu_lines.append(line)
    if edu_lines:
        parts.append("EDUCATION:\n" + "\n".join(edu_lines))

    summary = resume.get("summary") or ""
    if summary:
        parts.append("SUMMARY: " + str(summary)[:200])

    if not parts:
        return "No detailed resume on file - ask questions based on the target role and listed skills."
    return "\n\n".join(parts)


def get_calibration_guidance(difficulty: str, experience_level: str) -> str:
    """Tell the interviewer how hard to push, based on chosen difficulty + level."""
    difficulty = (difficulty or "auto").lower()
    experience_level = (experience_level or "fresher").lower()

    level_note = {
        "fresher": "Candidate is a FRESHER/entry-level. Focus on fundamentals, college projects, internships, and how they think and learn. Do not expect production-scale experience.",
        "junior": "Candidate is JUNIOR with some experience. Mix fundamentals with practical application.",
        "mid": "Candidate is MID-LEVEL. Expect solid practical depth and some design/trade-off reasoning.",
        "senior": "Candidate is SENIOR. Probe architecture, trade-offs, scale, and decision-making.",
    }.get(experience_level, "Calibrate to the candidate's apparent experience.")

    diff_note = {
        "easy": "DIFFICULTY EASY: keep questions supportive and foundational, one concept at a time, stay encouraging.",
        "medium": "DIFFICULTY MEDIUM: standard interview depth with natural follow-ups when answers are thin.",
        "hard": "DIFFICULTY HARD: probe deeply - ask for trade-offs, edge cases, and the 'why' behind choices; politely challenge vague answers.",
    }.get(difficulty, "DIFFICULTY AUTO: calibrate to the candidate's experience level and how well they are answering.")

    return f"{level_note}\n{diff_note}"


def generate_dynamic_response(interview: dict, candidate_answer: str) -> dict:
    """
    Generate the next question dynamically based on conversation context.
    Returns: {"acknowledgment": "...", "question": "...", "decision": "...", "next_stage": "..."}
    """
    
    if not AI_AVAILABLE:
        return generate_fallback_response(interview, candidate_answer)
    
    # Build conversation context
    conversation = interview.get("conversation_history", [])
    conv_text = "\n".join([
        f"{'Interviewer' if turn['role'] == 'interviewer' else 'Candidate'}: {turn['text'][:200]}"
        for turn in conversation[-8:]  # Last 8 turns for context
    ])
    
    current_stage = interview.get("current_stage", "greeting")
    questions_asked = interview.get("questions_asked", 0)
    max_questions = interview.get("max_questions", 10)
    skills = interview.get("skills", [])[:8]
    target_role = interview.get("target_role", "Software Developer")
    candidate_name = (interview.get("candidate_name") or "the candidate").split()[0]

    resume_context = build_resume_context(interview)
    calibration = get_calibration_guidance(
        interview.get("difficulty", "auto"),
        interview.get("experience_level", "fresher"),
    )

    prompt = f"""You are Alex, a friendly technical interviewer conducting a real interview for a {target_role} position.
You are interviewing {candidate_name}.

## CANDIDATE'S RESUME (use this to ask SPECIFIC, personalized questions):
{resume_context}

## CALIBRATION:
{calibration}

## CONVERSATION SO FAR:
{conv_text}

## CANDIDATE'S LATEST ANSWER:
"{candidate_answer}"

## CURRENT STATE:
- Stage: {current_stage}
- Questions asked: {questions_asked} / {max_questions}
- Candidate skills: {', '.join(skills) if skills else 'Not specified'}

## YOUR TASK:
Analyze the candidate's answer and decide what to do next.

## DECISION RULES:
1. **If answer was SHORT/VAGUE (< 30 words)** → Ask for specific example or clarification
2. **If they mentioned something INTERESTING** → Dig deeper into that topic
3. **If answer was COMPLETE and GOOD** → Acknowledge positively and move to next topic
4. **If they said "I don't know"** → Be encouraging, ask how they'd learn it
5. **If STRUGGLING** → Simplify or move on gracefully

## STAGE PROGRESSION (current: {current_stage}):
greeting → self_intro → background → skills_interest → technical → project → behavioral → closing

Only advance stage when current topic is adequately covered.

## RESUME-GROUNDING RULES (IMPORTANT):
- In the 'project' stage, ask about a SPECIFIC project from their resume BY NAME (use the actual project title and tech listed) - never a generic "tell me about a project".
- In the 'technical' stage, anchor questions to the skills/tech they actually listed or used in those projects.
- In 'background'/'experience', reference their actual company/internship/role when one exists.
- Never invent projects, companies, or tech the resume does not mention. If the resume lacks detail for a stage, ask a general role-appropriate question instead.

## RULES:
- Ask ONLY ONE question
- Be conversational and natural
- Use their name occasionally
- Keep it professional but warm
- ONE concept per question (no mixed behavioral+technical)

Return ONLY valid JSON:
{{
  "decision": "follow_up | dig_deeper | move_on | encourage | close",
  "acknowledgment": "Brief 1-2 sentence acknowledgment of their answer",
  "question": "Your next question",
  "next_stage": "{current_stage} or next stage name"
}}"""

    response_text = call_gemini(prompt)
    
    if response_text:
        try:
            # Parse JSON response
            text = response_text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Find JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]
            
            result = json.loads(text)
            print(f"✅ AI decision: {result.get('decision', 'unknown')}")
            return result
            
        except Exception as e:
            print(f"⚠️ Failed to parse AI response: {e}")
    
    return generate_fallback_response(interview, candidate_answer)


def generate_fallback_response(interview: dict, candidate_answer: str) -> dict:
    """Fallback response when AI is unavailable."""
    
    current_stage = interview.get("current_stage", "greeting")
    questions_asked = interview.get("questions_asked", 0)
    word_count = len(candidate_answer.split()) if candidate_answer else 0
    skills = interview.get("skills", [])
    name = interview.get("candidate_name", "there").split()[0]
    
    # Stage-based fallback responses
    if current_stage == "greeting":
        return {
            "decision": "move_on",
            "acknowledgment": f"Nice to meet you, {name}!",
            "question": "Could you please introduce yourself briefly? Tell me about your background and what you're looking for.",
            "next_stage": "self_intro"
        }
    
    elif current_stage == "self_intro":
        return {
            "decision": "move_on",
            "acknowledgment": "Thanks for that introduction!",
            "question": "What technologies or areas do you enjoy working on the most?",
            "next_stage": "skills_interest"
        }
    
    elif current_stage == "skills_interest":
        skill = skills[0] if skills else "your main skill"
        return {
            "decision": "move_on",
            "acknowledgment": "That's great to hear!",
            "question": f"Let's talk about {skill}. Can you explain your experience with it?",
            "next_stage": "technical"
        }
    
    elif current_stage == "technical":
        if word_count < 20:
            return {
                "decision": "follow_up",
                "acknowledgment": "I see.",
                "question": "Can you give me a specific example of how you've used that?",
                "next_stage": "technical"
            }
        return {
            "decision": "move_on",
            "acknowledgment": "Good explanation!",
            "question": "Tell me about a project you worked on. What was your role and what did you build?",
            "next_stage": "project"
        }
    
    elif current_stage == "project":
        return {
            "decision": "move_on",
            "acknowledgment": "That sounds like a good experience!",
            "question": "What would you say are your key strengths?",
            "next_stage": "behavioral"
        }
    
    elif current_stage == "behavioral":
        return {
            "decision": "move_on",
            "acknowledgment": "Thanks for sharing that!",
            "question": f"We're almost done, {name}. Do you have any questions for me?",
            "next_stage": "closing"
        }
    
    else:  # closing
        return {
            "decision": "close",
            "acknowledgment": "Great questions!",
            "question": f"Thank you so much for your time, {name}! It was great talking with you. You'll receive your feedback report shortly. Best of luck!",
            "next_stage": "completed"
        }


def generate_ai_acknowledgment(answer: str) -> str:
    """Generate acknowledgment using AI."""
    
    defaults = ["Thank you.", "Got it.", "I see.", "Interesting.", "Good."]
    
    if not AI_AVAILABLE or len(answer) < 20:
        return random.choice(defaults)
    
    prompt = f"""The candidate just answered: "{answer[:150]}..."

Generate a brief acknowledgment (5-12 words) before the next question.
Be encouraging but professional. Return ONLY the acknowledgment."""

    response_text = call_gemini(prompt)
    
    if response_text:
        ack = response_text.strip().strip('"').strip("'")
        if 3 < len(ack) < 80:
            return ack
    
    return random.choice(defaults)



# ==========================================
# Fallback Questions
# ==========================================

FALLBACK = {
    "intro": [
        "Hello! Please introduce yourself - your background, skills, and what you're passionate about.",
        "Welcome! Tell me about yourself and your career goals.",
    ],
    "general": [
        "What motivated you to pursue technology?",
        "Tell me about a challenging project you worked on.",
        "How do you stay updated with new technologies?",
        "Describe your problem-solving approach.",
        "How do you handle tight deadlines?",
    ],
    "tech": {
        "python": ["Explain Python decorators.", "List vs tuple?", "What is GIL?"],
        "javascript": ["var vs let vs const?", "Explain event loop.", "What are closures?"],
        "react": ["What are React hooks?", "State vs props?", "Virtual DOM?"],
        "sql": ["Explain JOINs.", "What is normalization?", "Optimize slow queries?"],
        "devops": ["Docker vs VM?", "Explain CI/CD.", "What is Kubernetes?"],
        "java": ["Interface vs abstract class?", "OOP principles?", "Spring framework?"],
        "default": ["What is REST API?", "SQL vs NoSQL?", "Explain MVC."],
    },
    "behavioral": [
        "Tell me about a team disagreement.",
        "Describe meeting a tight deadline.",
        "Your greatest achievement?",
    ],
    "closing": [
        "Where do you see yourself in 5 years?",
        "Why should we hire you?",
        "Any questions for me?",
    ],
}


def get_fallback_questions(target_role: str, skills: list, mode: str) -> list:
    """Fallback questions when AI unavailable."""
    
    questions = [random.choice(FALLBACK["intro"])]
    questions.extend(random.sample(FALLBACK["general"], 2))
    
    # Tech questions based on skills
    skills_lower = " ".join(s.lower() for s in skills) if skills else ""
    role_lower = target_role.lower()
    tech_qs = []
    
    for tech, qs in FALLBACK["tech"].items():
        if tech in skills_lower or tech in role_lower:
            tech_qs.extend(qs[:2])
            if len(tech_qs) >= 4:
                break
    
    if len(tech_qs) < 2:
        tech_qs.extend(FALLBACK["tech"]["default"][:2])
    
    questions.extend(tech_qs[:4])
    questions.append(random.choice(FALLBACK["behavioral"]))
    questions.append(random.choice(FALLBACK["closing"]))
    
    return questions


def detect_role(skills: list) -> str:
    """Detect role from skills."""
    if not skills:
        return "Software Developer"
    
    s = " ".join(s.lower() for s in skills)
    
    if any(k in s for k in ["react", "angular", "vue", "frontend", "css"]):
        return "Frontend Developer"
    if any(k in s for k in ["django", "flask", "fastapi", "express", "node"]):
        return "Backend Developer"
    if any(k in s for k in ["python", "pandas"]):
        return "Python Developer"
    if any(k in s for k in ["docker", "kubernetes", "devops", "jenkins"]):
        return "DevOps Engineer"
    if any(k in s for k in ["aws", "azure", "gcp", "cloud"]):
        return "Cloud Engineer"
    if any(k in s for k in ["machine learning", "tensorflow", "pytorch", "ml"]):
        return "ML Engineer"
    if any(k in s for k in ["java", "spring"]):
        return "Java Developer"
    
    return "Software Developer"


# ==========================================
# Endpoints
# ==========================================

@router.post("/interview/start")
def start_interview(request: StartInterviewRequest):
    """Start AI-powered conversational interview."""
    
    interview_id = str(uuid.uuid4())[:8]
    print(f"🎤 Starting conversational interview {interview_id}, AI: {AI_AVAILABLE}")
    
    # Extract info
    skills = []
    candidate_name = "Candidate"
    
    if request.mode == "resume" and request.parsed_resume:
        skills = flatten_skills(request.parsed_resume.get("skills", []))
        candidate_name = request.parsed_resume.get("name", "Candidate")
    
    # IMPORTANT: Use user's explicit target_role if provided
    # Only auto-detect from skills if no role specified
    if request.target_role and request.target_role not in ["", "Software Engineer", "Software Developer"]:
        # User explicitly selected a role (e.g., DevOps Engineer)
        target_role = request.target_role
        print(f"🎯 Using user-selected role: {target_role}")
    elif skills:
        # Auto-detect from skills only if no explicit role
        target_role = detect_role(skills)
        print(f"🎯 Auto-detected role from skills: {target_role}")
    else:
        target_role = request.target_role or "Software Developer"
        print(f"🎯 Using default role: {target_role}")
    
    print(f"📋 Role: {target_role}, Skills: {skills[:5]}")
    
    # Generate proper greeting (time-based)
    greeting = get_time_greeting(candidate_name)
    print(f"👋 Greeting: {greeting[:50]}...")
    
    # Create state with stage tracking
    interview = {
        "interview_id": interview_id,
        "user_id": request.user_id,
        "mode": request.mode,
        "target_role": target_role,
        "candidate_name": candidate_name,
        "skills": skills,
        "experience_level": request.experience_level,
        "difficulty": request.difficulty,
        "max_questions": request.max_questions,
        "max_duration_mins": request.max_duration_mins,
        # Conversational flow - no pre-generated questions
        "current_stage": "greeting",
        "questions_asked": 1,
        "conversation_history": [{
            "role": "interviewer",
            "text": greeting,
            "timestamp": datetime.now().isoformat(),
            "stage": "greeting"
        }],
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "parsed_resume": request.parsed_resume,
        "ai_enabled": AI_AVAILABLE
    }
    
    active_interviews[interview_id] = interview
    save_interview(interview)
    
    return {
        "interview_id": interview_id,
        "target_role": target_role,
        "ai_enabled": AI_AVAILABLE,
        "message": {"text": greeting, "type": "greeting"},
        "state": get_state(interview)
    }


@router.post("/interview/respond")
def respond(request: RespondRequest):
    """Submit answer, get dynamically generated next question."""
    
    interview = get_interview(request.interview_id)
    if not interview:
        raise HTTPException(404, "Interview not found")
    if interview["status"] != "active":
        raise HTTPException(400, "Interview not active")
    
    print(f"📝 Answer received: {request.answer[:50]}...")
    print(f"📊 Current stage: {interview.get('current_stage', 'unknown')}, Questions: {interview.get('questions_asked', 0)}")
    
    # Save candidate's answer
    interview["conversation_history"].append({
        "role": "candidate",
        "text": request.answer,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": request.answer_duration_seconds,
        "stage": interview.get("current_stage", "unknown")
    })
    
    # Check if max questions reached
    if interview["questions_asked"] >= interview["max_questions"]:
        interview["status"] = "completed"
        interview["current_stage"] = "completed"
        interview["end_time"] = datetime.now().isoformat()
        
        name = interview.get("candidate_name", "there").split()[0]
        closing_msg = f"Thank you so much for your time, {name}! It was great talking with you. You'll receive your detailed feedback report shortly. Best of luck!"
        
        interview["conversation_history"].append({
            "role": "interviewer",
            "text": closing_msg,
            "timestamp": datetime.now().isoformat(),
            "stage": "closing"
        })
        
        save_interview(interview)
        return {
            "message": {"text": closing_msg, "type": "conclusion"},
            "state": get_state(interview),
            "is_complete": True
        }
    
    # Generate dynamic response based on conversation context
    ai_response = generate_dynamic_response(interview, request.answer)
    
    decision = ai_response.get("decision", "move_on")
    acknowledgment = ai_response.get("acknowledgment", "")
    question = ai_response.get("question", "Tell me more about your experience.")
    next_stage = ai_response.get("next_stage", interview.get("current_stage", "technical"))
    
    print(f"🤖 AI Decision: {decision}, Next stage: {next_stage}")
    
    # Build response text
    if acknowledgment:
        response_text = f"{acknowledgment} {question}"
    else:
        response_text = question
    
    # Check if interview should end
    if decision == "close" or next_stage == "completed":
        interview["status"] = "completed"
        interview["current_stage"] = "completed"
        interview["end_time"] = datetime.now().isoformat()
        
        interview["conversation_history"].append({
            "role": "interviewer",
            "text": response_text,
            "timestamp": datetime.now().isoformat(),
            "stage": "closing"
        })
        
        save_interview(interview)
        return {
            "message": {"text": response_text, "type": "conclusion"},
            "state": get_state(interview),
            "is_complete": True
        }
    
    # Update interview state
    interview["current_stage"] = next_stage
    interview["questions_asked"] += 1
    
    # Add interviewer response to history
    interview["conversation_history"].append({
        "role": "interviewer",
        "text": response_text,
        "timestamp": datetime.now().isoformat(),
        "stage": next_stage,
        "decision": decision
    })
    
    save_interview(interview)
    
    # Determine message type
    msg_type = "followup" if decision in ["follow_up", "dig_deeper"] else "question"
    
    return {
        "message": {"text": response_text, "type": msg_type},
        "state": get_state(interview),
        "is_complete": False
    }


@router.post("/interview/end")
def end_interview(request: EndInterviewRequest):
    """End interview."""
    
    interview = get_interview(request.interview_id)
    if not interview:
        raise HTTPException(404, "Interview not found")
    
    interview["status"] = "completed"
    interview["end_time"] = datetime.now().isoformat()
    interview["end_reason"] = request.reason
    save_interview(interview)
    
    start = datetime.fromisoformat(interview["start_time"])
    end = datetime.fromisoformat(interview["end_time"])
    
    return {
        "message": {"text": f"Thank you, {interview['candidate_name']}!", "type": "conclusion"},
        "summary": {"duration_mins": (end - start).seconds // 60, "questions": interview["questions_asked"]},
        "report_id": request.interview_id
    }


@router.get("/interview/{interview_id}/status")
def status(interview_id: str, user_id: int):
    interview = get_interview(interview_id)
    if not interview:
        raise HTTPException(404, "Not found")
    return get_state(interview)


@router.get("/interview/{interview_id}/history")
def history(interview_id: str, user_id: int):
    interview = get_interview(interview_id)
    if not interview:
        raise HTTPException(404, "Not found")
    return {"history": interview["conversation_history"]}


# ==========================================
# Helpers
# ==========================================

def get_interview(interview_id: str):
    if interview_id in active_interviews:
        return active_interviews[interview_id]
    
    for path in [f"data/interviews/{interview_id}.json", f"data/conversations/{interview_id}.json"]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                active_interviews[interview_id] = data
                return data
    return None


def save_interview(interview: dict):
    iid = interview["interview_id"]
    active_interviews[iid] = interview
    
    for path in [f"data/interviews/{iid}.json", f"data/conversations/{iid}.json"]:
        with open(path, 'w') as f:
            json.dump(interview, f, indent=2)


def get_state(interview: dict) -> dict:
    start = datetime.fromisoformat(interview["start_time"])
    elapsed = (datetime.now() - start).seconds // 60
    
    return {
        "stage": interview["status"],
        "current_stage": interview.get("current_stage", "unknown"),
        "progress_percent": min(100, (interview["questions_asked"] / interview["max_questions"]) * 100),
        "questions_asked": interview["questions_asked"],
        "questions_remaining": max(0, interview["max_questions"] - interview["questions_asked"]),
        "time_elapsed_mins": elapsed,
        "time_remaining_mins": max(0, interview["max_duration_mins"] - elapsed),
        "target_role": interview.get("target_role"),
        "ai_enabled": interview.get("ai_enabled", False)
    }