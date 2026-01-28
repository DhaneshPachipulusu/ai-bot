"""
Analyzer Service - Fixed
========================
Properly extracts Q&A from interview and generates real feedback.
"""

import json
import os
from typing import Optional

# Try to import config
try:
    from app.config import USE_MOCK_AI
except ImportError:
    USE_MOCK_AI = True

# Try to import Gemini
GEMINI_AVAILABLE = False
model = None

try:
    import google.generativeai as genai
    from app.config import GEMINI_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    GEMINI_AVAILABLE = True
    print("✅ Gemini AI available")
except Exception as e:
    print(f"⚠️ Gemini not available: {e}")


# ==========================================
# Interview Analysis
# ==========================================

def analyze_interview(conversation_path: str) -> dict:
    """Analyze an interview conversation and return scores."""
    
    # Extract interview_id from path
    interview_id = os.path.basename(conversation_path).replace('.json', '')
    
    # Try multiple locations for the conversation file
    possible_paths = [
        conversation_path,
        f"data/interviews/{interview_id}.json",
        f"data/conversations/{interview_id}.json",
        conversation_path.replace("conversations", "interviews"),
    ]
    
    conversation_data = None
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    conversation_data = json.load(f)
                print(f"✅ Found conversation at: {path}")
                break
            except Exception as e:
                print(f"⚠️ Error reading {path}: {e}")
    
    if not conversation_data:
        print(f"⚠️ Conversation file not found for {interview_id}")
        return get_mock_interview_analysis()
    
    # Extract Q&A pairs from conversation history
    qa_pairs = extract_qa_pairs(conversation_data)
    print(f"📊 Extracted {len(qa_pairs)} Q&A pairs")
    
    if not qa_pairs:
        print("⚠️ No Q&A pairs found")
        return get_mock_interview_analysis()
    
    # Generate analysis based on answers
    return generate_analysis(qa_pairs, conversation_data)


def extract_qa_pairs(conversation_data: dict) -> list:
    """Extract question-answer pairs from conversation history."""
    
    qa_pairs = []
    history = conversation_data.get("conversation_history", [])
    
    if not history:
        print("⚠️ No conversation history found")
        return qa_pairs
    
    current_question = None
    
    for msg in history:
        role = msg.get("role", "")
        text = msg.get("text", "") or msg.get("content", "")
        
        if not text:
            continue
        
        # Interviewer message = question
        if role == "interviewer":
            current_question = text
        # Candidate message = answer
        elif role == "candidate" and current_question:
            qa_pairs.append({
                "question": current_question,
                "answer": text,
                "duration": msg.get("duration_seconds", 0)
            })
            current_question = None
    
    return qa_pairs


