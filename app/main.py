from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import resume, interview, analysis

app = FastAPI(title="AI Interview Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only include your route files here
app.include_router(resume.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")