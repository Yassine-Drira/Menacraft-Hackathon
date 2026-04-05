import ipaddress
from urllib.parse import urlparse

from engine import (
    account_behavior,
    bad_list,
    domain_age,
    https_check,
    profile_enrichment,
    style_consistency,
    typosquat,
    url_structure,
)

WEIGHTS = {
    "domain_age": 0.18,
    "typosquat": 0.17,
    "url_structure": 0.15,
    "https_check": 0.12,
    "bad_list": 0.18,
    "account_behavior": 0.12,
    "style_consistency": 0.08,
}


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
    missing_signals = max(0, 7 - available_count)
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

    enrichment = profile_enrichment.enrich(normalized, handle=handle)
    effective_handle = handle or enrichment.get("handle")
    effective_account = account or enrichment.get("account")
    effective_texts = texts or enrichment.get("texts")

    results = {
        "domain_age": domain_age.analyze(normalized),
        "typosquat": typosquat.analyze(normalized),
        "url_structure": url_structure.analyze(normalized),
        "https_check": https_check.analyze(normalized),
        "bad_list": bad_list.analyze(normalized),
        "account_behavior": account_behavior.analyze(effective_account, effective_handle),
        "style_consistency": style_consistency.analyze(effective_texts),
    }

    social_mode = bool(enrichment.get("platform"))
    if social_mode:
        # For social links, account-level evidence is more relevant than platform domain checks.
        for signal in ("domain_age", "typosquat", "url_structure", "bad_list"):
            results[signal]["sub_score"] = None
            results[signal]["flag"] = None
            if "all_flags" in results[signal]:
                results[signal]["all_flags"] = []

    # Known misinformation domains remain an immediate fail.
    if results["bad_list"]["sub_score"] == 0:
        final_score = 0
    else:
        final_score = _weighted_score(results)

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
        missing_signals = max(0, 7 - available_count)
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
    if results["bad_list"].get("sub_score") is not None and results["bad_list"]["sub_score"] == 0:
        critical_count += 1
    if results["account_behavior"].get("sub_score") is not None and results["account_behavior"]["sub_score"] <= 45:
        critical_count += 1
    if results["style_consistency"].get("sub_score") is not None and results["style_consistency"]["sub_score"] <= 55:
        critical_count += 1

    if critical_count >= 5:
        final_score -= 20
    elif critical_count >= 3:
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

    if available_count >= 7:
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

    # Quick mode skips slow external enrichments (WHOIS/profile scraping/bad-list IO).
    results = {
        "typosquat": typosquat.analyze(normalized),
        "url_structure": url_structure.analyze(normalized),
        "https_check": https_check.analyze(normalized),
    }

    weights = {
        "typosquat": 0.35,
        "url_structure": 0.35,
        "https_check": 0.30,
    }
    final_score = round(sum(results[k]["sub_score"] * weights[k] for k in weights))
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
