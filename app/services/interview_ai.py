"""
Interview AI Service
====================
Handles AI interactions for conversational interview.
"""

import json
import re
from typing import Optional
from datetime import datetime

from app.config import USE_MOCK_AI, client, GEMINI_MODEL
from app.models.interview_context import (
    InterviewContext,
    InterviewStage,
    ResponseType,
    InterviewMessage,
    AnswerQuality,
)
from app.prompts.interviewer_prompts import (
    build_interview_prompt,
    build_analysis_prompt,
)


# ======================
# GENERATE AI RESPONSE
# ======================

def generate_interviewer_response(
    context: InterviewContext,
    candidate_answer: Optional[str] = None,
) -> dict:
    """
    Generate the interviewer's next response.
    
    Returns:
        {
            "acknowledgment": "...",
            "response_type": "follow_up | new_topic | ...",
            "message": "...",
            "internal_analysis": {...}
        }
    """
    
    stage = context.state.current_stage
    
    if USE_MOCK_AI:
        return _generate_mock_response(context, candidate_answer, stage)
    
    try:
        # Build the prompt
        context_dict = context.model_dump(mode="json")
        prompt = build_interview_prompt(context_dict, stage)
        
        # Add candidate's answer if provided
        if candidate_answer:
            prompt += f"\n\nCANDIDATE'S LATEST RESPONSE:\n\"{candidate_answer}\"\n\nNow generate your response:"
        else:
            prompt += f"\n\nThis is the START of the interview. Generate your opening message for the {stage} stage:"
        
        # Call AI
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        
        # Parse response
        result = _parse_ai_response(response.text)
        return result
        
    except Exception as e:
        print(f"AI response generation error: {e}")
        return _generate_mock_response(context, candidate_answer, stage)


def analyze_answer(
    question: str,
    answer: str,
    stage: str,
    topic: Optional[str] = None,
) -> dict:
    """
    Analyze candidate's answer for quality and key points.
    
    Returns:
        {
            "quality": "excellent | good | adequate | weak | incomplete",
            "key_points": [...],
            "technologies_mentioned": [...],
            "follow_up_opportunities": [...],
            "needs_follow_up": true/false,
            ...
        }
    """
    
    if USE_MOCK_AI:
        return _mock_analyze_answer(answer)
    
    try:
        prompt = build_analysis_prompt(question, answer, stage, topic)
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        
        return _parse_ai_response(response.text)
        
    except Exception as e:
        print(f"Answer analysis error: {e}")
        return _mock_analyze_answer(answer)


# ======================
# GREETING GENERATION
# ======================

def generate_greeting(context: InterviewContext) -> InterviewMessage:
    """Generate opening greeting."""
    
    name = context.candidate.name or "there"
    role = context.candidate.target_role or "the role"
    
    # Define greetings OUTSIDE the if/else so it's always available
    greetings = [
        f"Hi {name}! Thanks for taking the time to speak with me today. Before we dive into the technical stuff, how are you doing?",
        f"Hello {name}! Great to meet you. I'm excited to learn about your experience. How's your day going so far?",
        f"Hey {name}! Thanks for joining me today. Let's keep this conversational - how are you feeling?",
    ]
    
    if USE_MOCK_AI:
        import random
        text = random.choice(greetings)
    else:
        response = generate_interviewer_response(context, None)
        text = response.get("message", greetings[0])
    
    return InterviewMessage(
        type=ResponseType.GREETING,
        acknowledgment=None,
        text=text,
        audio_text=text,
        topic=None,
    )
# ======================
# RESPONSE MESSAGE BUILDER
# ======================

def build_interview_message(
    ai_response: dict,
    stage: str,
    topic: Optional[str] = None,
) -> InterviewMessage:
    """Build InterviewMessage from AI response."""
    
    response_type = ai_response.get("response_type", "new_topic")
    
    # Map string to enum
    type_map = {
        "follow_up": ResponseType.FOLLOW_UP,
        "dig_deeper": ResponseType.DIG_DEEPER,
        "new_topic": ResponseType.NEW_TOPIC,
        "transition": ResponseType.TRANSITION,
        "clarification": ResponseType.CLARIFICATION,
        "encouragement": ResponseType.ENCOURAGEMENT,
        "greeting": ResponseType.GREETING,
        "closing": ResponseType.CLOSING,
    }
    
    msg_type = type_map.get(response_type, ResponseType.NEW_TOPIC)
    
    # Build message text
    acknowledgment = ai_response.get("acknowledgment", "")
    message = ai_response.get("message", "")
    
    # Combine for full text
    if acknowledgment:
        full_text = f"{acknowledgment} {message}"
    else:
        full_text = message
    
    # Clean up text
    full_text = full_text.strip()
    
    return InterviewMessage(
        type=msg_type,
        acknowledgment=acknowledgment if acknowledgment else None,
        text=full_text,
        audio_text=full_text,  # Could be optimized for TTS
        topic=topic,
    )


