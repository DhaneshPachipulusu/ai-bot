"""
Test Script for Conversational Interview API
=============================================
Run this script to test the new interview endpoints.

Usage:
    python test_interview_api.py

Make sure your FastAPI server is running first:
    uvicorn main:app --reload --port 8000
"""

import requests
import json
import time

# ======================
# CONFIGURATION
# ======================

BASE_URL = "http://localhost:8000/api"  # Change if your server runs elsewhere
USER_ID = 1  # Test user ID

# Sample parsed resume (simulating what comes from resume upload)
SAMPLE_RESUME = {
    "name": "Dhaneshwar Rao",
    "email": "dhaneshwar@example.com",
    "phone": "+91-9876543210",
    "current_role": "DevOps Engineer",
    "target_role": "Senior DevOps Engineer",
    "experience_years": 3,
    "skills": [
        "Docker", "Kubernetes", "AWS", "Python", "CI/CD",
        "Jenkins", "Terraform", "Linux", "Git", "Ansible"
    ],
    "projects": [
        {
            "name": "License Management Platform",
            "description": "Built a B2B SaaS licensing system",
            "technologies": ["FastAPI", "Docker", "SQLite", "Next.js"],
            "role": "Lead Developer"
        },
        {
            "name": "AI Interview Bot",
            "description": "Conversational AI for interview practice",
            "technologies": ["Python", "FastAPI", "React", "Gemini AI"],
            "role": "Full Stack Developer"
        }
    ],
    "experience": [
        {
            "company": "Tech Corp",
            "role": "DevOps Engineer",
            "duration": "2022 - Present",
            "achievements": [
                "Reduced deployment time by 40%",
                "Implemented CI/CD pipelines"
            ]
        }
    ],
    "education": {
        "degree": "B.Tech in Computer Science",
        "college": "NRI Institute of Technology",
        "year": 2022
    }
}


# ======================
# HELPER FUNCTIONS
# ======================

def print_separator():
    print("\n" + "=" * 60 + "\n")


def print_response(title, response):
    print(f"📋 {title}")
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
    except:
        print(f"   Response: {response.text[:200]}")


# ======================
# TEST FUNCTIONS
# ======================

def test_start_interview():
    """Test starting a new conversational interview"""
    print_separator()
    print("🚀 TEST 1: Starting Conversational Interview")
    print_separator()
    
    payload = {
        "user_id": USER_ID,
        "mode": "resume",
        "parsed_resume": SAMPLE_RESUME,
        "target_role": "Senior DevOps Engineer",
        "difficulty": "auto",
        "max_questions": 10,
        "max_duration_mins": 20
    }
    
    response = requests.post(f"{BASE_URL}/interview/start", json=payload)
    print_response("Start Interview", response)
    
    if response.status_code == 200:
        data = response.json()
        interview_id = data.get("interview_id")
        message = data.get("message", {}).get("text", "")
        
        print(f"\n✅ Interview Started!")
        print(f"   Interview ID: {interview_id}")
        print(f"   AI Greeting: {message}")
        
        return interview_id
    else:
        print(f"\n❌ Failed to start interview")
        return None


