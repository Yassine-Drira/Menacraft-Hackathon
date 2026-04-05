# Menacraft-Hackathon
ClipTrust — Axe 3: Source Credibility Engine
PRD complet — Sprint 7h solo — $0.00

Business refinement (v2):
The engine must evaluate the credibility of the publisher account behind a social reel, not only the URL/domain itself.
For a reel URL (Instagram/TikTok/X), the engine should attempt to infer the publisher handle, scrape public profile statistics where possible, and include account-level risk in the final source score.

What you are building
One sentence: given a reel URL or social account handle, return a trust score 0–100 with specific human-readable reasons covering domain risk and publisher-profile credibility.
Your module is one of three engines inside ClipTrust. The other two devs handle deepfake detection and caption consistency. You handle the source. At H6 you expose one clean FastAPI endpoint. At H7 the three modules are assembled into one unified verdict by Dev C.

The contract with the other devs
Your endpoint returns exactly this JSON, nothing more, nothing less:
json{
  "score": 34,
  "verdict": "suspicious",
  "flags": [
    "Domain created 12 days ago",
    "Domain mimics known brand: bbc-news-today.com vs bbc.com",
    "Listed in iffy.news misinformation database",
    "No HTTPS — plain HTTP in 2025"
  ],
  "axis": "source"
}
verdict is one of three values only: authentic, suspicious, fake.
score is 0–100. Below 40 = fake. 40–65 = suspicious. Above 65 = authentic.

Input contract refinement (v2):
POST body must always accept `url` and may accept optional enrichment payload:
json{
    "url": "https://www.instagram.com/reel/....",
    "handle": "optional_manual_handle",
    "account": {
        "account_age_days": 120,
        "followers_count": 12000,
        "following_count": 450,
        "posts_count": 380,
        "verified": false,
        "engagement_rate": 0.04,
        "posting_frequency_per_day": 3.1
    },
    "texts": ["recent caption 1", "recent caption 2", "recent caption 3"]
}
If optional fields are missing, engine tries to enrich from public profile scraping.

Stack — 100% free, 100% local, zero API key
python-whois        domain age + registrar info
tldextract          clean domain extraction from any URL
difflib             typosquatting detection (string similarity)
requests            HTTP/HTTPS check + headers
ssl                 certificate validation
pandas              iffy.news CSV lookup
re                  URL pattern analysis
FastAPI             your endpoint
uvicorn             local server
Install everything:
bashpip install fastapi uvicorn python-whois tldextract requests pandas
Download the free misinformation database (one time, no account needed):
bashcurl -o iffy.csv https://iffy.news/iffy-plus/iffy-plus.csv

Project structure
axe3/
├── main.py              ← FastAPI app + /analyze/source endpoint
├── engine/
│   ├── __init__.py
│   ├── domain_age.py    ← Signal 1
│   ├── typosquat.py     ← Signal 2
│   ├── url_structure.py ← Signal 3
│   ├── https_check.py   ← Signal 4
│   └── bad_list.py      ← Signal 5
│   ├── account_behavior.py   ← Signal 6 (publisher profile heuristics)
│   ├── style_consistency.py  ← Signal 7 (publisher text consistency)
│   └── profile_enrichment.py ← social URL -> handle/profile/text enrichment
├── data/
│   └── iffy.csv         ← free bad-domain list
├── scorer.py            ← aggregates 5 signals into final score
└── models.py            ← Pydantic input/output models

The 5 signals — full implementation
Signal 1 — Domain Age (weight 25%)
What it detects: Fake sites are born yesterday. A domain under 30 days old is a red flag. Under 1 year is a warning. Legit news sources have been around for years.
Score logic:

Domain age > 5 years → 100
Domain age 1–5 years → 75
Domain age 6–12 months → 50
Domain age 1–6 months → 25
Domain age < 30 days → 0

python# engine/domain_age.py
import whois
from datetime import datetime, timezone

def analyze(domain: str) -> dict:
    try:
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation is None:
            return {"sub_score": 20, "flag": "Domain registration date unavailable"}
        
        if creation.tzinfo is None:
            creation = creation.replace(tzinfo=timezone.utc)
        
        age_days = (datetime.now(timezone.utc) - creation).days
        
        if age_days < 30:
            return {"sub_score": 0, "flag": f"Domain created {age_days} days ago"}
        elif age_days < 180:
            return {"sub_score": 25, "flag": f"Domain only {age_days // 30} months old"}
        elif age_days < 365:
            return {"sub_score": 50, "flag": None}
        elif age_days < 1825:
            return {"sub_score": 75, "flag": None}
        else:
            return {"sub_score": 100, "flag": None}
    except Exception:
        return {"sub_score": 20, "flag": "Could not retrieve domain WHOIS data"}