# ======================
# PARSE AI RESPONSE
# ======================

def _parse_ai_response(text: str) -> dict:
    """Parse AI response text to extract JSON."""
    
    # Clean up the response
    text = text.strip()
    
    # Try to find JSON in the response
    # Sometimes AI wraps JSON in markdown code blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If JSON parsing fails, extract what we can
        return {
            "acknowledgment": "",
            "response_type": "new_topic",
            "message": text,
            "internal_analysis": {
                "answer_quality": "adequate",
                "key_points": [],
                "parse_error": True,
            }
        }


# ======================
# MOCK RESPONSES
# ======================

def _generate_mock_response(
    context: InterviewContext,
    candidate_answer: Optional[str],
    stage: str,
) -> dict:
    """Generate mock response when AI is not available."""
    
    name = context.candidate.name or "there"
    # Clean up name - use first name only
    first_name = name.split()[0] if name else "there"
    
    skills = context.probe_areas.skills
    projects = context.probe_areas.projects
    skills_probed = context.probe_areas.skills_probed
    questions_asked = context.state.questions_asked
    
    # Get next skill to ask about (not already probed)
    remaining_skills = [s for s in skills if s not in skills_probed]
    next_skill = remaining_skills[0] if remaining_skills else None
    second_skill = remaining_skills[1] if len(remaining_skills) > 1 else None
    
    # Get next project
    unprobed_projects = [p for p in projects if not p.probed]
    next_project = unprobed_projects[0].name if unprobed_projects else None
    
    # Track conversation to avoid repetition
    recent_messages = [t.text for t in context.conversation[-4:] if t.role == "interviewer"]
    
    # ============ GREETING ============
    if stage == "greeting":
        greetings = [
            f"Good morning {first_name}! Thanks for joining today. How are you doing?",
            f"Hi {first_name}! Great to meet you. How's your day going so far?",
            f"Hello {first_name}! Thanks for taking the time. How are you feeling today?",
        ]
        # Pick one that wasn't recently used
        for g in greetings:
            if not any(g[:30] in m for m in recent_messages):
                greeting = g
                break
        else:
            greeting = greetings[0]
            
        return {
            "acknowledgment": "",
            "response_type": "greeting",
            "message": greeting,
            "internal_analysis": {
                "answer_quality": "n/a",
                "suggested_next_topic": "introduction",
            }
        }
    
    # ============ INTRODUCTION ============
    elif stage == "introduction":
        if candidate_answer:
            return {
                "acknowledgment": f"Nice to hear that, {first_name}!",
                "response_type": "transition",
                "message": "Shall we begin? Please give me a brief introduction about yourself - your background, experience, and what you're looking for.",
                "internal_analysis": {
                    "answer_quality": "good",
                    "key_points": ["greeting done"],
                    "suggested_next_topic": "self_intro",
                }
            }
        else:
            return {
                "acknowledgment": "",
                "response_type": "new_topic",
                "message": f"Great {first_name}! Let's start. Can you give me a brief introduction about yourself?",
                "internal_analysis": {
                    "answer_quality": "n/a",
                    "suggested_next_topic": "self introduction",
                }
            }
    
    # ============ SKILLS DEEP DIVE ============
    elif stage == "skills_deep_dive":
        if candidate_answer:
            word_count = len(candidate_answer.split())
            
            # Check if this is response to intro or to a skill question
            is_intro_response = questions_asked <= 3
            
            if is_intro_response:
                # After intro, ask about skills comparison if we have 2 skills
                if next_skill and second_skill:
                    return {
                        "acknowledgment": f"Thanks for that introduction, {first_name}!",
                        "response_type": "new_topic",
                        "message": f"I see {next_skill} and {second_skill} on your resume. Can you tell me the difference between them and which one you prefer?",
                        "internal_analysis": {
                            "answer_quality": "good",
                            "topic_covered": True,
                            "suggested_next_topic": next_skill,
                        }
                    }
                elif next_skill:
                    return {
                        "acknowledgment": f"Thanks {first_name}!",
                        "response_type": "new_topic",
                        "message": f"I noticed {next_skill} on your resume. Can you tell me about your experience with it?",
                        "internal_analysis": {
                            "answer_quality": "good",
                            "suggested_next_topic": next_skill,
                        }
                    }
            
            # Follow-up questions based on answer quality
            if word_count < 20:
                follow_ups = [
                    "Can you give me a specific example?",
                    "Could you elaborate a bit more on that?",
                    "Can you walk me through a real scenario where you used this?",
                ]
                # Pick one not recently used
                for f in follow_ups:
                    if not any(f[:20] in m for m in recent_messages):
                        follow_up = f
                        break
                else:
                    follow_up = follow_ups[0]
                    
                return {
                    "acknowledgment": "I see.",
                    "response_type": "follow_up",
                    "message": follow_up,
                    "internal_analysis": {
                        "answer_quality": "incomplete",
                        "needs_follow_up": True,
                    }
                }
            else:
                # Good answer, move to technical question
                tech_questions = [
                    f"Good explanation! Quick technical question - what's the difference between a list and a tuple in Python?",
                    f"Nice! Can you explain what an API is and how you've worked with them?",
                    f"Great! What's the difference between GET and POST requests?",
                    f"Good! Can you explain what version control is and why it's important?",
                ]
                
                for q in tech_questions:
                    if not any(q[:30] in m for m in recent_messages):
                        question = q
                        break
                else:
                    question = f"Good answer! Let's move on. Tell me about {next_skill if next_skill else 'your technical skills'}."
                
                return {
                    "acknowledgment": "That's a solid answer!",
                    "response_type": "new_topic",
                    "message": question,
                    "internal_analysis": {
                        "answer_quality": "good",
                        "topic_covered": True,
                        "suggested_next_topic": next_skill,
                    }
                }
        else:
            if next_skill and second_skill:
                return {
                    "acknowledgment": "",
                    "response_type": "new_topic",
                    "message": f"I see {next_skill} and {second_skill} in your skills. What's the difference and when would you use each?",
                    "internal_analysis": {
                        "answer_quality": "n/a",
                        "suggested_next_topic": next_skill,
                    }
                }
            return {
                "acknowledgment": "",
                "response_type": "new_topic",
                "message": f"Tell me about your experience with {next_skill if next_skill else 'programming'}.",
                "internal_analysis": {
                    "answer_quality": "n/a",
                    "suggested_next_topic": next_skill,
                }
            }
    
    # ============ PROJECT DISCUSSION ============
    elif stage == "project_discussion":
        if candidate_answer:
            word_count = len(candidate_answer.split())
            
            # Check if we already asked about challenges
            asked_challenges = any("challenging" in m.lower() or "difficult" in m.lower() for m in recent_messages)
            
            if not asked_challenges:
                return {
                    "acknowledgment": "That sounds like an interesting project!",
                    "response_type": "follow_up",
                    "message": "What was the most challenging part, and how did you overcome it?",
                    "internal_analysis": {
                        "answer_quality": "good",
                        "key_points": ["project discussed"],
                    }
                }
            else:
                return {
                    "acknowledgment": "Great problem-solving!",
                    "response_type": "transition",
                    "message": "That shows good initiative. Now let's talk about how you work with others.",
                    "internal_analysis": {
                        "answer_quality": "good",
                        "topic_covered": True,
                    }
                }
        else:
            project_name = next_project if next_project else "your main project"
            return {
                "acknowledgment": "",
                "response_type": "new_topic",
                "message": f"Let's talk about {project_name}. What was your role and what did you build?",
                "internal_analysis": {
                    "answer_quality": "n/a",
                    "suggested_next_topic": project_name,
                }
            }
    
    # ============ BEHAVIORAL ============
    elif stage == "behavioral":
        behavioral_questions = [
            "What are your key strengths?",
            "What do you consider your weakness, and how are you working on it?",
            "Tell me about a time you faced a challenge. How did you handle it?",
            "What are your hobbies outside of work?",
        ]
        
        # Pick one not recently asked
        for q in behavioral_questions:
            if not any(q[:25] in m for m in recent_messages):
                question = q
                break
        else:
            question = behavioral_questions[0]
        
        if candidate_answer:
            return {
                "acknowledgment": "Thanks for sharing that!",
                "response_type": "new_topic",
                "message": question,
                "internal_analysis": {
                    "answer_quality": "good",
                }
            }
        else:
            return {
                "acknowledgment": "",
                "response_type": "new_topic",
                "message": f"Now let's understand you better. {question}",
                "internal_analysis": {
                    "answer_quality": "n/a",
                }
            }
    
    # ============ SITUATIONAL ============
    elif stage == "situational":
        if candidate_answer:
            return {
                "acknowledgment": "That's a thoughtful approach!",
                "response_type": "transition",
                "message": f"Great {first_name}, we're almost done. Do you have any questions for me?",
                "internal_analysis": {
                    "answer_quality": "good",
                }
            }
        else:
            return {
                "acknowledgment": "",
                "response_type": "new_topic",
                "message": "Imagine you find a critical bug right before a release. Walk me through what you would do.",
                "internal_analysis": {
                    "answer_quality": "n/a",
                }
            }
    
    # ============ CLOSING ============
    elif stage == "closing":
        if candidate_answer:
            return {
                "acknowledgment": "Great questions!",
                "response_type": "closing",
                "message": f"Thank you so much {first_name}! It was great talking with you. You'll receive your feedback report shortly. Our HR team will reach out to you. Best of luck!",
                "internal_analysis": {
                    "answer_quality": "n/a",
                    "interview_complete": True,
                }
            }
        else:
            return {
                "acknowledgment": "",
                "response_type": "closing",
                "message": f"Alright {first_name}, that's all from my side. Do you have any questions for me about the role or the company?",
                "internal_analysis": {
                    "answer_quality": "n/a",
                }
            }
    
    # Default fallback
    return {
        "acknowledgment": f"Thanks {first_name}.",
        "response_type": "new_topic",
        "message": "That's helpful. Let's continue - tell me more about your experience.",
        "internal_analysis": {
            "answer_quality": "adequate",
        }
    }


