"""
Analysis Routes
===============
API endpoints for interview and resume analysis.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any
from app.services.analyzer import analyze_interview, analyze_resume
from app import database as db
import json
import os

router = APIRouter()


# ==========================================
# Analyze Interview
# ==========================================

@router.post("/analyze-interview")
def analyze_interview_endpoint(interview_id: str):
    """Analyze interview and save report to database"""
    
    print(f"📊 Analyzing interview: {interview_id}")
    
    # Try to get interview from database first
    interview = None
    try:
        interview = db.get_interview_by_id(interview_id)
    except Exception as e:
        print(f"⚠️ Could not get interview from DB: {e}")
    
    # Get user_id from interview data file if not in DB
    user_id = None
    if interview:
        user_id = interview.get("user_id")
    else:
        # Try to get from file
        for path in [f"data/interviews/{interview_id}.json", f"data/conversations/{interview_id}.json"]:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    user_id = data.get("user_id")
                    break
    
    if not user_id:
        print(f"⚠️ Could not find user_id for interview {interview_id}")
        user_id = 1  # Default
    
    # Analyze conversation
    path = f"data/conversations/{interview_id}.json"
    analysis_result = analyze_interview(path)
    
    print(f"✅ Analysis complete. Overall score: {analysis_result.get('overall_score')}")
    print(f"📝 Q&A feedback count: {len(analysis_result.get('qa_feedback', []))}")
    
    # Save to database
    try:
        db.save_report(
            interview_id=interview_id,
            user_id=user_id,
            analysis=analysis_result
        )
        print(f"✅ Report saved to database")
    except Exception as e:
        print(f"⚠️ Could not save report to DB: {e}")
    
    return analysis_result


# ==========================================
# ATS Resume Analysis
# ==========================================

class ResumeAnalysisRequest(BaseModel):
    user_id: int
    parsed_resume: dict = {}
    job_description: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow extra fields


@router.post("/analyze-resume")
def analyze_resume_endpoint(request: ResumeAnalysisRequest):
    """
    Analyze resume for ATS compatibility.
    """
    
    print(f"📄 Analyzing resume for user {request.user_id}")
    print(f"📄 Resume keys: {list(request.parsed_resume.keys()) if request.parsed_resume else 'Empty'}")
    
    # Handle case where parsed_resume might be empty
    if not request.parsed_resume:
        return {
            "error": "No resume data provided",
            "ats_score": 0,
            "keyword_score": 0,
            "format_score": 0,
            "content_score": 0,
            "sections": [],
            "ats_checks": [],
            "skills_found": [],
            "missing_skills": [],
            "strengths": [],
            "critical_issues": ["No resume data provided"],
            "improvements": ["Please upload a valid resume"],
            "experience_level": "Unknown"
        }
    
    try:
        analysis_result = analyze_resume(
            request.parsed_resume,
            request.job_description
        )
        return analysis_result
    
    except Exception as e:
        print(f"❌ Resume analysis error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "ats_score": 0,
            "keyword_score": 0,
            "format_score": 0,
            "content_score": 0,
            "sections": [],
            "ats_checks": [],
            "skills_found": [],
            "missing_skills": [],
            "strengths": [],
            "critical_issues": [f"Analysis error: {str(e)}"],
            "improvements": [],
            "experience_level": "Unknown"
        }