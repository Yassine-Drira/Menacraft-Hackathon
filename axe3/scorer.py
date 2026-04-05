import ipaddress
from urllib.parse import urlparse

import tldextract

from engine import (
    ai_url_reasoner,
    account_behavior,
    domain_age,
    https_check,
    reel_handle,
    style_consistency,
    typosquat,
    url_structure,
)

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())

WEIGHTS = {
    "domain_age": 0.20,
    "typosquat": 0.20,
    "url_structure": 0.19,
    "https_check": 0.16,
    "ai_reasoner": 0.15,
    "account_behavior": 0.06,
    "style_consistency": 0.04,
}

TOTAL_SIGNALS = len(WEIGHTS)


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _is_ip_or_localhost(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host == "localhost":
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _to_verdict(score: int) -> str:
    if score >= 65:
        return "authentic"
    if score >= 40:
        return "suspicious"
    return "fake"


def _is_public_domain(url: str) -> bool:
    host = (urlparse(url).hostname or "").strip().lower()
    if not host or "." not in host:
        return False

    extracted = _EXTRACT(url)
    if not extracted.domain or not extracted.suffix:
        return False

    return True


def _weighted_score(results: dict) -> int:
    active = [k for k, v in results.items() if v.get("sub_score") is not None]
    if not active:
        return 0

    total_weight = sum(WEIGHTS[k] for k in active)
    if total_weight <= 0:
        return 0

    value = sum(results[k]["sub_score"] * WEIGHTS[k] for k in active) / total_weight
    return round(value)


def _compute_confidence(
    results: dict,
    available_count: int,
    enrichment: dict,
    account_completeness: int,
) -> int:
    confidence = 92

    # Coverage is the strongest confidence signal.
    missing_signals = max(0, TOTAL_SIGNALS - available_count)
    confidence -= 9 * missing_signals

    if enrichment.get("platform"):
        # Social scraping can be partial; lower certainty if profile fields are sparse.
        if account_completeness < 4:
            confidence -= 4 * (4 - account_completeness)

        if results["style_consistency"].get("sub_score") is None:
            confidence -= 8

    domain_flag = (results["domain_age"].get("flag") or "").lower()
    if "whois unavailable" in domain_flag or "registration date unavailable" in domain_flag:
        confidence -= 6

    for extra_flag in enrichment.get("flags", []):
        lower = extra_flag.lower()
        if "unavailable" in lower or "limited" in lower or "could not" in lower:
            confidence -= 4

    return max(20, min(99, confidence))


def compute(url: str, handle: str | None = None, account: dict | None = None, texts: list[str] | None = None) -> dict:
    normalized = normalize_url(url)

    if not normalized:
        return {
            "score": 0,
            "confidence": 95,
            "verdict": "fake",
            "flags": ["URL is required"],
            "axis": "source",
        }

    if _is_ip_or_localhost(normalized):
        score = 30
        return {
            "score": score,
            "confidence": 95,
            "verdict": _to_verdict(score),
            "flags": ["Direct IP address, no domain name"],
            "axis": "source",
        }

    if not _is_public_domain(normalized):
        return {
            "score": 0,
            "confidence": 96,
            "verdict": "fake",
            "flags": ["Malformed or non-public domain; cannot establish source credibility"],
            "axis": "source",
        }

    # Auto-enrichment is intentionally disabled to avoid added latency.
    enrichment = {"platform": None, "flags": []}
    effective_handle = handle
    effective_account = account
    effective_texts = texts

    # Lightweight publisher inference for social reel URLs (handle-only, short timeout, cached).
    if not effective_handle:
        inferred = reel_handle.infer_handle(normalized, timeout=1.4)
        if inferred.get("handle"):
            effective_handle = inferred["handle"]
        if inferred.get("flag"):
            enrichment["flags"].append(inferred["flag"])

    link_only_mode = not any([effective_handle, effective_account, effective_texts])

    ai_timeout = 5.5 if link_only_mode else 2.5

    results = {
        "domain_age": domain_age.analyze(normalized),
        "typosquat": typosquat.analyze(normalized),
        "url_structure": url_structure.analyze(normalized),
        "https_check": https_check.analyze(normalized),
        "ai_reasoner": ai_url_reasoner.analyze(normalized, timeout=ai_timeout),
        "account_behavior": account_behavior.analyze(effective_account, effective_handle),
        "style_consistency": style_consistency.analyze(effective_texts),
    }

    social_mode = bool(enrichment.get("platform"))
    if social_mode:
        # For social links, account-level evidence is more relevant than platform domain checks.
        for signal in ("domain_age", "typosquat", "url_structure", "ai_reasoner"):
            results[signal]["sub_score"] = None
            results[signal]["flag"] = None
            if "all_flags" in results[signal]:
                results[signal]["all_flags"] = []

    final_score = _weighted_score(results)

    if link_only_mode:
        # Strict standards when only URL evidence is present.
        # Use dynamic uncertainty penalties instead of a hard cap to avoid score flattening.
        url_signal_names = ["domain_age", "typosquat", "url_structure", "https_check", "ai_reasoner"]
        available_url_count = sum(1 for name in url_signal_names if results[name].get("sub_score") is not None)

        # Conservative compression for link-only assessments.
        final_score = round(final_score * 0.78)

        # Missing URL evidence lowers trust confidence and score.
        final_score -= (len(url_signal_names) - available_url_count) * 6

        domain_sub_score = results["domain_age"].get("sub_score") or 0
        domain_flag = (results["domain_age"].get("flag") or "").lower()
        if domain_sub_score <= 25:
            if "created" in domain_flag or "months old" in domain_flag:
                final_score -= 20
            else:
                # WHOIS-unavailable is uncertainty, not direct evidence of fraud.
                final_score -= 6
        if (results["https_check"].get("sub_score") or 0) <= 30:
            final_score -= 25
        if (results["url_structure"].get("sub_score") or 0) <= 70:
            final_score -= 15
        if (results["typosquat"].get("sub_score") or 0) <= 35:
            final_score -= 20
        if (results["ai_reasoner"].get("sub_score") or 100) <= 40:
            final_score -= 20

        if "whois unavailable" in domain_flag or "registration date unavailable" in domain_flag:
            final_score -= 4

        if results["ai_reasoner"].get("sub_score") is None:
            final_score -= 4

        if (results["https_check"].get("sub_score") or 0) <= 20:
            final_score = min(final_score, 20)

    available_count = sum(1 for r in results.values() if r.get("sub_score") is not None)

    account_completeness = 0
    if effective_account:
        expected_fields = [
            "account_age_days",
            "followers_count",
            "following_count",
            "posts_count",
            "verified",
            "engagement_rate",
            "posting_frequency_per_day",
        ]
        account_completeness = sum(1 for f in expected_fields if effective_account.get(f) is not None)

    # Confidence control: keep uncertainty penalties but avoid a single repeated score.
    if available_count <= 5 and final_score >= 65:
        missing_signals = max(0, TOTAL_SIGNALS - available_count)
        confidence_penalty = 2 * missing_signals

        domain_flag = (results["domain_age"].get("flag") or "").lower()
        if "whois unavailable" in domain_flag or "registration date unavailable" in domain_flag:
            confidence_penalty += 2

        if enrichment.get("platform"):
            confidence_penalty += 2

            if results["style_consistency"].get("sub_score") is None:
                confidence_penalty += 2

            if account_completeness < 4:
                confidence_penalty += (4 - account_completeness)

        final_score -= confidence_penalty

    critical_count = 0
    if results["domain_age"].get("sub_score") is not None and results["domain_age"]["sub_score"] <= 25:
        critical_count += 1
    if results["typosquat"].get("sub_score") is not None and results["typosquat"]["sub_score"] == 0:
        critical_count += 1
    if results["url_structure"].get("sub_score") is not None and results["url_structure"]["sub_score"] <= 55:
        critical_count += 1
    if results["https_check"].get("sub_score") is not None and results["https_check"]["sub_score"] <= 30:
        critical_count += 1
    if results["ai_reasoner"].get("sub_score") is not None and results["ai_reasoner"]["sub_score"] <= 30:
        critical_count += 1
    if results["account_behavior"].get("sub_score") is not None and results["account_behavior"]["sub_score"] <= 45:
        critical_count += 1
    if results["style_consistency"].get("sub_score") is not None and results["style_consistency"]["sub_score"] <= 55:
        critical_count += 1

    if critical_count >= 4:
        final_score -= 20
    elif critical_count >= 2:
        final_score -= 10

    final_score = max(0, min(100, final_score))

    flags = []
    for signal_result in results.values():
        if signal_result.get("flag"):
            flags.append(signal_result["flag"])
        if signal_result.get("all_flags"):
            for extra in signal_result["all_flags"][1:]:
                flags.append(extra)

    if available_count <= 5:
        flags.append("Limited evidence: account behavior and style samples were not provided")

    if link_only_mode:
        flags.append("Strict URL-only mode: score is conservative without publisher evidence")

    if available_count >= 6:
        flags.append("High evidence coverage: URL, account behavior, and style consistency analyzed")

    if enrichment.get("platform") and account_completeness < 4:
        flags.append("Partial social profile data only; confidence reduced")

    if social_mode:
        flags.append("Social mode: prioritized account behavior and creator-style evidence")

    for extra_flag in enrichment.get("flags", []):
        if extra_flag not in flags:
            flags.append(extra_flag)

    confidence = _compute_confidence(
        results=results,
        available_count=available_count,
        enrichment=enrichment,
        account_completeness=account_completeness,
    )

    return {
        "score": final_score,
        "confidence": confidence,
        "verdict": _to_verdict(final_score),
        "flags": flags if flags else ["No specific issues detected"],
        "axis": "source",
    }


def quick_compute(url: str) -> dict:
    """Fast fallback mode used when deep analysis exceeds watchdog timeout."""
    normalized = normalize_url(url)

    if not normalized:
        return {
            "score": 0,
            "confidence": 95,
            "verdict": "fake",
            "flags": ["URL is required"],
            "axis": "source",
        }

    if _is_ip_or_localhost(normalized):
        score = 30
        return {
            "score": score,
            "confidence": 95,
            "verdict": _to_verdict(score),
            "flags": [
                "Direct IP address, no domain name",
                "Fast fallback mode used",
            ],
            "axis": "source",
        }

    # Quick mode skips the slowest checks while still using multiple URL signals.
    results = {
        "typosquat": typosquat.analyze(normalized),
        "url_structure": url_structure.analyze(normalized),
        "https_check": https_check.analyze(normalized),
        "ai_reasoner": ai_url_reasoner.analyze(normalized, timeout=1.2),
    }

    weights = {
        "typosquat": 0.30,
        "url_structure": 0.30,
        "https_check": 0.25,
        "ai_reasoner": 0.15,
    }
    active = [k for k in weights if results[k].get("sub_score") is not None]
    if active:
        tw = sum(weights[k] for k in active)
        final_score = round(sum(results[k]["sub_score"] * weights[k] for k in active) / tw)
    else:
        final_score = 0
    final_score = max(0, min(100, final_score))

    flags = []
    for signal_result in results.values():
        if signal_result.get("flag"):
            flags.append(signal_result["flag"])
        if signal_result.get("all_flags"):
            for extra in signal_result["all_flags"][1:]:
                flags.append(extra)

    flags.append("Fast fallback mode: deep analysis timeout safeguard triggered")

    return {
        "score": final_score,
        "confidence": 48,
        "verdict": _to_verdict(final_score),
        "flags": flags if flags else ["Fast fallback mode used"],
        "axis": "source",
    }