def test_respond(interview_id, answer):
    """Test responding to the AI"""
    print_separator()
    print(f"💬 Sending Answer: \"{answer[:50]}...\"")
    print_separator()
    
    payload = {
        "interview_id": interview_id,
        "user_id": USER_ID,
        "answer": answer,
        "answer_duration_seconds": len(answer.split()) * 2  # Rough estimate
    }
    
    response = requests.post(f"{BASE_URL}/interview/respond", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        message = data.get("message", {})
        state = data.get("state", {})
        hint = data.get("performance_hint")
        is_complete = data.get("is_complete", False)
        
        print(f"🤖 AI Response:")
        print(f"   Type: {message.get('type')}")
        if message.get('acknowledgment'):
            print(f"   Acknowledgment: {message.get('acknowledgment')}")
        print(f"   Message: {message.get('text')}")
        print(f"\n📊 State:")
        print(f"   Stage: {state.get('stage')}")
        print(f"   Progress: {state.get('progress_percent')}%")
        print(f"   Questions Asked: {state.get('questions_asked')}")
        
        if hint:
            print(f"\n💡 Performance Hint:")
            print(f"   Quality: {hint.get('answer_quality')}")
            print(f"   Suggestion: {hint.get('suggestion')}")
        
        if is_complete:
            print(f"\n🎉 Interview Complete!")
        
        return data
    else:
        print_response("Response Error", response)
        return None


def test_get_status(interview_id):
    """Test getting interview status"""
    print_separator()
    print("📊 TEST: Get Interview Status")
    print_separator()
    
    response = requests.get(
        f"{BASE_URL}/interview/{interview_id}/status",
        params={"user_id": USER_ID}
    )
    print_response("Status", response)
    return response.json() if response.status_code == 200 else None


def test_end_interview(interview_id):
    """Test ending the interview"""
    print_separator()
    print("🛑 TEST: End Interview")
    print_separator()
    
    payload = {
        "interview_id": interview_id,
        "user_id": USER_ID,
        "reason": "user_ended"
    }
    
    response = requests.post(f"{BASE_URL}/interview/end", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        summary = data.get("summary", {})
        
        print(f"✅ Interview Ended")
        print(f"\n📋 Summary:")
        print(f"   Duration: {summary.get('duration_mins')} mins")
        print(f"   Questions Answered: {summary.get('questions_answered')}")
        print(f"   Strong Areas: {', '.join(summary.get('strong_areas', []))}")
        print(f"   Areas to Improve: {', '.join(summary.get('areas_to_improve', []))}")
        print(f"   Overall: {summary.get('overall_performance')}")
        
        return data
    else:
        print_response("End Error", response)
        return None


# ======================
# FULL CONVERSATION TEST
# ======================

def run_full_conversation_test():
    """Run a complete interview conversation"""
    
    print("\n" + "🎯" * 30)
    print("   CONVERSATIONAL INTERVIEW TEST")
    print("🎯" * 30)
    
    # Sample answers for testing
    test_answers = [
        # Greeting response
        "Hi! I'm doing great, thanks for asking. A little nervous but excited!",
        
        # Introduction
        "I'm a DevOps engineer with 3 years of experience. I started as a developer but fell in love with automation and infrastructure. Currently I work with Docker, Kubernetes, and AWS. I've built CI/CD pipelines that reduced our deployment time by 40%.",
        
        # Skill question
        "I've been using Docker for about 3 years now. I containerize all our microservices, write multi-stage Dockerfiles for optimized images, and manage our Docker Compose setups for local development. I've also worked with Docker Swarm before moving to Kubernetes.",
        
        # Follow-up
        "The biggest challenge was optimizing image sizes. Our initial images were over 1GB. I implemented multi-stage builds, used Alpine base images, and proper layer caching. Got them down to under 200MB which significantly improved our CI/CD times.",
        
        # Project question
        "The License Management Platform was a B2B SaaS system I built for controlling access to Docker-based applications. I designed the architecture using FastAPI, implemented machine fingerprint-based licensing, and built a Next.js admin dashboard. It uses RSA-4096 signatures for security.",
        
        # Behavioral
        "There was a time when our production deployment failed at 2 AM. I quickly rolled back to the previous version, then spent time analyzing logs. Found it was a database migration issue. I documented the incident and we implemented better testing for migrations after that.",
    ]
    
    # Start interview
    interview_id = test_start_interview()
    
    if not interview_id:
        print("❌ Could not start interview. Make sure your server is running!")
        return
    
    time.sleep(1)  # Brief pause
    
    # Have a conversation
    for i, answer in enumerate(test_answers):
        print(f"\n{'👤' * 20}")
        print(f"   TURN {i + 1}")
        print(f"{'👤' * 20}")
        
        result = test_respond(interview_id, answer)
        
        if result and result.get("is_complete"):
            break
        
        time.sleep(0.5)  # Brief pause between turns
    
    # Get final status
    test_get_status(interview_id)
    
    # End interview
    test_end_interview(interview_id)
    
    print("\n" + "✅" * 30)
    print("   TEST COMPLETED!")
    print("✅" * 30 + "\n")


# ======================
# SIMPLE API CHECK
# ======================

def check_api_health():
    """Quick check if API is running"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/")
        if response.status_code == 200:
            print("✅ API is running!")
            return True
        else:
            print(f"⚠️ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure server is running:")
        print("   uvicorn main:app --reload --port 8000")
        return False


# ======================
# MAIN
# ======================

if __name__ == "__main__":
    print("\n🔍 Checking API health...")
    
    if check_api_health():
        print("\n🚀 Starting conversational interview test...\n")
        run_full_conversation_test()
    else:
        print("\n💡 Start your server first:")
        print("   cd your-backend-folder")
        print("   uvicorn main:app --reload --port 8000")