# AI Interview Platform

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

An AI interviewer that reads a candidate's resume, conducts an adaptive spoken
technical interview about their own projects, and produces an evidence-based
readiness report.

Built as a full-stack system: FastAPI + Gemini backend, Next.js frontend, and a
complete deployment path through Docker, Kubernetes, Helm, Terraform and
Prometheus.

---

## 🎥 Demo

> _Recording to be added._ Until then, [`INTERVIEW_CONVERSATIONS.txt`](INTERVIEW_CONVERSATIONS.txt)
> contains four complete interview transcripts with their scored reports —
> a strong candidate, an over-claimer, a nervous candidate, and one who deflects
> every question back to the same project.

---

## What problem does this solve?

Mock interviews are the highest-value preparation a student can get, and the
constraint is arithmetic, not willingness:

| | |
|---|---|
| Final-year students in a batch | 300 |
| Useful mock interviews each | 3 |
| Total needed | **900** |
| Meaningful mocks one trainer runs per day | 6 |
| Trainer-days required | **150** |
| Working days in a placement season | ~60 |

A placement cell would need 2.5 full-time trainers doing nothing else. So most
students get one mock, or none — and the ones who ask are the ones who least
need it.

There is a second problem underneath. A mock interview run from a generic
question bank ignores the resume. A candidate whose resume says *Docker, AWS,
FastAPI* gets asked "what is OOPs", the same as everyone else. Companies don't
interview that way, so the practice doesn't transfer.

**This platform interviews the candidate about their own resume, and grades what
they can actually demonstrate rather than what they claim.**

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Resume parsing** | PDF/DOCX → structured JSON (skills, projects, experience) |
| **ATS analysis** | Score out of 100 with section-by-section feedback |
| **Resume builder** | Guided build → AI refinement → ATS score → PDF download |
| **Spoken interview** | Questions asked aloud in Indian English; candidate answers by speaking |
| **Adaptive questioning** | 8 stages, difficulty calibrated from years of experience |
| **Competency ledger** | Per-skill evidence record: confirmed / partial / unproven / no-experience |
| **Scored report** | 6 dimensions plus strengths, gaps and a readiness call |
| **Role practice** | Interview by target role with no resume — for first-years |
| **Prep kit** | Self-intro templates, aptitude formulas, HR answers, technical primers |
| **Admin dashboard** | Cohort view: who has practised, who hasn't, who isn't ready |

### What makes the interviewer different

It is a **state machine with an LLM inside it**, not a prompt wrapper. The model
generates the language; deterministic code controls the flow. Specifically:

- **Claims are not evidence.** Saying "I know Kubernetes" is recorded as a
  *claim*. It only becomes `confirmed` if the candidate can describe something
  they personally built, probed to a failure case or trade-off.
- **Honesty scores above bluffing.** "I haven't used Kafka" is recorded as
  `no_experience`, which is graded differently from claiming Kafka and failing
  to describe it (`unproven`).
- **It never asks the same thing three times.** Escalation is
  clarify → concrete prompt → diagnose *why* they keep missing → pivot.
- **It detects deflection.** A candidate who answers five different questions
  with the same project summary gets that recorded as a behavioural signal, and
  the interviewer moves on rather than looping.
- **Evidence can't leak between topics.** A strong answer about idempotency
  given to a rate-limiting question credits idempotency, not rate limiting.

---

## 🏗 Architecture

```
                            User
                             │
                             ▼
                     Next.js Frontend
              (speech in/out, MediaPipe eye
               tracking — both run in-browser)
                             │
                             ▼
                       Nginx / Ingress
                             │
                             ▼
                    FastAPI Backend
                  33 endpoints, async
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
          Interview Engine         Evaluation Engine
       state machine + Gemini    competency ledger →
       adaptive questioning       evidence-based score
                 │                       │
                 └───────────┬───────────┘
                             ▼
                          Results
              SQLite  ·  JSON interview state
                             │
                             ▼
                        Monitoring
                     /metrics endpoint
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
              Prometheus             Grafana
            5 alert rules          dashboards
```

**Deployment pipeline:**

```
                      GitHub Actions
                    lint · test · build
                             ↓
                          Docker
                 multi-stage · non-root
                             ↓
                       Trivy scan
                    HIGH / CRITICAL
                             ↓
                         GHCR
                  sha · semver · latest
                             ↓
                      Kubernetes
              HPA 2→10 pods · health probes
                             ↓
                          Helm
                  parameterised install
                             ↓
                       AWS / EKS
                 Terraform · VPC · ECR
```

---

## 📐 System Design

### Interview state

The HTTP layer is stateless. Each interview gets a UUID; its full state lives in
`data/interviews/{id}.json` - a JSON document holding the resume, the
conversation, the competency ledger and every claim the candidate has made.

