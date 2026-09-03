"""
Analyzer Service
================
- Interview report analysis (charts + AI insights)
- Resume ATS scoring (rule-based, stable)
"""

import json
import os
import time
from typing import Optional

# ==========================================
# AI Setup
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
        print("✅ Gemini AI available for analysis")
    else:
        print("⚠️ AI disabled - using rule-based analysis")
except Exception as e:
    print(f"⚠️ Gemini import failed: {e}")


# Same two failure modes as the interview turn: free-tier 429s and 503
# overload. A dropped call here is what stamps "Rule-based" on the report,
# so it is worth a longer wait than an interactive turn - the candidate is
# waiting on one request, not one of ten.
MODEL_CHAIN = [m for m in (GEMINI_MODEL, "gemini-2.5-flash-lite") if m]
_RETRY_BUDGET_SECONDS = 20.0
_BACKOFF = (1.0, 3.0, 6.0)


def _is_transient(err: Exception) -> bool:
    s = str(err)
    return any(k in s for k in
               ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "overloaded"))


def call_gemini(prompt: str) -> Optional[str]:
    if not client:
        return None

    deadline = time.monotonic() + _RETRY_BUDGET_SECONDS
    last_error = None

    for model in MODEL_CHAIN:
        for attempt, pause in enumerate((0.0,) + _BACKOFF):
            if pause:
                if time.monotonic() + pause > deadline:
                    break
                time.sleep(pause)
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if attempt or model != MODEL_CHAIN[0]:
                    print(f"✅ Analysis recovered on {model} (attempt {attempt + 1})")
                return response.text.strip()
            except Exception as e:
                last_error = e
                if not _is_transient(e):
                    print(f"⚠️ Analysis Gemini error ({model}): {str(e)[:120]}")
                    return None
                if time.monotonic() > deadline:
                    break

    print(f"⚠️ Analysis falling back to rule-based: {str(last_error)[:120]}")
    return None


# ==========================================
# INTERVIEW ANALYSIS
# ==========================================

def analyze_interview(conversation_path: str) -> dict:
    if not os.path.exists(conversation_path):
        return fallback_interview("Interview file not found")

    with open(conversation_path, "r") as f:
        data = json.load(f)

    qa_pairs = extract_qa(data)
    if not qa_pairs:
        return fallback_interview("No interview answers found")

    # ---------- Rule-based scores (for charts) ----------
    score_block = rule_interview_scores(qa_pairs)

    # The competency ledger is built turn by turn DURING the interview, so it
    # survives even when this final analysis call is rate-limited. It is also
    # the only signal that separates a candidate who knows things from one who
    # merely talks at length, so it overrides the length-based heuristics.
    ledger = data.get("competencies") or {}
    if ledger:
        score_block = apply_competency_evidence(
            score_block, ledger,
            [m for m in data.get('conversation_history', [])
             if m.get('role') == 'interviewer'])

    # ---------- AI insights (textual value) ----------
    ai_block = {}
    if AI_AVAILABLE:
        try:
            ai_block = ai_interview_feedback(qa_pairs)
            ai_block["analysis_mode"] = "ai"
        except Exception:
            ai_block = {"analysis_mode": "rule_based"}

    # ---------- Merge Q&A pairs with AI feedback ----------
    # Get per-question feedback from AI (indexed by question number)
    per_q_feedback = ai_block.get("per_question_feedback", {})
    
    # Create merged qa_feedback with ALL questions
    merged_qa_feedback = []
    for i, qa in enumerate(qa_pairs):
        question = qa["question"]
        user_answer = qa["answer"]
        
        # Get AI feedback for this question by index (1-based in AI response)
        q_idx = str(i + 1)
        ai_fb = per_q_feedback.get(q_idx, {})
        
        # Handle case where ai_fb might be a string or dict
        if isinstance(ai_fb, str):
            ai_fb = {"better_answer": ai_fb}
        
        merged_qa_feedback.append({
            "question": question,
            "user_answer": user_answer,
            "better_answer": ai_fb.get("better_answer", "") if isinstance(ai_fb, dict) else "",
            "feedback": ai_fb.get("feedback", "") if isinstance(ai_fb, dict) else "",
            "score": ai_fb.get("score", calculate_answer_score(user_answer)) if isinstance(ai_fb, dict) else calculate_answer_score(user_answer)
        })

    # Remove qa_feedback from ai_block if it exists (we're using merged version)
    ai_block_clean = {k: v for k, v in ai_block.items() if k not in ["qa_feedback", "per_question_feedback"]}

    merged = {
        **score_block,
        **ai_block_clean,
        "qa_feedback": merged_qa_feedback,
        "analysis_mode": ai_block.get("analysis_mode", "rule_based"),
    }
    # AI text is richer when available, but the ledger's scores are the
    # evidence-based ones and must not be overwritten by the AI block.
    if ledger:
        merged["scores"] = score_block["scores"]
        merged["overall_score"] = score_block["overall_score"]
        merged["competencies"] = ledger
        merged["evidence_ratio"] = score_block.get("evidence_ratio")
        # The AI block writes prettier prose but its readiness call is not
        # evidence-based; letting it through is how one candidate ended up
        # labelled differently in the report and on the dashboard.
        merged["job_readiness"] = score_block["job_readiness"]
        for k in ("strengths", "improvements", "evidence_confidence",
                  "competencies_assessed", "scored_dimensions"):
            if k in score_block:
                merged[k] = score_block[k]
    return merged


