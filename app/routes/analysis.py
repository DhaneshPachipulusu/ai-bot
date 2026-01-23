from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.analyzer import analyze_interview, analyze_resume
from app import database as db

router = APIRouter()


# ==========================================
# Analyze Interview (existing)
# ==========================================
@router.post("/analyze-interview")
def analyze(interview_id: str):
    """Analyze interview and save report to database"""
    
    interview = db.get_interview_by_id(interview_id)
    
    if not interview:
        return {"error": "Interview not found"}
    
    path = f"data/conversations/{interview_id}.json"
    analysis_result = analyze_interview(path)
    
    db.save_report(
        interview_id=interview_id,
        user_id=interview["user_id"],
        analysis=analysis_result
    )
    
    return analysis_result


# ==========================================
# ATS Resume Analysis (new)
# ==========================================
class ResumeAnalysisRequest(BaseModel):
    user_id: int
    parsed_resume: dict
    job_description: Optional[str] = None


@router.post("/analyze-resume")
def analyze_resume_endpoint(request: ResumeAnalysisRequest):
    """
    Analyze resume for ATS compatibility.
    
    Returns:
    - ats_score: Overall ATS compatibility (0-100)
    - keyword_score, format_score, content_score: Breakdown
    - sections: Score for each resume section
    - ats_checks: Pass/fail for common ATS checks
    - critical_issues: Must-fix problems
    - improvements: Recommended enhancements
    """
    
    try:
        analysis_result = analyze_resume(
            request.parsed_resume,
            request.job_description
        )
        
        # Optionally save to database
        # db.save_resume_analysis(
        #     user_id=request.user_id,
        #     analysis=analysis_result
        # )
        
        return analysis_result
    
    except Exception as e:
        return {"error": str(e)}