Signal 2 — Typosquatting Detection (weight 25%)
What it detects: Fake sites copy the name of trusted brands with tiny variations. bbc-news.info, cnn-breaking.com, reuter5.com. You compare the input domain against a hardcoded list of 30 known legitimate news brands using Levenshtein distance. Distance ≤ 2 with a different domain = red flag.
Score logic:

No similarity to any known brand → 100
Similar but not identical (distance 1–2) → 0 + flag naming the brand it mimics
Exact match to known brand → 100 (it IS the real brand)

python# engine/typosquat.py
import tldextract
from difflib import SequenceMatcher

KNOWN_BRANDS = [
    "bbc", "cnn", "reuters", "apnews", "aljazeera", "theguardian",
    "nytimes", "washingtonpost", "lemonde", "lefigaro", "franceinfo",
    "euronews", "dw", "france24", "sky", "nbcnews", "abcnews",
    "cbsnews", "foxnews", "huffpost", "buzzfeed", "vice", "vox",
    "theatlantic", "economist", "forbes", "businessinsider",
    "techcrunch", "wired", "politico"
]

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def analyze(url: str) -> dict:
    extracted = tldextract.extract(url)
    domain_name = extracted.domain.lower()
    
    # Exact match = real brand, safe
    if domain_name in KNOWN_BRANDS:
        return {"sub_score": 100, "flag": None}
    
    # Check similarity against all known brands
    for brand in KNOWN_BRANDS:
        sim = similarity(domain_name, brand)
        if sim >= 0.75 and domain_name != brand:
            return {
                "sub_score": 0,
                "flag": f"Domain '{domain_name}' mimics known brand '{brand}' (similarity {int(sim*100)}%)"
            }
    
    return {"sub_score": 100, "flag": None}

Signal 3 — URL Structure Analysis (weight 20%)
What it detects: Fake news sites have patterns in their URLs that real outlets don't. Excessive subdomains, suspicious TLDs (.xyz .click .info .top .online), clickbait path keywords, excessive hyphens in the domain name.
Score logic: Each red flag deducts points from 100. Minimum 0.
python# engine/url_structure.py
import tldextract
import re

SUSPICIOUS_TLDS = {".xyz", ".click", ".info", ".top", ".online", ".site",
                   ".club", ".win", ".loan", ".download", ".stream", ".gq",
                   ".tk", ".ml", ".cf", ".ga"}

CLICKBAIT_KEYWORDS = ["breaking", "viral", "shocking", "exposed", "truth",
                      "secret", "leaked", "urgent", "alert", "banned",
                      "censored", "real-news", "uncensored"]

def analyze(url: str) -> dict:
    flags = []
    score = 100
    
    extracted = tldextract.extract(url)
    domain = extracted.domain.lower()
    suffix = "." + extracted.suffix.lower()
    subdomain = extracted.subdomain.lower()
    
    # Suspicious TLD
    if suffix in SUSPICIOUS_TLDS:
        score -= 40
        flags.append(f"Suspicious TLD: {suffix}")
    
    # Excessive hyphens in domain (real brands don't do bbc-news-today-live)
    hyphen_count = domain.count("-")
    if hyphen_count >= 2:
        score -= 25
        flags.append(f"Suspicious domain: {hyphen_count} hyphens in domain name")
    elif hyphen_count == 1:
        score -= 10
    
    # Excessive subdomains
    if subdomain and subdomain not in ("www", "m", "mobile"):
        sub_parts = subdomain.split(".")
        if len(sub_parts) > 1:
            score -= 20
            flags.append(f"Unusual subdomain structure: {subdomain}")
    
    # Clickbait keywords in the full URL
    url_lower = url.lower()
    found_kw = [kw for kw in CLICKBAIT_KEYWORDS if kw in url_lower]
    if found_kw:
        score -= 20
        flags.append(f"Clickbait keywords in URL: {', '.join(found_kw[:2])}")
    
    # Numbers replacing letters (reuter5.com, cnn1.net)
    if re.search(r'[a-z]\d|\d[a-z]', domain):
        score -= 15
        flags.append("Numbers mixed into domain name (e.g. reuter5)")
    
    main_flag = flags[0] if flags else None
    return {"sub_score": max(0, score), "flag": main_flag, "all_flags": flags}