def _mock_analyze_answer(answer: str) -> dict:
    """Mock analysis when AI is not available."""
    
    word_count = len(answer.split())
    
    # Simple quality assessment based on length
    if word_count < 10:
        quality = "incomplete"
    elif word_count < 30:
        quality = "weak"
    elif word_count < 80:
        quality = "adequate"
    elif word_count < 150:
        quality = "good"
    else:
        quality = "excellent"
    
    # Check for technical terms
    tech_keywords = [
        "python", "javascript", "react", "docker", "kubernetes", "aws", "api",
        "database", "sql", "git", "ci/cd", "agile", "microservices", "cloud",
        "deployed", "implemented", "built", "designed", "led", "managed",
    ]
    
    answer_lower = answer.lower()
    technologies = [kw for kw in tech_keywords if kw in answer_lower]
    
    return {
        "quality": quality,
        "length_assessment": "appropriate" if 30 <= word_count <= 150 else ("too_short" if word_count < 30 else "too_long"),
        "key_points": [],
        "technologies_mentioned": technologies,
        "claims_made": [],
        "follow_up_opportunities": [],
        "red_flags": [],
        "green_flags": technologies[:3],
        "sentiment": "confident" if word_count > 50 else "neutral",
        "specificity": "specific" if word_count > 50 else "vague",
        "needs_follow_up": word_count < 30,
        "suggested_follow_up": "Can you give me a specific example?" if word_count < 30 else None,
        "topic_covered": word_count >= 30,
    }


# ======================
# CLOSING MESSAGE
# ======================

def generate_closing_message(context: InterviewContext) -> InterviewMessage:
    """Generate final closing message."""
    
    name = context.candidate.name or "there"
    strong_areas = context.performance.strong_areas[:2]
    
    strong_text = ""
    if strong_areas:
        strong_text = f"I was particularly impressed by your knowledge of {', '.join(strong_areas)}. "
    
    text = f"Thank you so much for your time today, {name}! {strong_text}You'll receive your detailed feedback report shortly. Best of luck with your career journey!"
    
    return InterviewMessage(
        type=ResponseType.CLOSING,
        acknowledgment=None,
        text=text,
        audio_text=text,
        topic=None,
    )