```
POST /api/interview/start
  ├─ parse resume (Gemini)          → structured JSON
  ├─ extract probe areas            → skills, projects, gaps
  ├─ calibrate difficulty           → 0-2 yrs easy · 3-5 medium · 6+ hard
  ├─ build topic list
  └─ persist interview state        → data/interviews/{uuid}.json

POST /api/interview/respond         ← called once per candidate answer
  ├─ load context
  ├─ build 3-layer prompt (below)
  ├─ await Gemini                   → next question + evaluation
  ├─ update competency ledger
  └─ save context
```

### The three-layer prompt

Separating these is what stopped the interviewer oscillating between
too-agreeable and too-rigid:

| Layer | Content | Changes |
|---|---|---|
| **1 — System** | Standing interviewer policy, sent as `system_instruction` | Never |
| **2 — State** | Resume, competency ledger, claims made, depth reached, coverage tags | Every turn |
| **3 — Task** | This turn's directive + JSON output contract | Every turn |

### Two voices, opposite rules

The model emits an *evaluator* and an *interviewer* each turn:

- **Evaluator** (`competency`, `claim_check`, `answer_quality`) — internal. May
  be blunt and repetitive.
- **Interviewer** (`acknowledgment`, `question`) — spoken to a nervous student.
  Must never narrate the evaluator's state.

Enforced in code by `strip_narration()`, because prose instructions alone
produced *"I understand the overall project…"* nine turns running.

### Graceful degradation

No request path has a hard dependency on the AI service:

```
Gemini call
  ├─ 429 / 503 → retry with backoff, then fall through the model chain
  │              (3.5-flash-lite → 2.5-flash → 2.5-flash-lite)
  ├─ no API key → USE_MOCK_AI auto-enables at startup
  └─ total failure → role-detected fallback question bank
                     + rule-based scoring from the competency ledger
```

The ledger is built turn-by-turn *during* the interview, so it survives the case
where the final analysis call is rate-limited — which is exactly when the
heuristics are all that's left.

---

## 🤖 AI workflow

```
Resume ──► Gemini parse ──► probe areas ──► interview state
                                                  │
        ┌─────────────────────────────────────────┘
        ▼
   ┌─► build layer-2 state (ledger, claims, depth, coverage)
   │        │
   │        ▼
   │   Gemini (system_instruction + state + contract)
   │        │
   │        ▼
   │   { answered_question, claims_in_this_answer, claim_check,
   │     depth_reached, competency{name,status,note}, decision,
   │     acknowledgment, question }
   │        │
   │        ├─ relevance gate    → wrong question? credit what was evidenced
   │        ├─ depth gate        → confirmed refused below depth 4
   │        ├─ repetition guard  → same answer twice? name it once, pivot
   │        ├─ topic budget      → subject asked 3×? banned
   │        └─ narration strip   → evaluator language removed from speech
   │        │
   └────────┴─► update ledger, persist, return question
```

**The depth ladder.** A competency cannot reach `confirmed` until the candidate
has been probed past description into evidence:

```
1 concept → 2 application → 3 personal implementation
                              → 4 concrete detail → 5 failure case → 6 trade-off
                                 └────── confirmed possible from here ──────┘
```

**Models.** `gemini-3.5-flash-lite` leads the chain (15 RPM free tier vs 5 for
2.5-flash), with the configured model and `2.5-flash-lite` behind it.

---

## ☁ Deployment architecture

```
                    ┌──────────── AWS ────────────┐
                    │                             │
   Internet ──► ALB / Ingress                     │
                    │                             │
        ┌───────────┴───────────┐                 │
        ▼                       ▼                 │
   frontend pods           backend pods           │
   HPA 2→6 @75% CPU        HPA 2→10 @70% CPU      │
        │                       │                 │
        │                  ┌────┴────┐            │
        │                  ▼         ▼            │
        │            PVC data   PVC uploads       │
        │              5Gi         10Gi           │
        └───────────────────────────┬─────────────┘
                                    │
                              ECR · VPC (3 AZ)
                          public + private subnets
```

**Pod hardening:** `runAsNonRoot`, `allowPrivilegeEscalation: false`,
`capabilities: drop: ["ALL"]`, resource requests *and* limits
(100m/256Mi → 1000m/1Gi), rolling updates at `maxUnavailable: 0`.

**Three install paths:**

| Path | Command | Use |
|---|---|---|
| Compose | `make up` | local development |
| Kustomize | `make k8s-apply` | direct cluster apply |
| Helm | `make helm-install` | parameterised, ships a `ServiceMonitor` |

Terraform provisions VPC across 3 AZs, EKS and ECR. A single NAT gateway is a
deliberate cost trade-off — it drops AZ-level NAT redundancy, which is fine for
this workload and wrong for anything with an availability SLA.

---

## 🔄 CI/CD

```
push to main ──► lint backend (ruff)  ──┐
             └─► lint + build frontend ─┴─► Docker Buildx
                                             │  multi-platform
                                             │  GHA layer cache
                                             ▼
                                           GHCR
                                   tags: branch · PR · semver
                                         · short-sha · latest
                                             │
                                             ▼
                                       Trivy scan
                                     HIGH / CRITICAL
```

Defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Python 3.11,
Node 20.

---

## 📊 Monitoring

