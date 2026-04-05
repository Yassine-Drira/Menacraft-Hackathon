# ClipTrust Axe 3 - Jury Master Document

Date: April 5, 2026
Project: Menacraft Hackathon - Source Credibility Engine (Axe 3)
Status: Production-ready for jury demo

---

## 1) What This Project Delivers

ClipTrust Axe 3 is a source credibility engine.
Given any URL (news domain, social profile, reel/post URL, or even risky raw host input), it returns:

- `score` (0 to 100)
- `confidence` (20 to 99)
- `verdict` (`authentic`, `suspicious`, or `fake`)
- `flags` (human-readable evidence)
- `axis` (`source`)

Core value for judges:

- Fast: typical responses around 1 to 2 seconds
- Explainable: every result includes reasons
- Robust: graceful fallback when deep analysis times out
- Practical: single API endpoint + health endpoint + optional UI

---

## 2) Problem Statement

Misinformation spreads through links and social media posts faster than users can verify credibility.

Most systems are either:

- pure black-box classifiers with weak explainability, or
- narrow domain checks that ignore publisher credibility context.

This engine solves both issues by combining multi-signal URL/domain intelligence with optional publisher/account evidence and confidence-aware output.

---

## 3) Jury Pitch Script (Use This Verbatim)

### 60-second version

We built the Source Credibility engine for ClipTrust.
Given any URL, we output a trust score from 0 to 100, a confidence score, a verdict, and plain-language evidence flags.

What makes this different is explainability and safety:
- We combine multiple signals instead of a single heuristic.
- We degrade gracefully when data is missing.
- We return conservative scoring in URL-only mode.
- We include a timeout fallback path so the API remains responsive.

On our labeled benchmark set of 24 URLs, we reached 95.8% accuracy with one conservative miss.
This is a practical, transparent, production-ready source-risk triage engine.

### 3-minute version

1. Problem
Users need fast source trust signals before they trust and share content.

2. Approach
We evaluate weighted source signals (domain, URL risk, transport security, AI URL risk reasoning, and optional publisher behavior/style evidence).

3. Output design
Each response is interpretable:
- score
- confidence
- verdict
- flags
This makes decisions auditable by humans.

4. Validation
We benchmarked 24 labeled URLs:
- Accuracy: 95.8%
- One miss: expected fake, predicted suspicious (conservative direction)

5. Reliability
We protect responsiveness with a deep-analysis watchdog timeout and a fast fallback mode.

6. Impact
The engine is immediately usable in a larger misinformation pipeline and ready for live judging demos.

---

## 4) End-to-End Architecture

### Request flow

1. Client calls `POST /analyze/source`.
2. API validates URL input.
3. Deep analysis runs in a thread pool with a 12s timeout guard.
4. If deep analysis finishes in time, full result is returned.
5. If timeout occurs, fast fallback scoring is returned with explicit timeout flag.

### Runtime components

- FastAPI application server
- Scoring orchestrator
- Signal analyzers under `axe3/engine/`
- Optional UI file for root route

### API behavior highlights

- `GET /health` returns service liveness and axis.
- `GET /` serves local UI page.
- CORS is open for integration simplicity during demo/hackathon use.

---

## 5) Project Structure and Functionality Map

```
Menacraft-Hackathon/
├── axe3/
│   ├── main.py
│   ├── models.py
│   ├── scorer.py
│   ├── run_server.py
│   ├── data/
│   │   └── iffy.csv
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── domain_age.py
│   │   ├── typosquat.py
│   │   ├── url_structure.py
│   │   ├── https_check.py
│   │   ├── ai_url_reasoner.py
│   │   ├── account_behavior.py
│   │   ├── style_consistency.py
│   │   ├── reel_handle.py
│   │   ├── profile_enrichment.py
│   │   └── bad_list.py
│   └── ui/
│       └── index.html
├── benchmark_urls.json
├── benchmark_results.json
├── run_benchmark.py
├── judge_demo.ps1
├── start_axe3.ps1
└── JURY_MASTER_DOCUMENT.md
```

### Functional responsibility per file

- `axe3/main.py`
  - Defines API routes.
  - Runs deep analysis with timeout protection.
  - Falls back to quick scoring mode when needed.

- `axe3/models.py`
  - Request/response schema contracts.
  - Enforces stable payload format for integration.

- `axe3/scorer.py`
  - Core orchestration of all signals.
  - Weighting logic, confidence logic, verdict thresholds.
  - Conservative URL-only behavior and fallback computation.

- `axe3/engine/domain_age.py`
  - WHOIS-based age and registration risk signal.

- `axe3/engine/typosquat.py`
  - Detects brand mimic patterns.

- `axe3/engine/url_structure.py`
  - Scores suspicious URL/TLD/path characteristics.

- `axe3/engine/https_check.py`
  - Transport and SSL posture analysis.

- `axe3/engine/ai_url_reasoner.py`
  - LLM-style URL risk reasoning signal.

- `axe3/engine/account_behavior.py`
  - Optional publisher account credibility signal.

- `axe3/engine/style_consistency.py`
  - Optional text/style consistency signal.

- `axe3/engine/reel_handle.py`
  - Lightweight social handle inference.

- `axe3/engine/profile_enrichment.py`
  - Profile extraction helper logic.

