from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.question_generator import generate_role_questions

router = APIRouter()


class RoleQuestionsRequest(BaseModel):
    role: str
    level: str  # Entry Level, Junior, Mid Level, Senior


@router.post("/generate-role-questions")
def generate_role_questions_endpoint(request: RoleQuestionsRequest):
    """
    Generate interview questions based on role and level.
    No resume needed - uses general questions for the role.
    
    Includes:
    - Self introduction
    - Technical questions for the role
    - Behavioral questions
    - Scenario-based questions
    - Closing
    """
    
    try:
        questions = generate_role_questions(
            role=request.role,
            level=request.level
        )
        
        return questions
    
    except Exception as e:
        return {"error": str(e)}