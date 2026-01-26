import json
from app.config import USE_MOCK_AI, client
from app.utils.prompts import RESUME_PARSE_PROMPT

MOCK_RESUME_DATA = {
    "name": "Pachipulusu Dhaneswara Rao",
    "skills": ["Python", "Docker", "AWS"]
}


def parse_resume(resume_text: str) -> dict:
    """
    Parse resume text and extract structured information.
    Always returns a dict with 'name' at the top level.
    """
    if USE_MOCK_AI:
        return MOCK_RESUME_DATA

    try:
        prompt = f"""
{RESUME_PARSE_PROMPT}

Return ONLY valid JSON.
No explanation.
Resume:
{resume_text}
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        # Parse the response
        result = json.loads(response.text.strip())
        
        # Ensure name exists at top level
        if not result.get("name") or not isinstance(result.get("name"), str) or not result.get("name").strip():
            # Try to extract name from various possible locations
            name = _extract_name_from_result(result)
            result["name"] = name if name else "there"
        
        return result

    except Exception as e:
        print(f"Resume parsing error: {e}")
        
        # Return error info BUT KEEP name at top level for greeting
        return {
            "name": MOCK_RESUME_DATA.get("name", "there"),  # Name at top level!
            "skills": MOCK_RESUME_DATA.get("skills", []),
            "error": "Resume parsing failed",
            "reason": str(e),
            "fallback": MOCK_RESUME_DATA
        }


def _extract_name_from_result(result: dict) -> str:
    """
    Try to extract name from various possible locations in parsed result.
    """
    # Direct name field
    if result.get("name"):
        return result["name"]
    
    # Contact info
    contact = result.get("contact", {})
    if isinstance(contact, dict) and contact.get("name"):
        return contact["name"]
    
    # Personal info
    personal = result.get("personal_info", {})
    if isinstance(personal, dict):
        if personal.get("name"):
            return personal["name"]
        if personal.get("full_name"):
            return personal["full_name"]
    
    # Header section
    header = result.get("header", {})
    if isinstance(header, dict) and header.get("name"):
        return header["name"]
    
    # Basics section (common in some formats)
    basics = result.get("basics", {})
    if isinstance(basics, dict) and basics.get("name"):
        return basics["name"]
    
    return None