Signal 4 — HTTPS and Certificate Check (weight 15%)
What it detects: Every legitimate news source uses HTTPS with a valid certificate in 2025. Plain HTTP = immediate red flag. A self-signed or expired SSL certificate is also suspicious.
python# engine/https_check.py
import requests
import ssl
import socket
from datetime import datetime

def analyze(url: str) -> dict:
    # Check if URL uses HTTP instead of HTTPS
    if url.startswith("http://"):
        return {"sub_score": 0, "flag": "Site uses plain HTTP, no encryption"}
    
    try:
        # Try HTTPS connection with a short timeout
        response = requests.get(url, timeout=5, verify=True,
                                 headers={"User-Agent": "Mozilla/5.0"})
        
        # Check for too many redirects (often signals shady setup)
        if len(response.history) > 4:
            return {"sub_score": 40, "flag": f"Excessive redirects ({len(response.history)}) before reaching final URL"}
        
        return {"sub_score": 100, "flag": None}
    
    except requests.exceptions.SSLError:
        return {"sub_score": 10, "flag": "Invalid or self-signed SSL certificate"}
    
    except requests.exceptions.ConnectionError:
        return {"sub_score": 20, "flag": "Could not connect to domain"}
    
    except requests.exceptions.Timeout:
        return {"sub_score": 30, "flag": "Domain timed out (may be down or blocking)"}
    
    except Exception as e:
        return {"sub_score": 30, "flag": "HTTPS check failed"}

Signal 5 — Known Bad Domain List (weight 15%)
What it detects: iffy.news maintains a free, downloadable CSV of domains with a history of publishing misinformation, propaganda, or manipulated content. No API. Just a CSV you query locally.
python# engine/bad_list.py
import pandas as pd
import tldextract
import os

_df = None

def _load():
    global _df
    if _df is None:
        csv_path = os.path.join(os.path.dirname(__file__), "../data/iffy.csv")
        try:
            _df = pd.read_csv(csv_path, usecols=[0], header=0, names=["domain"])
            _df["domain"] = _df["domain"].str.lower().str.strip()
        except Exception:
            _df = pd.DataFrame({"domain": []})
    return _df

def analyze(url: str) -> dict:
    df = _load()
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}".lower()
    
    if domain in df["domain"].values:
        return {
            "sub_score": 0,
            "flag": f"Domain '{domain}' is listed in iffy.news misinformation database"
        }
    
    return {"sub_score": 100, "flag": None}

Signal 6 — Account Behavior Heuristics (business critical)
What it detects: suspicious publisher behavior such as very new account, abnormal follower/following ratio, low post history, bot-like posting frequency, synthetic handle patterns.

Signal 7 — Writing Style Consistency (business critical)
What it detects: inconsistency or manipulation signs across the publisher's recent captions/posts (stylometric drift and sensational wording spikes).

Social enrichment layer
When `url` is from Instagram/TikTok/X and optional account fields are not provided:
- infer handle from URL/page
- scrape public profile metadata when available
- extract recent text snippets when available
- feed results into Signal 6 and Signal 7
- if scraping fails, keep service stable and emit informative flags

Scorer — aggregates all 5 signals
python# scorer.py
from engine import domain_age, typosquat, url_structure, https_check, bad_list

WEIGHTS = {
    "domain_age":    0.25,
    "typosquat":     0.25,
    "url_structure": 0.20,
    "https_check":   0.15,
    "bad_list":      0.15,
}

def compute(url: str) -> dict:
    results = {
        "domain_age":    domain_age.analyze(url),
        "typosquat":     typosquat.analyze(url),
        "url_structure": url_structure.analyze(url),
        "https_check":   https_check.analyze(url),
        "bad_list":      bad_list.analyze(url),
    }
    
    # Weighted average
    final_score = sum(
        results[k]["sub_score"] * WEIGHTS[k]
        for k in WEIGHTS
    )
    final_score = round(final_score)
    
    # Collect all flags (filter None)
    flags = []
    for k in results:
        r = results[k]
        if r.get("flag"):
            flags.append(r["flag"])
        if r.get("all_flags"):
            for f in r["all_flags"][1:]:  # avoid duplicate of main flag
                flags.append(f)
    
    # Verdict
    if final_score >= 65:
        verdict = "authentic"
    elif final_score >= 40:
        verdict = "suspicious"
    else:
        verdict = "fake"
    
    return {
        "score": final_score,
        "verdict": verdict,
        "flags": flags if flags else ["No specific issues detected"],
        "axis": "source"
    }

Pydantic models
python# models.py
from pydantic import BaseModel
from typing import List

class SourceRequest(BaseModel):
    url: str