- `axe3/engine/bad_list.py`
  - Known misinformation/bad-list lookup.

- `run_benchmark.py`, `benchmark_urls.json`, `benchmark_results.json`
  - Reproducible evaluation dataset and outputs.

- `judge_demo.ps1`
  - Deterministic short demo script for stage use.

---

## 6) API Contract (Authoritative)

### `POST /analyze/source`

Request body:

```json
{
  "url": "https://example.com",
  "handle": "optional_manual_handle",
  "account": {
    "account_age_days": null,
    "followers_count": null,
    "following_count": null,
    "posts_count": null,
    "verified": null,
    "engagement_rate": null,
    "posting_frequency_per_day": null
  },
  "texts": ["optional recent post text"]
}
```

Response body:

```json
{
  "score": 0,
  "confidence": 0,
  "verdict": "authentic",
  "flags": ["human-readable evidence"],
  "axis": "source"
}
```

Verdict thresholds:

- `score >= 65` => `authentic`
- `40 <= score < 65` => `suspicious`
- `score < 40` => `fake`

### Other endpoints

- `GET /health` -> `{"status":"ok","axis":"source"}`
- `GET /` -> serves `axe3/ui/index.html`

---

## 7) Scoring Model and Signal Weights

Current deep-analysis weighted signals:

- Domain age: 20%
- Typosquat risk: 20%
- URL structure risk: 19%
- HTTPS/SSL check: 16%
- AI URL reasoning: 15%
- Account behavior: 6%
- Style consistency: 4%

Model behavior design choices:

- If only URL evidence is available, scoring is intentionally conservative.
- Missing evidence decreases confidence.
- Multiple critical low signals trigger additional penalties.
- Timeout safeguard can trigger quick mode with explicit fallback flag.

Quick fallback mode uses a reduced signal set and lower confidence output by design.

---

## 8) Confidence Logic (Why Judges Should Trust the Output)

Confidence is not random; it reflects evidence completeness and reliability:

- High confidence when more independent signals are available.
- Lower confidence when account/style signals are missing.
- Additional confidence penalties for unavailable WHOIS or limited enrichment.
- Confidence bounded to safe range (20 to 99).

This prevents overclaiming certainty when data coverage is weak.

---

## 9) Benchmark Evidence (Reproducible)

Dataset:

- 24 labeled URLs in `benchmark_urls.json`
- Classes: authentic, suspicious, fake

Observed result from `benchmark_results.json`:

- Correct: 23 / 24
- Accuracy: 95.8%

Class-level outcomes:

- Authentic: 11/11 correct
- Suspicious: 6/6 correct
- Fake: 6/7 correct

Only mismatch:

- `http://world-news-click-now.xyz`
  - Expected: fake
  - Predicted: suspicious
  - Interpretation: conservative miss, not overconfident authentic

---

## 10) Demo Runbook (Stage-Proof)

### Step 1: Start API

From workspace root:

```powershell
.\.venv\Scripts\python.exe .\axe3\run_server.py
```

### Step 2: Verify health

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health
```

Expected:

```json
{"status":"ok","axis":"source"}
```

### Step 3: Run benchmark (optional evidence block)

```powershell
.\.venv\Scripts\python.exe .\run_benchmark.py
```

### Step 4: Live proof cases (recommended order)

1. Authentic source: `https://bbc.com`
2. Social source: `https://instagram.com/instagram`
3. Fake typosquat: `https://bbc-news-live.com`
4. Suspicious source: `http://suspicious-news.com`
5. Edge input: `8.8.8.8`

### Step 5: Key talking points while showing outputs

- Explain top 1-2 evidence flags.
- Mention confidence meaning (coverage-driven certainty).
- Mention timeout safeguard and fallback resilience.
- Close with benchmark accuracy and confusion profile.

---

## 11) Claims You Can Safely Make to Jury

Use these exact claim styles:

- "95.8% accuracy on our internal 24-URL labeled benchmark set."
- "Every prediction includes explainable evidence flags."
- "Confidence decreases when evidence coverage is partial."
- "API remains responsive through timeout watchdog and fast fallback mode."

Avoid making unsupported claims such as universal internet-scale accuracy.

---

## 12) Risk and Limitation Disclosure

Known limitations:

- Social platform access constraints can limit profile enrichment depth.
- WHOIS data quality varies by registrar/TLD.
- No persistence/caching layer in current demo version.
- Calibration can be improved with larger external benchmark datasets.

These are disclosed explicitly to maintain technical honesty.

---

## 13) Why This Is Jury-Ready

This project is jury-ready because it balances:

- Performance (fast enough for live use)
- Explainability (flags + confidence)
- Reliability (fallback safeguards)
- Reproducibility (benchmark files and scripts)
- Practical integration (clean API contract)

It is not a fragile prototype; it is a demonstrable, structured engine with clear behavior under normal and degraded conditions.

---

## 14) One-Page Closing Statement

ClipTrust Axe 3 provides a transparent source credibility score for links and social sources using multi-signal analysis, confidence-aware outputs, and resilient API behavior.
On a labeled 24-URL benchmark, it reaches 95.8% accuracy while preserving explainability and conservative handling of uncertainty.
This makes it suitable for real-time source-risk triage in misinformation defense workflows.