# One definition, used by the analyzer, the AI prompt and the admin dashboard.
# These disagreed: the report called 7.3 "Developing" while the dashboard
# called the same number "Job Ready", which a placement officer would spot
# immediately.
READY_AT = 7.5
DEVELOPING_AT = 5.5


def readiness_label(overall: float) -> str:
    if overall >= READY_AT:
        return "Ready"
    if overall >= DEVELOPING_AT:
        return "Developing"
    return "Needs Work"


def apply_competency_evidence(score_block: dict, ledger: dict,
                              interviewer_turns_hint=None) -> dict:
    """Re-score from demonstrated competence rather than answer length.

    Without this, a fluent candidate who substantiates nothing scores the same
    as one who substantiates everything - both write long answers full of
    technical nouns. The ledger records whether a claim actually survived
    probing, which is the distinction that matters.
    """
    # A polite hello is not a competency. Counting "Communication: confirmed"
    # from the greeting turn hands every candidate a free confirmed entry, and
    # on a short ledger that single entry can swing the whole score.
    TRIVIAL = ("communication", "greeting", "comfort", "rapport", "background")

    def is_trivial(name):
        n = name.lower()
        return any(w in n for w in TRIVIAL) and "technical" not in n

    scored = {k: v for k, v in ledger.items() if not is_trivial(k)}

    statuses = [v.get("status") for v in scored.values()]
    confirmed = statuses.count("confirmed")
    partial = statuses.count("partial")
    unproven = statuses.count("unproven")
    # Honestly disclosed gaps are a real finding but not a failed claim. They
    # count toward how much was assessed without dragging the ratio down the
    # way an unsupported claim does.
    no_exp = statuses.count("no_experience")
    # A probe the model labelled "not_assessed" but annotated as a dodge is a
    # failed probe. Leaving it out of the denominator made the identical
    # behaviour free or costly depending on which word the model picked.
    dodged = sum(1 for v in scored.values()
                 if v.get("status") == "not_assessed"
                 and (v.get("note") or "").strip())
    unproven += dodged
    assessed = confirmed + partial + unproven + no_exp
    if not assessed:
        # Every recorded competency was a greeting or rapport note, so an
        # entire interview produced no technical evidence at all. That is a
        # strong negative signal, not a reason to leave the heuristic score
        # alone - falling through here is what let a candidate who answered
        # nothing score highest.
        if len(ledger) and len(interviewer_turns_hint or []) >= 6:
            out = dict(score_block)
            s = {k: min(v, 4) for k, v in (score_block.get("scores") or {}).items()}
            out["scores"] = s
            out["overall_score"] = round(sum(s.values()) / max(len(s), 1), 1)
            out["evidence_ratio"] = 0.0
            out["job_readiness"] = "Needs Work"
            out["competencies"] = ledger
            out["improvements"] = [
                "No technical competency could be established across the whole "
                "interview. Every question was answered with a general project "
                "summary rather than specifics. Prepare, for each resume skill: "
                "what you personally built, how it worked, and what you would "
                "change."]
            out["strengths"] = ["Completed the interview and engaged politely."]
            return out
        return score_block

    # 1.0 = every probed competency held up, 0.0 = none did.
    evidence = (confirmed + 0.5 * partial + 0.25 * no_exp) / assessed

    # One confirmed competency is not the same evidence as six. Without this,
    # an interview that only ever established Docker scored a perfect 10 on
    # technical, because 1-of-1 and 6-of-6 both read as a ratio of 1.0.
    # Around five probed competencies is where the ratio starts to mean
    # something; below that the heuristic keeps most of its weight.
    confidence = min(1.0, assessed / 5.0)

    scores = dict(score_block.get("scores") or {})

    def blend(key, weight):
        """Pull a heuristic score toward the evidence ratio."""
        base = scores.get(key, 6)
        target = 2.0 + 8.0 * evidence
        scores[key] = max(1, min(10, round(
            base + (target - base) * weight * confidence)))

    # Weighted by how much each dimension depends on demonstrated substance.
    blend("technical", 0.85)
    blend("problem_solving", 0.75)
    blend("clarity", 0.45)
    blend("communication", 0.30)
    blend("confidence", 0.25)

    # pace and confidence are delivery traits, never blended with evidence,
    # and carry adverse-impact risk on accent and nervousness - which the
    # interviewer prompt explicitly forbids judging. Keep them on the report
    # as observations; keep them out of the number that ranks people.
    JOB_RELATED = ("technical", "problem_solving", "clarity", "communication")
    graded = [scores[k] for k in JOB_RELATED if k in scores]
    overall = round(sum(graded) / max(len(graded), 1), 1)

    out = dict(score_block)
    out["scores"] = scores
    out["overall_score"] = overall
    out["evidence_ratio"] = round(evidence, 2)
    out["evidence_confidence"] = round(confidence, 2)
    out["scored_dimensions"] = list(JOB_RELATED)
    out["observation_only"] = ["pace", "confidence"]
    out["competencies_assessed"] = assessed
    out["competencies"] = ledger
    out["job_readiness"] = readiness_label(overall)

    proven = [k for k, v in scored.items() if v.get("status") == "confirmed"]
    gaps = [(k, v.get("note", "")) for k, v in scored.items()
            if v.get("status") in ("unproven", "no_experience")]

    strengths = [f"{k} - {ledger[k].get('note') or 'demonstrated with specifics'}"
                 for k in proven[:5]]
    # "Claimed but not substantiated" is the right words for a resume skill the
    # candidate could not back up. It is the wrong words - and discouraging -
    # for something they were asked about and honestly said they had not
    # learned. Telling a student they failed to substantiate a claim they never
    # made punishes exactly the behaviour an interview should reward.
    HONEST = ("do not know", "dont know", "don't know", "not know",
              "haven't used", "havent used", "has not used", "no experience",
              "only seen videos", "no production experience", "admitted",
              "honestly stated", "not yet learned", "never used")

    def phrase(name, note):
        low = (note or "").lower()
        if any(h in low for h in HONEST):
            return (f"{name} - no experience yet, which you said openly. That is "
                    f"the right answer when it is true; the next step is to build "
                    f"something small with it so you have an example. {note}").strip()
        return f"{name} - claimed but not substantiated. {note}".strip()

    improvements = [phrase(k, note) for k, note in gaps[:5]]
    # A competency left partial because the interview ran out of turns is not
    # the same finding as one left partial because the answer was thin, and a
    # candidate should not read the first as though it were the second.
    under_probed = [k for k, v in scored.items()
                    if v.get("status") == "partial"
                    and any(w in (v.get("note") or "").lower() for w in
                            ("not asked", "did not ask", "no further", "ran out",
                             "not probed", "insufficient probing", "but did not answer"))]
    if under_probed:
        improvements.append(
            "Not fully explored before time ran out: " + ", ".join(under_probed[:3])
            + ". These are gaps in the interview, not necessarily in you.")

    if confidence < 1.0:
        improvements.append(
            "Only %d technical area%s could be assessed in this interview, so "
            "these scores are indicative rather than conclusive. Giving fuller "
            "answers across more topics would produce a firmer assessment."
            % (assessed, "" if assessed == 1 else "s"))
    honest_gaps = sum(
        1 for k, v in scored.items()
        if v.get("status") == "unproven"
        and any(h in (v.get("note") or "").lower() for h in HONEST))
    claimed_gaps = unproven - honest_gaps

    if honest_gaps and not claimed_gaps:
        improvements.insert(0, (
            f"{honest_gaps} area{'' if honest_gaps == 1 else 's'} came up that "
            "you have not worked with yet, and you said so directly rather than "
            "bluffing. Interviewers respect that. Build one small project in "
            "each and you can answer them properly next time."))
    elif unproven or partial or no_exp:
        # The summary must use the ledger's own words. "1 of 6 areas could not
        # be backed up" over a ledger holding one unproven, three partials and
        # one openly-declared gap tells the candidate something the table
        # directly below it contradicts.
        bits = []
        if claimed_gaps:
            bits.append("%d could not be backed up with specifics" % claimed_gaps)
        if partial:
            bits.append("%d were only partly established" % partial)
        if no_exp or honest_gaps:
            bits.append("%d you openly said you have not used yet"
                        % (no_exp + honest_gaps))
        if bits:
            improvements.insert(0, (
                "Of %d areas probed: %s. For the first group, prepare a "
                "concrete example - what you personally built, how it worked, "
                "and what you would change."
                % (assessed, "; ".join(bits))))
    # Once a ledger exists it is the only honest source of strengths. The
    # length/keyword heuristic otherwise credits a candidate who established
    # nothing with "uses specific technical terms".
    out["strengths"] = strengths or [
        "Completed the interview and stayed engaged throughout."]
    if improvements:
        out["improvements"] = improvements
    return out