class SourceResponse(BaseModel):
    score: int
    verdict: str
    flags: List[str]
    axis: str

FastAPI endpoint — main.py
python# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import SourceRequest, SourceResponse
from scorer import compute

app = FastAPI(title="ClipTrust — Source Credibility Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze/source", response_model=SourceResponse)
def analyze_source(req: SourceRequest):
    if not req.url or len(req.url) < 4:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        result = compute(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "axis": "source"}
Run it:
bashuvicorn main:app --reload --port 8002
Test it immediately in your browser: http://localhost:8002/docs

Your 7-hour timeline
H0:00 – H0:30   Setup
                pip install everything
                download iffy.csv
                create folder structure
                git init

H0:30 – H1:30   Signal 1 + 2
                implement domain_age.py
                implement typosquat.py
                test both with 3 real URLs in a Python REPL

H1:30 – H2:30   Signal 3 + 4
                implement url_structure.py
                implement https_check.py
                test with HTTP-only sites and suspicious TLDs

H2:30 – H3:00   Signal 5
                download iffy.csv
                implement bad_list.py
                verify a known bad domain returns score 0

H3:00 – H4:00   Scorer + models
                implement scorer.py
                implement models.py
                test the full pipeline end-to-end in Python
                print results for 5 different URLs

H4:00 – H5:00   FastAPI endpoint
                implement main.py
                run uvicorn
                test /analyze/source via Swagger UI at /docs
                fix edge cases (timeouts, empty input, bad URL)

H5:00 – H6:00   Robustness
                add try/except everywhere
                add timeout=5 to all network calls
                handle edge cases: no http prefix, IP addresses, localhost
                make sure the server never crashes on bad input

H6:00 – H6:30   Sync with team
                send your JSON schema to Dev C
                confirm port 8002
                test with their aggregator endpoint

H6:30 – H7:00   Demo prep
                prepare 4 URLs to demo live:
                  1. bbc.com              → score ~90, authentic
                  2. bbc-news-today.xyz   → score ~5, fake
                  3. reuters.com          → score ~95, authentic
                  4. domain from iffy.csv → score 0, fake

The 4 demo URLs to prepare
URLExpected verdictKey flag shownhttps://bbc.comauthentic ~92No issueshttps://bbc-breaking-news.xyzfake ~8Mimics BBC + suspicious TLDhttps://reuters.comauthentic ~95No issuesany domain from iffy.csvfake ~0Listed in misinformation database
These four cases cover every signal. Your demo takes 60 seconds and the jury sees every feature fire.

Edge cases to handle before H6
python# Add this at the top of scorer.py before calling any engine

import re

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

Input has no https:// prefix → add it before analysis
Input is an IP address → return score 30, flag "Direct IP address, no domain name"
WHOIS lookup times out → return sub_score 20, flag "WHOIS unavailable"
iffy.csv not found → skip signal 5, don't crash
URL is a social media link (instagram.com/...) → extract the base domain and score that


What makes this impressive to the jury
The jury will not see three separate tools. They will see one ClipTrust interface where they paste a reel URL. Behind the scenes your engine fires. What they notice:
The score is not random. When you test bbc-breaking-today.xyz live, the score drops to near zero and the flags say exactly why — domain 6 days old, mimics BBC at 82% similarity, suspicious TLD, listed in database. Four specific reasons. In plain English. In under 2 seconds.
That is what wins. Not the algorithm. The explanation.

Files checklist before H6
axe3/
├── main.py                ✅ FastAPI running on port 8002
├── scorer.py              ✅ returns correct JSON contract
├── models.py              ✅ Pydantic models
├── engine/
│   ├── __init__.py        ✅ empty file
│   ├── domain_age.py      ✅ tested
│   ├── typosquat.py       ✅ tested
│   ├── url_structure.py   ✅ tested
│   ├── https_check.py     ✅ tested
│   └── bad_list.py        ✅ tested
└── data/
    └── iffy.csv           ✅ downloaded
One command to verify everything works before you call it done:
bashcurl -X POST http://localhost:8002/analyze/source \
  -H "Content-Type: application/json" \
  -d '{"url": "https://bbc-breaking-news.xyz"}'
Expected response:
json{
  "score": 8,
  "verdict": "fake",
  "flags": [
    "Domain created 6 days ago",
    "Domain 'bbc-breaking-news' mimics known brand 'bbc' (similarity 87%)",
    "Suspicious TLD: .xyz",
    "Suspicious domain: 2 hyphens in domain name"
  ],
  "axis": "source"
}
If you see that, you are done. Ship it.