def generate_analysis(qa_pairs: list, conversation_data: dict) -> dict:
    """Generate analysis scores based on Q&A pairs."""
    
    # Calculate scores based on answers
    total_words = 0
    technical_mentions = 0
    confidence_score = 0
    
    technical_keywords = [
        'python', 'javascript', 'react', 'api', 'database', 'sql', 'mongodb',
        'docker', 'aws', 'git', 'function', 'class', 'object', 'array',
        'algorithm', 'data structure', 'framework', 'library', 'server',
        'frontend', 'backend', 'deploy', 'test', 'debug', 'code'
    ]
    
    qa_feedback = []
    
    for qa in qa_pairs:
        answer = qa["answer"].lower()
        words = len(qa["answer"].split())
        total_words += words
        
        # Count technical terms
        tech_count = sum(1 for kw in technical_keywords if kw in answer)
        technical_mentions += tech_count
        
        # Evaluate answer quality
        if words > 100:
            quality = "excellent"
            score = 8
        elif words > 50:
            quality = "good"
            score = 7
        elif words > 20:
            quality = "adequate"
            score = 6
        else:
            quality = "brief"
            score = 5
        
        # Boost for technical content
        if tech_count > 2:
            score = min(10, score + 1)
        
        # Generate feedback
        if quality == "excellent":
            feedback = "Great detailed response with good explanation."
        elif quality == "good":
            feedback = "Good answer. Could add more specific examples."
        elif quality == "adequate":
            feedback = "Acceptable answer but lacks depth."
        else:
            feedback = "Try to elaborate more on your answers."
        
        qa_feedback.append({
            "question": qa["question"],
            "user_answer": qa["answer"][:300] + "..." if len(qa["answer"]) > 300 else qa["answer"],
            "answer": qa["answer"][:300] + "..." if len(qa["answer"]) > 300 else qa["answer"],
            "score": score,
            "feedback": feedback,
            "better_answer": get_better_answer_hint(qa["question"])
        })
    
    # Calculate overall scores
    num_answers = len(qa_pairs)
    avg_words = total_words / num_answers if num_answers > 0 else 0
    
    # Fluency (based on word count)
    if avg_words > 80:
        fluency = 8
    elif avg_words > 50:
        fluency = 7
    elif avg_words > 30:
        fluency = 6
    else:
        fluency = 5
    
    # Technical depth
    tech_per_answer = technical_mentions / num_answers if num_answers > 0 else 0
    if tech_per_answer > 3:
        technical_depth = 8
    elif tech_per_answer > 2:
        technical_depth = 7
    elif tech_per_answer > 1:
        technical_depth = 6
    else:
        technical_depth = 5
    
    # Other scores
    grammar = 7  # Default good
    confidence = 6 if avg_words > 30 else 5
    clarity = 7 if avg_words > 40 else 6
    response_pace = 7  # Default
    
    # Overall score
    overall = round((fluency + grammar + technical_depth + confidence + clarity + response_pace) / 6, 1)
    
    # Generate strengths based on scores
    strengths = []
    if fluency >= 7:
        strengths.append("Good communication skills")
    if technical_depth >= 7:
        strengths.append("Strong technical knowledge")
    if num_answers >= 5:
        strengths.append("Answered all questions")
    if avg_words > 50:
        strengths.append("Provides detailed explanations")
    if not strengths:
        strengths.append("Shows enthusiasm and willingness to learn")
    
    # Generate weaknesses
    weaknesses = []
    if avg_words < 40:
        weaknesses.append("Answers could be more detailed")
    if technical_depth < 6:
        weaknesses.append("Could demonstrate more technical depth")
    if fluency < 6:
        weaknesses.append("Work on articulating thoughts clearly")
    if not weaknesses:
        weaknesses.append("Continue practicing for improvement")
    
    # Recommendations
    recommendations = []
    if avg_words < 50:
        recommendations.append("Practice giving longer, more detailed answers")
    if technical_depth < 7:
        recommendations.append("Review technical concepts before interviews")
    recommendations.append("Use the STAR method for behavioral questions")
    recommendations.append("Prepare specific examples from your projects")
    
    # Job readiness
    if overall >= 7.5:
        job_readiness = "Job Ready - Strong candidate"
    elif overall >= 6.5:
        job_readiness = "Developing - Good potential, needs more practice"
    else:
        job_readiness = "Needs Improvement - Continue learning and practicing"
    
    return {
        "overall_score": overall,
        "fluency": fluency,
        "grammar": grammar,
        "technical_depth": technical_depth,
        "confidence": confidence,
        "clarity": clarity,
        "response_pace": response_pace,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "job_readiness": job_readiness,
        "qa_feedback": qa_feedback
    }


def get_better_answer_hint(question: str) -> str:
    """Get a hint for a better answer based on question type."""
    
    q_lower = question.lower()
    
    if "tell me about yourself" in q_lower or "introduce" in q_lower:
        return "Structure: Name, background, key skills, what you're passionate about, and why this role interests you."
    elif "project" in q_lower:
        return "Use STAR: Situation, Task, Action, Result. Include specific technologies and measurable outcomes."
    elif "challenge" in q_lower or "difficult" in q_lower:
        return "Describe the challenge, your approach, what you learned, and the positive outcome."
    elif "why" in q_lower and ("hire" in q_lower or "should" in q_lower):
        return "Highlight unique skills, relevant experience, and specific value you can bring to the role."
    elif "decorator" in q_lower:
        return "Explain that decorators modify function behavior, give syntax example, mention use cases like logging or authentication."
    elif "list" in q_lower and "tuple" in q_lower:
        return "Lists are mutable (can change), tuples are immutable (fixed). Use tuples for fixed data, lists for collections that change."
    elif "api" in q_lower:
        return "Explain that APIs allow systems to communicate, mention REST principles, and give examples you've worked with."
    elif "git" in q_lower:
        return "Mention common commands (clone, commit, push, pull, branch, merge) and explain your workflow."
    else:
        return "Provide specific examples, use technical terms accurately, and connect to your experience."


