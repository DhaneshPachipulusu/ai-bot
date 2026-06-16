"""
Resume Intelligence Engine — API Routes
========================================
3 endpoints:
  POST /api/resume-builder/parse     — upload file → locked schema JSON
  POST /api/resume-builder/optimize  — schema → AI-refined schema
  POST /api/resume-builder/generate  — final schema → PDF download URL
  GET  /api/resume-builder/download/<filename> — download PDF
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import re
import json

from app.config import client, USE_MOCK_AI, GEMINI_MODEL
from app.services.resume_builder import (
    normalize_to_schema,
    refine_resume,
    calculate_score,
    empty_schema
)
from app.services.pdf_generator import generate_resume_pdf, get_resume_filename

router = APIRouter()

os.makedirs("downloads", exist_ok=True)
os.makedirs("uploads", exist_ok=True)


# ==========================================
# Pydantic Models (locked schema)
# ==========================================

class BasicsModel(BaseModel):
    full_name: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""

class SkillsModel(BaseModel):
    languages: List[str] = []
    cloud_infrastructure: List[str] = []
    devops_automation: List[str] = []
    databases: List[str] = []
    monitoring: List[str] = []
    frameworks_tools: List[str] = []

class ExperienceModel(BaseModel):
    company: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = "Present"
    bullets: List[str] = []

class ProjectModel(BaseModel):
    name: str = ""
    type: str = ""
    year: str = ""
    bullets: List[str] = []

class EducationModel(BaseModel):
    degree: str = ""
    institution: str = ""
    cgpa: str = ""
    start_year: str = ""
    end_year: str = ""

class ResumeSchema(BaseModel):
    basics: BasicsModel = BasicsModel()
    summary: str = ""
    skills: SkillsModel = SkillsModel()
    experience: List[ExperienceModel] = []
    projects: List[ProjectModel] = []
    education: List[EducationModel] = []
    certifications: List[str] = []
    achievements: List[str] = []

class OptimizeRequest(BaseModel):
    schema_data: dict

class GenerateRequest(BaseModel):
    schema_data: dict


# ==========================================
# ENDPOINT 1: PARSE — Upload → Locked Schema
# ==========================================

@router.post("/resume-builder/parse")
async def parse_resume_file(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF/DOCX), extract text, parse into locked schema.
    Uses AI-based extraction (Gemini) for accuracy, regex as fallback.
    """
    try:
        # Validate file type
        filename = file.filename or "resume.pdf"
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in [".pdf", ".docx", ".doc", ".txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT."
            )
        
        # Save file
        file_path = f"uploads/{filename}"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"📄 Uploaded: {filename} ({len(content)} bytes)")
        
        # Extract text
        if ext == ".pdf":
            text = _extract_pdf_text(file_path)
        elif ext in [".docx", ".doc"]:
            text = _extract_docx_text(file_path)
        elif ext == ".txt":
            text = content.decode("utf-8", errors="ignore")
        else:
            text = ""
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract enough text from the file."
            )
        
        print(f"📝 Extracted {len(text)} chars")
        
        # PRIMARY: AI-based extraction → locked schema
        raw_parsed = None
        if not USE_MOCK_AI and client:
            raw_parsed = _ai_extract(text)
        
        # FALLBACK: regex-based extraction
        if not raw_parsed:
            print("⚠️ AI extraction unavailable, using regex fallback")
            raw_parsed = _extract_info_from_text(text)
        
        # Normalize → locked schema (handles both flat & nested formats)
        schema = normalize_to_schema(raw_parsed)
        
        # Calculate initial score
        score = calculate_score(schema)
        
        print(f"✅ Parsed into locked schema. Score: {score}")
        
        return {
            "schema": schema,
            "score": score,
            "raw_text_length": len(text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Parse error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINT 2: OPTIMIZE — Schema → Refined Schema
# ==========================================

@router.post("/resume-builder/optimize")
async def optimize_resume(request: OptimizeRequest):
    """
    Takes locked schema, runs AI refinement, returns improved schema.
    """
    try:
        schema = request.schema_data
        
        # Normalize first (safety net)
        schema = normalize_to_schema(schema)
        
        before_score = calculate_score(schema)
        
        # AI refinement
        refined = refine_resume(schema)
        
        after_score = calculate_score(refined)
        
        print(f"✅ Optimized: {before_score} → {after_score}")
        
        return {
            "schema": refined,
            "before_score": before_score,
            "after_score": after_score,
            "improvement": after_score - before_score
        }
        
    except Exception as e:
        print(f"❌ Optimize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINT 3: GENERATE — Schema → PDF
# ==========================================

@router.post("/resume-builder/generate")
async def generate_pdf(request: GenerateRequest):
    """
    Takes final locked schema, generates PDF, returns download URL.
    """
    try:
        schema = request.schema_data
        
        # Normalize (safety net)
        schema = normalize_to_schema(schema)
        
        name = schema.get("basics", {}).get("full_name", "Resume")
        filename = get_resume_filename(name, timestamp=True)
        output_path = os.path.join("downloads", filename)
        
        generate_resume_pdf(schema, output_path)
        
        score = calculate_score(schema)
        
        pdf_url = f"/api/resume-builder/download/{filename}"
        
        print(f"✅ Generated PDF: {filename}")
        
        return {
            "pdf_url": pdf_url,
            "pdf_filename": filename,
            "final_score": score
        }
        
    except Exception as e:
        print(f"❌ Generate error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINT 4: DOWNLOAD
# ==========================================

@router.get("/resume-builder/download/{filename}")
async def download_resume(filename: str):
    """Download generated resume PDF."""
    from fastapi.responses import FileResponse
    
    file_path = os.path.join("downloads", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename
    )


# ==========================================
# AI-BASED EXTRACTION (PRIMARY)
# ==========================================

def _ai_extract(text: str) -> dict:
    """
    Use Gemini AI to extract resume data directly into the locked schema.
    Returns the parsed dict or None if AI extraction fails.
    """
    try:
        prompt = f"""
You are a precise resume data extractor. Extract ALL information from this resume
text into the EXACT JSON structure below. Be thorough — do not miss any data.

EXTRACTION RULES:
- Extract the person's FULL NAME, phone, email, LinkedIn URL, GitHub URL, and location.
- Extract ALL skills and categorize them into the correct groups.
  Remove non-technical skills (VS Code, Data Structures, Problem Solving, Communication).
  Remove category labels like "Languages:" or "Technologies:" — just list the skills.
  Fix capitalization: DOCKER → Docker, KUBERNETES → Kubernetes.
- Extract ALL work experience entries with company name, role/title, start date, end date, and bullet points.
  Each bullet should be a separate string in the "bullets" array.
  If no company name is explicitly stated, use the organization/team name.
- Extract ALL projects with name, technologies/type, year, and description bullets.
  Do NOT include "Tech Stack:" lines as bullets — integrate tech into the project bullets.
- Extract education — ONLY B.Tech/Bachelor/Master level. REMOVE SSC, Intermediate, 12th, 10th.
- Extract certifications as a flat list of strings.
- Extract achievements as a flat list of strings. Merge fragmented entries into complete sentences.

OUTPUT THIS EXACT JSON STRUCTURE (no other keys):
{{
  "basics": {{
    "full_name": "",
    "phone": "",
    "email": "",
    "location": "",
    "linkedin": "",
    "github": ""
  }},
  "summary": "",
  "skills": {{
    "languages": [],
    "cloud_infrastructure": [],
    "devops_automation": [],
    "databases": [],
    "monitoring": [],
    "frameworks_tools": []
  }},
  "experience": [
    {{
      "company": "",
      "role": "",
      "start_date": "",
      "end_date": "",
      "bullets": []
    }}
  ],
  "projects": [
    {{
      "name": "",
      "type": "",
      "year": "",
      "bullets": []
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "cgpa": "",
      "start_year": "",
      "end_year": ""
    }}
  ],
  "certifications": [],
  "achievements": []
}}

RESUME TEXT:
{text[:6000]}

Return ONLY valid JSON. No explanation. No markdown. No commentary.
"""
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        
        result_text = response.text.strip()
        
        # Extract JSON from response
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        
        if start >= 0 and end > start:
            parsed = json.loads(result_text[start:end])
            print(f"✅ AI extraction successful")
            return parsed
        else:
            print("⚠️ AI returned non-JSON response")
            return None
            
    except Exception as e:
        print(f"⚠️ AI extraction failed: {e}")
        return None


# ==========================================
# TEXT EXTRACTION HELPERS
# ==========================================

def _extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except ImportError:
        pass
    
    try:
        from pdfminer.high_level import extract_text
        return extract_text(file_path).strip()
    except ImportError:
        pass
    
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="No PDF library available. Install PyMuPDF, pdfminer, or PyPDF2."
        )


def _extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX."""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="python-docx not installed. Run: pip install python-docx"
        )


# ==========================================
# TEXT → RAW DICT PARSER (regex-based)
# ==========================================

def _extract_info_from_text(text: str) -> dict:
    """
    Extract structured info from resume text using regex patterns.
    Returns a raw dict that normalize_to_schema() will clean up.
    """
    result = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "achievements": []
    }
    
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    text_lower = text.lower()
    
    # --- Email ---
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        result["email"] = emails[0]
    
    # --- Phone ---
    phone_patterns = [
        r'\+91[-\s]?\d{10}', r'\+91[-\s]?\d{5}[-\s]?\d{5}',
        r'\d{10}', r'\d{5}[-\s]?\d{5}'
    ]
    for pat in phone_patterns:
        phones = re.findall(pat, text)
        if phones:
            result["phone"] = phones[0]
            break
    
    # --- LinkedIn ---
    linkedin = re.findall(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s,)]+', text)
    if linkedin:
        result["linkedin"] = linkedin[0]
    
    # --- GitHub ---
    github = re.findall(r'(?:https?://)?(?:www\.)?github\.com/[^\s,)]+', text)
    if github:
        result["github"] = github[0]
    
    # --- Name (first non-empty line that's not an email/phone/url) ---
    for line in lines[:5]:
        if '@' in line or re.match(r'\+?\d{10}', line.replace(' ', '').replace('-', '')):
            continue
        if 'linkedin' in line.lower() or 'github' in line.lower():
            continue
        if len(line) < 50 and len(line.split()) <= 5:
            result["name"] = line
            break
    
    # --- Section extraction ---
    section_map = {
        "summary": ["summary", "objective", "about me", "profile", "career objective"],
        "skills": ["skills", "technical skills", "technologies", "competencies"],
        "experience": ["experience", "work experience", "employment", "internship", "work history"],
        "education": ["education", "academic", "qualification"],
        "projects": ["projects", "academic projects", "personal projects", "key projects"],
        "certifications": ["certifications", "certificates", "courses"],
        "achievements": ["achievements", "awards", "honors", "accomplishments", "extracurricular"]
    }
    
    # Find section positions
    section_positions = []
    for key, keywords in section_map.items():
        for kw in keywords:
            pattern = re.compile(rf'^\s*{re.escape(kw)}\s*$', re.IGNORECASE | re.MULTILINE)
            for m in pattern.finditer(text):
                section_positions.append((m.start(), key, kw))
    
    section_positions.sort(key=lambda x: x[0])
    
    # Extract section texts
    sections = {}
    for i, (pos, key, kw) in enumerate(section_positions):
        end_pos = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(text)
        section_text = text[pos:end_pos]
        # Remove the header line
        section_text = re.sub(rf'^\s*{re.escape(kw)}\s*$', '', section_text, count=1, flags=re.IGNORECASE | re.MULTILINE).strip()
        if key not in sections:
            sections[key] = section_text
    
    # --- Summary ---
    if "summary" in sections:
        result["summary"] = sections["summary"][:500]
    
    # --- Skills ---
    if "skills" in sections:
        raw_skills = sections["skills"]
        # Extract individual skills from text
        skill_items = re.split(r'[,•|\n]+', raw_skills)
        result["skills"] = [s.strip() for s in skill_items if s.strip() and len(s.strip()) < 50]
    
    # Also find known skills in full text
    known_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "SQL",
        "HTML", "CSS", "Bash", "Ruby", "PHP", "Rust", "Kotlin", "Swift",
        "AWS", "EC2", "S3", "Lambda", "VPC", "RDS", "Azure", "GCP",
        "Docker", "Kubernetes", "Jenkins", "Git", "GitHub Actions", "CI/CD",
        "Terraform", "Ansible", "Linux", "Nginx",
        "React", "Node.js", "FastAPI", "Flask", "Django", "Express", "Next.js",
        "Spring Boot", "Angular", "Vue.js",
        "MongoDB", "PostgreSQL", "MySQL", "Redis", "DynamoDB", "Firebase",
        "Prometheus", "Grafana", "CloudWatch",
        "TensorFlow", "PyTorch", "Scikit-learn", "NumPy", "Pandas", "OpenCV",
        "LangChain", "Hugging Face", "Streamlit"
    ]
    for skill in known_skills:
        if skill.lower() in text_lower and skill not in result["skills"]:
            result["skills"].append(skill)
    
    # --- Experience ---
    if "experience" in sections:
        result["experience"] = _parse_experience(sections["experience"])
    
    # --- Education ---
    if "education" in sections:
        result["education"] = _parse_education(sections["education"])
    
    # --- Projects ---
    if "projects" in sections:
        result["projects"] = _parse_projects(sections["projects"])
    
    # --- Certifications ---
    if "certifications" in sections:
        items = re.split(r'[•\n]+', sections["certifications"])
        result["certifications"] = [i.strip() for i in items if i.strip() and len(i.strip()) > 3]
    
    # --- Achievements ---
    if "achievements" in sections:
        items = re.split(r'[•\n]+', sections["achievements"])
        result["achievements"] = [i.strip() for i in items if i.strip() and len(i.strip()) > 3]
    
    return result


def _parse_experience(text: str) -> list:
    """Parse experience section into structured entries."""
    entries = []
    
    # Split by common role patterns
    blocks = re.split(
        r'\n(?=\s*(?:intern|engineer|developer|associate|analyst|trainee|assistant))',
        text, flags=re.IGNORECASE
    )
    
    if len(blocks) <= 1:
        # Try splitting by date patterns
        blocks = re.split(r'\n(?=.*(?:\d{4}\s*[-–]\s*(?:Present|\d{4})))', text)
    
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue
        
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        
        entry = {"title": "", "company": "", "start_date": "", "end_date": "Present", "responsibilities": []}
        
        # First line is usually title/role
        entry["title"] = lines[0] if lines else ""
        
        # Look for company and dates
        for line in lines[:3]:
            # Date pattern
            date_match = re.search(r'(\w+\s*\d{4})\s*[-–]\s*(Present|\w+\s*\d{4})', line)
            if date_match:
                entry["start_date"] = date_match.group(1)
                entry["end_date"] = date_match.group(2)
            
            # Company (if line has | separator)
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    entry["title"] = parts[0].strip()
                    entry["company"] = parts[1].strip()
        
        # Bullets — everything after first 1-2 lines
        for line in lines[1:]:
            line = line.strip()
            if line.startswith(('•', '-', '▪', '►', '*')):
                line = line.lstrip('•-▪►* ').strip()
            if len(line) > 15 and not re.search(r'\d{4}\s*[-–]', line):
                entry["responsibilities"].append(line)
        
        if entry["title"] or entry["responsibilities"]:
            entries.append(entry)
    
    return entries


def _parse_education(text: str) -> list:
    """Parse education section."""
    entries = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    current = {}
    for line in lines:
        # Degree pattern
        degree_match = re.search(
            r'(B\.?Tech|B\.?E\.?|Bachelor|Master|M\.?Tech|M\.?S\.?|MBA|Ph\.?D)',
            line, re.IGNORECASE
        )
        if degree_match:
            if current:
                entries.append(current)
            current = {"degree": line, "institution": "", "gpa": "", "graduation_date": ""}
        elif current and not current.get("institution"):
            # Check for institution name or GPA
            gpa_match = re.search(r'(?:CGPA|GPA|Percentage)\s*:?\s*([\d.]+)', line, re.IGNORECASE)
            if gpa_match:
                current["gpa"] = gpa_match.group(1)
            elif len(line) > 5:
                current["institution"] = line
        elif current:
            # Additional info (dates, GPA)
            gpa_match = re.search(r'(?:CGPA|GPA)\s*:?\s*([\d.]+)', line, re.IGNORECASE)
            if gpa_match:
                current["gpa"] = gpa_match.group(1)
            year_match = re.findall(r'20\d{2}', line)
            if year_match:
                current["graduation_date"] = year_match[-1]
    
    if current:
        entries.append(current)
    
    return entries


def _parse_projects(text: str) -> list:
    """Parse projects section."""
    entries = []
    
    # Split by project headers (lines that look like titles)
    blocks = re.split(r'\n(?=[A-Z][\w\s-]{3,40}(?:\n|$))', text)
    
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 15:
            continue
        
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        
        proj = {"name": lines[0], "description": "", "technologies": ""}
        
        bullets = []
        for line in lines[1:]:
            line = line.strip()
            if line.startswith(('•', '-', '▪', '►', '*')):
                line = line.lstrip('•-▪►* ').strip()
            if re.match(r'^(Tech\s*Stack|Technologies)', line, re.IGNORECASE):
                proj["technologies"] = re.sub(r'^(Tech\s*Stack|Technologies)\s*:?\s*', '', line, flags=re.IGNORECASE)
            elif len(line) > 10:
                bullets.append(line)
        
        proj["description"] = " ".join(bullets[:3])
        
        if proj["name"]:
            entries.append(proj)
    
    return entries[:5]  # Max 5 projects