def calculate_answer_score(answer: str) -> int:
    """Calculate a simple score based on answer length and keywords"""
    words = len(answer.split())
    tech_keywords = ["docker", "aws", "ec2", "s3", "api", "sql", "git", "ci", "cd", "deployment", "kubernetes", "terraform"]
    tech_hits = sum(1 for k in tech_keywords if k in answer.lower())
    
    # Base score on word count
    if words > 80:
        score = 8
    elif words > 50:
        score = 7
    elif words > 30:
        score = 6
    else:
        score = 5
    
    # Bonus for technical keywords
    if tech_hits >= 3:
        score = min(10, score + 1)
    
    return score


# Conversational turns that are not interview questions and must not be
# scored. "How are you doing today?" is small talk; grading the reply to it
# drags every average down and pollutes the per-question feedback list.
NON_SCORING_STAGES = {"greeting"}


def extract_qa(data: dict) -> list:
    pairs = []
    current_q = None

    for msg in data.get("conversation_history", []):
        role = msg.get("role")
        text = msg.get("text") or msg.get("content") or ""
        stage = (msg.get("stage") or "").lower()

        if role == "interviewer":
            current_q = None if stage in NON_SCORING_STAGES else text
        elif role == "candidate" and current_q:
            pairs.append({"question": current_q, "answer": text})
            current_q = None

    return pairs


