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


# ------------------------------------------------------- role classification
def test_a_java_backend_candidate_is_not_labelled_devops():
    """Docker was matched before Java, so two Java backend candidates were
    interviewed for DevOps and then charged "unproven" on cloud questions
    they were never applying for."""
    from app.routes.interview_v2 import detect_role
    assert detect_role(["Java", "Spring Boot", "PostgreSQL", "Docker",
                        "JUnit"]) == "Java Developer"
    assert detect_role(["Java", "Spring Boot", "MySQL", "Docker"]) == "Java Developer"


def test_ml_does_not_match_html():
    from app.routes.interview_v2 import detect_role
    assert detect_role(["HTML", "CSS"]) != "ML Engineer"


def test_genuine_infrastructure_skills_still_classify_that_way():
    from app.routes.interview_v2 import detect_role
    assert detect_role(["Kubernetes", "Jenkins", "Ansible"]) == "DevOps Engineer"


# ------------------------------------------------------- competency naming
@pytest.mark.parametrize("name", ["Kubernetes", "Testing", "Database",
                                  "Docker", "Kafka", "Spring", "Cache"])
def test_technology_names_are_kept_as_competencies(name):
    """These collided with the question-routing tags and were silently
    discarded, deleting confirmed evidence and moving the score."""
    from app.routes.interview_v2 import NON_COMPETENCY_NAMES
    assert name.lower() not in NON_COMPETENCY_NAMES


@pytest.mark.parametrize("name", ["internship", "behavioural", "greeting",
                                  "project", "career", "background"])
def test_conversation_sections_are_rejected_as_competencies(name):
    from app.routes.interview_v2 import NON_COMPETENCY_NAMES
    assert name in NON_COMPETENCY_NAMES


# ------------------------------------------------------------- score model
def test_report_and_dashboard_agree_on_readiness():
    """The report called 7.3 "Developing" while the admin dashboard called the
    same number "Job Ready"."""
    from app.services.analyzer import readiness_label
    r = score(led(A="confirmed", B="confirmed", C="confirmed",
                  D="confirmed", E="no_experience"))
    assert r["job_readiness"] == readiness_label(r["overall_score"])


def test_delivery_traits_are_not_part_of_the_composite():
    """pace was never blended with evidence - constant 7 for every candidate -
    yet carried a sixth of the score."""
    r = score(led(A="confirmed", B="confirmed", C="confirmed"))
    assert "pace" not in r["scored_dimensions"]
    assert "confidence" not in r["scored_dimensions"]
    assert set(r["observation_only"]) == {"pace", "confidence"}


def test_a_dodged_probe_is_not_free():
    """A failed probe labelled not_assessed was excluded from the denominator,
    so the same behaviour cost nothing or cost a lot depending on which word
    the model happened to pick."""
    dodged = apply_competency_evidence(dict(BASE), {
        "Java Exceptions": {"status": "not_assessed",
                            "note": "gave a canned summary instead of answering"},
        "Docker": {"status": "confirmed", "note": "multi-stage build"}})
    clean = apply_competency_evidence(dict(BASE), {
        "Docker": {"status": "confirmed", "note": "multi-stage build"}})
    assert dodged["evidence_ratio"] < clean["evidence_ratio"]


def test_honest_candidate_with_broad_evidence_can_reach_ready():
    """Five confirmed competencies plus one openly declared gap was rated
    "Developing" - the label punished breadth, since a wider interview has
    more chances to surface a gap."""
    r = score(led(A="confirmed", B="confirmed", C="confirmed", D="confirmed",
                  E="confirmed", F="no_experience"))
    assert r["job_readiness"] == "Ready"


# ------------------------------------------------- claims survive the window
def test_claims_survive_the_truncated_context_window():
    """Layer 3 made checking earlier claims the top priority while layer 2
    passed only the last 8 turns truncated to 200 chars, so a claim from turn
    2 was invisible by turn 10 and claim_check was "none" in every transcript
    - including one where the candidate contradicted himself three times."""
    from app.routes.interview_v2 import collect_claims
    conv = [{"role": "candidate", "text": "...",
             "claims": ["deployed on kubernetes"]}]
    conv += [{"role": "candidate", "text": "filler"} for _ in range(20)]
    conv.append({"role": "candidate", "text": "...",
                 "claims": ["it was a team project"]})
    claims = collect_claims(conv)
    assert [c["claim"] for c in claims] == ["deployed on kubernetes",
                                            "it was a team project"]
    assert claims[0]["turn"] == 0


def test_collect_claims_ignores_malformed_entries():
    from app.routes.interview_v2 import collect_claims
    conv = [{"role": "candidate", "claims": ["real", "", None, 42]},
            {"role": "candidate"}]
    assert [c["claim"] for c in collect_claims(conv)] == ["real"]


# ------------------------------------------------------------- depth ladder
def test_confirmation_requires_reaching_the_evidence_rungs():
    """Zero trade-off or failure-case questions were asked across 69
    interviewer turns, because the coverage guard always pivoted first - yet
    competencies were still being marked confirmed off a description."""
    from app.routes.interview_v2 import CONFIRM_REQUIRES_DEPTH
    assert CONFIRM_REQUIRES_DEPTH >= 4


# --------------------------------------------------- depth probe escalation
def test_depth_probe_is_due_only_once_the_ladder_is_climbed():
    from app.routes.interview_v2 import next_depth_probe
    assert next_depth_probe({"Docker": 0}, "Docker") is None
    assert next_depth_probe({"Docker": 2}, "Docker") is None
    assert next_depth_probe({"Docker": 3}, "Docker")[0] == 4
    assert next_depth_probe({"Docker": 5}, "Docker")[0] == 6
    assert next_depth_probe({"Docker": 6}, "Docker") is None
    assert next_depth_probe({}, None) is None


