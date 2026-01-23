import sqlite3
from datetime import datetime
import json
import os

DATABASE = "interview_bot.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Initialize database with tables"""
    conn = get_db()
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            college TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Interviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            interview_id TEXT UNIQUE NOT NULL,
            questions TEXT NOT NULL,
            answers TEXT,
            status TEXT DEFAULT 'in_progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            overall_score REAL,
            fluency REAL,
            grammar REAL,
            technical_depth REAL,
            confidence REAL,
            clarity REAL,
            response_pace REAL,
            strengths TEXT,
            weaknesses TEXT,
            recommendations TEXT,
            job_readiness TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (interview_id) REFERENCES interviews(interview_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables created!")


def create_nri_users():
    """Create 10 NRI college test users"""
    conn = get_db()
    c = conn.cursor()
    
    for i in range(1, 11):
        username = f"nri{i}"
        password = username  # Same as username
        try:
            c.execute(
                "INSERT INTO users (username, password, college) VALUES (?, ?, ?)",
                (username, password, "NRI Institute of Technology")
            )
            print(f"✅ Created user: {username}")
        except sqlite3.IntegrityError:
            print(f"⚠️  User {username} already exists")
    
    conn.commit()
    conn.close()


# ==================
# AUTH FUNCTIONS
# ==================

def verify_login(username: str, password: str):
    """Check if username and password match"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute(
        "SELECT id, username, college FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "college": row["college"]
        }
    return None


# ==================
# INTERVIEW FUNCTIONS
# ==================

def save_interview(user_id: int, interview_id: str, questions: list):
    """Save a new interview"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute(
        "INSERT INTO interviews (user_id, interview_id, questions) VALUES (?, ?, ?)",
        (user_id, interview_id, json.dumps(questions))
    )
    
    conn.commit()
    conn.close()


def update_interview_answers(interview_id: str, question: str, answer: str):
    """Add an answer to interview"""
    conn = get_db()
    c = conn.cursor()
    
    # Get current answers
    c.execute("SELECT answers FROM interviews WHERE interview_id = ?", (interview_id,))
    row = c.fetchone()
    
    if row["answers"]:
        answers = json.loads(row["answers"])
    else:
        answers = []
    
    answers.append({"question": question, "answer": answer})
    
    c.execute(
        "UPDATE interviews SET answers = ? WHERE interview_id = ?",
        (json.dumps(answers), interview_id)
    )
    
    conn.commit()
    conn.close()


def complete_interview(interview_id: str):
    """Mark interview as completed"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute(
        "UPDATE interviews SET status = 'completed', completed_at = ? WHERE interview_id = ?",
        (datetime.now().isoformat(), interview_id)
    )
    
    conn.commit()
    conn.close()


def get_interview_by_id(interview_id: str):
    """Get interview data"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute(
        "SELECT * FROM interviews WHERE interview_id = ?",
        (interview_id,)
    )
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "interview_id": row["interview_id"],
            "questions": json.loads(row["questions"]),
            "answers": json.loads(row["answers"]) if row["answers"] else [],
            "status": row["status"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"]
        }
    return None


# ==================
# REPORT FUNCTIONS
# ==================

def save_report(interview_id: str, user_id: int, analysis: dict):
    """Save interview analysis report"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO reports (
            interview_id, user_id, overall_score, fluency, grammar, 
            technical_depth, confidence, clarity, response_pace,
            strengths, weaknesses, recommendations, job_readiness
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        interview_id,
        user_id,
        analysis.get('overall_score'),
        analysis.get('fluency'),
        analysis.get('grammar'),
        analysis.get('technical_depth'),
        analysis.get('confidence'),
        analysis.get('clarity'),
        analysis.get('response_pace'),
        json.dumps(analysis.get('strengths', [])),
        json.dumps(analysis.get('weaknesses', [])),
        json.dumps(analysis.get('recommendations', [])),
        analysis.get('job_readiness')
    ))
    
    conn.commit()
    conn.close()


def get_user_reports(user_id: int):
    """Get all reports for a user"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            r.id, r.interview_id, r.overall_score, r.fluency, r.grammar,
            r.technical_depth, r.confidence, r.clarity, r.response_pace,
            r.strengths, r.weaknesses, r.recommendations, r.job_readiness,
            r.created_at, i.completed_at
        FROM reports r
        JOIN interviews i ON r.interview_id = i.interview_id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    ''', (user_id,))
    
    reports = []
    for row in c.fetchall():
        reports.append({
            "id": row["id"],
            "interview_id": row["interview_id"],
            "overall_score": row["overall_score"],
            "fluency": row["fluency"],
            "grammar": row["grammar"],
            "technical_depth": row["technical_depth"],
            "confidence": row["confidence"],
            "clarity": row["clarity"],
            "response_pace": row["response_pace"],
            "strengths": json.loads(row["strengths"]) if row["strengths"] else [],
            "weaknesses": json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else [],
            "job_readiness": row["job_readiness"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"]
        })
    
    conn.close()
    return reports


def get_report_by_interview(interview_id: str):
    """Get report for specific interview"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM reports WHERE interview_id = ?", (interview_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "interview_id": row["interview_id"],
            "user_id": row["user_id"],
            "overall_score": row["overall_score"],
            "fluency": row["fluency"],
            "grammar": row["grammar"],
            "technical_depth": row["technical_depth"],
            "confidence": row["confidence"],
            "clarity": row["clarity"],
            "response_pace": row["response_pace"],
            "strengths": json.loads(row["strengths"]) if row["strengths"] else [],
            "weaknesses": json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else [],
            "job_readiness": row["job_readiness"],
            "created_at": row["created_at"]
        }
    return None


# ==================
# ADMIN FUNCTIONS
# ==================

def get_all_users_stats():
    """Get stats for all users (admin dashboard)"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            u.id, u.username, u.college,
            COUNT(DISTINCT i.id) as total_interviews,
            COUNT(DISTINCT CASE WHEN i.status = 'completed' THEN i.id END) as completed_interviews,
            AVG(r.overall_score) as avg_score
        FROM users u
        LEFT JOIN interviews i ON u.id = i.user_id
        LEFT JOIN reports r ON u.id = r.user_id
        GROUP BY u.id
    ''')
    
    users = []
    for row in c.fetchall():
        users.append({
            "id": row["id"],
            "username": row["username"],
            "college": row["college"],
            "total_interviews": row["total_interviews"] or 0,
            "completed_interviews": row["completed_interviews"] or 0,
            "avg_score": round(row["avg_score"], 2) if row["avg_score"] else 0
        })
    
    conn.close()
    return users


# ==================
# INITIALIZATION
# ==================

def setup_database():
    """Setup database and create test users"""
    print("🔧 Setting up database...")
    init_db()
    create_nri_users()
    print("\n✅ Database setup complete!")
    print("\n📋 Test Users:")
    print("=" * 30)
    for i in range(1, 11):
        print(f"Username: nri{i} | Password: nri{i}")
    print("=" * 30)


if __name__ == "__main__":
    setup_database()