# ==========================================
# INTERVIEW SCORING (RULE-BASED)
# ==========================================

def rule_interview_scores(qa_pairs: list) -> dict:
    total_words = sum(len(q["answer"].split()) for q in qa_pairs)
    avg_words = total_words / len(qa_pairs)

    tech_keywords = [
        "docker", "aws", "ec2", "s3", "api", "sql", "git",
        "ci", "cd", "monitoring", "deployment"
    ]

    tech_hits = sum(
        sum(1 for k in tech_keywords if k in q["answer"].lower())
        for q in qa_pairs
    )

    communication = 8 if avg_words > 80 else 7 if avg_words > 50 else 6
    clarity = 7 if avg_words > 40 else 6
    pace = 7 if avg_words < 120 else 6
    confidence = 7 if avg_words > 30 else 6
    technical = 8 if tech_hits >= len(qa_pairs) else 7 if tech_hits > 3 else 6
    problem_solving = 7 if tech_hits > 2 else 6

    overall = round(
        (communication + clarity + pace + confidence + technical + problem_solving) / 6,
        1
    )

    strengths, improvements = _derive_feedback(
        qa_pairs, avg_words, tech_hits, overall
    )

    return {
        "scores": {
            "communication": communication,
            "clarity": clarity,
            "pace": pace,
            "confidence": confidence,
            "technical": technical,
            "problem_solving": problem_solving
        },
        "overall_score": overall,
        "strengths": strengths,
        "improvements": improvements,
        "job_readiness": readiness_label(overall),
    }


