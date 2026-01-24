from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.routes import resume, interview, analysis
from app import database as db
import os
from app.routes import career

app = FastAPI(title="AI Interview Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://ai-bot-ewl3.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    if not os.path.exists("interview_bot.db"):
        print("🔧 Database not found. Creating...")
        db.setup_database()
    else:
        print("✅ Database found!")


# Existing routes
app.include_router(resume.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(career.router, prefix="/api")


# ==================
# NEW AUTH ROUTES
# ==================

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(credentials: LoginRequest):
    """Login endpoint"""
    user = db.verify_login(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {
        "success": True,
        "user": user
    }


# ==================
# REPORTS ROUTES
# ==================

@app.get("/api/user/{user_id}/reports")
def get_user_reports(user_id: int):
    """Get all reports for a user"""
    reports = db.get_user_reports(user_id)
    return {"reports": reports}


@app.get("/api/report/{interview_id}")
def get_report(interview_id: str):
    """Get specific report"""
    report = db.get_report_by_interview(interview_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# ==================
# ADMIN ROUTES
# ==================

@app.get("/api/admin/users")
def get_all_users():
    """Admin: Get all users with stats"""
    users = db.get_all_users_stats()
    return {"users": users}


@app.get("/")
def root():
    return {
        "message": "AI Interview Bot API",
        "status": "running",
        "database": "connected" if os.path.exists("interview_bot.db") else "not found"
    }