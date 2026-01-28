"""
AI Interview Bot - Main Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

# Import database
from app import database as db

# Import routers
from app.routes import resume, interview, career
from app.routes import analysis
from app.routes.interview_v2 import router as interview_v2_router


app = FastAPI(title="AI Interview Bot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-bot-ewl3.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================
# Startup
# ==================

@app.on_event("startup")
def startup_event():
    print("🚀 Starting AI Interview Bot API...")
    
    if not os.path.exists("interview_bot.db"):
        print("🔧 Database not found. Creating...")
        db.setup_database()
    else:
        print("✅ Database found!")
        # Run migrations for existing DB
        db.migrate_add_role_column()
        db.create_admin_user()


# ==================
# Register Routers
# ==================

app.include_router(resume.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(career.router, prefix="/api")
app.include_router(interview_v2_router, prefix="/api")

# Also register interview_v2 without /api prefix (fallback for frontend issues)
app.include_router(interview_v2_router, prefix="")


# ==================
# Auth Routes
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
# Reports Routes
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
# Admin Routes
# ==================

@app.get("/api/admin/users")
def get_all_users():
    """Admin: Get all users with stats"""
    users = db.get_all_users_stats()
    return {"users": users}


# ==================
# Health Check
# ==================

@app.get("/")
def root():
    return {
        "message": "AI Interview Bot API",
        "status": "running",
        "database": "connected" if os.path.exists("interview_bot.db") else "not found"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}