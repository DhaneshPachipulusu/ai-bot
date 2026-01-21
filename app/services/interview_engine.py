import uuid
import json
import os
from datetime import datetime

DATA_DIR = "data/conversations"


def start_interview(questions: dict) -> dict:
    interview_id = str(uuid.uuid4())

    os.makedirs(DATA_DIR, exist_ok=True)

    interview_data = {
        "interview_id": interview_id,
        "started_at": datetime.utcnow().isoformat(),
        "current_index": 0,
        "questions": questions["questions"],
        "answers": [],
        "status": "in_progress"
    }

    _save(interview_id, interview_data)

    return {
        "interview_id": interview_id,
        "question": questions["questions"][0]
    }


def submit_answer(interview_id: str, answer: str) -> dict:
    data = _load(interview_id)

    idx = data["current_index"]

    data["answers"].append({
        "question": data["questions"][idx],
        "answer": answer,
        "timestamp": datetime.utcnow().isoformat()
    })

    data["current_index"] += 1

    if data["current_index"] >= len(data["questions"]):
        data["status"] = "completed"
        _save(interview_id, data)
        return {"message": "Interview completed"}

    next_question = data["questions"][data["current_index"]]
    _save(interview_id, data)

    return {
        "interview_id": interview_id,
        "next_question": next_question
    }


def _save(interview_id: str, data: dict):
    with open(f"{DATA_DIR}/{interview_id}.json", "w") as f:
        json.dump(data, f, indent=2)


def _load(interview_id: str) -> dict:
    with open(f"{DATA_DIR}/{interview_id}.json") as f:
        return json.load(f)
