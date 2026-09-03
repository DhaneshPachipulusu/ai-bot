"""
Interview V2 Routes - AI Powered
================================
Uses Gemini AI (google-genai SDK) for dynamic questions and follow-ups.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import re
import uuid

from app.prompts.interviewer_system import INTERVIEWER_SYSTEM
import json
import os
import random
from datetime import datetime

router = APIRouter()

# Create data directories
os.makedirs("data/interviews", exist_ok=True)
os.makedirs("data/conversations", exist_ok=True)

# ==========================================
# AI Setup - Using google-genai SDK
# ==========================================

AI_AVAILABLE = False
client = None
GEMINI_MODEL = "gemini-2.5-flash"

try:
    from app.config import client as gemini_client, USE_MOCK_AI, GEMINI_MODEL as MODEL
    GEMINI_MODEL = MODEL
    
    if gemini_client and not USE_MOCK_AI:
        client = gemini_client
        AI_AVAILABLE = True
        print("✅ Gemini AI available for interviews")
    else:
        print("⚠️ AI disabled - using fallback questions")
except Exception as e:
    print(f"⚠️ Gemini import failed: {e}")


# Models tried in order for a single turn. The free tier rate-limits per
# model, and individual models return 503 when Google is at capacity, so a
# second model is a cheap way to survive both without a visible fallback.
# Ordered by free-tier RPM headroom: 3.5-flash-lite allows 15/min against
# 2.5-flash's 5, so it goes first and the configured model backs it up.
MODEL_CHAIN = []
for _m in ("gemini-3.5-flash-lite", GEMINI_MODEL, "gemini-2.5-flash-lite"):
    if _m and _m not in MODEL_CHAIN:
        MODEL_CHAIN.append(_m)

# An interview turn is interactive: a candidate is sitting there waiting.
# Retrying is worth a few seconds, never the 37s the API sometimes suggests.
# Escalation ladder: clarify -> concrete prompt -> diagnose -> pivot. Three
# attempts at one competency, never a fourth.
# Words that name where you are in the interview, not what the candidate can
# do. Technology names are deliberately absent.
NON_COMPETENCY_NAMES = {
    "internship", "behavioural", "behavioral", "project", "career", "greeting",
    "background", "general", "none", "n/a", "self intro", "introduction",
    "communication", "rapport",
}

# Depth ladder rung a competency must reach before it can be "confirmed".
# 1 concept, 2 application, 3 personal implementation, 4 concrete detail,
# 5 failure case, 6 trade-off.
CONFIRM_REQUIRES_DEPTH = 4

# Turns a competency may hold while the candidate is still climbing the ladder.
# The coverage guard caps a competency at 3 turns, but reaching a trade-off
# question is depth 6 and takes about five - so the guard made the top of the
# ladder unreachable and no trade-off question was ever asked. A competency
# whose depth is still increasing has earned the extra turns; one that is
# stuck has not.
MAX_TURNS_WHILE_DEEPENING = 6

MAX_CONSECUTIVE_REDIRECTS = 3


def _tokens(text):
    return {w for w in re.findall(r"[a-z]{4,}", (text or "").lower())}


# Topics worth tracking by name. Counting competency names does not work:
# the model calls the same subject "Docker", "Containerization", "Docker &
# Deployment" or omits it entirely, so a per-name counter resets every turn
# and the same question gets asked seven times.
TOPIC_WORDS = {
    "docker": ("docker", "container", "dockerfile", "image"),
    "kubernetes": ("kubernetes", "k8s", "pod", "orchestr"),
    "ci_cd": ("ci/cd", "pipeline", "jenkins", "github action", "deploy"),
    "iac": ("terraform", "ansible", "cloudformation", "infrastructure as code"),
    "cloud": ("aws", "azure", "gcp", "cloud", "ec2", "s3"),
    "database": ("postgres", "mysql", "sql", "index", "query", "transaction"),
    "kafka": ("kafka", "queue", "message broker", "event stream"),
    "cache": ("redis", "cache", "caching"),
    "testing": ("test", "junit", "pytest", "testcontainer", "mock"),
    "java_core": ("hashmap", "collection", "thread", "concurren", "interface",
                  "abstract class", "exception"),
    "spring": ("spring", "dependency injection", "bean", "jpa", "hibernate"),
    "internship": ("internship", "intern ", "company", "responsibilit"),
    "project": ("project", "you build", "you built", "architecture"),
    "behavioural": ("disagree", "conflict", "team", "pressure", "deadline"),
    "career": ("five years", "career", "goal", "strength"),
}


def topics_in(text):
    low = (text or "").lower()
    return {name for name, words in TOPIC_WORDS.items()
            if any(w in low for w in words)}


def topic_ask_counts(conversation):
    """How many interviewer questions have already touched each topic."""
    counts = {}
    for turn in conversation:
        if turn.get("role") != "interviewer":
            continue
        for name in topics_in(turn.get("text", "")):
            counts[name] = counts.get(name, 0) + 1
    return counts


# The depth ladder asked for these in prose and got zero of them across 69
# interviewer turns. Naming the exact question and making it a directive is
# the difference between a rule the model follows and one it does not.
DEPTH_PROBES = {
    4: ("concrete detail",
        "Ask for one specific mechanism: the exact call, the exact field, "
        "the exact config value. \"What did the code actually do when that "
        "request arrived?\""),
    5: ("failure case",
        "Ask what went wrong: \"What happened when that broke - and how did "
        "you find out?\" A candidate who has really built it has a failure "
        "story; one who has read about it does not."),
    6: ("trade-off",
        "Ask why this and not the alternative: \"Why that approach over the "
        "obvious alternative, and what did it cost you?\" or \"What would "
        "you change if you rebuilt it now?\""),
}


def next_depth_probe(depth_by_competency, current_competency):
    """The rung this competency owes before it can be confirmed."""
    if not current_competency:
        return None
    reached = int(depth_by_competency.get(current_competency, 0) or 0)
    if reached < 3 or reached >= 6:
        return None
    return reached + 1, DEPTH_PROBES.get(reached + 1)


def collect_claims(conversation):
    """Every claim the candidate has made, with the turn it was made on.

    Layer 3 makes checking a new answer against earlier claims the highest
    priority, but layer 2 only ever showed the last eight turns truncated to
    200 characters. A claim made on turn 2 was gone by turn 10, so
    contradiction detection was structurally impossible - claim_check came
    back "none" in every transcript, including one where the candidate
    contradicted himself three times. Claims are accumulated here instead, so
    they survive the context window.
    """
    claims = []
    for i, turn in enumerate(conversation):
        for c in (turn.get("claims") or []):
            if isinstance(c, str) and c.strip():
                claims.append({"turn": i, "claim": c.strip()[:120]})
    return claims


def detect_repetition(conversation, latest_answer):
    """How many earlier answers were substantially the same as this one.

    A candidate repeating a prepared project summary across unrelated questions
    is a behavioural signal. Without measuring it the model just asks an ever
    more specific version of the same question, which is what burned eight
    turns on Docker in testing.
    """
    now = _tokens(latest_answer)
    if len(now) < 4:
        return 0, 0.0
    best, hits = 0.0, 0
    for turn in conversation:
        if turn.get("role") != "candidate":
            continue
        prior = _tokens(turn.get("text", ""))
        if len(prior) < 4:
            continue
        overlap = len(now & prior) / float(len(now | prior))
        if overlap >= 0.6:
            hits += 1
        best = max(best, overlap)
    return hits, round(best, 2)

_RETRY_BUDGET_SECONDS = 8.0
_BACKOFF = (0.6, 1.8)


def _is_transient(err: Exception) -> bool:
    """429 (rate limited) and 503 (overloaded) both clear on their own."""
    s = str(err)
    return any(k in s for k in
               ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "overloaded"))


async def call_gemini(prompt: str,
                      system_instruction: Optional[str] = None) -> Optional[str]:
    """Call Gemini via the SDK's async client, retrying transient failures.

    Uses client.aio so the request awaits on the event loop instead of
    occupying a threadpool worker. An interview turn blocks for seconds,
    so this is what lets concurrent candidates share one process.

    Free-tier quota and model overload are the two failure modes that
    actually happen in practice, and both are temporary. Without this the
    caller drops to the canned question bank mid-interview, which reads to
    the candidate as the product breaking.
    """
    if not client:
        return None

    deadline = asyncio.get_event_loop().time() + _RETRY_BUDGET_SECONDS
    last_error = None

    for model in MODEL_CHAIN:
        for attempt, pause in enumerate((0.0,) + _BACKOFF):
            if pause:
                if asyncio.get_event_loop().time() + pause > deadline:
                    break
                await asyncio.sleep(pause)
            try:
                cfg = ({"system_instruction": system_instruction}
                       if system_instruction else None)
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=cfg,
                )
                if attempt or model != MODEL_CHAIN[0]:
                    print(f"✅ Gemini recovered on {model} (attempt {attempt + 1})")
                return response.text.strip()
            except Exception as e:
                last_error = e
                if not _is_transient(e):
                    print(f"⚠️ Gemini API error ({model}): {e}")
                    return None
                print(f"⏳ {model} transient failure, retrying: {str(e)[:80]}")
                if asyncio.get_event_loop().time() > deadline:
                    break

    print(f"⚠️ Gemini unavailable after retries: {str(last_error)[:120]}")
    return None


# ==========================================
# Request/Response Models
# ==========================================

class StartInterviewRequest(BaseModel):
    user_id: int
    mode: str = "resume"
    parsed_resume: Optional[dict] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = "fresher"
    difficulty: Optional[str] = "auto"
    max_questions: Optional[int] = 10
    max_duration_mins: Optional[int] = 25


class RespondRequest(BaseModel):
    interview_id: str
    user_id: int
    answer: str
    answer_duration_seconds: Optional[int] = None


class EndInterviewRequest(BaseModel):
    interview_id: str
    user_id: int
    reason: Optional[str] = "user_ended"


# ==========================================
# In-memory storage
# ==========================================

active_interviews = {}


# ==========================================
# AI Functions
# ==========================================

# Interview stages for natural flow
INTERVIEW_STAGES = [
    "greeting",
    "self_intro", 
    "background",
    "skills_interest",
    "technical",
    "project",
    "behavioral",
    "closing"
]


def get_time_greeting(candidate_name: str) -> str:
    """Generate contextual greeting based on time of day."""
    hour = datetime.now().hour
    
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    # Clean up name. Resumes often carry the full name in caps
    # ("PACHIPULUSU DHANESWARA RAO"), which shouts when dropped into a
    # greeting, so normalise the case before using the leading token.
    if candidate_name and candidate_name != "Candidate":
        first = candidate_name.split()[0]
        name = first.title() if first.isupper() or first.islower() else first
    else:
        name = "there"
    
    greetings = [
        f"{time_greeting}, {name}! I'm your interviewer today. This will be a relaxed, conversational session. How are you doing today?",
        f"{time_greeting}, {name}! Thanks for joining. Before we dive in, how's your day going so far?",
        f"{time_greeting}! Great to meet you, {name}. Let's keep this casual. How are you feeling today?",
    ]
    
    return random.choice(greetings)


def flatten_skills(skills) -> list:
    """Normalize skills into a flat list of strings.

    Skills can arrive as a flat list (from /upload-resume) or as a nested dict
    (from the resume-builder schema: {languages: [...], databases: [...], ...}).
    Without this, dict-shaped skills silently break the keyword logic downstream.
    """
    if isinstance(skills, dict):
        flat = []
        for value in skills.values():
            if isinstance(value, list):
                flat.extend(str(v) for v in value if v)
            elif value:
                flat.append(str(value))
        return flat
    if isinstance(skills, list):
        return [str(s) for s in skills if s]
    return []


def build_resume_context(interview: dict) -> str:
    """Build a compact summary of the candidate's actual resume.

    This is what makes the interview genuinely resume-based: the model can ask
    about *their* projects/experience by name instead of generic placeholders.
    """
    resume = interview.get("parsed_resume") or {}
    parts = []

    # Experience / internships
    exp_lines = []
    for exp in (resume.get("experience") or [])[:3]:
        if not isinstance(exp, dict):
            continue
        title = exp.get("title") or exp.get("role") or ""
        company = exp.get("company") or ""
        date = exp.get("date") or ""
        header = " | ".join(p for p in [title, company, date] if p)
        bullets = exp.get("responsibilities") or exp.get("bullets") or []
        if isinstance(bullets, str):
            bullets = [bullets]
        line = f"- {header}" if header else "-"
        if bullets:
            line += ": " + "; ".join(b for b in bullets[:2] if b)
        elif exp.get("description"):
            line += ": " + str(exp["description"])[:160]
        if line.strip("- "):
            exp_lines.append(line)
    if exp_lines:
        parts.append("EXPERIENCE / INTERNSHIPS:\n" + "\n".join(exp_lines))

    # Projects
    proj_lines = []
    for proj in (resume.get("projects") or [])[:3]:
        if not isinstance(proj, dict):
            continue
        name = proj.get("name") or proj.get("title") or ""
        tech = proj.get("technologies") or proj.get("tech") or ""
        desc = proj.get("description") or ""
        if not desc and isinstance(proj.get("bullets"), list):
            desc = "; ".join(str(b) for b in proj["bullets"][:2] if b)
        line = f"- {name}" if name else "-"
        if tech:
            line += f" (tech: {tech})"
        if desc:
            line += f": {str(desc)[:160]}"
        if line.strip("- "):
            proj_lines.append(line)
    if proj_lines:
        parts.append("PROJECTS:\n" + "\n".join(proj_lines))

    # Education
    edu_lines = []
    for edu in (resume.get("education") or [])[:2]:
        if not isinstance(edu, dict):
            continue
        degree = edu.get("degree") or ""
        inst = edu.get("institution") or ""
        score = edu.get("score") or edu.get("cgpa") or ""
        bits = [b for b in [degree, inst, score] if b]
        line = "- " + (" | ".join(bits) if bits else str(edu.get("description") or "")[:120])
        if line.strip("- "):
            edu_lines.append(line)
    if edu_lines:
        parts.append("EDUCATION:\n" + "\n".join(edu_lines))

    summary = resume.get("summary") or ""
    if summary:
        parts.append("SUMMARY: " + str(summary)[:200])

    if not parts:
        return "No detailed resume on file - ask questions based on the target role and listed skills."
    return "\n\n".join(parts)


def get_calibration_guidance(difficulty: str, experience_level: str) -> str:
    """Tell the interviewer how hard to push, based on chosen difficulty + level."""
    difficulty = (difficulty or "auto").lower()
    experience_level = (experience_level or "fresher").lower()

    level_note = {
        "fresher": "Candidate is a FRESHER/entry-level. Focus on fundamentals, college projects, internships, and how they think and learn. Do not expect production-scale experience.",
        "junior": "Candidate is JUNIOR with some experience. Mix fundamentals with practical application.",
        "mid": "Candidate is MID-LEVEL. Expect solid practical depth and some design/trade-off reasoning.",
        "senior": "Candidate is SENIOR. Probe architecture, trade-offs, scale, and decision-making.",
    }.get(experience_level, "Calibrate to the candidate's apparent experience.")

    diff_note = {
        "easy": "DIFFICULTY EASY: keep questions supportive and foundational, one concept at a time, stay encouraging.",
        "medium": "DIFFICULTY MEDIUM: standard interview depth with natural follow-ups when answers are thin.",
        "hard": "DIFFICULTY HARD: probe deeply - ask for trade-offs, edge cases, and the 'why' behind choices; politely challenge vague answers.",
    }.get(difficulty, "DIFFICULTY AUTO: calibrate to the candidate's experience level and how well they are answering.")

    return f"{level_note}\n{diff_note}"


async def generate_dynamic_response(interview: dict, candidate_answer: str) -> dict:
    """
    Generate the next question dynamically based on conversation context.
    Returns: {"acknowledgment": "...", "question": "...", "decision": "...", "next_stage": "..."}
    """
    
    if not AI_AVAILABLE:
        return generate_fallback_response(interview, candidate_answer)
    
    # Build conversation context
    conversation = interview.get("conversation_history", [])
    conv_text = "\n".join([
        f"{'Interviewer' if turn['role'] == 'interviewer' else 'Candidate'}: {turn['text'][:200]}"
        for turn in conversation[-8:]  # Last 8 turns for context
    ])
    
    current_stage = interview.get("current_stage", "greeting")
    questions_asked = interview.get("questions_asked", 0)
    max_questions = interview.get("max_questions", 10)
    skills = interview.get("skills", [])[:8]
    target_role = interview.get("target_role", "Software Developer")
    candidate_name = (interview.get("candidate_name") or "the candidate").split()[0]

    resume_context = build_resume_context(interview)
    calibration = get_calibration_guidance(
        interview.get("difficulty", "auto"),
        interview.get("experience_level", "fresher"),
    )

    last_question = ""
    for turn in reversed(conversation):
        if turn.get("role") == "interviewer":
            last_question = turn.get("text", "")
            break

    # How many times in a row we have already re-asked the same thing. Without
    # this the model redirects forever: it keeps correctly detecting that the
    # candidate dodged, and keeps re-asking, and the interview stops moving.
    # A "diagnose" turn is still an unanswered question, so it counts toward
    # the escalation ladder: redirect -> diagnose -> pivot.
    redirects_used = 0
    for turn in reversed(conversation):
        if turn.get("role") != "interviewer":
            continue
        if turn.get("decision") in ("redirect", "diagnose"):
            redirects_used += 1
        else:
            break

    ledger = interview.get("competencies") or {}
    competency_summary = ("; ".join(f"{k}: {v.get('status')}"
                                    for k, v in ledger.items())
                          or "none assessed yet")

    # Consecutive turns spent probing the SAME competency. This is what the
    # pivot rule needs: redirects_used only counts unanswered questions, but a
    # strong candidate can also get stuck being asked the same follow-up.
    current_competency, competency_attempts = None, 0
    for turn in reversed(conversation):
        if turn.get("role") != "interviewer":
            continue
        name = (turn.get("competency_name") or "").strip()
        if not name:
            break
        if current_competency is None:
            current_competency = name
        if name == current_competency:
            competency_attempts += 1
        else:
            break

    repeat_hits, repeat_sim = detect_repetition(conversation, candidate_answer)
    claims_so_far = collect_claims(conversation)

    # Deepest rung reached per competency, so the model can see what still
    # needs a trade-off or failure-case probe before it can be confirmed.
    depth_by_competency = {}
    for turn in conversation:
        nm = turn.get("competency_name")
        if nm:
            depth_by_competency[nm] = max(depth_by_competency.get(nm, 0),
                                          int(turn.get("depth_reached") or 0))

    asked = topic_ask_counts(conversation)
    exhausted_topics = sorted(k for k, v in asked.items() if v >= 3)
    untouched = sorted(set(TOPIC_WORDS) - set(asked))

    # ---- Layer 2: interview state -----------------------------------
    # Everything that varies per turn, as structured data rather than prose.
    # The model reasons better over a labelled state block than over a wall of
    # instructions restated each turn.
    state_block = json.dumps({
        "role_being_interviewed_for": target_role,
        "candidate_name": candidate_name,
        "stage": current_stage,
        "turn_budget": {"asked": questions_asked, "max": max_questions},
        "resume": resume_context,
        "claimed_skills": skills,
        "calibration": calibration,
        "question_you_just_asked": last_question,
        "candidate_latest_answer": candidate_answer,
        "times_already_reasked_this": redirects_used,
        "consecutive_turns_on_this_competency": competency_attempts,
        "competency_being_probed": current_competency,
        "this_answer_repeats_earlier_answers": repeat_hits,
        "max_similarity_to_an_earlier_answer": repeat_sim,
        "competencies_so_far": competency_summary,
        "every_claim_the_candidate_has_made": claims_so_far,
        "deepest_probe_level_per_competency": depth_by_competency,
        "question_coverage_tags_used": asked,
        "coverage_tags_exhausted_DO_NOT_ASK_AGAIN": exhausted_topics,
        "coverage_tags_not_yet_used": untouched[:8],
        "NOTE_on_coverage_tags": ("These are question-routing tags only. NEVER "
                                  "use them as a competency name."),
        "recent_conversation": conv_text,
    }, indent=2, ensure_ascii=False)

    untouched_list = ", ".join(untouched[:8]) or "none left"

    # A competency sitting at depth 3+ is one question away from being
    # provable. Spell that question out rather than hoping the ladder is read.
    # Depth on the two most recent turns for this competency: if it rose, the
    # candidate is producing evidence and the coverage cap should not fire.
    _recent = [int(x.get("depth_reached") or 0)
               for x in conversation
               if x.get("role") == "interviewer"
               and x.get("competency_name") == current_competency]
    deepening = len(_recent) >= 2 and _recent[-1] > _recent[-2]
    turn_cap = (MAX_TURNS_WHILE_DEEPENING if deepening
                else MAX_CONSECUTIVE_REDIRECTS)

    _probe = next_depth_probe(depth_by_competency, current_competency)
    depth_directive = ""
    if _probe:
        lvl, (label, how) = _probe
        depth_directive = (
            "ASK THE " + label.upper() + " QUESTION NOW - HIGHEST PRIORITY.\n"
            + chr(34) + current_competency + chr(34)
            + " has reached depth " + str(lvl - 1)
            + " and cannot be confirmed below depth "
            + str(CONFIRM_REQUIRES_DEPTH) + ". " + how + "\n"
            + "Do not pivot to a new topic this turn. Set depth_reached="
            + str(lvl) + ".\n\n")

    # ---- Layer 3: this turn's task + output contract -----------------
    # Precedence matters. A fresh technical contradiction is the single most
    # informative thing that can happen in an interview, so it outranks the
    # redirect ladder - otherwise the escalation rule below swallows it and the
    # candidate walks away with an unexamined claim.
    ladder = {
        0: ('This question has not been re-asked yet. If the answer missed it, '
            'decision="redirect": name the gap and re-ask ONCE, simplified.'),
        1: ('You have already re-asked once. DO NOT re-ask again. '
            'decision="diagnose": work out WHY they keep missing it and ask '
            'about that instead - usually they are conflating two things.'),
    }.get(redirects_used,
          'You have re-asked twice. STOP pursuing this. decision="move_on": '
          'record the competency as "unproven" and pivot to a different one.')

    escalation = f"""Apply these IN ORDER and stop at the first that fits.

