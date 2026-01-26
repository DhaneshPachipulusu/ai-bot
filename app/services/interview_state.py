"""
Interview State Service
=======================
Manages interview context, state transitions, and persistence.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

from app.models.interview_context import (
    InterviewContext,
    InterviewState,
    InterviewStage,
    DifficultyLevel,
    CandidateInfo,
    ProbeAreas,
    ProjectInfo,
    PerformanceMetrics,
    ConversationTurn,
    ResponseType,
)

# Storage directory
DATA_DIR = "data/interviews"
os.makedirs(DATA_DIR, exist_ok=True)


# ======================
# CREATE INTERVIEW
# ======================

def _extract_candidate_name(parsed_resume: Optional[dict]) -> str:
    """
    Extract candidate name from parsed resume with multiple fallback strategies.
    Returns a proper name or 'there' for greeting.
    """
    if not parsed_resume:
        return "there"
    
    # Strategy 1: Direct name field
    name = parsed_resume.get("name")
    if name and isinstance(name, str) and name.strip() and name.strip().lower() != "candidate":
        return name.strip()
    
    # Strategy 2: Check if there's a fallback object (error case from parser)
    fallback = parsed_resume.get("fallback")
    if fallback and isinstance(fallback, dict):
        fallback_name = fallback.get("name")
        if fallback_name and isinstance(fallback_name, str) and fallback_name.strip():
            return fallback_name.strip()
    
    # Strategy 3: Check contact info
    contact = parsed_resume.get("contact", {})
    if isinstance(contact, dict):
        contact_name = contact.get("name")
        if contact_name and isinstance(contact_name, str) and contact_name.strip():
            return contact_name.strip()
    
    # Strategy 4: Check personal_info
    personal = parsed_resume.get("personal_info", {})
    if isinstance(personal, dict):
        personal_name = personal.get("name") or personal.get("full_name")
        if personal_name and isinstance(personal_name, str) and personal_name.strip():
            return personal_name.strip()
    
    # Strategy 5: Check header section
    header = parsed_resume.get("header", {})
    if isinstance(header, dict):
        header_name = header.get("name")
        if header_name and isinstance(header_name, str) and header_name.strip():
            return header_name.strip()
    
    # Default fallback - use "there" for natural greeting
    return "there"


def create_interview_context(
    user_id: int,
    mode: str,
    parsed_resume: Optional[dict] = None,
    target_role: Optional[str] = None,
    experience_level: Optional[str] = None,
    difficulty: str = "auto",
    max_questions: int = 12,
    max_duration_mins: int = 30,
) -> InterviewContext:
    """
    Create a new interview context from resume or career selection.
    """
    
    interview_id = str(uuid.uuid4())
    
    # Extract candidate info
    if parsed_resume:
        # Use robust name extraction
        candidate_name = _extract_candidate_name(parsed_resume)
        
        candidate = CandidateInfo(
            name=candidate_name,
            email=parsed_resume.get("email") or parsed_resume.get("contact", {}).get("email"),
            phone=parsed_resume.get("phone") or parsed_resume.get("contact", {}).get("phone"),
            experience_years=_extract_experience_years(parsed_resume),
            current_role=parsed_resume.get("current_role") or parsed_resume.get("title"),
            target_role=target_role or parsed_resume.get("target_role", "Software Engineer"),
            location=parsed_resume.get("location"),
        )
        
        # Extract probe areas from resume
        probe_areas = _extract_probe_areas(parsed_resume)
    else:
        # Career mode - minimal info
        candidate = CandidateInfo(
            name="there",  # Changed from "Candidate" to "there" for natural greeting
            target_role=target_role or "Software Engineer",
        )
        probe_areas = _get_role_probe_areas(target_role, experience_level)
    
    # Determine initial difficulty
    if difficulty == "auto":
        difficulty_level = _determine_difficulty(parsed_resume, experience_level)
    else:
        difficulty_level = DifficultyLevel(difficulty)
    
    # Build topics to cover
    topics_remaining = _build_topic_list(probe_areas)
    
    # Create interview state
    state = InterviewState(
        current_stage=InterviewStage.GREETING,
        topics_covered=[],
        topics_remaining=topics_remaining,
        current_topic=None,
        follow_up_queue=[],
        difficulty_level=difficulty_level,
        questions_asked=0,
        max_questions=max_questions,
        time_started=datetime.utcnow(),
        max_duration_mins=max_duration_mins,
        is_paused=False,
        is_completed=False,
    )
    
    # Create context
    context = InterviewContext(
        interview_id=interview_id,
        user_id=user_id,
        mode=mode,
        candidate=candidate,
        probe_areas=probe_areas,
        state=state,
        performance=PerformanceMetrics(),
        conversation=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    # Save to storage
    save_context(context)
    
    return context


# ======================
# STATE TRANSITIONS
# ======================

def get_next_stage(current_stage: InterviewStage) -> InterviewStage:
    """Get the next stage in the interview flow."""
    stage_flow = [
        InterviewStage.GREETING,
        InterviewStage.INTRODUCTION,
        InterviewStage.SKILLS_DEEP_DIVE,
        InterviewStage.PROJECT_DISCUSSION,
        InterviewStage.BEHAVIORAL,
        InterviewStage.SITUATIONAL,
        InterviewStage.CLOSING,
        InterviewStage.COMPLETED,
    ]
    
    try:
        current_index = stage_flow.index(current_stage)
        if current_index < len(stage_flow) - 1:
            return stage_flow[current_index + 1]
    except ValueError:
        pass
    
    return InterviewStage.COMPLETED


def should_transition_stage(context: InterviewContext) -> bool:
    """
    Determine if we should move to the next stage.
    """
    state = context.state
    stage = InterviewStage(state.current_stage)
    
    # Greeting: Transition after 1-2 exchanges
    if stage == InterviewStage.GREETING:
        greeting_turns = len([t for t in context.conversation if t.stage == "greeting"])
        return greeting_turns >= 2
    
    # Introduction: Transition after candidate introduces themselves
    if stage == InterviewStage.INTRODUCTION:
        intro_turns = len([t for t in context.conversation if t.stage == "introduction"])
        return intro_turns >= 2
    
    # Skills: Transition after covering 3-5 skills or time
    if stage == InterviewStage.SKILLS_DEEP_DIVE:
        skills_covered = len(context.probe_areas.skills_probed)
        return skills_covered >= 4 or state.questions_asked >= 7
    
    # Projects: Transition after discussing 1-2 projects
    if stage == InterviewStage.PROJECT_DISCUSSION:
        projects_probed = len([p for p in context.probe_areas.projects if p.probed])
        return projects_probed >= 2 or state.questions_asked >= 10
    
    # Behavioral: Transition after 2-3 behavioral questions
    if stage == InterviewStage.BEHAVIORAL:
        behavioral_turns = len([t for t in context.conversation if t.stage == "behavioral"])
        return behavioral_turns >= 4
    
    # Situational: Transition after 1-2 situational questions
    if stage == InterviewStage.SITUATIONAL:
        situational_turns = len([t for t in context.conversation if t.stage == "situational"])
        return situational_turns >= 2
    
    # Closing: Complete after farewell
    if stage == InterviewStage.CLOSING:
        closing_turns = len([t for t in context.conversation if t.stage == "closing"])
        return closing_turns >= 2
    
    return False


def transition_to_next_stage(context: InterviewContext) -> InterviewContext:
    """
    Move to the next interview stage.
    """
    current_stage = InterviewStage(context.state.current_stage)
    next_stage = get_next_stage(current_stage)
    
    context.state.current_stage = next_stage
    context.updated_at = datetime.utcnow()
    
    save_context(context)
    return context


# ======================
# CONVERSATION MANAGEMENT
# ======================

def add_interviewer_turn(
    context: InterviewContext,
    text: str,
    response_type: ResponseType,
    topic: Optional[str] = None,
) -> InterviewContext:
    """Add interviewer's turn to conversation."""
    
    turn = ConversationTurn(
        turn_number=len(context.conversation) + 1,
        role="interviewer",
        text=text,
        timestamp=datetime.utcnow(),
        stage=InterviewStage(context.state.current_stage),
        response_type=response_type,
        topic=topic or context.state.current_topic,
    )
    
    context.conversation.append(turn)
    context.state.questions_asked += 1
    context.updated_at = datetime.utcnow()
    
    save_context(context)
    return context


