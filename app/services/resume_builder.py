"""
Resume Intelligence Engine — Service Layer
==========================================
Phase 1: Schema Normalization
Phase 2: AI-Powered Content Refinement (fresher-focused)

Locked JSON Schema:
{
  "basics": { "full_name", "phone", "email", "location", "linkedin", "github" },
  "summary": "",
  "skills": { "languages", "cloud_infrastructure", "devops_automation", "databases", "monitoring", "frameworks_tools" },
  "experience": [{ "company", "role", "start_date", "end_date", "bullets" }],
  "projects": [{ "name", "type", "year", "bullets" }],
  "education": [{ "degree", "institution", "cgpa", "start_year", "end_year" }],
  "certifications": [],
  "achievements": []
}
"""

import json
import re
from typing import Optional
from app.config import client, USE_MOCK_AI, GEMINI_MODEL


# ==========================================
# EMPTY LOCKED SCHEMA
# ==========================================

def empty_schema() -> dict:
    """Returns a blank locked schema."""
    return {
        "basics": {
            "full_name": "",
            "phone": "",
            "email": "",
            "location": "",
            "linkedin": "",
            "github": ""
        },
        "summary": "",
        "skills": {
            "languages": [],
            "cloud_infrastructure": [],
            "devops_automation": [],
            "databases": [],
            "monitoring": [],
            "frameworks_tools": []
        },
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "achievements": []
    }


# ==========================================
# PHASE 1: NORMALIZE ANY DICT → LOCKED SCHEMA
# ==========================================

def normalize_to_schema(raw: dict) -> dict:
    """
    Takes any parsed resume dict (from regex or AI) and maps it
    into the locked JSON schema. Handles both old flat format
    and new nested format.
    """
    schema = empty_schema()
    
    # --- Basics ---
    if "basics" in raw and isinstance(raw["basics"], dict):
        b = raw["basics"]
        schema["basics"]["full_name"] = str(b.get("full_name", "") or b.get("name", "")).strip()
        schema["basics"]["phone"] = str(b.get("phone", "")).strip()
        schema["basics"]["email"] = str(b.get("email", "")).strip()
        schema["basics"]["location"] = str(b.get("location", "")).strip()
        schema["basics"]["linkedin"] = str(b.get("linkedin", "")).strip()
        schema["basics"]["github"] = str(b.get("github", "")).strip()
    else:
        # Flat format fallback
        schema["basics"]["full_name"] = str(raw.get("name", "") or raw.get("full_name", "")).strip()
        schema["basics"]["phone"] = str(raw.get("phone", "")).strip()
        schema["basics"]["email"] = str(raw.get("email", "")).strip()
        schema["basics"]["location"] = str(raw.get("location", "")).strip()
        schema["basics"]["linkedin"] = str(raw.get("linkedin", "")).strip()
        schema["basics"]["github"] = str(raw.get("github", "")).strip()
    
    # --- Summary ---
    schema["summary"] = str(raw.get("summary", "")).strip()
    
    # --- Skills ---
    if "skills" in raw and isinstance(raw["skills"], dict):
        sk = raw["skills"]
        for key in ["languages", "cloud_infrastructure", "devops_automation", "databases", "monitoring", "frameworks_tools"]:
            schema["skills"][key] = _ensure_list(sk.get(key, []))
    elif "skills" in raw and isinstance(raw["skills"], list):
        # Flat list → auto-categorize
        schema["skills"] = _categorize_skills_flat(raw["skills"])
    
    # --- Experience ---
    for exp in raw.get("experience", []):
        if not isinstance(exp, dict):
            continue
        schema["experience"].append({
            "company": str(exp.get("company", "")).strip(),
            "role": str(exp.get("role", "") or exp.get("title", "")).strip(),
            "start_date": str(exp.get("start_date", "")).strip(),
            "end_date": str(exp.get("end_date", "Present")).strip() or "Present",
            "bullets": _ensure_list(exp.get("bullets", []) or exp.get("responsibilities", []))
        })
    
    # --- Projects ---
    for proj in raw.get("projects", []):
        if not isinstance(proj, dict):
            continue
        bullets = _ensure_list(proj.get("bullets", []))
        # If no bullets but has description, split into bullets
        if not bullets and proj.get("description"):
            bullets = _split_into_bullets(str(proj["description"]))
        schema["projects"].append({
            "name": str(proj.get("name", "")).strip(),
            "type": str(proj.get("type", "") or proj.get("technologies", "")).strip(),
            "year": str(proj.get("year", "")).strip(),
            "bullets": bullets
        })
    
    # --- Education ---
    for edu in raw.get("education", []):
        if not isinstance(edu, dict):
            continue
        entry = {
            "degree": str(edu.get("degree", "")).strip(),
            "institution": str(edu.get("institution", "")).strip(),
            "cgpa": str(edu.get("cgpa", "") or edu.get("gpa", "")).strip(),
            "start_year": str(edu.get("start_year", "")).strip(),
            "end_year": str(edu.get("end_year", "") or edu.get("graduation_date", "")).strip()
        }
        # Filter out SSC/Intermediate
        if not _is_school_level(entry):
            schema["education"].append(entry)
    
    # --- Certifications ---
    schema["certifications"] = _ensure_list(raw.get("certifications", []))
    
    # --- Achievements ---
    schema["achievements"] = _ensure_list(raw.get("achievements", []))
    
    return schema