PRIORITY 1 - UNEXAMINED TECHNICAL CLAIM OR CONTRADICTION.
Check the latest answer against everything claimed earlier. If it contradicts an
earlier claim, or states something technically questionable, decision="challenge"
and probe it NOW. This outranks everything below - an unexamined claim is a
failed interview. Classic cases: "real-time" that turns out to be REST polling,
an "optimisation" with no stated change, a resume skill they cannot apply.

PRIORITY 2 - A CLAIMED SKILL WITH NO HANDS-ON EVIDENCE.
If they admit a skill is theory-only, do NOT just drop it. Give a small concrete
hypothetical and evaluate the reasoning, then move on:
"Fine that you haven't run it. Given this Spring Boot app and a MySQL database,
 what would you put in a container, and why?"
Finding the boundary of what they know IS the assessment.

PRIORITY 3 - ANSWER DID NOT MATCH THE QUESTION.
{ladder}

PRIORITY 4 - ANSWER WAS FINE.
Probe one level deeper on it (depth ladder), or move to a competency still
"not_assessed".

{depth_directive}DEPTH BEFORE COVERAGE - one exception to the guard below.
If the current competency has reached depth 3 and the candidate is answering
well, you get ONE more turn to ask the trade-off or failure-case question that
would confirm it. Coverage beats depth in general; it does not beat closing out
a competency you are one question away from proving.