def _derive_feedback(qa_pairs, avg_words, tech_hits, overall):
    """Build honest strengths/improvements from measured signals.

    The AI path supplies far better text, but when it is unavailable the
    report must still say something true and specific rather than render an
    empty Strengths box next to a "no critical areas" message.
    """
    n = len(qa_pairs)
    shortest = min((len(q["answer"].split()) for q in qa_pairs), default=0)
    thin = [i + 1 for i, q in enumerate(qa_pairs)
            if len(q["answer"].split()) < 25]

    strengths, improvements = [], []

    if avg_words > 80:
        strengths.append(
            f"Answers are substantial - averaging {avg_words:.0f} words, "
            "enough to show real depth."
        )
    elif avg_words > 45:
        strengths.append(
            f"Answers are a reasonable length (about {avg_words:.0f} words "
            "on average) and stay on topic."
        )
    if tech_hits >= n:
        strengths.append(
            f"Strong technical vocabulary - {tech_hits} concrete tool or "
            "technology references across the interview."
        )
    elif tech_hits > 2:
        strengths.append(
            f"Uses specific technical terms ({tech_hits} references) rather "
            "than staying vague."
        )
    if n >= 5:
        strengths.append(
            f"Completed all {n} questions without dropping out."
        )
    if not strengths:
        strengths.append("Completed the interview end to end.")

    if avg_words < 45:
        improvements.append(
            f"Answers are short - averaging {avg_words:.0f} words. Aim for "
            "60-90: state the situation, what you did, and the result."
        )
    if thin:
        improvements.append(
            "Under-developed answers on question"
            + ("s " if len(thin) > 1 else " ")
            + ", ".join(f"Q{i}" for i in thin[:4])
            + " - each needs a concrete example."
        )
    if tech_hits <= 2:
        improvements.append(
            "Few specific technologies named. Interviewers look for concrete "
            "tools and versions, not general descriptions."
        )
    if shortest < 12:
        improvements.append(
            "At least one answer was barely a sentence. Never leave a "
            "question with a one-line reply."
        )
    if not improvements:
        improvements.append(
            "No structural weaknesses detected by the rule-based pass. Re-run "
            "with AI analysis enabled for detailed per-answer critique."
        )

    return strengths, improvements


# ==========================================
# INTERVIEW AI FEEDBACK (TEXT)
# ==========================================

