"""
Resume Routes
=============
Upload and parse resume with improved extraction.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import re

router = APIRouter()

# Create uploads directory
os.makedirs("uploads", exist_ok=True)


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse a resume file."""
    
    # Validate file type
    allowed_types = [".pdf", ".docx", ".doc"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Parse resume
    try:
        parsed = parse_resume(file_path, file_ext)
        print(f"✅ Parsed resume: {parsed.get('name')} - {len(parsed.get('skills', []))} skills")
        return parsed
    except Exception as e:
        print(f"❌ Resume parsing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def parse_resume(file_path: str, file_ext: str) -> dict:
    """Parse resume file and extract information."""
    
    # Extract text
    if file_ext == ".pdf":
        text = extract_pdf_text(file_path)
    elif file_ext in [".docx", ".doc"]:
        text = extract_docx_text(file_path)
    else:
        text = ""
    
    if not text:
        return {"error": "Could not extract text from resume"}
    
    print(f"📄 Extracted {len(text)} characters from resume")
    
    # Parse extracted text
    parsed = extract_resume_info(text)
    parsed["raw_text"] = text[:3000]
    
    return parsed


def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    
    # Try PyPDF2 first
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            print("✅ Extracted text using PyPDF2")
            return text
    except ImportError:
        print("⚠️ PyPDF2 not installed")
    except Exception as e:
        print(f"⚠️ PyPDF2 failed: {e}")
    
    # Try pdfplumber as fallback
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            print("✅ Extracted text using pdfplumber")
            return text
    except ImportError:
        print("⚠️ pdfplumber not installed")
    except Exception as e:
        print(f"⚠️ pdfplumber failed: {e}")
    
    return text


def extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        print("✅ Extracted text using python-docx")
        return text
    except ImportError:
        print("⚠️ python-docx not installed")
        return ""
    except Exception as e:
        print(f"⚠️ DOCX extraction failed: {e}")
        return ""


def extract_resume_info(text: str) -> dict:
    """Extract structured information from resume text."""
    
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
        "certifications": []
    }
    
    if not text:
        return result
    
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    text_lower = text.lower()
    
    # ==========================================
    # Extract Contact Information
    # ==========================================
    
    # Email - look for email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    if emails:
        result["email"] = emails[0]
        print(f"📧 Found email: {result['email']}")
    
    # Phone - various formats
    phone_patterns = [
        r'\+91[-\s]?\d{10}',
        r'\+91[-\s]?\d{5}[-\s]?\d{5}',
        r'\d{10}',
        r'\d{5}[-\s]?\d{5}',
        r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,5}[-\s\.]?[0-9]{4,6}'
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            result["phone"] = phones[0]
            print(f"📱 Found phone: {result['phone']}")
            break
    
    # Name - usually first line, not containing @ or numbers
    for line in lines[:5]:
        # Skip if line contains email, phone, or common headers
        if '@' in line or re.search(r'\d{5,}', line):
            continue
        if any(word in line.lower() for word in ['resume', 'cv', 'curriculum', 'objective', 'summary']):
            continue
        # Check if it looks like a name (2-4 words, mostly letters)
        words = line.split()
        if 1 <= len(words) <= 5 and all(re.match(r'^[A-Za-z\.]+$', w) for w in words):
            result["name"] = line
            print(f"👤 Found name: {result['name']}")
            break
    
    # Location - look for city/state patterns
    location_patterns = [
        r'([A-Z][a-z]+),?\s*(Andhra Pradesh|Telangana|Karnataka|Tamil Nadu|Maharashtra|Delhi|Gujarat|Kerala)',
        r'(Vijayawada|Hyderabad|Bangalore|Chennai|Mumbai|Delhi|Pune|Kolkata)',
    ]
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            result["location"] = match.group(0)
            break
    
    # LinkedIn
    linkedin_pattern = r'(?:linkedin\.com/in/|linkedin[:\s]+)([a-zA-Z0-9-]+)'
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        result["linkedin"] = linkedin_match.group(1)
    elif 'linkedin' in text_lower:
        result["linkedin"] = "Present"
    
    # GitHub
    github_pattern = r'(?:github\.com/|github[:\s]+)([a-zA-Z0-9-]+)'
    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        result["github"] = github_match.group(1)
    elif 'github' in text_lower:
        result["github"] = "Present"
    
    # ==========================================
    # Extract Sections
    # ==========================================
    
    # Find section boundaries
    section_headers = {
        'education': ['education', 'academic', 'qualification', 'academics'],
        'experience': ['experience', 'work experience', 'employment', 'work history', 'internship'],
        'skills': ['skills', 'technical skills', 'technologies', 'tech stack', 'competencies'],
        'projects': ['projects', 'personal projects', 'academic projects', 'key projects'],
        'certifications': ['certifications', 'certificates', 'courses', 'achievements'],
        'summary': ['summary', 'objective', 'about', 'profile', 'about me']
    }
    
    # ==========================================
    # Extract Education
    # ==========================================
    
    edu_section = extract_section_text(text, section_headers['education'])
    if edu_section:
        result["education"] = parse_education_section(edu_section)
        print(f"🎓 Found {len(result['education'])} education entries")
    
    # ==========================================
    # Extract Experience
    # ==========================================
    
    exp_section = extract_section_text(text, section_headers['experience'])
    if exp_section:
        result["experience"] = parse_experience_section(exp_section)
        print(f"💼 Found {len(result['experience'])} experience entries")
    
    # Also check for inline experience (company names with dates)
    if not result["experience"]:
        result["experience"] = find_inline_experience(text)
        if result["experience"]:
            print(f"💼 Found {len(result['experience'])} inline experience entries")
    
    # ==========================================
    # Extract Skills
    # ==========================================
    
    # Look in skills section first
    skills_section = extract_section_text(text, section_headers['skills'])
    if skills_section:
        result["skills"] = parse_skills_section(skills_section)
    
    # Also scan entire text for known skills
    additional_skills = find_known_skills(text)
    for skill in additional_skills:
        if skill not in result["skills"]:
            result["skills"].append(skill)
    
    print(f"🛠️ Found {len(result['skills'])} skills")
    
    # ==========================================
    # Extract Projects
    # ==========================================
    
    proj_section = extract_section_text(text, section_headers['projects'])
    if proj_section:
        result["projects"] = parse_projects_section(proj_section)
        print(f"📁 Found {len(result['projects'])} projects")
    
    # ==========================================
    # Extract Certifications
    # ==========================================
    
    cert_section = extract_section_text(text, section_headers['certifications'])
    if cert_section:
        result["certifications"] = parse_certifications_section(cert_section)
    
    # ==========================================
    # Extract Summary
    # ==========================================
    
    summary_section = extract_section_text(text, section_headers['summary'])
    if summary_section:
        result["summary"] = summary_section[:500]
    
    return result


def extract_section_text(text: str, keywords: list) -> str:
    """Extract text for a specific section."""
    
    lines = text.split('\n')
    section_start = -1
    section_end = len(lines)
    
    # Common section headers to detect end of current section
    all_section_keywords = [
        'education', 'experience', 'skills', 'projects', 'certifications',
        'achievements', 'summary', 'objective', 'contact', 'references',
        'work history', 'technical skills', 'extracurricular', 'hobbies'
    ]
    
    # Find section start
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for keyword in keywords:
            if keyword in line_lower and len(line_lower) < 50:
                section_start = i + 1
                break
        if section_start > -1:
            break
    
    if section_start == -1:
        return ""
    
    # Find section end (next section header)
    for i in range(section_start, len(lines)):
        line_lower = lines[i].lower().strip()
        # Check if this line is a new section header
        for kw in all_section_keywords:
            if kw in line_lower and kw not in keywords and len(line_lower) < 50:
                section_end = i
                break
        if section_end != len(lines):
            break
    
    return '\n'.join(lines[section_start:section_end])


def parse_education_section(section: str) -> list:
    """Parse education section into structured data."""
    
    education = []
    lines = [l.strip() for l in section.split('\n') if l.strip()]
    
    # Patterns for degrees and dates
    degree_patterns = [
        r'B\.?Tech|Bachelor|B\.?E\.|B\.?Sc|M\.?Tech|Master|MBA|MCA|BCA|Intermediate|SSC|HSC|12th|10th|Diploma'
    ]
    date_pattern = r'\d{2}[-/]\d{4}|\d{4}\s*[-–]\s*\d{4}|\d{4}\s*[-–]\s*Present'
    
    current_edu = {}
    
    for line in lines:
        # Check for degree keywords
        has_degree = any(re.search(p, line, re.IGNORECASE) for p in degree_patterns)
        has_date = re.search(date_pattern, line)
        
        # Check for institution keywords
        institution_keywords = ['institute', 'college', 'university', 'school', 'academy', 'vidya']
        has_institution = any(kw in line.lower() for kw in institution_keywords)
        
        # Check for score/grade
        score_pattern = r'CGPA[:\s-]*(\d+\.?\d*)|(\d+\.?\d*)\s*CGPA|(\d+)\s*%'
        score_match = re.search(score_pattern, line, re.IGNORECASE)
        
        if has_institution and not current_edu.get('institution'):
            current_edu['institution'] = line
        elif has_degree and not current_edu.get('degree'):
            current_edu['degree'] = line
        elif has_date:
            current_edu['date'] = re.search(date_pattern, line).group(0)
        
        if score_match:
            current_edu['score'] = score_match.group(0)
        
        # If we have enough info, save and start new entry
        if current_edu.get('institution') or current_edu.get('degree'):
            if has_date or len(current_edu) >= 2:
                if current_edu not in education:
                    education.append(current_edu.copy())
                current_edu = {}
    
    # Don't forget last entry
    if current_edu and current_edu not in education:
        education.append(current_edu)
    
    # If no structured data found, create entries from lines
    if not education:
        for line in lines[:6]:  # Take first 6 lines
            if len(line) > 10:
                education.append({"description": line})
    
    return education[:5]


def parse_experience_section(section: str) -> list:
    """Parse experience section into structured data."""
    
    experience = []
    lines = [l.strip() for l in section.split('\n') if l.strip()]
    
    date_pattern = r'\d{2}[-/]\d{4}|\d{4}\s*[-–]\s*\d{4}|\d{4}\s*[-–]\s*Present|\w+\s+\d{4}\s*[-–]\s*\w+\s+\d{4}|\w+\s+\d{4}\s*[-–]\s*Present'
    
    current_exp = {}
    current_bullets = []
    
    for line in lines:
        has_date = re.search(date_pattern, line, re.IGNORECASE)
        
        # Check for job title keywords
        title_keywords = ['engineer', 'developer', 'intern', 'analyst', 'manager', 'lead', 'associate', 'consultant']
        has_title = any(kw in line.lower() for kw in title_keywords)
        
        # Check if line is a bullet point
        is_bullet = line.startswith('•') or line.startswith('-') or line.startswith('*')
        
        if has_date and has_title:
            # Save previous experience
            if current_exp:
                current_exp['responsibilities'] = current_bullets
                experience.append(current_exp.copy())
            
            current_exp = {
                'title': line,
                'date': re.search(date_pattern, line).group(0)
            }
            current_bullets = []
        elif has_title and not current_exp.get('title'):
            current_exp['title'] = line
        elif is_bullet or (current_exp.get('title') and len(line) > 20):
            current_bullets.append(line.lstrip('•-* '))
    
    # Save last experience
    if current_exp:
        current_exp['responsibilities'] = current_bullets
        experience.append(current_exp)
    
    return experience[:5]


def find_inline_experience(text: str) -> list:
    """Find experience mentioned inline in the text."""
    
    experience = []
    
    # Look for common patterns like "Company Name (Date - Date)" or "Role at Company"
    patterns = [
        r'(\w+\s+(?:Engineer|Developer|Intern|Analyst))\s*\(([^)]+)\)\s*(?:at|@|[-–])?\s*(\w+)',
        r'(\w+)\s*[-–]\s*((?:\d{2}[-/]\d{4}|\w+\s+\d{4})\s*[-–]\s*(?:\d{2}[-/]\d{4}|\w+\s+\d{4}|Present))',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) >= 2:
                experience.append({
                    'title': match[0],
                    'date': match[1] if len(match) > 1 else ''
                })
    
    return experience[:5]


def parse_skills_section(section: str) -> list:
    """Parse skills section."""
    
    skills = []
    
    # Remove common prefixes
    section = re.sub(r'(Languages|Developer Tools|Technologies|Frameworks)[:\s]*', '', section, flags=re.IGNORECASE)
    
    # Split by various delimiters
    parts = re.split(r'[,•|;:\n]+', section)
    
    for part in parts:
        skill = part.strip()
        # Clean up
        skill = re.sub(r'^[-•*]\s*', '', skill)
        
        if skill and 2 <= len(skill) <= 40:
            # Avoid duplicates
            if skill not in skills and skill.lower() not in [s.lower() for s in skills]:
                skills.append(skill)
    
    return skills


def find_known_skills(text: str) -> list:
    """Find known skills in text."""
    
    known_skills = [
        # Languages
        "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin",
        # Web
        "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring", "Bootstrap",
        # Databases
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "NoSQL", "SQLite", "Oracle", "Firebase",
        # Cloud & DevOps
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Jenkins", "GitHub Actions", "Terraform",
        "EC2", "S3", "Lambda", "EBS", "VPC", "Route53", "CloudFront",
        # Tools
        "Git", "GitHub", "GitLab", "VS Code", "Linux", "Bash", "PowerShell",
        # ML/AI
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn", "OpenCV",
        "NLP", "Computer Vision", "LLM", "Hugging Face",
        # Data
        "Data Science", "Data Analysis", "Power BI", "Tableau", "Excel",
        # Concepts
        "REST", "API", "GraphQL", "Microservices", "Agile", "Scrum", "OOP", "Data Structure",
        # Soft skills
        "Communication", "Leadership", "Teamwork", "Problem Solving"
    ]
    
    found = []
    text_lower = text.lower()
    
    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append(skill)
    
    return found


def parse_projects_section(section: str) -> list:
    """Parse projects section."""
    
    projects = []
    lines = [l.strip() for l in section.split('\n') if l.strip()]
    
    current_project = {}
    current_description = []
    
    for line in lines:
        # Check if this is a project title
        # Project titles usually: have GitHub link, tech keywords, or are short headers
        has_github = 'github' in line.lower()
        has_date = re.search(r'\d{2}[-/]\d{4}|\d{4}', line)
        is_bullet = line.startswith('•') or line.startswith('-') or line.startswith('*') or line.startswith('●')
        has_tech_prefix = line.lower().startswith('technologies:') or line.lower().startswith('tech stack:')
        
        # Check for project name patterns (title case, contains keywords like "using", "with", "|")
        looks_like_title = (
            (has_github or has_date or '|' in line or ' – ' in line or ' - ' in line) and 
            not is_bullet and 
            not has_tech_prefix and
            len(line) < 150
        )
        
        # Also detect titles that are short and in title case without bullets
        if not looks_like_title and not is_bullet and not has_tech_prefix:
            words = line.split()
            if 3 <= len(words) <= 15 and any(w[0].isupper() for w in words if w):
                # Check for project-like keywords
                project_keywords = ['prediction', 'detection', 'system', 'app', 'application', 'platform', 'tool', 'website', 'api', 'bot', 'ai', 'ml', 'using', 'based']
                if any(kw in line.lower() for kw in project_keywords):
                    looks_like_title = True
        
        if looks_like_title:
            # Save previous project
            if current_project:
                current_project['description'] = ' '.join(current_description)
                if current_project.get('name'):
                    projects.append(current_project.copy())
            
            current_project = {'name': line}
            current_description = []
        elif has_tech_prefix:
            # This is technologies line - add to current project
            current_project['technologies'] = line
        elif is_bullet or (current_project.get('name') and len(line) > 10):
            current_description.append(line.lstrip('•-*● '))
    
    # Save last project
    if current_project:
        current_project['description'] = ' '.join(current_description)
        if current_project.get('name'):
            projects.append(current_project)
    
    # If still no projects found, try alternative parsing
    if not projects:
        projects = find_projects_alternative(section)
    
    return projects[:6]


def find_projects_alternative(text: str) -> list:
    """Alternative project finding for edge cases."""
    
    projects = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for GitHub links or project indicators
        if 'github' in line.lower() or any(kw in line.lower() for kw in ['prediction', 'detection', 'system', 'platform', 'application']):
            if not line.startswith('●') and not line.startswith('•') and not line.startswith('-'):
                project = {'name': line}
                descriptions = []
                
                # Collect following bullet points
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith('●') or next_line.startswith('•') or next_line.startswith('-'):
                        descriptions.append(next_line.lstrip('●•- '))
                        i += 1
                    elif next_line.lower().startswith('technologies:'):
                        project['technologies'] = next_line
                        i += 1
                    elif next_line and not any(kw in next_line.lower() for kw in ['github', 'prediction', 'detection']):
                        # Might be continuation
                        if len(next_line) > 20:
                            descriptions.append(next_line)
                        i += 1
                    else:
                        break
                
                project['description'] = ' '.join(descriptions)
                projects.append(project)
                continue
        
        i += 1
    
    return projects


def parse_certifications_section(section: str) -> list:
    """Parse certifications section."""
    
    certs = []
    lines = [l.strip() for l in section.split('\n') if l.strip()]
    
    for line in lines:
        line = line.lstrip('•-* ')
        if len(line) > 5:
            certs.append(line)
    
    return certs[:10]