"""Offline regression tests for the interview engine.

Every case here is a bug that was found by running a live interview against
the Gemini API - roughly three minutes and a chunk of rate-limit quota per
attempt. These run in under a second with no network, which is the difference
between "check the fix" and "hope the fix worked".

Run:  pytest tests/ -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.analyzer import (  # noqa: E402
    apply_competency_evidence, extract_qa, rule_interview_scores,
)
from app.routes.interview_v2 import (  # noqa: E402
    build_closing_message, detect_repetition, topic_ask_counts, topics_in,
)

BASE = {
    "scores": {"communication": 6, "clarity": 6, "pace": 7,
               "confidence": 7, "technical": 6, "problem_solving": 6},
    "overall_score": 6.3,
}


def led(**kw):
    """Shorthand: led(Docker='confirmed', Kafka='unproven')."""
    return {k.replace("_", " "): {"status": v, "note": ""} for k, v in kw.items()}


def score(ledger, base=None):
    return apply_competency_evidence(dict(base or BASE), ledger)


# ---------------------------------------------------------------- transcript
def test_greeting_exchange_is_not_scored_as_a_question():
    """Grading "how are you?" / "im good" dragged every average down."""
    data = {"conversation_history": [
        {"role": "interviewer", "text": "How are you today?", "stage": "greeting"},
        {"role": "candidate", "text": "im good sir"},
        {"role": "interviewer", "text": "Explain idempotency.", "stage": "technical"},
        {"role": "candidate", "text": "unique index on the event id"},
    ]}
    qa = extract_qa(data)
    assert len(qa) == 1
    assert "idempotency" in qa[0]["question"].lower()


# --------------------------------------------------------------- repetition
def test_identical_answer_is_detected_as_repetition():
    conv = [{"role": "candidate", "text": "i built a bus tracking system with "
                                          "spring boot and mysql for college"}] * 3
    hits, sim = detect_repetition(conv, "i built a bus tracking system with "
                                        "spring boot and mysql for college")
    assert hits == 3 and sim == pytest.approx(1.0)


def test_distinct_answer_is_not_flagged():
    conv = [{"role": "candidate", "text": "i built a bus tracking system with "
                                          "spring boot and mysql for college"}]
    hits, _ = detect_repetition(conv, "idempotency key with a unique index in "
                                      "postgres, insert conflict returns existing")
    assert hits == 0


# ------------------------------------------------------------- topic budget
def test_one_subject_counted_across_different_wordings():
    """The old guard counted competency NAMES, which the model varies, so
    Docker got asked ten times in eighteen turns."""
    conv = [{"role": "interviewer", "text": t} for t in [
        "walk me through your Dockerfile",
        "how did you containerize the service?",
        "what base image did you use?",
    ]]
    assert topic_ask_counts(conv)["docker"] == 3


def test_topic_vocabulary_matches_synonyms():
    assert "kubernetes" in topics_in("how do your pods scale?")
    assert "ci_cd" in topics_in("describe your Jenkins pipeline")


# ------------------------------------------------------------------ scoring
def test_strong_candidate_outranks_overclaimer():
    strong = score(led(Idempotency="confirmed", Testing="confirmed",
                       Docker="confirmed", Concurrency="confirmed",
                       Indexing="confirmed", Cloud="no_experience"))
    bluff = score(led(Kubernetes="unproven", Kafka="unproven", Redis="unproven",
                      Testing="unproven", Migrations="unproven",
                      Java="partial"))
    assert strong["overall_score"] > bluff["overall_score"] + 1.5
    assert strong["scores"]["technical"] > bluff["scores"]["technical"] + 2


def test_honest_gaps_beat_unsupported_claims():
    """Saying "I haven't used Kafka" must not be graded like claiming Kafka
    and failing to describe it."""
    honest = score(led(A="no_experience", B="no_experience", C="no_experience",
                       D="no_experience", E="partial"))
    bluff = score(led(A="unproven", B="unproven", C="unproven",
                      D="unproven", E="partial"))
    assert honest["overall_score"] > bluff["overall_score"]


def test_single_competency_cannot_produce_a_perfect_score():
    """One confirmed area scored technical 10, because 1-of-1 and 6-of-6 both
    read as a ratio of 1.0."""
    thin = score(led(Docker="confirmed"))
    full = score(led(**{f"C{i}": "confirmed" for i in range(6)}))
    assert thin["scores"]["technical"] <= 7
    assert full["scores"]["technical"] >= 9
    assert thin["evidence_confidence"] < full["evidence_confidence"]


def test_thin_evidence_is_declared_in_the_report():
    thin = score(led(Docker="confirmed"))
    assert any("indicative rather than conclusive" in s
               for s in thin["improvements"])


def test_greeting_only_ledger_scores_low_not_high():
    """This scored 7.8 - the highest of any candidate - because the greeting
    was the only entry, the trivial filter emptied the set, and a fallback
    then trusted it at ratio 1.0."""
    r = apply_competency_evidence(
        dict(BASE),
        {"General Communication": {"status": "confirmed", "note": "polite"}},
        [{"role": "interviewer"}] * 12,
    )
    assert r["overall_score"] <= 4.5
    assert r["job_readiness"] == "Needs Work"


def test_strengths_never_come_from_answer_length():
    """A candidate who established nothing was credited with "uses specific
    technical terms" by the old length heuristic."""
    r = score(led(A="unproven", B="unproven", C="unproven"))
    joined = " ".join(r["strengths"]).lower()
    assert "specific technical terms" not in joined
    assert "without dropping out" not in joined


