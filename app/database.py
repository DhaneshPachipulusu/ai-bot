import sqlite3
from datetime import datetime
import json
import os

DATABASE = "interview_bot.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with tables"""
    conn = get_db()
    c = conn.cursor()
    
    # Users table - WITH ROLE FIELD
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            college TEXT NOT NULL,
            role TEXT DEFAULT 'student',
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
    
    # Reports table - WITH qa_feedback
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id TEXT UNIQUE NOT NULL,
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
            qa_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables created!")


def create_admin_user():
    """Create admin user if not exists"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute(
            "INSERT INTO users (username, password, college, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin123", "Admin Office", "admin")
        )
        print("✅ Admin user created (admin / admin123)")
    except sqlite3.IntegrityError:
        # Check if existing admin has role set
        c.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
        print("⚠️ Admin user already exists - updated role")
    
    conn.commit()
    conn.close()


def create_demo_users():
    """Create 10 Deccan College demo users"""
    conn = get_db()
    c = conn.cursor()
    
    for i in range(1, 11):
        username = f"deccan{i}"
        password = f"deccan{i}"
        try:
            c.execute(
                "INSERT INTO users (username, password, college, role) VALUES (?, ?, ?, ?)",
                (username, password, "Deccan College", "student")
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
    """Check if username and password match, return user with role"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute(
        "SELECT id, username, college, role FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "college": row["college"],
            "role": row["role"] or "student"  # Default to student if null
        }
    return None


# ==================
# INTERVIEW FUNCTIONS
# ==================

def save_interview(user_id: int, interview_id: str, questions: list):
    """Save a new interview"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute(
            "INSERT INTO interviews (user_id, interview_id, questions) VALUES (?, ?, ?)",
            (user_id, interview_id, json.dumps(questions))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ Interview {interview_id} already exists")
    finally:
        conn.close()


def update_interview_answers(interview_id: str, question: str, answer: str):
    """Add an answer to interview"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT answers FROM interviews WHERE interview_id = ?", (interview_id,))
    row = c.fetchone()
    
    if row and row["answers"]:
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
    """Get interview data - check both DB and JSON files"""
    # First try database
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
            "questions": json.loads(row["questions"]) if row["questions"] else [],
            "answers": json.loads(row["answers"]) if row["answers"] else [],
            "status": row["status"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"]
        }
    
    # Try JSON file (for interview_v2)
    for path in [f"data/interviews/{interview_id}.json", f"data/conversations/{interview_id}.json"]:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    return {
                        "id": None,
                        "user_id": data.get("user_id"),
                        "interview_id": interview_id,
                        "questions": data.get("questions", []),
                        "answers": data.get("conversation_history", []),
                        "status": data.get("status", "completed"),
                        "created_at": data.get("start_time"),
                        "completed_at": data.get("end_time")
                    }
            except Exception as e:
                print(f"⚠️ Error reading {path}: {e}")
    
    return None


# ==================
# REPORT FUNCTIONS
# ==================