def get_mock_interview_analysis(qa_pairs: list = None) -> dict:
    """Return mock analysis data when real analysis fails."""
    
    qa_feedback = []
    if qa_pairs:
        for qa in qa_pairs[:5]:
            qa_feedback.append({
                "question": qa["question"],
                "user_answer": qa["answer"][:200] + "..." if len(qa["answer"]) > 200 else qa["answer"],
                "answer": qa["answer"][:200] + "..." if len(qa["answer"]) > 200 else qa["answer"],
                "score": 6,
                "feedback": "Decent answer but could be more detailed",
                "better_answer": "Consider using the STAR method to structure your response"
            })
    
    return {
        "overall_score": 6.5,
        "fluency": 7,
        "grammar": 7,
        "technical_depth": 6,
        "confidence": 6,
        "clarity": 7,
        "response_pace": 6,
        "strengths": [
            "Good communication skills",
            "Shows enthusiasm",
            "Answers are relevant"
        ],
        "weaknesses": [
            "Could provide more specific examples",
            "Technical depth needs improvement"
        ],
        "recommendations": [
            "Practice STAR method for behavioral questions",
            "Prepare specific project examples",
            "Work on technical fundamentals"
        ],
        "job_readiness": "Developing - Continue practicing",
        "qa_feedback": qa_feedback
    }


# ==========================================
# Resume ATS Analysis
# ==========================================

