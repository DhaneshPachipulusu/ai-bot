import uuid

INTERVIEWS = {}

def create_interview(questions: list):
    interview_id = str(uuid.uuid4())

    INTERVIEWS[interview_id] = {
        "questions": questions,
        "current_index": 0,
        "answers": []
    }

    return {
        "interview_id": interview_id,
        "question": questions[0]
    }


def submit_answer(interview_id: str, answer: str):
    interview = INTERVIEWS.get(interview_id)

    if not interview:
        return {"error": "Invalid interview ID"}

    interview["answers"].append(answer)
    interview["current_index"] += 1

    # 🔚 INTERVIEW FINISHED
    if interview["current_index"] >= len(interview["questions"]):
        return {
            "interview_id": interview_id,
            "finished": True
        }

    # ➡️ NEXT QUESTION
    return {
        "interview_id": interview_id,
        "next_question": interview["questions"][interview["current_index"]]
    }