def test_each_probe_names_the_actual_question_to_ask():
    """Asking for trade-off questions in prose produced zero across 69 turns.
    The directive has to contain the question itself."""
    from app.routes.interview_v2 import DEPTH_PROBES
    assert "?" in DEPTH_PROBES[5][1] and "broke" in DEPTH_PROBES[5][1]
    assert "?" in DEPTH_PROBES[6][1]
    assert "alternative" in DEPTH_PROBES[6][1]


def test_directive_text_has_no_stray_control_characters():
    """A \n written into a non-raw patch string produced a real newline
    inside an f-string and broke the module once already."""
    from app.routes.interview_v2 import DEPTH_PROBES
    for _lvl, (label, how) in DEPTH_PROBES.items():
        assert not any(ord(c) < 32 for c in label + how)


def test_deep_dive_gets_more_turns_than_a_stuck_probe():
    """Reaching a trade-off question is depth 6 and takes about five turns on
    one competency, but the coverage guard pivoted at three - so the top of
    the ladder was unreachable and no trade-off question was ever asked."""
    from app.routes.interview_v2 import (MAX_TURNS_WHILE_DEEPENING,
                                         MAX_CONSECUTIVE_REDIRECTS)
    assert MAX_TURNS_WHILE_DEEPENING >= 5
    assert MAX_TURNS_WHILE_DEEPENING > MAX_CONSECUTIVE_REDIRECTS


# ------------------------------------------------- answer/question relevance
def test_summary_line_matches_the_ledger():
    """The report said "1 of 6 areas could not be backed up" over a ledger
    holding one unproven, three partials and one declared gap - a claim the
    table directly below it contradicted."""
    r = apply_competency_evidence(dict(BASE), {
        "Idempotency": {"status": "confirmed", "note": "concrete"},
        "Testing": {"status": "unproven", "note": "repeated introduction"},
        "Caching": {"status": "no_experience", "note": "openly admitted"},
        "Concurrency": {"status": "partial", "note": "did not answer follow-up"},
        "Docker": {"status": "partial", "note": "multi-stage build"},
        "Spring DI": {"status": "partial", "note": "constructor injection"}})
    summary = r["improvements"][0]
    assert "Of 6 areas probed" in summary
    assert "1 could not be backed up" in summary
    assert "3 were only partly established" in summary
    assert "1 you openly said you have not used yet" in summary


def test_under_probed_partial_is_not_blamed_on_the_candidate():
    """"Partial because the interview ran out of turns" is a different finding
    from "partial because the answer was thin"."""
    r = apply_competency_evidence(dict(BASE), {
        "Concurrency": {"status": "partial",
                        "note": "explained it but did not answer the follow-up"},
        "Docker": {"status": "confirmed", "note": "multi-stage build"}})
    assert any("not necessarily in you" in s for s in r["improvements"])


def test_running_out_of_turns_is_recorded_as_such():
    """Turn completion is not competency completion - the report must be able
    to tell the difference."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "app", "routes", "interview_v2.py"),
        encoding="utf-8").read()
    assert 'interview["end_reason"] = "turn_budget_exhausted"' in src
    assert 'interview["end_reason"] = "interviewer_closed"' in src


def test_every_field_the_code_reads_is_also_requested_from_the_model():
    """The relevance gate read competency_actually_evidenced but the JSON
    contract never asked for it, so it was always empty and the gate fired
    zero times across three live runs. Same class of bug as reading
    answer_addresses_the_question while the model filled answered_question."""
    import re as _re
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "app", "routes", "interview_v2.py"),
        encoding="utf-8").read()
    contract = src[src.index("Return ONLY valid JSON"):]
    contract = contract[:contract.index('}}"""')]
    for field in _re.findall(r'ai_response\.get\("([a-z_]+)"', src):
        if field in ("competency",):
            continue
        assert '"%s"' % field in contract, (
            "%s is read from the model response but never requested in the "
            "JSON contract" % field)


# ------------------------------------------------------- the relevance gate
def test_strong_answer_to_the_wrong_question_does_not_credit_it():
    """Meera was asked how rate limiting works across instances and answered
    with PostgreSQL idempotency. Real knowledge, wrong competency - and the
    engine counted it as progress on rate limiting."""
    from app.routes.interview_v2 import redirect_misplaced_evidence
    comp, redirected = redirect_misplaced_evidence(
        {"name": "Distributed Rate Limiting", "status": "confirmed",
         "note": "explained idempotency keys"},
        answered_question=False,
        evidenced="Idempotency Design")
    assert redirected
    assert comp["status"] == "unproven"
    assert "Idempotency Design" in comp["note"]


def test_missing_the_question_cannot_leave_a_confirmed_status():
    from app.routes.interview_v2 import redirect_misplaced_evidence
    comp, redirected = redirect_misplaced_evidence(
        {"name": "Kafka", "status": "confirmed", "note": "textbook definition"},
        answered_question=False, evidenced=None)
    assert redirected and comp["status"] == "unproven"


def test_an_answered_question_is_left_alone():
    from app.routes.interview_v2 import redirect_misplaced_evidence
    original = {"name": "Docker", "status": "confirmed", "note": "multi-stage"}
    comp, redirected = redirect_misplaced_evidence(
        dict(original), answered_question=True, evidenced=None)
    assert not redirected and comp == original


def test_evidencing_the_same_competency_is_not_a_redirect():
    from app.routes.interview_v2 import redirect_misplaced_evidence
    comp, redirected = redirect_misplaced_evidence(
        {"name": "Docker", "status": "partial", "note": "n"},
        answered_question=False, evidenced="docker")
    assert not redirected and comp["status"] == "partial"
