"""
Interview V2 Routes - Improved for Demo
=======================================
Better questions and flow for conversational interviews.
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

# Create data directory
os.makedirs("data/interviews", exist_ok=True)


# ==========================================
# Request/Response Models
# ==========================================

class StartInterviewRequest(BaseModel):
    user_id: int
    mode: str = "resume"  # "resume" or "career"
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
# Question Bank - Better Questions for Demo
# ==========================================

# Introduction questions
INTRO_QUESTIONS = [
    "Hello! Please introduce yourself briefly - your name, background, and what you're passionate about.",
    "Welcome to this interview! Tell me about yourself and why you're interested in this role.",
]

# General questions for all roles
GENERAL_QUESTIONS = [
    "What motivated you to pursue a career in technology?",
    "Tell me about a challenging project you've worked on. What was your role and how did you overcome obstacles?",
    "How do you stay updated with the latest technologies and industry trends?",
    "Describe a situation where you had to learn something new quickly. How did you approach it?",
    "What's your approach to debugging when you encounter a difficult problem?",
    "How do you prioritize tasks when working on multiple projects?",
]

# Technical questions by domain
TECHNICAL_QUESTIONS = {
    "python": [
        "Can you explain what Python decorators are and give an example of when you would use them?",
        "What's the difference between a list and a tuple in Python? When would you use each?",
        "How does memory management work in Python? What is garbage collection?",
        "Explain the difference between shallow copy and deep copy in Python.",
    ],
    "javascript": [
        "Explain the difference between var, let, and const in JavaScript.",
        "What is the event loop in JavaScript and how does it work?",
        "Can you explain what closures are in JavaScript with an example?",
        "What's the difference between == and === in JavaScript?",
    ],
    "react": [
        "What are React hooks and why were they introduced?",
        "Explain the difference between state and props in React.",
        "What is the virtual DOM and how does React use it for performance?",
        "How do you manage global state in a React application?",
    ],
    "devops": [
        "What is Docker and how is it different from a virtual machine?",
        "Explain what a CI/CD pipeline is and why it's important.",
        "What is Kubernetes and when would you use it?",
        "How do you approach monitoring and logging in production systems?",
    ],
    "sql": [
        "Explain the different types of SQL JOINs with examples.",
        "What is database normalization and why is it important?",
        "How would you optimize a slow-running SQL query?",
        "What's the difference between WHERE and HAVING clauses?",
    ],
    "aws": [
        "What AWS services have you worked with? Describe a project using AWS.",
        "Explain the difference between EC2 and Lambda. When would you use each?",
        "What is a VPC and why is it important for security?",
        "How does S3 storage class selection affect cost and performance?",
    ],
    "ml": [
        "Can you explain the difference between supervised and unsupervised learning?",
        "What is overfitting and how do you prevent it?",
        "Describe a machine learning project you've worked on.",
        "How do you evaluate the performance of a classification model?",
    ],
}

# Behavioral questions
BEHAVIORAL_QUESTIONS = [
    "Tell me about a time you disagreed with a team member. How did you handle it?",
    "Describe a project where you had to meet a tight deadline. How did you manage your time?",
    "Give an example of how you've contributed to a team's success.",
    "What do you consider your greatest professional achievement so far?",
]

# Closing questions
CLOSING_QUESTIONS = [
    "Where do you see yourself professionally in the next 3-5 years?",
    "Why should we consider you for this role? What unique value can you bring?",
    "Do you have any questions about the role or the company?",
]


def get_questions_for_role(target_role: str, skills: list, experience_level: str) -> list:
    """Generate relevant questions based on role and skills."""
    
    questions = []
    
    # Start with intro
    questions.append(random.choice(INTRO_QUESTIONS))
    
    # Add 2-3 general questions
    questions.extend(random.sample(GENERAL_QUESTIONS, min(2, len(GENERAL_QUESTIONS))))
    
    # Detect relevant technical domains from skills
    skills_lower = " ".join(s.lower() for s in skills) if skills else ""
    role_lower = target_role.lower()
    
    # Add technical questions based on skills
    tech_questions_added = 0
    
    for domain, qs in TECHNICAL_QUESTIONS.items():
        if domain in skills_lower or domain in role_lower:
            # Add 2 questions from this domain
            questions.extend(random.sample(qs, min(2, len(qs))))
            tech_questions_added += 2
            if tech_questions_added >= 4:
                break
    
    # If no specific domain matched, add Python questions (common)
    if tech_questions_added == 0:
        questions.extend(random.sample(TECHNICAL_QUESTIONS["python"], 2))
    
    # Add 1 behavioral question
    questions.append(random.choice(BEHAVIORAL_QUESTIONS))
    
    # End with closing question
    questions.append(random.choice(CLOSING_QUESTIONS))
    
    return questions


# ==========================================
# Interview Endpoints
# ==========================================

@router.post("/interview/start")
def start_interview(request: StartInterviewRequest):
    """Start a new conversational interview session."""
    
    interview_id = str(uuid.uuid4())[:8]
    
    print(f"🎤 Starting interview {interview_id} for user {request.user_id}")
    
    # Determine target role from resume or request
    target_role = request.target_role or "Software Developer"
    skills = []
    candidate_name = "Candidate"
    
    if request.mode == "resume" and request.parsed_resume:
        skills = request.parsed_resume.get("skills", [])
        candidate_name = request.parsed_resume.get("name", "Candidate")
        
        if isinstance(skills, list) and skills:
            skill_text = " ".join(s.lower() for s in skills[:10])
            if "react" in skill_text or "frontend" in skill_text or "next" in skill_text:
                target_role = "Frontend Developer"
            elif "python" in skill_text or "django" in skill_text or "fastapi" in skill_text:
                target_role = "Python Developer"
            elif "devops" in skill_text or "docker" in skill_text or "kubernetes" in skill_text:
                target_role = "DevOps Engineer"
            elif "aws" in skill_text or "azure" in skill_text or "cloud" in skill_text:
                target_role = "Cloud Engineer"
            elif "machine learning" in skill_text or "ml" in skill_text or "data science" in skill_text:
                target_role = "ML Engineer"
            elif "java" in skill_text or "spring" in skill_text:
                target_role = "Java Developer"
    
    print(f"📋 Target role: {target_role}")
    print(f"🛠️ Skills: {skills[:5]}...")
    
    # Generate questions
    questions = get_questions_for_role(target_role, skills, request.experience_level)
    
    # Limit to requested max
    questions = questions[:request.max_questions]
    
    # Create interview state
    interview_state = {
        "interview_id": interview_id,
        "user_id": request.user_id,
        "mode": request.mode,
        "target_role": target_role,
        "candidate_name": candidate_name,
        "experience_level": request.experience_level,
        "max_questions": len(questions),
        "max_duration_mins": request.max_duration_mins,
        "questions": questions,
        "questions_asked": 0,
        "current_question_index": 0,
        "conversation_history": [],
        "topics_covered": [],
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "parsed_resume": request.parsed_resume
    }
    
    # Get first question (intro)
    first_question = questions[0]
    
    # Add to conversation history
    interview_state["conversation_history"].append({
        "role": "interviewer",
        "text": first_question,
        "timestamp": datetime.now().isoformat()
    })
    interview_state["questions_asked"] = 1
    interview_state["current_question_index"] = 0
    
    # Store interview
    active_interviews[interview_id] = interview_state
    save_interview(interview_state)
    
    return {
        "interview_id": interview_id,
        "target_role": target_role,  # Return detected role to frontend
        "message": {
            "text": first_question,
            "type": "question",
            "topic": "introduction"
        },
        "state": get_state_response(interview_state)
    }


@router.post("/interview/respond")
def respond_to_interview(request: RespondRequest):
    """Submit an answer and get the next question."""
    
    interview = get_interview(request.interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview["status"] != "active":
        raise HTTPException(status_code=400, detail="Interview is not active")
    
    print(f"📝 Received answer for interview {request.interview_id}")
    print(f"   Answer preview: {request.answer[:50]}...")
    
    # Add candidate's answer to history
    interview["conversation_history"].append({
        "role": "candidate",
        "text": request.answer,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": request.answer_duration_seconds
    })
    
    # Move to next question
    interview["current_question_index"] += 1
    
    # Check if interview should end
    is_complete = (
        interview["questions_asked"] >= interview["max_questions"] or
        interview["current_question_index"] >= len(interview["questions"])
    )
    
    if is_complete:
        interview["status"] = "completed"
        interview["end_time"] = datetime.now().isoformat()
        save_interview(interview)
        
        conclusion = f"That was excellent, {interview.get('candidate_name', 'Candidate')}! Thank you for your thoughtful answers. This concludes our interview. You'll receive your performance report shortly. Best of luck!"
        
        return {
            "message": {
                "text": conclusion,
                "type": "conclusion"
            },
            "state": get_state_response(interview),
            "is_complete": True
        }
    
    # Get next question
    next_question = interview["questions"][interview["current_question_index"]]
    
    # Add acknowledgment based on answer length
    acknowledgments = [
        "Great, thank you for that answer.",
        "Interesting perspective.",
        "Thanks for sharing that.",
        "Good point.",
        "I appreciate your detailed response.",
    ]
    
    ack = random.choice(acknowledgments) if len(request.answer) > 50 else ""
    full_response = f"{ack} {next_question}".strip()
    
    # Add to history
    interview["conversation_history"].append({
        "role": "interviewer",
        "text": full_response,
        "timestamp": datetime.now().isoformat()
    })
    interview["questions_asked"] += 1
    
    # Save state
    save_interview(interview)
    
    return {
        "message": {
            "text": full_response,
            "type": "question"
        },
        "state": get_state_response(interview),
        "is_complete": False,
        "performance_hint": {
            "answer_quality": "good" if len(request.answer) > 100 else "brief",
            "suggestion": None if len(request.answer) > 50 else "Try to elaborate more on your answers"
        }
    }


@router.post("/interview/end")
def end_interview(request: EndInterviewRequest):
    """End the interview session early."""
    
    interview = get_interview(request.interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview["status"] = "completed"
    interview["end_time"] = datetime.now().isoformat()
    interview["end_reason"] = request.reason
    
    save_interview(interview)
    
    # Calculate duration
    start = datetime.fromisoformat(interview["start_time"])
    end = datetime.fromisoformat(interview["end_time"])
    duration_mins = (end - start).seconds // 60
    
    return {
        "message": {
            "text": f"Thank you for your time, {interview.get('candidate_name', 'Candidate')}! Your interview has been recorded and you can view your report now.",
            "type": "conclusion"
        },
        "summary": {
            "duration_mins": duration_mins,
            "questions_answered": interview["questions_asked"],
            "strong_areas": ["Communication", "Technical Knowledge"],
            "areas_to_improve": ["Could provide more specific examples"],
            "overall_performance": "Good"
        },
        "report_id": request.interview_id
    }


@router.get("/interview/{interview_id}/status")
def get_status(interview_id: str, user_id: int):
    """Get current interview status."""
    
    interview = get_interview(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return get_state_response(interview)


@router.get("/interview/{interview_id}/history")
def get_history(interview_id: str, user_id: int):
    """Get conversation history."""
    
    interview = get_interview(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return {
        "interview_id": interview_id,
        "history": interview["conversation_history"]
    }


@router.post("/interview/{interview_id}/pause")
def pause_interview(interview_id: str, user_id: int):
    """Pause the interview."""
    
    interview = get_interview(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview["status"] = "paused"
    interview["paused_at"] = datetime.now().isoformat()
    save_interview(interview)
    
    return {"status": "paused", "interview_id": interview_id}


@router.post("/interview/{interview_id}/resume")
def resume_interview(interview_id: str, user_id: int):
    """Resume a paused interview."""
    
    interview = get_interview(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview["status"] = "active"
    save_interview(interview)
    
    return {"status": "active", "interview_id": interview_id}


# ==========================================
# Helper Functions
# ==========================================

def get_interview(interview_id: str) -> Optional[dict]:
    """Get interview from memory or file."""
    
    # Check memory first
    if interview_id in active_interviews:
        return active_interviews[interview_id]
    
    # Try loading from file
    file_path = f"data/interviews/{interview_id}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            interview = json.load(f)
            active_interviews[interview_id] = interview
            return interview
    
    return None


def save_interview(interview: dict):
    """Save interview to memory and file."""
    
    interview_id = interview["interview_id"]
    active_interviews[interview_id] = interview
    
    # Also save conversation history to correct location for analysis
    conversations_dir = "data/conversations"
    os.makedirs(conversations_dir, exist_ok=True)
    
    file_path = f"data/interviews/{interview_id}.json"
    conv_path = f"data/conversations/{interview_id}.json"
    
    with open(file_path, 'w') as f:
        json.dump(interview, f, indent=2)
    
    # Also save to conversations folder for analyzer
    with open(conv_path, 'w') as f:
        json.dump(interview, f, indent=2)


def get_state_response(interview: dict) -> dict:
    """Get formatted interview state for response."""
    
    start_time = datetime.fromisoformat(interview["start_time"])
    elapsed_mins = (datetime.now() - start_time).seconds // 60
    remaining_mins = max(0, interview["max_duration_mins"] - elapsed_mins)
    
    questions_remaining = interview["max_questions"] - interview["questions_asked"]
    progress = (interview["questions_asked"] / interview["max_questions"]) * 100
    
    return {
        "stage": interview["status"],
        "progress_percent": min(100, progress),
        "topics_covered": interview.get("topics_covered", []),
        "current_topic": "general",
        "questions_asked": interview["questions_asked"],
        "questions_remaining": max(0, questions_remaining),
        "time_elapsed_mins": elapsed_mins,
        "time_remaining_mins": remaining_mins,
        "target_role": interview.get("target_role", "Software Developer")
    }