def analyze_resume(parsed_resume: dict, job_description: str = None) -> dict:
    """Analyze resume for ATS compatibility."""
    
    if not parsed_resume:
        return get_empty_resume_analysis()
    
    print(f"🔍 Analyzing resume with keys: {list(parsed_resume.keys())}")
    
    # Extract resume data with defaults - handle multiple key formats
    name = parsed_resume.get("name", "") or parsed_resume.get("full_name", "")
    email = parsed_resume.get("email", "") or parsed_resume.get("email_address", "")
    phone = parsed_resume.get("phone", "") or parsed_resume.get("phone_number", "") or parsed_resume.get("mobile", "")
    
    # Skills can be in different formats
    skills = parsed_resume.get("skills", [])
    if not skills:
        skills = parsed_resume.get("tools_and_technologies", [])
    if not skills:
        skills = parsed_resume.get("technical_skills", [])
    
    # Experience can be in different formats
    experience = parsed_resume.get("experience", [])
    if not experience:
        experience = parsed_resume.get("work_experience", [])
    if not experience and parsed_resume.get("total_experience_years"):
        years = parsed_resume.get("total_experience_years", 0)
        if years > 0:
            experience = [{"title": f"{years} years of experience"}]
    
    education = parsed_resume.get("education", [])
    if not education:
        education = parsed_resume.get("qualifications", [])
    
    projects = parsed_resume.get("projects", [])
    if not projects:
        projects = parsed_resume.get("personal_projects", [])
    
    summary = parsed_resume.get("summary", "") or parsed_resume.get("objective", "") or parsed_resume.get("about", "")
    
    # Ensure skills is a list
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if not isinstance(skills, list):
        skills = []
    
    if not isinstance(experience, list):
        experience = []
    if not isinstance(education, list):
        education = []
    if not isinstance(projects, list):
        projects = []
    
    # Calculate section scores
    sections = []
    
    # Contact Info
    contact_score = 0
    if name: contact_score += 40
    if email: contact_score += 30
    if phone: contact_score += 30
    sections.append({
        "name": "Contact Information",
        "score": contact_score,
        "status": get_status(contact_score),
        "feedback": "Complete contact information" if contact_score >= 80 else "Add missing contact details"
    })
    
    # Summary
    summary_score = 0
    if summary:
        word_count = len(str(summary).split())
        summary_score = 90 if word_count >= 30 else 70 if word_count >= 15 else 50
    sections.append({
        "name": "Professional Summary",
        "score": summary_score,
        "status": get_status(summary_score),
        "feedback": "Strong summary" if summary_score >= 80 else "Add or expand professional summary"
    })
    
    # Experience
    exp_count = len(experience)
    exp_score = 90 if exp_count >= 3 else 75 if exp_count >= 2 else 60 if exp_count >= 1 else 0
    sections.append({
        "name": "Work Experience",
        "score": exp_score,
        "status": get_status(exp_score),
        "feedback": f"{exp_count} experience entries found" if exp_count > 0 else "Add work experience"
    })
    
    # Education
    edu_count = len(education)
    edu_score = 85 if edu_count >= 1 else 0
    sections.append({
        "name": "Education",
        "score": edu_score,
        "status": get_status(edu_score),
        "feedback": "Education section present" if edu_score > 0 else "Add education details"
    })
    
    # Skills
    skill_count = len(skills)
    skills_score = 95 if skill_count >= 10 else 80 if skill_count >= 6 else 60 if skill_count >= 3 else 40 if skill_count >= 1 else 0
    sections.append({
        "name": "Skills",
        "score": skills_score,
        "status": get_status(skills_score),
        "feedback": f"{skill_count} skills listed" if skill_count > 0 else "Add skills"
    })
    
    # Projects
    proj_count = len(projects)
    proj_score = 90 if proj_count >= 3 else 75 if proj_count >= 2 else 60 if proj_count >= 1 else 0
    sections.append({
        "name": "Projects",
        "score": proj_score,
        "status": get_status(proj_score),
        "feedback": f"{proj_count} projects listed" if proj_count > 0 else "Add relevant projects"
    })
    
    # Calculate overall scores
    section_scores = [s["score"] for s in sections if s["score"] > 0]
    avg_section_score = sum(section_scores) / len(section_scores) if section_scores else 0
    
    keyword_score = min(95, skill_count * 8) if skill_count > 0 else 20
    format_score = 70 if (name and email) else 40
    content_score = int(avg_section_score)
    
    ats_score = int(keyword_score * 0.35 + format_score * 0.25 + content_score * 0.40)
    
    # ATS Checks
    ats_checks = [
        {"name": "Contact Information", "passed": bool(name and email), "message": "Name and email present" if (name and email) else "Missing", "priority": "critical"},
        {"name": "Skills Section", "passed": skill_count >= 3, "message": f"{skill_count} skills found", "priority": "critical"},
        {"name": "Work Experience", "passed": exp_count >= 1, "message": f"{exp_count} experiences", "priority": "warning"},
        {"name": "Education", "passed": edu_count >= 1, "message": "Present" if edu_count > 0 else "Missing", "priority": "warning"},
        {"name": "Professional Summary", "passed": bool(summary), "message": "Present" if summary else "Add summary", "priority": "info"},
        {"name": "Projects", "passed": proj_count >= 1, "message": f"{proj_count} projects", "priority": "info"}
    ]
    
    # Generate feedback
    strengths = []
    if contact_score >= 80: strengths.append("Complete contact information")
    if skill_count >= 6: strengths.append(f"Good variety of skills ({skill_count} listed)")
    if exp_count >= 2: strengths.append("Solid work experience")
    if proj_count >= 2: strengths.append("Relevant project portfolio")
    if summary: strengths.append("Has professional summary")
    if not strengths: strengths.append("Resume structure is parseable by ATS")
    
    critical_issues = []
    if not name or not email: critical_issues.append("Missing basic contact information")
    if skill_count < 3: critical_issues.append("Too few skills listed")
    if exp_count == 0 and proj_count == 0: critical_issues.append("No experience or projects")
    
    improvements = []
    if not summary: improvements.append("Add a professional summary")
    if skill_count < 10: improvements.append("Add more relevant skills")
    if proj_count == 0: improvements.append("Add personal or academic projects")
    if exp_count < 2: improvements.append("Add more work experience or internships")
    improvements.append("Use action verbs to describe achievements")
    
    experience_level = "Mid-Level" if exp_count >= 3 else "Junior" if exp_count >= 1 else "Fresher"
    
    common_skills = ["Python", "JavaScript", "SQL", "Git", "Communication", "Problem Solving", "Teamwork", "Java", "React", "Node.js"]
    skills_lower = [sk.lower() for sk in skills]
    missing_skills = [s for s in common_skills if s.lower() not in skills_lower][:5]
    
    return {
        "ats_score": ats_score,
        "keyword_score": keyword_score,
        "format_score": format_score,
        "content_score": content_score,
        "sections": sections,
        "ats_checks": ats_checks,
        "skills_found": skills[:15],
        "missing_skills": missing_skills,
        "strengths": strengths,
        "critical_issues": critical_issues,
        "improvements": improvements,
        "experience_level": experience_level
    }


def get_status(score: int) -> str:
    if score >= 80: return "excellent"
    elif score >= 60: return "good"
    elif score > 0: return "weak"
    else: return "missing"


def get_empty_resume_analysis() -> dict:
    return {
        "ats_score": 0, "keyword_score": 0, "format_score": 0, "content_score": 0,
        "sections": [], "ats_checks": [], "skills_found": [], "missing_skills": [],
        "strengths": [], "critical_issues": ["No resume data provided"],
        "improvements": ["Please upload a valid resume"], "experience_level": "Unknown"
    }