def save_report(interview_id: str, user_id: int, analysis: dict):
    """Save interview analysis report - with qa_feedback"""
    conn = get_db()
    c = conn.cursor()
    
    # Check if report already exists
    c.execute("SELECT id FROM reports WHERE interview_id = ?", (interview_id,))
    existing = c.fetchone()
    
    if existing:
        # Update existing report
        c.execute('''
            UPDATE reports SET
                overall_score = ?, fluency = ?, grammar = ?, 
                technical_depth = ?, confidence = ?, clarity = ?, response_pace = ?,
                strengths = ?, weaknesses = ?, recommendations = ?, job_readiness = ?,
                qa_feedback = ?
            WHERE interview_id = ?
        ''', (
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
            analysis.get('job_readiness'),
            json.dumps(analysis.get('qa_feedback', [])),
            interview_id
        ))
        print(f"✅ Updated existing report for {interview_id}")
    else:
        # Insert new report
        c.execute('''
            INSERT INTO reports (
                interview_id, user_id, overall_score, fluency, grammar, 
                technical_depth, confidence, clarity, response_pace,
                strengths, weaknesses, recommendations, job_readiness, qa_feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            analysis.get('job_readiness'),
            json.dumps(analysis.get('qa_feedback', []))
        ))
        print(f"✅ Saved new report for {interview_id}")
    
    conn.commit()
    conn.close()


def get_user_reports(user_id: int):
    """Get all reports for a user - NO JOIN required"""
    conn = get_db()
    c = conn.cursor()
    
    # Simple query - no JOIN with interviews table
    c.execute('''
        SELECT 
            id, interview_id, user_id, overall_score, fluency, grammar,
            technical_depth, confidence, clarity, response_pace,
            strengths, weaknesses, recommendations, job_readiness,
            qa_feedback, created_at
        FROM reports
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    
    reports = []
    for row in c.fetchall():
        reports.append({
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
            "qa_feedback": json.loads(row["qa_feedback"]) if row["qa_feedback"] else [],
            "created_at": row["created_at"],
            "completed_at": row["created_at"]  # Use created_at as fallback
        })
    
    conn.close()
    return reports


def get_report_by_interview(interview_id: str):
    """Get report for specific interview - includes qa_feedback"""
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
            "qa_feedback": json.loads(row["qa_feedback"]) if row["qa_feedback"] else [],
            "created_at": row["created_at"]
        }
    return None


# ==================
# ADMIN FUNCTIONS
# ==================

def get_all_users_stats():
    """Get stats for all users (admin dashboard) - excludes admin users"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            u.id, u.username, u.college, u.role,
            COUNT(DISTINCT r.id) as total_interviews,
            COUNT(DISTINCT r.id) as completed_interviews,
            AVG(r.overall_score) as avg_score
        FROM users u
        LEFT JOIN reports r ON u.id = r.user_id
        WHERE u.role = 'student' OR u.role IS NULL
        GROUP BY u.id
    ''')
    
    users = []
    for row in c.fetchall():
        users.append({
            "id": row["id"],
            "username": row["username"],
            "college": row["college"],
            "role": row["role"] or "student",
            "total_interviews": row["total_interviews"] or 0,
            "completed_interviews": row["completed_interviews"] or 0,
            "avg_score": round(row["avg_score"], 2) if row["avg_score"] else 0
        })
    
    conn.close()
    return users


# ==================
# MIGRATION - Add missing columns
# ==================

def migrate_add_role_column():
    """Add role column to existing database if missing"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Check if role column exists in users
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'role' not in columns:
            print("🔧 Adding 'role' column to users table...")
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
            conn.commit()
            print("✅ Role column added!")
        else:
            print("✅ Role column already exists")
        
        # Check if qa_feedback column exists in reports
        c.execute("PRAGMA table_info(reports)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'qa_feedback' not in columns:
            print("🔧 Adding 'qa_feedback' column to reports table...")
            c.execute("ALTER TABLE reports ADD COLUMN qa_feedback TEXT")
            conn.commit()
            print("✅ qa_feedback column added!")
        else:
            print("✅ qa_feedback column already exists")
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
    finally:
        conn.close()


# ==================
# INITIALIZATION
# ==================

def setup_database():
    """Setup database and create test users"""
    print("🔧 Setting up database...")
    init_db()
    migrate_add_role_column()  # Add missing columns
    create_admin_user()        # Create admin user
    create_demo_users()        # Create Deccan College students
    
    print("\n✅ Database setup complete!")
    print("\n📋 Login Credentials:")
    print("=" * 40)
    print("🔐 ADMIN:  admin / admin123")
    print("=" * 40)
    for i in range(1, 11):
        print(f"👤 Student: deccan{i} / deccan{i}")
    print("=" * 40)


if __name__ == "__main__":
    setup_database()