COVERAGE GUARD - applies otherwise.
You have spent {competency_attempts} consecutive turns on
"{current_competency}"; your limit this turn is {turn_cap} (raised while the
candidate keeps producing deeper evidence). At the limit, STOP: mark it with the best status the
evidence supports and move to a DIFFERENT competency, even if the candidate is
strong and you merely want more detail. Coverage beats depth on one point.

TOPIC BUDGET - HARD RULE, overrides everything above.
Topics already asked about, with counts: {asked}
BANNED, asked three or more times already: {exhausted_topics}
You may NOT ask about a banned topic again in any form or wording. Whatever
you were going to establish there, you will not establish by asking a seventh
time - record it from what you already have and choose something else.
Untouched topics you could use instead: {untouched_list}

REPETITION GUARD.
This answer substantially repeats {repeat_hits} earlier answer(s)
(similarity {repeat_sim}). If that count is 2 or more, do not ask a more
specific version of the same question - name the pattern once, neutrally, and
pivot to another area. Never suggest the candidate is automated, scripted, or
not listening."""

    prompt = f"""## INTERVIEW STATE
{state_block}

## THIS TURN
{escalation}

Decide the single next thing to say. Ground any project or skill question in
the resume above - name the actual project. Never invent projects, companies or
technologies the resume does not mention.

