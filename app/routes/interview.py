from fastapi import APIRouter
from pydantic import BaseModel
import os, json, uuid
from app import database as db

router = APIRouter()

DATA_DIR = "data/conversations"
os.makedirs(DATA_DIR, exist_ok=True)


# ======================
# SCHEMAS
# ======================

class StartInterviewPayload(BaseModel):
    user_id: int
    questions: list[str]


class AnswerPayload(BaseModel):
    user_id: int
    interview_id: str
    question: str
    answer: str


# ======================
# START INTERVIEW
# ======================

@router.post("/start-interview")
def start_interview(payload: dict):
    user_id = payload.get("user_id")
    questions = payload.get("questions")

    if not isinstance(questions, list):
        return {"error": "questions must be a list"}
    
    if not user_id:
        return {"error": "user_id is required"}

    interview_id = str(uuid.uuid4())
    
    # Save to database
    db.save_interview(user_id, interview_id, questions)
    
    # Also save to file as backup (optional - you can remove this later)
    path = f"data/conversations/{interview_id}.json"
    os.makedirs("data/conversations", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "interview_id": interview_id,
            "user_id": user_id,
            "questions": questions,
            "answers": []
        }, f, indent=2)

    return {
        "interview_id": interview_id,
        "question": questions[0]
    }


# ======================
# SUBMIT ANSWER
# ======================

@router.post("/submit-answer")
def submit_answer(payload: dict):
    user_id = payload.get("user_id")
    interview_id = payload["interview_id"]
    question = payload["question"]
    answer = payload["answer"]

    # Save to database
    db.update_interview_answers(interview_id, question, answer)
    
    # Also save to file as backup (optional)
    path = f"data/conversations/{interview_id}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        data["answers"].append({
            "question": question,
            "answer": answer
        })
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    # Get interview data from database
    interview = db.get_interview_by_id(interview_id)
    next_index = len(interview["answers"])

    if next_index >= len(interview["questions"]):
        # Mark interview as completed
        db.complete_interview(interview_id)
        return {"status": "completed"}

    return {
        "next_question": interview["questions"][next_index]
    }