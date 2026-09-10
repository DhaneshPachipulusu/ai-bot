"""
PDF Generator — Template Rendering Engine
==========================================
Reads the LOCKED JSON SCHEMA and renders a constant premium PDF template.

Template sections (fixed order):
1. Header (Name + Contact)
2. Professional Summary
3. Technical Skills (categorized)
4. Work Experience
5. Projects
6. Education
7. Certifications
8. Achievements

Template is CONSTANT. Only data changes.
"""

import os
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)
from reportlab.lib import colors


# ==========================================
# DESIGN TOKENS
# ==========================================
BLACK = colors.HexColor('#000000')
DARK = colors.HexColor('#1a1a1a')
MEDIUM = colors.HexColor('#333333')
SUBTLE = colors.HexColor('#555555')
ACCENT = colors.HexColor('#2c3e50')


def _s(val) -> str:
    """Convert any value to string, treating None/null as empty."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("none", "null", "n/a"):
        return ""
    return s


def _safe(text) -> str:
    """Escape XML-unsafe chars, preserve <b>/<i> tags."""
    text = _s(text)
    if not text:
        return ""
    text = re.sub(r'&(?!amp;|lt;|gt;)', '&amp;', text)
    text = re.sub(r'<(?!/?(b|i|u|br)\b)', '&lt;', text)
    return text


def generate_resume_pdf(schema: dict, output_path: str) -> str:
    """
    Render locked schema into a premium ATS-friendly PDF.
    Template is constant — only data changes.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.55*inch,
        leftMargin=0.55*inch,
        topMargin=0.4*inch,
        bottomMargin=0.4*inch
    )
    
    story = []
    
    # ==========================================
    # STYLES (constant template)
    # ==========================================
    
    s_name = ParagraphStyle(
        'Name', fontName='Helvetica-Bold', fontSize=22,
        textColor=BLACK, alignment=TA_CENTER, spaceAfter=4, leading=26
    )
    s_contact = ParagraphStyle(
        'Contact', fontName='Helvetica', fontSize=8.5,
        textColor=SUBTLE, alignment=TA_CENTER, spaceAfter=6, leading=11
    )
    s_section = ParagraphStyle(
        'Section', fontName='Helvetica-Bold', fontSize=10.5,
        textColor=ACCENT, spaceBefore=8, spaceAfter=3, leading=13
    )
    s_summary = ParagraphStyle(
        'Summary', fontName='Helvetica', fontSize=9.5,
        textColor=DARK, spaceAfter=2, leading=13, alignment=TA_JUSTIFY
    )
    s_role = ParagraphStyle(
        'Role', fontName='Helvetica-Bold', fontSize=10,
        textColor=BLACK, spaceAfter=1, leading=13
    )
    s_meta = ParagraphStyle(
        'Meta', fontName='Helvetica-Oblique', fontSize=9,
        textColor=SUBTLE, spaceAfter=3, leading=11
    )
    s_bullet = ParagraphStyle(
        'Bullet', fontName='Helvetica', fontSize=9.5,
        textColor=DARK, leftIndent=14, bulletIndent=2,
        spaceAfter=2, leading=12.5
    )
    s_proj = ParagraphStyle(
        'ProjName', fontName='Helvetica-Bold', fontSize=9.5,
        textColor=BLACK, spaceAfter=1, leading=12
    )
    s_edu = ParagraphStyle(
        'Edu', fontName='Helvetica', fontSize=9.5,
        textColor=DARK, spaceAfter=2, leading=12
    )
    s_cert = ParagraphStyle(
        'Cert', fontName='Helvetica', fontSize=9,
        textColor=DARK, leftIndent=14, bulletIndent=2,
        spaceAfter=1.5, leading=11.5
    )
    s_skills = ParagraphStyle(
        'Skills', fontName='Helvetica', fontSize=9,
        textColor=DARK, spaceAfter=2, leading=12
    )
    
    def heading(title: str):
        story.append(Paragraph(title.upper(), s_section))
        story.append(HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceAfter=4))
    
    # ==========================================
    # 1. HEADER — Name + Contact
    # ==========================================
    basics = schema.get("basics", {})
    name = _s(basics.get("full_name")) or "Your Name"
    story.append(Paragraph(name.upper(), s_name))
    
    contact = []
    for f in ["phone", "email"]:
        v = _s(basics.get(f))
        if v:
            contact.append(v)
    for f in ["linkedin", "github"]:
        v = _s(basics.get(f))
        if v:
            v = v.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            contact.append(v)
    if contact:
        story.append(Paragraph("  |  ".join(contact), s_contact))
    
    story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceAfter=4))
    
    # ==========================================
    # 2. PROFESSIONAL SUMMARY
    # ==========================================
    summary = _s(schema.get("summary"))
    if summary:
        heading("Professional Summary")
        # Cap at 400 chars
        if len(summary) > 400:
            summary = summary[:400].rsplit(' ', 1)[0] + '.'
        story.append(Paragraph(_safe(summary), s_summary))
        story.append(Spacer(1, 2))
    
    # ==========================================
    # 3. TECHNICAL SKILLS (categorized)
    # ==========================================
    skills = schema.get("skills", {})
    if isinstance(skills, dict):
        cat_labels = {
            "languages": "Languages",
            "cloud_infrastructure": "Cloud & Infrastructure",
            "devops_automation": "DevOps & Automation",
            "databases": "Databases",
            "monitoring": "Monitoring & Observability",
            "frameworks_tools": "Frameworks & Tools"
        }
        lines = []
        for key, label in cat_labels.items():
            items = skills.get(key, [])
            if items and isinstance(items, list):
                items_str = ", ".join(_s(s) for s in items if _s(s))
                if items_str:
                    lines.append(f"<b>{label}:</b> {_safe(items_str)}")
        
        if lines:
            heading("Technical Skills")
            story.append(Paragraph("<br/>".join(lines), s_skills))
            story.append(Spacer(1, 2))
    
    # ==========================================
    # 4. WORK EXPERIENCE
    # ==========================================
    experience = schema.get("experience", [])
    if experience:
        heading("Work Experience")
        
        for idx, exp in enumerate(experience):
            if not isinstance(exp, dict):
                continue
            
            role = _s(exp.get("role")) or "Position"
            company = _s(exp.get("company"))
            start = _s(exp.get("start_date"))
            end = _s(exp.get("end_date")) or "Present"
            
            title_line = f"<b>{_safe(role)}</b>"
            if company:
                title_line += f"  |  {_safe(company)}"
            story.append(Paragraph(title_line, s_role))
            
            date_range = f"{start} – {end}" if start else ""
            if date_range:
                story.append(Paragraph(date_range, s_meta))
            
            for b in exp.get("bullets", []):
                b = _s(b)
                if b:
                    story.append(Paragraph(f"•  {_safe(b)}", s_bullet))
            
            if idx < len(experience) - 1:
                story.append(Spacer(1, 4))
        
        story.append(Spacer(1, 2))
    
    # ==========================================
    # 5. PROJECTS
    # ==========================================
    projects = schema.get("projects", [])
    if projects:
        heading("Projects")
        
        for idx, proj in enumerate(projects):
            if not isinstance(proj, dict):
                continue
            
            pname = _s(proj.get("name")) or "Project"
            ptype = _s(proj.get("type"))
            pyear = _s(proj.get("year"))
            
            name_line = f"<b>{_safe(pname)}</b>"
            if ptype:
                name_line += f"  <i>({_safe(ptype)})</i>"
            if pyear:
                name_line += f"  —  {_safe(pyear)}"
            story.append(Paragraph(name_line, s_proj))
            
            for b in proj.get("bullets", []):
                b = _s(b)
                if b:
                    story.append(Paragraph(f"•  {_safe(b)}", s_bullet))
            
            if idx < len(projects) - 1:
                story.append(Spacer(1, 3))
        
        story.append(Spacer(1, 2))
    
    # ==========================================
    # 6. EDUCATION
    # ==========================================
    education = schema.get("education", [])
    if education:
        heading("Education")
        
        for edu in education:
            if not isinstance(edu, dict):
                continue
            parts = []
            degree = _s(edu.get("degree"))
            institution = _s(edu.get("institution"))
            cgpa = _s(edu.get("cgpa"))
            end_year = _s(edu.get("end_year"))
            
            if degree:
                parts.append(f"<b>{_safe(degree)}</b>")
            if institution:
                parts.append(_safe(institution))
            if end_year:
                parts.append(end_year)
            if cgpa:
                parts.append(f"CGPA: {cgpa}")
            
            if parts:
                story.append(Paragraph("  |  ".join(parts), s_edu))
                story.append(Spacer(1, 2))
    
    # ==========================================
    # 7. CERTIFICATIONS
    # ==========================================
    certs = schema.get("certifications", [])
    if certs:
        heading("Certifications")
        for c in certs:
            c = _s(c)
            if c:
                story.append(Paragraph(f"•  {_safe(c)}", s_cert))
    
    # ==========================================
    # 8. ACHIEVEMENTS
    # ==========================================
    achievements = schema.get("achievements", [])
    if achievements:
        heading("Achievements")
        for a in achievements:
            a = _s(a)
            if a:
                story.append(Paragraph(f"•  {_safe(a)}", s_cert))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Generated PDF: {output_path}")
    return output_path


def get_resume_filename(name: str, timestamp: bool = True) -> str:
    """Generate a professional filename."""
    clean = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    clean = clean.replace(' ', '_')
    clean = "_".join(w.capitalize() for w in clean.split('_') if w)
    if not clean:
        clean = "Resume"
    
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{clean}_Resume_{ts}.pdf"
    return f"{clean}_Resume.pdf"