A competency may NOT be marked "confirmed" below depth 4. Levels 1-3 are
description; 4-6 are evidence. If you want to confirm something, ask the
failure-case or trade-off question first - "what happened when that broke?",
"why that and not the alternative?", "what would you change now?". Those are
the highest-yield questions in an interview and the ones most often skipped.

Status rules: "confirmed" needs a specific thing they personally did - a
textbook definition is "partial" at best. Use "no_experience" when they simply
have not used it and said so; use "unproven" only when they claimed it and
could not back it up. Those two are different findings.

Name the competency for the SKILL the answer actually evidenced, not for the
section of the interview you are in. Good names: "PostgreSQL Indexing",
"Docker Image Packaging", "Idempotency Design", "Java Concurrency",
"Integration Testing". Bad names, never use these: "internship", "greeting",
"behavioural", "project", "background" - those describe where you are in the
conversation, not what the candidate proved. If one answer demonstrates a real
skill, record THAT skill, even if you asked the question to probe something
else.

The fields above marked SPOKEN are read aloud to the candidate; the rest are
internal. Be blunt and repetitive in the internal fields. Keep the spoken ones
short and human - do not explain your reasoning to the candidate.

Also record what you now know about the competency you were probing. That
ledger is the real output of the interview: "Internship Experience: unproven -
repeatedly redirected to a college project, never named the company" is worth
far more than "candidate did not answer".