`prometheus-fastapi-instrumentator` exposes `/metrics`. Five alert rules, chosen
on the RED method — the three things that mean users are having a bad time:

| Alert | Condition | For |
|---|---|---|
| `BackendDown` | `up{job="backend"} == 0` | 2m |
| `HighErrorRate` | 5xx ratio > 5% | 5m |
| `HighLatencyP95` | p95 > 1.5s | 10m |
| `HostHighCPU` | > 85% | 10m |
| `HostLowDisk` | < 15% free | 5m |

Grafana dashboards are provisioned from
[`monitoring/grafana/`](monitoring/grafana/). Stack starts with
`docker compose -f monitoring/docker-compose.monitoring.yml up`.

---

## 🧪 Testing

```bash
pytest tests/ -q          # 57 tests, ~2s, no network
```

Every test is a regression case for a bug that was originally found by running a
live interview against the Gemini API — about three minutes and a chunk of
rate-limit quota per attempt. Moving them offline is the difference between
*checking* a fix and *hoping* it worked.

They cover the properties that matter rather than implementation detail:

- Greeting exchanges are never scored as interview questions
- One subject counted across different phrasings (Docker was once asked 10× in 18 turns)
- A single confirmed competency cannot produce a perfect score
- Honest gaps outrank unsupported claims
- Strengths are never derived from answer length
- Closings cannot claim coverage they didn't achieve
- **Four-persona ranking is stable** — strong > honest > bluffer > deflector
- Every field the code reads is also requested in the model contract

`tools/iv_personas.py` and `tools/iv_run.py` drive four simulated candidates end
to end against a live server for behavioural testing.

---

## 🚀 Local setup

**Requirements:** Python 3.11+, Node 20+, a Gemini API key.

```bash
git clone https://github.com/DhaneshPachipulusu/ai-bot.git
cd ai-bot

cp .env.example .env          # add GEMINI_API_KEY
```

**Backend**

```bash
python -m venv .venv && .venv/Scripts/activate     # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

**Everything at once**

```bash
make up                        # docker compose
```

> **Note:** the spoken interview uses browser speech APIs and needs **Chrome or
> Edge**. Other browsers fall back to typed input.

---

## 📸 Screenshots

> _To be added._ Suggested: resume analysis with ATS score, live interview with
> the eye-contact indicator, scored report with the competency ledger, admin
> cohort dashboard.

---

## 🎯 What I learned

**Prose instructions don't bind; code does.** The depth ladder sat in the system
prompt across several revisions and produced *zero* trade-off questions in 69
interviewer turns. It only started working when the coverage guard was changed
to yield to it and the exact question text was injected as a directive. Same
lesson with the repetitive narration — three rewrites of the wording achieved
less than one regex.

**A slow feedback loop is a design flaw.** Ten rounds of fixes were spent
diagnosing one bug at a time, in production, because each check cost a
three-minute live interview. Two of those fixes broke something else. Writing
the offline suite should have been step one, not step ten.

**Rules that contradict each other are unfollowable.** "Cover more topics" and
"go deeper" were both in the prompt; coverage always won, so depth 5 and 6 were
unreachable *by construction*. No amount of rewording fixes a contradiction.

**Measure the measurement.** For several rounds the test harness answered by
keyword-matching the interviewer's whole message, so a *better* question got a
*worse* answer and the score dropped. I was tuning the engine against a broken
oracle and reading the noise as signal.

**Interviewer failures were landing on the candidate's record.** A bug ordering
`docker` before `java` in role detection classified a Java backend candidate as
DevOps — she was then asked about Terraform and recorded "Cloud Infrastructure:
unproven". The report had nowhere to say *"not established because the
interviewer asked the wrong questions."*

**Honesty has to be scored differently from bluffing,** or the system teaches
students to bluff. That single distinction — `no_experience` vs `unproven` —
is what moved the bluffing persona below the nervous one who admits gaps.

---

## 🔗 Live Demo

> Not currently hosted — the Kubernetes manifests and Terraform are written and
> validated, but no cluster is kept running. Run locally with `make up`.

---

## Project layout

```
backend/              FastAPI service
  routes/             HTTP endpoints - interview_v2.py is the live engine
  services/           analyzer, resume tooling, PDF generation
  prompts/            layer-1 interviewer system prompt
  config.py           single source of env configuration
frontend/             Next.js 16 app, 15 screens
tests/                offline regression suite
tools/                persona-driven behavioural harness
k8s/ helm/ terraform/ deployment
monitoring/ nginx/    observability and routing
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment guide.

---

## Known gaps

Stated plainly, because they're real:

- **Passwords are stored in plaintext.** `verify_login` compares raw strings.
  Needs bcrypt/Argon2 and JWT sessions before any real user data.
- **Some routes trust a client-supplied `user_id`** rather than deriving it from
  a verified token.
- **SQLite + `ReadWriteOnce` PVC** is single-writer — the scaling ceiling.
  Postgres and Redis are the migration path.
- **No live deployment.** Validated locally, never run against a real cohort.
- The eye-contact detection and per-answer timing are captured but not yet
  used in the report.
