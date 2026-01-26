"""
Interview Context Models
========================
Data structures for conversational interview system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# ======================
# ENUMS
# ======================

class InterviewStage(str, Enum):
    """Interview stages - flows in order"""
    GREETING = "greeting"
    INTRODUCTION = "introduction"
    SKILLS_DEEP_DIVE = "skills_deep_dive"
    PROJECT_DISCUSSION = "project_discussion"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    CLOSING = "closing"
    COMPLETED = "completed"


class DifficultyLevel(str, Enum):
    """Adaptive difficulty"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AnswerQuality(str, Enum):
    """Quality assessment of candidate's answer"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    WEAK = "weak"
    INCOMPLETE = "incomplete"
    OFF_TOPIC = "off_topic"
    NO_ANSWER = "no_answer"


class ResponseType(str, Enum):
    """Type of AI response"""
    GREETING = "greeting"
    FOLLOW_UP = "follow_up"
    DIG_DEEPER = "dig_deeper"
    NEW_TOPIC = "new_topic"
    TRANSITION = "transition"
    CLARIFICATION = "clarification"
    ENCOURAGEMENT = "encouragement"
    CLOSING = "closing"


# ======================
# CANDIDATE INFO
# ======================

class CandidateInfo(BaseModel):
    """Candidate details from resume"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    location: Optional[str] = None


# ======================
# PROBE AREAS (What to ask about)
# ======================

class ProjectInfo(BaseModel):
    """Project to discuss"""
    name: str
    description: Optional[str] = None
    technologies: list[str] = []
    role: Optional[str] = None
    probed: bool = False  # Have we asked about this?
    key_points_mentioned: list[str] = []  # What candidate said


class ProbeAreas(BaseModel):
    """Areas to probe during interview"""
    skills: list[str] = []  # Technical skills to ask about
    skills_probed: list[str] = []  # Skills already covered
    
    projects: list[ProjectInfo] = []
    
    experience: list[dict] = []  # Work experience
    
    achievements: list[str] = []  # Claims to verify
    
    education: Optional[dict] = None
    
    certifications: list[str] = []
    
    gaps: list[str] = []  # Things missing or unclear
    
    strengths_claimed: list[str] = []  # Self-reported strengths


# ======================
# INTERVIEW STATE
# ======================

class InterviewState(BaseModel):
    """Current state of the interview"""
    current_stage: InterviewStage = InterviewStage.GREETING
    
    topics_covered: list[str] = []
    topics_remaining: list[str] = []
    current_topic: Optional[str] = None
    
    follow_up_queue: list[str] = []  # Things to follow up on
    
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    
    questions_asked: int = 0
    max_questions: int = 15
    
    time_started: Optional[datetime] = None
    max_duration_mins: int = 30
    
    is_paused: bool = False
    is_completed: bool = False


# ======================
# PERFORMANCE TRACKING
# ======================

class PerformanceMetrics(BaseModel):
    """Track candidate performance"""
    strong_areas: list[str] = []
    weak_areas: list[str] = []
    
    technical_depth: Optional[str] = None  # shallow / moderate / deep
    communication_clarity: Optional[str] = None  # unclear / clear / excellent
    confidence_level: Optional[str] = None  # low / medium / high
    
    answers_quality: list[dict] = []  # Per-answer quality tracking
    
    overall_impression: Optional[str] = None


# ======================
# CONVERSATION TURN
# ======================

class ConversationTurn(BaseModel):
    """Single turn in conversation"""
    turn_number: int
    role: Literal["interviewer", "candidate"]
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # For interviewer turns
    stage: Optional[InterviewStage] = None
    response_type: Optional[ResponseType] = None
    topic: Optional[str] = None
    
    # For candidate turns
    duration_seconds: Optional[int] = None
    word_count: Optional[int] = None
    
    # Analysis (for candidate turns)
    analysis: Optional[dict] = None


# ======================
# MAIN INTERVIEW CONTEXT
# ======================

class InterviewContext(BaseModel):
    """
    Complete interview context - the brain of the conversation.
    This object is updated after every turn.
    """
    # Identifiers
    interview_id: str
    user_id: int
    
    # Mode
    mode: Literal["resume", "career"] = "resume"
    
    # Candidate info
    candidate: CandidateInfo
    
    # What to probe
    probe_areas: ProbeAreas
    
    # Current state
    state: InterviewState
    
    # Performance tracking
    performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    
    # Full conversation history
    conversation: list[ConversationTurn] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ======================
# API REQUEST/RESPONSE MODELS
# ======================

class StartInterviewRequest(BaseModel):
    """Request to start interview"""
    user_id: int
    mode: Literal["resume", "career"] = "resume"
    
    # For resume mode
    parsed_resume: Optional[dict] = None
    
    # For career mode
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    
    # Settings
    difficulty: Literal["auto", "easy", "medium", "hard"] = "auto"
    max_questions: int = 12
    max_duration_mins: int = 30


class InterviewMessage(BaseModel):
    """AI interviewer message"""
    type: ResponseType
    acknowledgment: Optional[str] = None  # Brief acknowledgment of their answer
    text: str  # Main message/question
    audio_text: Optional[str] = None  # TTS-optimized version
    topic: Optional[str] = None


class InterviewStateResponse(BaseModel):
    """State info for frontend"""
    stage: str
    progress_percent: int
    topics_covered: list[str]
    current_topic: Optional[str]
    questions_asked: int
    questions_remaining: int
    time_elapsed_mins: int
    time_remaining_mins: int


class StartInterviewResponse(BaseModel):
    """Response after starting interview"""
    interview_id: str
    message: InterviewMessage
    state: InterviewStateResponse


class RespondRequest(BaseModel):
    """Request to process candidate's answer"""
    interview_id: str
    user_id: int
    answer: str
    answer_duration_seconds: Optional[int] = None
    
    # Optional audio metrics from frontend
    audio_metrics: Optional[dict] = None


class PerformanceHint(BaseModel):
    """Hint for frontend about answer quality"""
    answer_quality: str
    suggestion: Optional[str] = None


class RespondResponse(BaseModel):
    """Response after processing answer"""
    message: InterviewMessage
    state: InterviewStateResponse
    performance_hint: Optional[PerformanceHint] = None
    is_complete: bool = False


class EndInterviewRequest(BaseModel):
    """Request to end interview"""
    interview_id: str
    user_id: int
    reason: Literal["user_ended", "time_limit", "completed"] = "user_ended"


class InterviewSummary(BaseModel):
    """Summary after interview ends"""
    duration_mins: int
    questions_answered: int
    strong_areas: list[str]
    areas_to_improve: list[str]
    overall_performance: str


class EndInterviewResponse(BaseModel):
    """Response after ending interview"""
    message: InterviewMessage
    summary: InterviewSummary
    report_id: str