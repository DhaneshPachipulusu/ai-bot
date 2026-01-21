from fastapi import APIRouter
from app.services.analyzer import analyze_interview

router = APIRouter()


@router.post("/analyze-interview")
def analyze(interview_id: str):
    path = f"data/conversations/{interview_id}.json"
    return analyze_interview(path)
