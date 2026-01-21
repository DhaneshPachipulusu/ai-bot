from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid, os, json
from app.utils.file_utils import extract_text
from app.services.resume_parser import parse_resume
from app.services.question_generator import generate_questions

router = APIRouter()

@router.post("/upload-resume", operation_id="upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX allowed")

    resume_id = str(uuid.uuid4())
    file_path = f"data/resumes/{resume_id}_{file.filename}"

    os.makedirs("data/resumes", exist_ok=True)
    os.makedirs("data/parsed", exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    resume_text = extract_text(file_path)
    parsed_data = parse_resume(resume_text)

    parsed_path = f"data/parsed/{resume_id}.json"
    with open(parsed_path, "w") as f:
        json.dump(parsed_data, f, indent=2)

    return {
        "resume_id": resume_id,
        "parsed_resume": parsed_data
    }


# ADD THIS NEW ENDPOINT
@router.post("/generate-questions")
def generate_questions_endpoint(payload: dict):
    """
    Generate interview questions from parsed resume data
    """
    parsed_resume = payload.get("parsed_resume")
    
    if not parsed_resume:
        raise HTTPException(status_code=400, detail="parsed_resume is required")
    
    questions = generate_questions(parsed_resume)
    return questions