def ai_interview_feedback(qa_pairs: list) -> dict:
    # Build numbered Q&A text for AI
    qa_text = "\n\n".join(
        [f"Q{i+1}: {q['question']}\nA{i+1}: {q['answer']}" for i, q in enumerate(qa_pairs)]
    )

    prompt = f"""
You are evaluating a technical interview. Return VALID JSON only.

## IMPORTANT - HOW THE ANSWERS WERE CAPTURED:
The candidate's answers below were AUTOMATICALLY TRANSCRIBED from spoken audio using
browser speech-to-text, which frequently mis-hears technical terms. Read through obvious
mis-transcriptions to the INTENDED technical term, for example:
- "Mongo baby" -> MongoDB
- "embroidery model" -> embedding model
- "Croma" / "Croma didi" -> Chroma
- "rat pipeline" / "rag pipeline" -> RAG pipeline
- "vectors baby" / "vector baby" -> vector database
- "swag" / "swag systems" -> stack / systems

Do NOT penalize pronunciation, spelling, grammar, or transcription artifacts, and NEVER list
"pronunciation", "spelling", or "unclear words" as a weakness - those are speech-to-text noise,
NOT the candidate. Judge ONLY the candidate's actual technical understanding and the substance
of what they meant to say.

{qa_text}

For EACH question above (Q1 through Q{len(qa_pairs)}), provide a suggested better answer.

Return JSON in this EXACT format:
{{
  "strengths": ["strength 1", "strength 2", ...],
  "improvements": ["improvement 1", "improvement 2", ...],
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "job_readiness": "Ready" or "Developing" or "Needs Improvement",
  "per_question_feedback": {{
    "1": {{"better_answer": "improved answer for Q1", "score": 7}},
    "2": {{"better_answer": "improved answer for Q2", "score": 8}},
    ... (include ALL {len(qa_pairs)} questions)
  }}
}}

IMPORTANT: Include feedback for ALL {len(qa_pairs)} questions in per_question_feedback.
Base "improvements" and "score" on technical content only, never on how words were transcribed.
"""

    raw = call_gemini(prompt)
    if not raw:
        raise ValueError("Empty AI response")

    start = raw.find("{")
    end = raw.rfind("}") + 1
    return json.loads(raw[start:end])


def fallback_interview(reason: str) -> dict:
    return {
        "analysis_mode": "error",
        "reason": reason,
        "scores": {},
        "overall_score": 0,
        "strengths": [],
        "improvements": [],
        "suggestions": [],
        "qa_feedback": [],
        "job_readiness": "Unable to assess"
    }


# ==========================================
# ATS RESUME ANALYSIS (KEY FEATURE)
# ==========================================