def add_candidate_turn(
    context: InterviewContext,
    text: str,
    duration_seconds: Optional[int] = None,
    analysis: Optional[dict] = None,
) -> InterviewContext:
    """Add candidate's turn to conversation."""
    
    turn = ConversationTurn(
        turn_number=len(context.conversation) + 1,
        role="candidate",
        text=text,
        timestamp=datetime.utcnow(),
        duration_seconds=duration_seconds,
        word_count=len(text.split()),
        analysis=analysis,
    )
    
    context.conversation.append(turn)
    context.updated_at = datetime.utcnow()
    
    save_context(context)
    return context


def update_topics(
    context: InterviewContext,
    topics_covered: list[str] = None,
    skills_probed: list[str] = None,
) -> InterviewContext:
    """Update covered topics and probed skills."""
    
    if topics_covered:
        for topic in topics_covered:
            if topic not in context.state.topics_covered:
                context.state.topics_covered.append(topic)
            if topic in context.state.topics_remaining:
                context.state.topics_remaining.remove(topic)
    
    if skills_probed:
        for skill in skills_probed:
            if skill not in context.probe_areas.skills_probed:
                context.probe_areas.skills_probed.append(skill)
    
    context.updated_at = datetime.utcnow()
    save_context(context)
    return context


def update_performance(
    context: InterviewContext,
    answer_quality: str,
    strong_area: Optional[str] = None,
    weak_area: Optional[str] = None,
) -> InterviewContext:
    """Update performance metrics."""
    
    context.performance.answers_quality.append({
        "question_number": context.state.questions_asked,
        "quality": answer_quality,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    if strong_area and strong_area not in context.performance.strong_areas:
        context.performance.strong_areas.append(strong_area)
    
    if weak_area and weak_area not in context.performance.weak_areas:
        context.performance.weak_areas.append(weak_area)
    
    context.updated_at = datetime.utcnow()
    save_context(context)
    return context


def mark_project_probed(context: InterviewContext, project_name: str) -> InterviewContext:
    """Mark a project as discussed."""
    for project in context.probe_areas.projects:
        if project.name.lower() == project_name.lower():
            project.probed = True
            break
    
    context.updated_at = datetime.utcnow()
    save_context(context)
    return context


def complete_interview(context: InterviewContext) -> InterviewContext:
    """Mark interview as completed."""
    context.state.is_completed = True
    context.state.current_stage = InterviewStage.COMPLETED
    context.updated_at = datetime.utcnow()
    save_context(context)
    return context


# ======================
# PERSISTENCE
# ======================

def save_context(context: InterviewContext) -> None:
    """Save interview context to storage."""
    path = f"{DATA_DIR}/{context.interview_id}.json"
    
    # Convert to dict for JSON serialization
    data = context.model_dump(mode="json")
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_context(interview_id: str) -> Optional[InterviewContext]:
    """Load interview context from storage."""
    path = f"{DATA_DIR}/{interview_id}.json"
    
    if not os.path.exists(path):
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return InterviewContext(**data)


def delete_context(interview_id: str) -> bool:
    """Delete interview context."""
    path = f"{DATA_DIR}/{interview_id}.json"
    
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


# ======================
# HELPER FUNCTIONS
# ======================

def _extract_experience_years(resume: dict) -> Optional[int]:
    """Extract years of experience from resume."""
    # Try direct field
    if "experience_years" in resume:
        return resume["experience_years"]
    
    # Try to calculate from experience list
    experience = resume.get("experience", [])
    if experience:
        # Rough estimate
        return len(experience) * 2
    
    return None


def _extract_probe_areas(resume: dict) -> ProbeAreas:
    """Extract areas to probe from resume."""
    
    # Handle error case with fallback
    if resume.get("error") and resume.get("fallback"):
        resume = resume.get("fallback", resume)
    
    # Skills
    skills = resume.get("skills", [])
    if isinstance(skills, dict):
        # Handle categorized skills
        all_skills = []
        for category, skill_list in skills.items():
            if isinstance(skill_list, list):
                all_skills.extend(skill_list)
        skills = all_skills
    
    # Projects
    projects = []
    for proj in resume.get("projects", [])[:5]:
        if isinstance(proj, dict):
            projects.append(ProjectInfo(
                name=proj.get("name", "Unknown Project"),
                description=proj.get("description"),
                technologies=proj.get("technologies", []),
                role=proj.get("role"),
                probed=False,
            ))
        elif isinstance(proj, str):
            projects.append(ProjectInfo(name=proj, probed=False))
    
    # Achievements
    achievements = resume.get("achievements", [])
    if not achievements:
        # Try to extract from experience
        for exp in resume.get("experience", []):
            if isinstance(exp, dict):
                achievements.extend(exp.get("achievements", [])[:2])
    
    return ProbeAreas(
        skills=skills[:15],  # Limit to top 15
        skills_probed=[],
        projects=projects,
        experience=resume.get("experience", []),
        achievements=achievements[:5],
        education=resume.get("education"),
        certifications=resume.get("certifications", []),
        gaps=[],  # Could be analyzed by AI
        strengths_claimed=resume.get("strengths", []),
    )


def _get_role_probe_areas(role: str, level: str) -> ProbeAreas:
    """Get probe areas for career mode (no resume)."""
    
    # Default skills by role
    role_skills = {
        "Frontend Developer": ["JavaScript", "React", "CSS", "TypeScript", "HTML", "REST APIs"],
        "Backend Developer": ["Python", "APIs", "Databases", "SQL", "Docker", "Security"],
        "DevOps Engineer": ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux", "Terraform"],
        "Data Analyst": ["SQL", "Python", "Excel", "Visualization", "Statistics"],
        "Full Stack Developer": ["JavaScript", "Python", "React", "Node.js", "Databases", "APIs"],
    }
    
    skills = role_skills.get(role, ["Programming", "Problem Solving", "Databases"])
    
    return ProbeAreas(
        skills=skills,
        skills_probed=[],
        projects=[],
        experience=[],
        achievements=[],
        gaps=[],
        strengths_claimed=[],
    )


def _determine_difficulty(resume: Optional[dict], level: str) -> DifficultyLevel:
    """Determine starting difficulty."""
    if level:
        level_map = {
            "junior": DifficultyLevel.EASY,
            "entry": DifficultyLevel.EASY,
            "mid": DifficultyLevel.MEDIUM,
            "senior": DifficultyLevel.HARD,
            "lead": DifficultyLevel.HARD,
        }
        return level_map.get(level.lower(), DifficultyLevel.MEDIUM)
    
    if resume:
        years = _extract_experience_years(resume)
        if years:
            if years <= 2:
                return DifficultyLevel.EASY
            elif years <= 5:
                return DifficultyLevel.MEDIUM
            else:
                return DifficultyLevel.HARD
    
    return DifficultyLevel.MEDIUM


def _build_topic_list(probe_areas: ProbeAreas) -> list[str]:
    """Build list of topics to cover."""
    topics = []
    
    # Add top skills
    topics.extend(probe_areas.skills[:5])
    
    # Add project names
    for proj in probe_areas.projects[:3]:
        topics.append(f"Project: {proj.name}")
    
    # Add standard topics
    topics.extend(["Behavioral", "Situational", "Career Goals"])
    
    return topics


# ======================
# UTILITY FUNCTIONS
# ======================

def get_progress_percent(context: InterviewContext) -> int:
    """Calculate interview progress percentage."""
    stage_weights = {
        "greeting": 5,
        "introduction": 15,
        "skills_deep_dive": 45,
        "project_discussion": 65,
        "behavioral": 80,
        "situational": 90,
        "closing": 95,
        "completed": 100,
    }
    
    base_progress = stage_weights.get(context.state.current_stage, 0)
    
    # Adjust based on questions within stage
    questions_progress = min(
        (context.state.questions_asked / context.state.max_questions) * 100,
        100
    )
    
    return int((base_progress + questions_progress) / 2)


def get_time_remaining(context: InterviewContext) -> int:
    """Get remaining time in minutes."""
    if not context.state.time_started:
        return context.state.max_duration_mins
    
    elapsed = (datetime.utcnow() - context.state.time_started).total_seconds() / 60
    remaining = context.state.max_duration_mins - elapsed
    
    return max(0, int(remaining))


def get_time_elapsed(context: InterviewContext) -> int:
    """Get elapsed time in minutes."""
    if not context.state.time_started:
        return 0
    
    elapsed = (datetime.utcnow() - context.state.time_started).total_seconds() / 60
    return int(elapsed)