# ==========================================
# PHASE 2: AI REFINEMENT (FRESHER-FOCUSED)
# ==========================================

def refine_resume(schema: dict) -> dict:
    """
    AI-powered content refinement.
    Takes locked schema, returns locked schema with improved content.
    Optimized for college freshers / entry-level roles.
    """
    if USE_MOCK_AI or not client:
        return schema
    
    try:
        prompt = f"""
You are a senior resume architect for COLLEGE FRESHERS and ENTRY-LEVEL candidates.

Your job: take this structured resume and REFINE the content.
DO NOT change the JSON structure. Only improve the VALUES.

RULES:
1. SUMMARY — Write a strong 2-3 line summary positioning as an aspiring
   developer/engineer with hands-on project experience. Tone: confident but not
   exaggerating. Mention key tech and project highlights.

2. SKILLS — Clean up each category:
   - Remove duplicates, fix capitalization
   - Remove non-technical items (VS Code, Data Structures, Problem Solving,
     Communication, MS Office)
   - If a skill is in the wrong category, move it to the correct one

3. EXPERIENCE — For each bullet:
   - Start with strong action verb (Built, Developed, Automated, Deployed, Configured)
   - Max 2 lines per bullet
   - No passive voice, no "Responsible for"
   - Even if intern, make it sound results-driven
   - Keep company and dates exactly as-is

4. PROJECTS — For each bullet:
   - Start with action verb
   - Max 2 lines
   - Integrate tech naturally (no separate "Tech Stack:" lines)
   - Make it sound like real engineering work, not college assignments

5. EDUCATION — Keep as-is. Do NOT add or remove entries.

6. CERTIFICATIONS / ACHIEVEMENTS — Keep as-is. Only fix grammar.

7. CRITICAL — Do NOT invent fake metrics, achievements, or companies.
   Only improve clarity, grammar, impact, and verb strength.

CURRENT RESUME:
{json.dumps(schema, indent=2)}

Return ONLY valid JSON in the EXACT SAME STRUCTURE.
No explanation. No markdown. No commentary. Just the JSON.
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start >= 0 and end > start:
            refined = json.loads(text[start:end])
            
            # Validate structure — must have all locked keys
            refined = _validate_schema(refined, schema)
            
            # Code-level cleanup after AI
            refined["skills"] = _clean_skills(refined.get("skills", {}))
            refined["experience"] = _clean_experience(refined.get("experience", []), schema.get("experience", []))
            refined["projects"] = _clean_projects(refined.get("projects", []))
            
            # Re-filter education (safety net)
            refined["education"] = [e for e in refined.get("education", []) if not _is_school_level(e)]
            if not refined["education"] and schema.get("education"):
                refined["education"] = schema["education"]
            
            print("✅ Resume refined by AI")
            return refined
        else:
            print("⚠️ Could not parse AI response, returning original")
            return schema
            
    except Exception as e:
        print(f"⚠️ AI refinement failed: {e}")
        return schema


def calculate_score(schema: dict) -> int:
    """Calculate an ATS readiness score (0-100) from the locked schema."""
    score = 0
    
    # Basics (20 pts)
    b = schema.get("basics", {})
    if b.get("full_name"): score += 5
    if b.get("email"): score += 5
    if b.get("phone"): score += 3
    if b.get("linkedin"): score += 4
    if b.get("github"): score += 3
    
    # Summary (10 pts)
    summary = schema.get("summary", "")
    if len(summary) > 50: score += 10
    elif summary: score += 5
    
    # Skills (20 pts)
    skills = schema.get("skills", {})
    total_skills = sum(len(v) for v in skills.values() if isinstance(v, list))
    if total_skills >= 12: score += 20
    elif total_skills >= 8: score += 15
    elif total_skills >= 4: score += 10
    elif total_skills > 0: score += 5
    
    # Experience (20 pts)
    exp = schema.get("experience", [])
    if len(exp) >= 2: score += 10
    elif len(exp) >= 1: score += 7
    total_bullets = sum(len(e.get("bullets", [])) for e in exp)
    if total_bullets >= 6: score += 10
    elif total_bullets >= 3: score += 7
    elif total_bullets > 0: score += 3
    
    # Projects (15 pts)
    proj = schema.get("projects", [])
    if len(proj) >= 3: score += 10
    elif len(proj) >= 2: score += 8
    elif len(proj) >= 1: score += 5
    proj_bullets = sum(len(p.get("bullets", [])) for p in proj)
    if proj_bullets >= 4: score += 5
    elif proj_bullets > 0: score += 3
    
    # Education (10 pts)
    if schema.get("education"): score += 10
    
    # Certifications (5 pts)
    if schema.get("certifications"): score += 5
    
    return min(score, 100)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _ensure_list(val) -> list:
    """Ensure value is a list of non-empty strings."""
    if not val:
        return []
    if isinstance(val, str):
        return [val.strip()] if val.strip() else []
    return [str(v).strip() for v in val if str(v).strip()]


def _split_into_bullets(text: str) -> list:
    """Split a long description into bullet points."""
    if "•" in text:
        return [p.strip() for p in text.split("•") if p.strip()]
    if "\n" in text:
        return [p.strip() for p in text.split("\n") if p.strip()]
    if len(text) < 200:
        return [text]
    sentences = re.split(r'(?<=[.!])\s+', text)
    return [s.strip() for s in sentences if s.strip()][:3]


def _is_school_level(edu: dict) -> bool:
    """Check if education entry is SSC/Intermediate/school level."""
    remove_kw = [
        "ssc", "10th", "10 th", "class 10", "class x",
        "intermediate", "12th", "12 th", "class 12", "class xii",
        "high school", "secondary", "junior college",
        "sr. secondary", "sr secondary", "higher secondary",
        "matriculation", "hsc", "diploma"
    ]
    combined = f"{edu.get('degree', '')} {edu.get('institution', '')}".lower()
    return any(kw in combined for kw in remove_kw)


def _categorize_skills_flat(skills_list: list) -> dict:
    """Take a flat skill list and categorize into the locked schema groups."""
    cats = {
        "languages": [],
        "cloud_infrastructure": [],
        "devops_automation": [],
        "databases": [],
        "monitoring": [],
        "frameworks_tools": []
    }
    
    kw_map = {
        "languages": ["python", "java", "javascript", "typescript", "c++", "c#",
                       "go", "golang", "sql", "bash", "shell", "ruby", "php",
                       "html", "css", "rust", "kotlin", "swift", "scala", "r "],
        "cloud_infrastructure": ["aws", "ec2", "s3", "lambda", "vpc", "rds", "iam",
                                  "cloudfront", "route53", "cloudformation", "terraform",
                                  "azure", "gcp", "google cloud", "linux", "nginx"],
        "devops_automation": ["docker", "kubernetes", "k8s", "jenkins", "github actions",
                               "gitlab ci", "ci/cd", "cicd", "ansible", "git", "github",
                               "gitlab", "helm", "argocd"],
        "databases": ["mongodb", "postgres", "postgresql", "mysql", "redis", "dynamodb",
                       "sqlite", "firebase", "cassandra", "elasticsearch", "neo4j"],
        "monitoring": ["prometheus", "grafana", "nagios", "cloudwatch", "datadog",
                        "elk", "kibana", "logstash", "splunk", "new relic"],
        "frameworks_tools": ["react", "node.js", "nodejs", "fastapi", "flask", "express",
                              "django", "next.js", "nextjs", "spring", "spring boot",
                              "angular", "vue", "streamlit", "gradio", "bootstrap",
                              "tailwind", "celery", "rabbitmq", "kafka",
                              "scikit-learn", "numpy", "pandas", "opencv", "tensorflow",
                              "pytorch", "langchain", "hugging face", "matplotlib"]
    }
    
    # Junk skills to skip entirely
    junk = ["vs code", "vscode", "visual studio code", "data structure",
            "data structures", "problem solving", "problem-solving",
            "communication", "teamwork", "leadership", "ms office",
            "microsoft office", "operating system"]
    
    seen = set()
    for skill in skills_list:
        s = str(skill).strip()
        if not s:
            continue
        sl = s.lower()
        if sl in seen or any(j in sl for j in junk):
            continue
        seen.add(sl)
        
        placed = False
        for cat, keywords in kw_map.items():
            if any(kw in sl for kw in keywords):
                cats[cat].append(s)
                placed = True
                break
        
        if not placed:
            cats["frameworks_tools"].append(s)
    
    return cats


def _clean_skills(skills: dict) -> dict:
    """Code-level skill cleanup after AI refinement."""
    if not isinstance(skills, dict):
        return empty_schema()["skills"]
    
    junk = ["vs code", "vscode", "data structure", "data structures",
            "problem solving", "problem-solving", "communication",
            "teamwork", "ms office"]
    
    cleaned = {}
    for cat in ["languages", "cloud_infrastructure", "devops_automation",
                 "databases", "monitoring", "frameworks_tools"]:
        raw = skills.get(cat, [])
        if not isinstance(raw, list):
            raw = []
        seen = set()
        clean_list = []
        for s in raw:
            s = str(s).strip()
            sl = s.lower()
            if sl and sl not in seen and not any(j in sl for j in junk):
                seen.add(sl)
                clean_list.append(s)
        cleaned[cat] = clean_list
    
    return cleaned


def _clean_experience(experience: list, original: list) -> list:
    """Ensure company + dates are present."""
    cleaned = []
    for idx, exp in enumerate(experience):
        if not isinstance(exp, dict):
            continue
        # Fallback company/dates from original
        if not exp.get("company") and idx < len(original):
            orig = original[idx] if isinstance(original[idx], dict) else {}
            exp["company"] = orig.get("company", "")
        if not exp.get("start_date") and idx < len(original):
            orig = original[idx] if isinstance(original[idx], dict) else {}
            exp["start_date"] = orig.get("start_date", "")
            exp["end_date"] = orig.get("end_date", "Present")
        if not exp.get("end_date"):
            exp["end_date"] = "Present"
        # Truncate long bullets
        exp["bullets"] = [_truncate(b) for b in exp.get("bullets", []) if str(b).strip()]
        cleaned.append(exp)
    return cleaned


def _clean_projects(projects: list) -> list:
    """Clean project bullets — remove tech stack lines, truncate."""
    cleaned = []
    for proj in projects:
        if not isinstance(proj, dict):
            continue
        bullets = []
        for b in proj.get("bullets", []):
            b = str(b).strip()
            # Skip "Tech Stack:" lines
            if re.match(r'^(tech\s*stack|technologies?\s*(used)?|built\s*with)\s*:', b, re.IGNORECASE):
                continue
            b = re.sub(r'\s*Tech\s*Stack\s*:.*$', '', b, flags=re.IGNORECASE).strip()
            if b:
                bullets.append(_truncate(b))
        proj["bullets"] = bullets
        cleaned.append(proj)
    return cleaned


def _truncate(text: str, max_chars: int = 200) -> str:
    """Truncate to ~2 lines."""
    text = str(text).strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(' ', 1)[0]
    if not truncated.endswith('.'):
        truncated += '.'
    return truncated


def _validate_schema(refined: dict, original: dict) -> dict:
    """Ensure refined output has all locked schema keys, falling back to original."""
    # Basics
    if "basics" not in refined or not isinstance(refined["basics"], dict):
        refined["basics"] = original.get("basics", empty_schema()["basics"])
    else:
        for key in ["full_name", "phone", "email", "location", "linkedin", "github"]:
            if not refined["basics"].get(key):
                refined["basics"][key] = original.get("basics", {}).get(key, "")
    
    # Summary
    if not refined.get("summary"):
        refined["summary"] = original.get("summary", "")
    
    # Skills
    if "skills" not in refined or not isinstance(refined["skills"], dict):
        refined["skills"] = original.get("skills", empty_schema()["skills"])
    
    # Lists
    for key in ["experience", "projects", "education", "certifications", "achievements"]:
        if key not in refined or not isinstance(refined[key], list):
            refined[key] = original.get(key, [])
    
    return refined