def analyze_resume(parsed_resume: dict, job_description: str = None) -> dict:
    if not parsed_resume:
        return {"ats_score": 0, "error": "No resume data"}

    name = parsed_resume.get("name")
    email = parsed_resume.get("email")
    phone = parsed_resume.get("phone")
    skills = parsed_resume.get("skills", [])
    experience = parsed_resume.get("experience", [])
    education = parsed_resume.get("education", [])
    projects = parsed_resume.get("projects", [])
    summary = parsed_resume.get("summary")

    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    # Calculate section scores
    contact_score = (40 if name else 0) + (30 if email else 0) + (30 if phone else 0)
    skill_score = 95 if len(skills) >= 10 else 80 if len(skills) >= 6 else 60 if len(skills) >= 3 else 30
    exp_score = 90 if len(experience) >= 3 else 75 if len(experience) >= 2 else 60 if len(experience) >= 1 else 20
    edu_score = 85 if education else 0
    proj_score = 90 if len(projects) >= 3 else 75 if len(projects) >= 2 else 60 if len(projects) >= 1 else 0
    summary_score = 80 if summary else 0

    ats_score = int(
        contact_score * 0.15 +
        skill_score * 0.25 +
        exp_score * 0.25 +
        edu_score * 0.15 +
        proj_score * 0.10 +
        summary_score * 0.10
    )

    # Build sections array
    def get_status(score):
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "weak"
        return "missing"

    sections = [
        {
            "name": "Contact Information",
            "score": contact_score,
            "status": get_status(contact_score),
            "feedback": "Complete" if contact_score >= 80 else "Add email and phone" if not email or not phone else "Add name"
        },
        {
            "name": "Professional Summary",
            "score": summary_score,
            "status": get_status(summary_score),
            "feedback": "Good summary present" if summary else "Add a professional summary"
        },
        {
            "name": "Skills",
            "score": skill_score,
            "status": get_status(skill_score),
            "feedback": f"{len(skills)} skills found" if skills else "No skills detected"
        },
        {
            "name": "Work Experience",
            "score": exp_score,
            "status": get_status(exp_score),
            "feedback": f"{len(experience)} positions found" if experience else "No experience detected"
        },
        {
            "name": "Education",
            "score": edu_score,
            "status": get_status(edu_score),
            "feedback": "Education section present" if education else "Add education details"
        },
        {
            "name": "Projects",
            "score": proj_score,
            "status": get_status(proj_score),
            "feedback": f"{len(projects)} projects found" if projects else "Consider adding projects"
        }
    ]

    # Build ATS checks
    ats_checks = [
        {
            "name": "Contact Information",
            "passed": bool(name and email),
            "message": "Missing name or email" if not (name and email) else "",
            "priority": "critical"
        },
        {
            "name": "Skills Section",
            "passed": len(skills) >= 3,
            "message": "Add more relevant skills" if len(skills) < 3 else "",
            "priority": "critical"
        },
        {
            "name": "Work Experience",
            "passed": len(experience) >= 1,
            "message": "Add work experience or internships" if not experience else "",
            "priority": "critical"
        },
        {
            "name": "Education",
            "passed": bool(education),
            "message": "Add education details" if not education else "",
            "priority": "warning"
        },
        {
            "name": "Professional Summary",
            "passed": bool(summary),
            "message": "Add a 2-3 line professional summary" if not summary else "",
            "priority": "warning"
        },
        {
            "name": "Projects",
            "passed": len(projects) >= 1,
            "message": "Add projects to showcase your work" if not projects else "",
            "priority": "info"
        }
    ]

    # Calculate strengths
    strengths = []
    if contact_score >= 80:
        strengths.append("Complete contact information")
    if len(skills) >= 6:
        strengths.append(f"Strong skills section with {len(skills)} skills")
    if len(experience) >= 2:
        strengths.append("Good work experience history")
    if education:
        strengths.append("Education section present")
    if summary:
        strengths.append("Professional summary included")
    if len(projects) >= 2:
        strengths.append("Projects demonstrate hands-on experience")

    # Calculate critical issues
    critical_issues = []
    if not name or not email:
        critical_issues.append("Missing basic contact information (name/email)")
    if len(skills) < 3:
        critical_issues.append("Too few skills listed - ATS may reject")
    if not experience:
        critical_issues.append("No work experience detected")

    # Calculate improvements
    improvements = []
    if not summary:
        improvements.append("Add a professional summary")
    if len(skills) < 6:
        improvements.append("Add more relevant skills")
    if len(projects) < 2:
        improvements.append("Add more projects")
    if not phone:
        improvements.append("Add phone number")

    # Common keywords to suggest if job description provided
    common_tech_skills = ["Python", "JavaScript", "React", "Node.js", "SQL", "AWS", "Docker", "Git"]
    missing_skills = [s for s in common_tech_skills if s.lower() not in [sk.lower() for sk in skills]][:5]

    return {
        "ats_score": ats_score,
        "keyword_score": skill_score,
        "format_score": contact_score,
        "content_score": exp_score,
        "sections": sections,
        "ats_checks": ats_checks,
        "skills_found": skills,
        "missing_skills": missing_skills,
        "strengths": strengths if strengths else ["Resume uploaded successfully"],
        "critical_issues": critical_issues,
        "improvements": [i for i in improvements if i],
        "experience_level": (
            "Mid-Level" if len(experience) >= 3
            else "Junior" if len(experience) >= 1
            else "Fresher"
        )
    }