Return ONLY valid JSON, no markdown fence:
{{
  "answered_question": true or false,
  "answer_class": "direct | partial | related_but_off | unrelated | unclear | dont_know | contradiction",
  "claims_in_this_answer": ["short phrases the candidate asserted, e.g. 'real-time tracking', 'deployed on kubernetes', 'handles millions of requests'"],
  "claim_check": "none, or a one-line description of an inconsistency with every_claim_the_candidate_has_made above",
  "depth_reached": "1-6 on the depth ladder: 1 concept, 2 application, 3 personal implementation, 4 concrete detail, 5 failure case, 6 trade-off",
  "answer_quality": "strong | adequate | weak | evasive | off_topic",
  "candidate_level": "beginner | junior | intermediate | strong_intermediate | senior",
  "competency": {{"name": "the SPECIFIC TECHNICAL SKILL this answer gave evidence about", "status": "confirmed | partial | unproven | no_experience | not_assessed", "note": "one line of evidence"}},
  "decision": "follow_up | dig_deeper | challenge | redirect | diagnose | move_on | encourage | close",
  "acknowledgment": "SPOKEN. Neutral bridge, usually two or three words. No praise unless earned. Must NOT restate your evaluation or narrate that you are moving on.",
  "question": "SPOKEN. Your single next question, asked the way a person would ask it.",
  "next_stage": "{current_stage} or the next stage name"
}}"""

    response_text = await call_gemini(prompt, system_instruction=INTERVIEWER_SYSTEM)

    if response_text:
        try:
            # Parse JSON response
            text = response_text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Find JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]
            
            result = json.loads(text)
            print(f"✅ AI decision: {result.get('decision', 'unknown')}")
            return result
            
        except Exception as e:
            print(f"⚠️ Failed to parse AI response: {e}")
    
    return generate_fallback_response(interview, candidate_answer)


def generate_fallback_response(interview: dict, candidate_answer: str) -> dict:
    """Fallback response when AI is unavailable."""
    
    current_stage = interview.get("current_stage", "greeting")
    questions_asked = interview.get("questions_asked", 0)
    word_count = len(candidate_answer.split()) if candidate_answer else 0
    skills = interview.get("skills", [])
    name = interview.get("candidate_name", "there").split()[0]
    
    # Stage-based fallback responses
    if current_stage == "greeting":
        return {
            "decision": "move_on",
            "acknowledgment": f"Nice to meet you, {name}!",
            "question": "Could you please introduce yourself briefly? Tell me about your background and what you're looking for.",
            "next_stage": "self_intro"
        }
    
    elif current_stage == "self_intro":
        return {
            "decision": "move_on",
            "acknowledgment": "Thanks for that introduction!",
            "question": "What technologies or areas do you enjoy working on the most?",
            "next_stage": "skills_interest"
        }
    
    elif current_stage == "skills_interest":
        skill = skills[0] if skills else "your main skill"
        return {
            "decision": "move_on",
            "acknowledgment": "That's great to hear!",
            "question": f"Let's talk about {skill}. Can you explain your experience with it?",
            "next_stage": "technical"
        }
    
    elif current_stage == "technical":
        if word_count < 20:
            return {
                "decision": "follow_up",
                "acknowledgment": "I see.",
                "question": "Can you give me a specific example of how you've used that?",
                "next_stage": "technical"
            }
        return {
            "decision": "move_on",
            "acknowledgment": "Good explanation!",
            "question": "Tell me about a project you worked on. What was your role and what did you build?",
            "next_stage": "project"
        }
    
    elif current_stage == "project":
        return {
            "decision": "move_on",
            "acknowledgment": "That sounds like a good experience!",
            "question": "What would you say are your key strengths?",
            "next_stage": "behavioral"
        }
    
    elif current_stage == "behavioral":
        return {
            "decision": "move_on",
            "acknowledgment": "Thanks for sharing that!",
            "question": f"We're almost done, {name}. Do you have any questions for me?",
            "next_stage": "closing"
        }
    
    else:  # closing
        return {
            "decision": "close",
            "acknowledgment": "Great questions!",
            "question": f"Thank you so much for your time, {name}! It was great talking with you. You'll receive your feedback report shortly. Best of luck!",
            "next_stage": "completed"
        }


async def generate_ai_acknowledgment(answer: str) -> str:
    """Generate acknowledgment using AI."""
    
    defaults = ["Thank you.", "Got it.", "I see.", "Interesting.", "Good."]
    
    if not AI_AVAILABLE or len(answer) < 20:
        return random.choice(defaults)
    
    prompt = f"""The candidate just answered: "{answer[:150]}..."

