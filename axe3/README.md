# ClipTrust Axe 3 - Source Credibility Engine

This module analyzes a source URL and returns a credibility result for the `source` axis.

## What this service does

Input:
- Required: URL (example: `https://bbc.com`)
- Optional: social handle, account heuristics, and recent texts for style consistency checks

Output:
- `score` (0-100)
- `confidence` (0-100)
- `verdict` (`authentic`, `suspicious`, `fake`)
- `flags` (human-readable reasons)
- `axis` (`source`)

Example output:

```json
{
  "score": 34,
  "confidence": 71,
  "verdict": "suspicious",
  "flags": [
    "Domain created 12 days ago",
    "Domain 'bbc-news-today' mimics known brand 'bbc' (similarity 87%)",
    "Domain 'example.com' is listed in iffy.news misinformation database",
    "No HTTPS - plain HTTP in 2025"
  ],
  "axis": "source"
}
```

## Project structure

- `main.py` - FastAPI app and routes
- `models.py` - request/response models
- `scorer.py` - runs all signals, applies weights, builds final response
- `engine/domain_age.py` - Signal 1 (domain age)
- `engine/typosquat.py` - Signal 2 (brand mimic detection)
- `engine/url_structure.py` - Signal 3 (suspicious URL patterns)
- `engine/https_check.py` - Signal 4 (HTTPS/SSL/connectivity)
- `engine/bad_list.py` - Signal 5 (iffy bad-domain lookup)
- `engine/account_behavior.py` - Signal 6 (account behavior heuristics)
- `engine/style_consistency.py` - Signal 7 (writing style consistency heuristics)
- `data/iffy.csv` - local misinformation domain dataset

## Scoring model

Signal weights:
- Domain age: 18%
- Typosquat: 17%
- URL structure: 15%
- HTTPS check: 12%
- Bad-list: 18%
- Account behavior: 12%
- Style consistency: 8%

Verdict thresholds:
- `score >= 65` -> `authentic`
- `40 <= score < 65` -> `suspicious`
- `score < 40` -> `fake`

Special rule:
- If domain is found in `data/iffy.csv`, score is forced to `0`.

Anti-overfitting behavior:
- If only URL/domain signals are available (no account and no text samples), the engine adds an uncertainty penalty and a limitation flag.
- This prevents overconfident scores from limited evidence.

## Signals explained

1) Domain age (`engine/domain_age.py`)
- Very recent domains are high risk.
- WHOIS failures are handled safely (service does not crash).

2) Typosquatting (`engine/typosquat.py`)
- Detects domains that mimic known media brands.
- Exact known brand match is treated as safe for this signal.

3) URL structure (`engine/url_structure.py`)
- Penalizes suspicious TLDs (`.xyz`, `.click`, ...), clickbait words, unusual subdomains, and mixed letters/numbers.

4) HTTPS and SSL (`engine/https_check.py`)
- Plain HTTP gets a major penalty.
- SSL errors, timeouts, and connection failures are penalized and flagged.

5) Known bad domains (`engine/bad_list.py`)
- Checks base domain against local `iffy.csv`.

6) Account behavior (`engine/account_behavior.py`)
- Evaluates profile age, follower/following ratio, posting history, engagement anomalies, posting frequency, and suspicious handle patterns.

7) Writing style consistency (`engine/style_consistency.py`)
- Uses stylometric heuristics across multiple texts to detect inconsistent author style and recurring sensational language.

## API contract

### POST `/analyze/source`

Request body:

```json
{
  "url": "https://bbc.com",
  "handle": "bbc",
  "account": {
    "account_age_days": 6200,
    "followers_count": 56000000,
    "following_count": 120,
    "posts_count": 220000,
    "verified": true,
    "engagement_rate": 0.015,
    "posting_frequency_per_day": 18
  },
  "texts": [
    "Breaking: Parliament votes on emergency bill after long debate.",
    "Live update: Officials confirm timeline and publish full report.",
    "Analysis: Markets react as central bank signals cautious stance."
  ]
}
```

Response body:

```json
{
  "score": 100,
  "confidence": 95,
  "verdict": "authentic",
  "flags": ["No specific issues detected"],
  "axis": "source"
}
```

### GET `/health`

Response body:

```json
{
  "status": "ok",
  "axis": "source"
}
```

## Run locally (Windows PowerShell)

Recommended single command (stable demo path):

```powershell
Set-Location "C:/Users/yassi/Menacraft-Hackathon"
./start_axe3.ps1
```

This starts the backend with the project venv and avoids interpreter mismatch.

From repository root:

```powershell
Set-Location "C:/Users/yassi/Menacraft-Hackathon"
```

If using local venv:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi uvicorn python-whois tldextract requests pandas
Set-Location "./axe3"
python -m uvicorn main:app --port 8002
```

If using system Python directly:

```powershell
Set-Location "C:/Users/yassi/Menacraft-Hackathon/axe3"
C:/Users/yassi/AppData/Local/Programs/Python/Python310/python.exe -m pip install fastapi uvicorn python-whois tldextract requests pandas
C:/Users/yassi/AppData/Local/Programs/Python/Python310/python.exe -m uvicorn main:app --port 8002
```

Swagger docs:
- `http://127.0.0.1:8002/docs`

## Quick test commands

Health check:

```powershell
Invoke-RestMethod "http://127.0.0.1:8002/health" | ConvertTo-Json
```

Single analyze call:

```powershell
$body = @{ url = "https://bbc.com" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/analyze/source" -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
```

Batch demo:

```powershell
$base='http://127.0.0.1:8002/analyze/source'
$tests=@('https://bbc.com','https://bbc-breaking-news.xyz','https://reuters.com','https://100percentfedup.com','8.8.8.8')
foreach($u in $tests){
  Write-Output "URL: $u"
  $body = @{ url = $u } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri $base -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6
  Write-Output '---'
}
```

High-evidence analyze call (recommended for better accuracy):

```powershell
$payload = @{
  url = 'https://bbc.com'
  handle = 'bbc'
  account = @{
    account_age_days = 6200
    followers_count = 56000000
    following_count = 120
    posts_count = 220000
    verified = $true
    engagement_rate = 0.015
    posting_frequency_per_day = 18
  }
  texts = @(
    'Breaking: Parliament votes on emergency bill after long debate.',
    'Live update: Officials confirm timeline and publish full report.',
    'Analysis: Markets react as central bank signals cautious stance.'
  )
}
$body = $payload | ConvertTo-Json -Depth 8
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/analyze/source" -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8
```

## Edge cases handled

- Missing scheme (`bbc.com`) -> normalized to `https://bbc.com`
- IP/localhost input -> returns score 30 + explicit flag
- WHOIS unavailable -> safe fallback sub-score and flag
- Missing/invalid `iffy.csv` -> does not crash
- Social URLs -> base domain is extracted and analyzed

## Troubleshooting

1) Error: `No module named uvicorn`
- You are running with a different Python interpreter than the one where packages were installed.
- Install dependencies with the same interpreter you use to launch `uvicorn`.

2) Port 8002 already in use
- Stop the existing process or run with another port:

```powershell
python -m uvicorn main:app --port 8003
```

3) Dataset URL changes over time
- Replace `data/iffy.csv` with the latest exported file.
- Service remains stable even if this file fails to load.

## Integration handoff (Dev C)

Endpoint:
- `POST http://localhost:8002/analyze/source`

Guaranteed response schema:

```json
{
  "score": 0,
  "verdict": "fake",
  "flags": ["..."],
  "axis": "source"
}
```