def test_four_persona_ranking_is_stable():
    """The property that actually matters: the ordering must hold."""
    ranked = {
        "strong": score(led(A="confirmed", B="confirmed", C="confirmed",
                            D="confirmed", E="partial", F="no_experience")),
        "honest": score(led(A="partial", B="no_experience", C="no_experience",
                            D="no_experience", E="unproven")),
        "bluffer": score(led(A="partial", B="unproven", C="unproven",
                             D="unproven", E="unproven")),
        "deflector": score(led(A="unproven", B="unproven", C="unproven",
                               D="unproven", E="unproven", F="unproven")),
    }
    order = [k for k, _ in sorted(ranked.items(),
                                  key=lambda kv: -kv[1]["overall_score"])]
    assert order == ["strong", "honest", "bluffer", "deflector"]


# ------------------------------------------------------------------ closing
def test_closing_never_claims_coverage_it_did_not_achieve():
    """Two interviews signed off "we've covered a good range of topics" and
    "we have all the information we need" having established nothing."""
    msg = build_closing_message(
        {"competencies": led(Docker="unproven", CICD="unproven")}, "Ravi")
    low = msg.lower()
    assert "covered a good range" not in low
    assert "all the information we need" not in low
    assert "wasn't able to get much" in low


def test_closing_does_not_credit_a_greeting_as_an_achievement():
    msg = build_closing_message(
        {"competencies": {"Communication / Professional Greeting":
                          {"status": "confirmed"},
                          "Package Management": {"status": "unproven"}}},
        "Kavya")
    assert "greeting" not in msg.lower()


def test_closing_names_real_achievements_when_they_exist():
    msg = build_closing_message(
        {"competencies": led(Idempotency_Design="confirmed",
                             Integration_Testing="confirmed")}, "Meera")
    assert "Idempotency Design" in msg


# --------------------------------------------------------------- heuristics
def test_rule_scores_still_work_without_a_ledger():
    """Legacy interviews predate the ledger and must not crash."""
    qa = [{"question": "q", "answer": "i used docker and aws to deploy the api "
                                      "with a ci pipeline and monitoring"}] * 4
    r = rule_interview_scores(qa)
    assert 1 <= r["overall_score"] <= 10
    assert r["strengths"] and r["improvements"]


# ------------------------------------------- evaluator vs interviewer voice
NARRATED = [
    ("I understand the overall bus tracking system. Since we haven't been able "
     "to establish details, let's look at CI/CD. Can you describe a pipeline?",
     "Can you describe a pipeline?"),
    ("I notice you've shared that project overview several times. When you "
     "write classes in Java, how do you manage encapsulation?",
     "When you write classes in Java, how do you manage encapsulation?"),
    ("We've covered the bus tracking project extensively. How do you approach "
     "debugging a backend service?",
     "How do you approach debugging a backend service?"),
]


@pytest.mark.parametrize("spoken,expected", NARRATED)
def test_evaluator_narration_is_stripped_from_speech(spoken, expected):
    """The evaluator may be repetitive; the spoken interviewer may not.
    One transcript opened nine consecutive turns with "I understand the
    overall bus tracking project..." - accurate, and not how a person talks."""
    from app.routes.interview_v2 import strip_narration
    assert strip_narration(spoken) == expected


def test_a_normal_question_is_left_alone():
    from app.routes.interview_v2 import strip_narration
    plain = "Got it. Can you describe a CI/CD pipeline you have worked with?"
    assert strip_narration(plain) == plain


def test_narration_is_counted_so_the_first_one_is_allowed():
    """Naming the pattern once is good interviewing. The guard only trims
    after it has already happened twice."""
    from app.routes.interview_v2 import narration_count
    conv = [{"role": "interviewer", "text": s} for s, _ in NARRATED]
    conv.append({"role": "interviewer", "text": "What did you build?"})
    assert narration_count(conv) == 3


def test_no_control_characters_in_the_narration_pattern():
    """This regex was silently broken once: a \b written in a non-raw string
    became a literal backspace byte, so nothing ever matched."""
    from app.routes.interview_v2 import _NARRATION
    assert not any(ord(c) < 32 for c in _NARRATION.pattern)