Generate a brief acknowledgment (5-12 words) before the next question.
Be encouraging but professional. Return ONLY the acknowledgment."""

    response_text = await call_gemini(prompt)

    if response_text:
        ack = response_text.strip().strip('"').strip("'")
        if 3 < len(ack) < 80:
            return ack
    
    return random.choice(defaults)



# ==========================================
# Fallback Questions
# ==========================================

FALLBACK = {
    "intro": [
        "Hello! Please introduce yourself - your background, skills, and what you're passionate about.",
        "Welcome! Tell me about yourself and your career goals.",
    ],
    "general": [
        "What motivated you to pursue technology?",
        "Tell me about a challenging project you worked on.",
        "How do you stay updated with new technologies?",
        "Describe your problem-solving approach.",
        "How do you handle tight deadlines?",
    ],
    "tech": {
        "python": ["Explain Python decorators.", "List vs tuple?", "What is GIL?"],
        "javascript": ["var vs let vs const?", "Explain event loop.", "What are closures?"],
        "react": ["What are React hooks?", "State vs props?", "Virtual DOM?"],
        "sql": ["Explain JOINs.", "What is normalization?", "Optimize slow queries?"],
        "devops": ["Docker vs VM?", "Explain CI/CD.", "What is Kubernetes?"],
        "java": ["Interface vs abstract class?", "OOP principles?", "Spring framework?"],
        "default": ["What is REST API?", "SQL vs NoSQL?", "Explain MVC."],
    },
    "behavioral": [
        "Tell me about a team disagreement.",
        "Describe meeting a tight deadline.",
        "Your greatest achievement?",
    ],
    "closing": [
        "Where do you see yourself in 5 years?",
        "Why should we hire you?",
        "Any questions for me?",
    ],
}


def get_fallback_questions(target_role: str, skills: list, mode: str) -> list:
    """Fallback questions when AI unavailable."""
    
    questions = [random.choice(FALLBACK["intro"])]
    questions.extend(random.sample(FALLBACK["general"], 2))
    
    # Tech questions based on skills
    skills_lower = " ".join(s.lower() for s in skills) if skills else ""
    role_lower = target_role.lower()
    tech_qs = []
    
    for tech, qs in FALLBACK["tech"].items():
        if tech in skills_lower or tech in role_lower:
            tech_qs.extend(qs[:2])
            if len(tech_qs) >= 4:
                break
    
    if len(tech_qs) < 2:
        tech_qs.extend(FALLBACK["tech"]["default"][:2])
    
    questions.extend(tech_qs[:4])
    questions.append(random.choice(FALLBACK["behavioral"]))
    questions.append(random.choice(FALLBACK["closing"]))
    
    return questions


# Ordered most-specific-language-or-framework first. Infrastructure tools sit
# near the bottom because almost every backend engineer lists Docker, and
# matching on it first classified two Java backend candidates as DevOps - who
# were then interviewed on Terraform and charged "unproven" for not knowing it.
# Substrings are anchored on word boundaries: "ml" used to match "html".
_ROLE_RULES = [
    ("ML Engineer", ("machine learning", "tensorflow", "pytorch", "scikit",
                     "deep learning")),
    ("Data Engineer", ("spark", "airflow", "hadoop", "etl", "data warehouse")),
    ("Java Developer", ("java", "spring", "spring boot", "hibernate", "jpa")),
    ("Python Developer", ("django", "flask", "fastapi", "pandas", "python")),
    ("Frontend Developer", ("react", "angular", "vue", "frontend", "next.js")),
    ("Backend Developer", ("express", "node.js", "nestjs", "golang", ".net")),
    ("Cloud Engineer", ("aws", "azure", "gcp", "terraform", "cloudformation")),
    ("DevOps Engineer", ("kubernetes", "jenkins", "devops", "ansible",
                         "ci/cd", "docker")),
]


def detect_role(skills: list) -> str:
    """Best-effort role guess from resume skills.

    Only a fallback: an explicit target_role from the caller always wins. A
    wrong guess here does real damage, because the whole interview is then
    aimed at a job the candidate did not apply for and the gaps land on their
    report as if they were the candidate's.
    """
    if not skills:
        return "Software Developer"

    tokens = {w for s in skills for w in re.findall(r"[a-z0-9+#./]+", s.lower())}
    joined = " ".join(s.lower() for s in skills)

    for role, keys in _ROLE_RULES:
        for k in keys:
            hit = (k in tokens) if " " not in k and "." not in k else (k in joined)
            if hit:
                return role
    return "Software Developer"
    
    s = " ".join(s.lower() for s in skills)
    
    if any(k in s for k in ["react", "angular", "vue", "frontend", "css"]):
        return "Frontend Developer"
    if any(k in s for k in ["django", "flask", "fastapi", "express", "node"]):
        return "Backend Developer"
    if any(k in s for k in ["python", "pandas"]):
        return "Python Developer"
    if any(k in s for k in ["docker", "kubernetes", "devops", "jenkins"]):
        return "DevOps Engineer"
    if any(k in s for k in ["aws", "azure", "gcp", "cloud"]):
        return "Cloud Engineer"
    if any(k in s for k in ["machine learning", "tensorflow", "pytorch", "ml"]):
        return "ML Engineer"
    if any(k in s for k in ["java", "spring"]):
        return "Java Developer"
    
    return "Software Developer"


# ==========================================
# Endpoints
# ==========================================

@router.post("/interview/start")
def start_interview(request: StartInterviewRequest):
    """Start AI-powered conversational interview."""
    
    interview_id = str(uuid.uuid4())[:8]
    print(f"🎤 Starting conversational interview {interview_id}, AI: {AI_AVAILABLE}")
    
    # Extract info
    skills = []
    candidate_name = "Candidate"
    
    if request.mode == "resume" and request.parsed_resume:
        skills = flatten_skills(request.parsed_resume.get("skills", []))
        candidate_name = request.parsed_resume.get("name", "Candidate")
    
    # IMPORTANT: Use user's explicit target_role if provided
    # Only auto-detect from skills if no role specified
    if request.target_role and request.target_role not in ["", "Software Engineer", "Software Developer"]:
        # User explicitly selected a role (e.g., DevOps Engineer)
        target_role = request.target_role
        print(f"🎯 Using user-selected role: {target_role}")
    elif skills:
        # Auto-detect from skills only if no explicit role
        target_role = detect_role(skills)
        print(f"🎯 Auto-detected role from skills: {target_role}")
    else:
        target_role = request.target_role or "Software Developer"
        print(f"🎯 Using default role: {target_role}")
    
    print(f"📋 Role: {target_role}, Skills: {skills[:5]}")
    
    # Generate proper greeting (time-based)
    greeting = get_time_greeting(candidate_name)
    print(f"👋 Greeting: {greeting[:50]}...")
    
    # Create state with stage tracking
    interview = {
        "interview_id": interview_id,
        "user_id": request.user_id,
        "mode": request.mode,
        "target_role": target_role,
        "candidate_name": candidate_name,
        "skills": skills,
        "experience_level": request.experience_level,
        "difficulty": request.difficulty,
        "max_questions": request.max_questions,
        "max_duration_mins": request.max_duration_mins,
        # Conversational flow - no pre-generated questions
        "current_stage": "greeting",
        "questions_asked": 1,
        "conversation_history": [{
            "role": "interviewer",
            "text": greeting,
            "timestamp": datetime.now().isoformat(),
            "stage": "greeting"
        }],
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "parsed_resume": request.parsed_resume,
        "ai_enabled": AI_AVAILABLE
    }
    
    active_interviews[interview_id] = interview
    save_interview(interview)
    
    return {
        "interview_id": interview_id,
        "target_role": target_role,
        "ai_enabled": AI_AVAILABLE,
        "message": {"text": greeting, "type": "greeting"},
        "state": get_state(interview)
    }


@router.post("/interview/respond")
async def respond(request: RespondRequest):
    """Submit answer, get dynamically generated next question."""
    
    interview = get_interview(request.interview_id)
    if not interview:
        raise HTTPException(404, "Interview not found")
    if interview["status"] != "active":
        raise HTTPException(400, "Interview not active")
    
    print(f"📝 Answer received: {request.answer[:50]}...")
    print(f"📊 Current stage: {interview.get('current_stage', 'unknown')}, Questions: {interview.get('questions_asked', 0)}")
    
    # Save candidate's answer
    interview["conversation_history"].append({
        "role": "candidate",
        "text": request.answer,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": request.answer_duration_seconds,
        "stage": interview.get("current_stage", "unknown")
    })
    
    # Check if max questions reached
    if interview["questions_asked"] >= interview["max_questions"]:
        interview["status"] = "completed"
        # Out of turns. That is not the same as having established the
        # competencies, and no report may read as though it were.
        interview["current_stage"] = "completed"
        interview["end_reason"] = "turn_budget_exhausted"
        interview["end_time"] = datetime.now().isoformat()
        
        name = interview.get("candidate_name", "there").split()[0]
        closing_msg = build_closing_message(interview, name)
        
        interview["conversation_history"].append({
            "role": "interviewer",
            "text": closing_msg,
            "timestamp": datetime.now().isoformat(),
            "stage": "closing"
        })
        
        await asyncio.to_thread(save_interview, interview)
        return {
            "message": {"text": closing_msg, "type": "conclusion"},
            "state": get_state(interview),
            "is_complete": True
        }
    
    # Generate dynamic response based on conversation context
    ai_response = await generate_dynamic_response(interview, request.answer)
    
    # Recomputed here rather than passed out of generate_dynamic_response,
    # which has several return paths (parsed AI result, fallback response).
    repeat_hits, _repeat_sim = detect_repetition(
        interview["conversation_history"][:-1], request.answer)

    current_competency, competency_attempts_now = None, 0
    for turn in reversed(interview["conversation_history"]):
        if turn.get("role") != "interviewer":
            continue
        name = (turn.get("competency_name") or "").strip()
        if not name:
            break
        if current_competency is None:
            current_competency = name
        if name == current_competency:
            competency_attempts_now += 1
        else:
            break

    decision = ai_response.get("decision", "move_on")
    acknowledgment = ai_response.get("acknowledgment", "")
    answered_question = ai_response.get("answered_question", True)
    claim_check = ai_response.get("claim_check", "none")
    answer_quality = ai_response.get("answer_quality", "")

    claims_in_answer = ai_response.get("claims_in_this_answer") or []
    if not isinstance(claims_in_answer, list):
        claims_in_answer = []
    try:
        depth_reached = max(0, min(6, int(ai_response.get("depth_reached") or 0)))
    except (TypeError, ValueError):
        depth_reached = 0

    comp = ai_response.get("competency") or {}

    # A good answer to a different question is not evidence for this one. One
    # candidate answered a distributed rate-limiting question with PostgreSQL
    # idempotency - real knowledge, wrong competency - and the engine let it
    # count as progress. Credit what was actually evidenced; leave what was
    # asked about unproven.
    addressed = ai_response.get("answer_addresses_the_question")
    evidenced = (ai_response.get("competency_actually_evidenced") or "").strip()
    if addressed is False and isinstance(comp, dict) and comp.get("name"):
        comp = dict(comp)
        if evidenced and evidenced.lower() != comp["name"].strip().lower():
            print("↔ evidence redirected: asked %s, evidenced %s"
                  % (comp["name"], evidenced))
            comp["status"] = "unproven"
            comp["note"] = ("answered about %s instead; nothing established here"
                            % evidenced[:60])
        elif comp.get("status") == "confirmed":
            comp["status"] = "unproven"

    # Confirmed means evidence, and evidence starts at the concrete rung. A
    # model that has only heard a description will still call it confirmed, so
    # enforce the floor rather than asking for it in prose.
    if isinstance(comp, dict) and comp.get("status") == "confirmed"             and depth_reached and depth_reached < CONFIRM_REQUIRES_DEPTH:
        comp = dict(comp)
        comp["status"] = "partial"
        comp["note"] = ((comp.get("note") or "") +
                        " (described but not probed to failure/trade-off)").strip()
        print(f"↓ {comp.get('name')} confirmed->partial (depth {depth_reached})")

    # The model will otherwise reuse the coverage tags above as competency
    # names, collapsing every demonstrated skill into one "internship" entry
    # that overwrites itself each turn.
    # Reject only names that describe a SECTION of the conversation. Technology
    # names collide with the routing tags ("Kubernetes", "Testing", "Docker",
    # "Database", "Spring", "Kafka", "Cache") and are perfectly good competency
    # names - discarding those was deleting confirmed evidence and quietly
    # moving the candidate's score.
    if isinstance(comp, dict):
        nm = (comp.get("name") or "").strip().lower()
        if nm in NON_COMPETENCY_NAMES:
            comp = {}

    # Pivoting away from a topic without recording it loses the finding. The
    # model reliably moves on but does not reliably write down what it just
    # failed to establish, which makes a candidate who dodged eight areas look
    # better than one who dodged three.
    # The model names a competency only sometimes. Fall back to the stage it
    # was working in, otherwise a pivot leaves no trace and the interview looks
    # like it established nothing because nothing was written down.
    if not current_competency:
        prev_stage = interview.get("current_stage")
        if prev_stage and prev_stage not in ("greeting", "completed", "closing"):
            current_competency = prev_stage.replace("_", " ").title()

    if decision == "move_on" and current_competency:
        already = (interview.get("competencies") or {}).get(current_competency)
        naming_other = (isinstance(comp, dict)
                        and comp.get("name")
                        and comp["name"] != current_competency)
        if naming_other and (not already or already.get("status") == "not_assessed"):
            interview.setdefault("competencies", {})[current_competency] = {
                "status": "unproven",
                "note": "moved on after %d attempts without establishing evidence"
                        % max(competency_attempts_now, 1),
                "turn": interview.get("questions_asked", 0),
            }
            print(f"📌 auto-recorded {current_competency}: unproven (pivot)")
    if isinstance(comp, dict) and comp.get("name"):
        ledger = interview.setdefault("competencies", {})
        prior = ledger.get(comp["name"], {})
        # Never downgrade something already demonstrated.
        if prior.get("status") != "confirmed":
            ledger[comp["name"]] = {
                "status": comp.get("status", "not_assessed"),
                "note": comp.get("note", ""),
                "turn": interview.get("questions_asked", 0),
            }
        print(f"🎯 {comp['name']}: {comp.get('status')} - {comp.get('note','')[:80]}")
    elif current_competency and answer_quality in ("evasive", "off_topic"):
        led = interview.setdefault("competencies", {})
        if current_competency not in led:
            led[current_competency] = {
                "status": "unproven",
                "note": "answer was %s; no specifics offered" % answer_quality,
                "turn": interview.get("questions_asked", 0),
            }
            print(f"📌 recorded {current_competency}: unproven ({answer_quality})")
    question = ai_response.get("question", "Tell me more about your experience.")
    next_stage = ai_response.get("next_stage", interview.get("current_stage", "technical"))
    
    print(f"🤖 AI Decision: {decision}, Next stage: {next_stage}, "
          f"quality: {answer_quality or 'n/a'}, answered: {answered_question}")
    if claim_check and claim_check.lower() != "none":
        print(f"🔍 Claim check: {claim_check}")
    
    # Build response text
    if acknowledgment:
        response_text = f"{acknowledgment} {question}"
    else:
        response_text = question

    # Naming the pattern once is good interviewing; doing it every turn is a
    # template. Allow the first two, strip the rest.
    if narration_count(interview["conversation_history"]) >= 2:
        trimmed = strip_narration(response_text)
        if trimmed != response_text:
            print("✂️ stripped evaluator narration from spoken turn")
            response_text = trimmed
    
    # Check if interview should end
    if decision == "close" or next_stage == "completed":
        interview["status"] = "completed"
        # The interviewer judged there was no more value in continuing.
        interview["current_stage"] = "completed"
        interview["end_reason"] = "interviewer_closed"
        interview["end_time"] = datetime.now().isoformat()
        
        interview["conversation_history"].append({
            "role": "interviewer",
            "text": response_text,
            "timestamp": datetime.now().isoformat(),
            "stage": "closing"
        })
        
        await asyncio.to_thread(save_interview, interview)
        return {
            "message": {"text": response_text, "type": "conclusion"},
            "state": get_state(interview),
            "is_complete": True
        }
    
    # Update interview state. A redirect re-asks the question that was dodged,
    # so the topic is not finished and the stage must not advance. But cap it:
    # the model will happily re-ask the same question forever, which reads as
    # interrogation and stalls the interview.
    if decision in ("redirect", "diagnose"):
        prior_redirects = 0
        for turn in reversed(interview["conversation_history"][:-1]):
            if turn.get("role") != "interviewer":
                continue
            if turn.get("decision") in ("redirect", "diagnose"):
                prior_redirects += 1
            else:
                break
        if prior_redirects >= MAX_CONSECUTIVE_REDIRECTS:
            print(f"↪️ redirect cap hit ({prior_redirects}), forcing move_on")
            decision = "move_on"
            answer_quality = answer_quality or "evasive"
        else:
            next_stage = interview.get("current_stage", next_stage)
    interview["current_stage"] = next_stage
    interview["questions_asked"] += 1
    
    # Add interviewer response to history
    interview["conversation_history"].append({
        "role": "interviewer",
        "text": response_text,
        "timestamp": datetime.now().isoformat(),
        "stage": next_stage,
        "decision": decision,
        "answered_question": answered_question,
        "claim_check": claim_check,
        "answer_quality": answer_quality,
        "competency_name": (comp.get("name") if isinstance(comp, dict) else None),
        "repeats_earlier": repeat_hits,
        "depth_reached": depth_reached,
        "claims": claims_in_answer
    })
    
    await asyncio.to_thread(save_interview, interview)

    # Determine message type
    msg_type = ("followup"
                if decision in ["follow_up", "dig_deeper", "challenge",
                                "redirect", "diagnose"]
                else "question")
    
    return {
        "message": {"text": response_text, "type": msg_type},
        "state": get_state(interview),
        "is_complete": False
    }


@router.post("/interview/end")
def end_interview(request: EndInterviewRequest):
    """End interview."""
    
    interview = get_interview(request.interview_id)
    if not interview:
        raise HTTPException(404, "Interview not found")
    
    interview["status"] = "completed"
    interview["end_time"] = datetime.now().isoformat()
    interview["end_reason"] = request.reason
    save_interview(interview)
    
    start = datetime.fromisoformat(interview["start_time"])
    end = datetime.fromisoformat(interview["end_time"])
    
    return {
        "message": {"text": f"Thank you, {interview['candidate_name']}!", "type": "conclusion"},
        "summary": {"duration_mins": (end - start).seconds // 60, "questions": interview["questions_asked"]},
        "report_id": request.interview_id
    }


@router.get("/interview/{interview_id}/status")
def status(interview_id: str, user_id: int):
    interview = get_interview(interview_id)
    if not interview:
        raise HTTPException(404, "Not found")
    return get_state(interview)


@router.get("/interview/{interview_id}/history")
def history(interview_id: str, user_id: int):
    interview = get_interview(interview_id)
    if not interview:
        raise HTTPException(404, "Not found")
    return {"history": interview["conversation_history"]}


# ==========================================
# Helpers
# ==========================================

def get_interview(interview_id: str):
    if interview_id in active_interviews:
        return active_interviews[interview_id]
    
    for path in [f"data/interviews/{interview_id}.json", f"data/conversations/{interview_id}.json"]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                active_interviews[interview_id] = data
                return data
    return None


def save_interview(interview: dict):
    iid = interview["interview_id"]
    active_interviews[iid] = interview
    
    for path in [f"data/interviews/{iid}.json", f"data/conversations/{iid}.json"]:
        with open(path, 'w') as f:
            json.dump(interview, f, indent=2)


# Openers that narrate the evaluator's state rather than talking to a person.
# The prompt asks the model to avoid these; this strips them when it does not,
# because one of them per interview is fine and nine is a template.
_NARRATION = re.compile(
    r"^\s*(?:"
    r"I (?:understand|notice|see)[^.!?]*[.!?]\s*"
    r"|(?:Since\s+)?[Ww]e(?:'ve| have)\s+(?:covered|discussed|focused|hit|reached|established)[^.!?]*[.!?]\s*"
    r"|(?:Since\s+)?[Ww]e\s+(?:haven't|aren't|weren't)[^.!?]*[.!?]\s*"
    r")+",
    re.IGNORECASE)


def strip_narration(text: str) -> str:
    """Remove a leading evaluator-narration clause, keeping the real question."""
    out = _NARRATION.sub("", text or "", count=1).strip()
    return out if len(out) > 25 else (text or "").strip()


def narration_count(conversation) -> int:
    return sum(1 for t in conversation
               if t.get("role") == "interviewer"
               and _NARRATION.match(t.get("text") or ""))


def build_closing_message(interview: dict, name: str) -> str:
    """Close the interview by saying why, not just "thank you".

    Ending on a turn budget while a competency is still unproven is a real
    outcome and the candidate should hear it, rather than an abrupt sign-off
    straight after an answer that missed the question.
    """
    ledger = interview.get("competencies") or {}

    def trivial(name):
        return any(w in name.lower() for w in
                   ("greeting", "communication", "rapport", "comfort",
                    "background", "icebreaker"))

    # Saying "we got into Communication / Professional Greeting properly" is
    # exactly the false-coverage claim this message exists to avoid.
    unproven = [k for k, v in ledger.items()
                if v.get("status") == "unproven" and not trivial(k)]
    confirmed = [k for k, v in ledger.items()
                 if v.get("status") == "confirmed" and not trivial(k)]

    substantive = [k for k, v in ledger.items()
                   if v.get("status") in ("confirmed", "partial", "unproven",
                                          "no_experience")
                   and not any(w in k.lower()
                               for w in ("greeting", "communication", "rapport"))]

    parts = [f"That's our time, {name} - thanks for talking it through."]

    # Never imply an area was assessed when it was not. A closing that claims
    # good coverage over an interview that established nothing is a lie the
    # candidate will see contradicted in their own report.
    if confirmed:
        parts.append("We got into " + ", ".join(confirmed[:3]) + " properly.")
    elif substantive:
        parts.append(
            "I wasn't able to get much technical detail today, so there's less "
            "here than I'd have liked.")
    if unproven:
        parts.append(
            "We didn't manage to pin down " + ", ".join(unproven[:2]) +
            " - worth having a concrete example ready for those.")
    parts.append("Your report will follow shortly. Best of luck!")
    return " ".join(parts)


def get_state(interview: dict) -> dict:
    start = datetime.fromisoformat(interview["start_time"])
    elapsed = (datetime.now() - start).seconds // 60
    
    return {
        "stage": interview["status"],
        "current_stage": interview.get("current_stage", "unknown"),
        "progress_percent": min(100, (interview["questions_asked"] / interview["max_questions"]) * 100),
        "questions_asked": interview["questions_asked"],
        "questions_remaining": max(0, interview["max_questions"] - interview["questions_asked"]),
        "time_elapsed_mins": elapsed,
        "time_remaining_mins": max(0, interview["max_duration_mins"] - elapsed),
        "target_role": interview.get("target_role"),
        "ai_enabled": interview.get("ai_enabled", False)
    }