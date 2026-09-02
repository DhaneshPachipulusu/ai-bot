"""Drive long interviews for each persona, then pull the report.

Records where and why each interview stopped, which is the thing that is hard
to see from a single manual run. Paced to stay under the free-tier RPM cap.
"""

import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iv_personas import PERSONAS, pick  # noqa: E402

BASE = os.environ.get("IV_BASE", "http://127.0.0.1:8000")
MAX_TURNS = int(os.environ.get("IV_TURNS", "22"))
PACE = float(os.environ.get("IV_PACE", "4.5"))   # seconds between calls
OUT = os.environ.get("IV_OUT", "/tmp/ivtest")


def post(path, payload, timeout=120):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def run_one(label, name, bank, resume_extra, fh):
    resume = dict(resume_extra)
    resume["name"] = name

    def emit(s=""):
        print(s)
        fh.write(s + "\n")
        fh.flush()

    emit("=" * 78)
    emit("PERSONA: " + label)
    emit("=" * 78)

    start = post("/api/interview/start", {
        "user_id": 1, "mode": "resume",
        "target_role": resume_extra.get("target_role", "Software Developer"),
        "experience_level": "mid", "max_questions": MAX_TURNS,
        "parsed_resume": resume,
    })
    iid = start["interview_id"]
    question = start["message"]["text"]
    emit("\nALEX : " + question)

    used = set()
    turns = 0
    stop_reason = "hit MAX_TURNS in driver"

    for turns in range(1, MAX_TURNS + 1):
        answer = pick(bank, question, used)
        time.sleep(PACE)
        try:
            r = post("/api/interview/respond",
                     {"interview_id": iid, "user_id": 1, "answer": answer})
        except Exception as e:
            stop_reason = "REQUEST FAILED: %s" % str(e)[:120]
            emit("\n!! " + stop_reason)
            break

        emit("\nCAND : " + answer)
        emit("ALEX : " + r["message"]["text"])
        question = r["message"]["text"]

        if r.get("is_complete"):
            st = r.get("state", {})
            stop_reason = ("engine ended it - stage=%s asked=%s/%s"
                           % (st.get("current_stage"), st.get("questions_asked"),
                              MAX_TURNS))
            break

    emit("\n>>> STOPPED AFTER %d CANDIDATE TURNS - %s" % (turns, stop_reason))

    # ---- report -------------------------------------------------------
    time.sleep(PACE)
    try:
        rep = post("/api/analyze-interview?interview_id=" + iid, {}, timeout=180)
        rep = rep.get("report", rep)
    except Exception as e:
        emit("!! report failed: %s" % str(e)[:150])
        rep = {}

    emit("\n" + "-" * 78)
    emit("REPORT - %s" % label)
    emit("-" * 78)
    emit("mode=%s  overall=%s  readiness=%s"
         % (rep.get("analysis_mode"), rep.get("overall_score"),
            rep.get("job_readiness")))
    emit("scores: %s" % rep.get("scores"))
    emit("\nSTRENGTHS:")
    for s in (rep.get("strengths") or []):
        emit("  - %s" % s)
    emit("IMPROVEMENTS:")
    for s in (rep.get("improvements") or []):
        emit("  - %s" % s)

    # competency ledger straight off the stored interview
    ledger = {}
    for p in ("data/interviews/%s.json" % iid, "data/conversations/%s.json" % iid):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                ledger = (json.load(f).get("competencies") or {})
            break
    emit("\nCOMPETENCY LEDGER:")
    for k, v in ledger.items():
        emit("  %-30s %-14s %s" % (k, v.get("status"), (v.get("note") or "")[:60]))

    qa = rep.get("qa_feedback") or []
    emit("\nPER-QUESTION SCORES: %s"
         % ", ".join(str(q.get("score")) for q in qa))
    emit("")
    return {"label": label, "interview_id": iid, "turns": turns,
            "stop_reason": stop_reason, "overall": rep.get("overall_score"),
            "mode": rep.get("analysis_mode"),
            "ledger": {k: v.get("status") for k, v in ledger.items()}}


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for label, name, bank, extra in PERSONAS:
        path = os.path.join(OUT, label.split(" -")[0].lower() + ".txt")
        with open(path, "w", encoding="utf-8") as fh:
            summary.append(run_one(label, name, bank, extra, fh))

    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for s in summary:
        print("%-34s turns=%-3s overall=%-5s %s"
              % (s["label"], s["turns"], s["overall"], s["stop_reason"]))


if __name__ == "__main__":
    main()
