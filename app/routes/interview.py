from fastapi import APIRouter
from pydantic import BaseModel
import os, json, uuid

router = APIRouter()

DATA_DIR = "data/conversations"
os.makedirs(DATA_DIR, exist_ok=True)


# ======================
# SCHEMAS
# ======================

class StartInterviewPayload(BaseModel):
    questions: list[str]


class AnswerPayload(BaseModel):
    interview_id: str
    question: str
    answer: str


# ======================
# START INTERVIEW
# ======================

@router.post("/start-interview")
def start_interview(payload: dict):
    questions = payload.get("questions", [])

    if not isinstance(questions, list):
        return {"error": "questions must be a list"}
    
    # ADD THIS CHECK
    if len(questions) == 0:
        return {"error": "questions list cannot be empty"}

    interview_id = str(uuid.uuid4())
    path = f"data/conversations/{interview_id}.json"

    os.makedirs("data/conversations", exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "interview_id": interview_id,
            "questions": questions,
            "answers": []
        }, f, indent=2)

    return {
        "interview_id": interview_id,
        "question": questions[0]
    }
# ======================
# SUBMIT ANSWER (THIS FIXES YOUR ISSUE)
# ======================

@router.post("/submit-answer")
def submit_answer(payload: dict):
    interview_id = payload["interview_id"]
    question = payload["question"]
    answer = payload["answer"]

    path = f"data/conversations/{interview_id}.json"

    if not os.path.exists(path):
        return {"error": "interview not found"}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["answers"].append({
        "question": question,
        "answer": answer
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    next_index = len(data["answers"])

    if next_index >= len(data["questions"]):
        return {"status": "completed"}

    return {
        "next_question": data["questions"][next_index]
    }
