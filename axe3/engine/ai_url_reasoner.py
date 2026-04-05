import json
import os
import re
import subprocess
import time
from urllib.parse import urlparse

import requests

OLLAMA_API = os.environ.get("OLLAMA_API", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "5.5"))
OLLAMA_NUM_GPU = int(os.environ.get("OLLAMA_NUM_GPU", "0"))

_OLLAMA_DISABLED_UNTIL = 0.0
_OLLAMA_FAILURES = 0


def _clamp_score(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def _extract_json_object(text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _build_prompt(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    query_len = len(parsed.query or "")

    return (
        "You are a cybersecurity and misinformation URL risk analyst. "
        "Given a URL only, estimate source credibility logically using URL signals. "
        "Do not use external blocklists.\n"
        "Return STRICT JSON only with this schema:\n"
        "{\n"
        '  "trust_score": <integer 0-100>,\n'
        '  "risk_level": "low|medium|high",\n'
        '  "reasons": ["short reason 1", "short reason 2"]\n'
        "}\n"
        "Scoring policy:\n"
        "- 0 means highly untrustworthy URL source\n"
        "- 100 means highly trustworthy URL source\n"
        "- suspicious TLDs, typosquat-like naming, long random strings, excessive path/query entropy, and deceptive branding reduce trust\n"
        "- stable brand-like structure and clean URL patterns increase trust\n"
        f"Input URL: {url}\n"
        f"Host: {host}\n"
        f"Path: {path}\n"
        f"QueryLength: {query_len}\n"
    )


def analyze(url: str, timeout: float | None = None) -> dict:
    global _OLLAMA_DISABLED_UNTIL, _OLLAMA_FAILURES

    now = time.time()
    if now < _OLLAMA_DISABLED_UNTIL:
        return {
            "sub_score": None,
            "flag": "AI URL reasoning temporarily disabled after runtime failures",
            "available": False,
        }

    effective_timeout = timeout if timeout is not None else OLLAMA_TIMEOUT
    effective_timeout = max(1.0, float(effective_timeout))

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _build_prompt(url),
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 180,
            "num_gpu": OLLAMA_NUM_GPU,
        },
    }

    def _build_success_result(llm_text: str) -> dict:
        parsed = _extract_json_object(llm_text)
        if not parsed:
            return {
                "sub_score": None,
                "flag": "AI URL reasoning unavailable (invalid model output)",
                "available": False,
            }

        raw_score = parsed.get("trust_score", parsed.get("score", 50))
        try:
            score = _clamp_score(float(raw_score))
        except (TypeError, ValueError):
            score = 50

        reasons = parsed.get("reasons")
        if not isinstance(reasons, list):
            reasons = []

        reasons = [str(r).strip() for r in reasons if str(r).strip()]
        prefixed = [f"AI URL reasoning: {r}" for r in reasons[:3]]

        return {
            "sub_score": score,
            "flag": prefixed[0] if prefixed else None,
            "all_flags": prefixed,
            "available": True,
        }

    try:
        response = requests.post(OLLAMA_API, json=payload, timeout=(1.5, effective_timeout))
        if response.status_code < 400:
            _OLLAMA_FAILURES = 0
            data = response.json() if response.text else {}
            llm_text = (data.get("response") or "").strip()
            return _build_success_result(llm_text)

        # Fallback to local CLI for environments where /api/generate returns server errors.
        try:
            cli = subprocess.run(
                ["ollama", "run", OLLAMA_MODEL, payload["prompt"]],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=max(2.0, effective_timeout + 1.5),
                check=False,
            )
            if cli.returncode == 0 and (cli.stdout or "").strip():
                _OLLAMA_FAILURES = 0
                return _build_success_result(cli.stdout.strip())

            stderr_text = (cli.stderr or "").lower()
            if "unable to allocate cuda" in stderr_text or "error loading model" in stderr_text:
                _OLLAMA_DISABLED_UNTIL = time.time() + 1800
                return {
                    "sub_score": None,
                    "flag": "AI URL reasoning disabled: Ollama model failed to load (GPU memory)",
                    "available": False,
                }
        except Exception:
            pass

        _OLLAMA_FAILURES += 1
        if _OLLAMA_FAILURES >= 2:
            _OLLAMA_DISABLED_UNTIL = time.time() + 300

        return {
            "sub_score": None,
            "flag": f"AI URL reasoning unavailable (Ollama HTTP {response.status_code})",
            "available": False,
        }
    except requests.exceptions.ConnectionError:
        return {
            "sub_score": None,
            "flag": "AI URL reasoning unavailable (Ollama not reachable)",
            "available": False,
        }
    except requests.exceptions.Timeout:
        return {
            "sub_score": None,
            "flag": "AI URL reasoning unavailable (timeout)",
            "available": False,
        }
    except Exception:
        return {
            "sub_score": None,
            "flag": "AI URL reasoning unavailable",
            "available": False,
        }
