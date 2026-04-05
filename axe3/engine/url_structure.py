import re

import tldextract

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())

SUSPICIOUS_TLDS = {
    ".xyz", ".click", ".info", ".top", ".online", ".site", ".club", ".win",
    ".loan", ".download", ".stream", ".gq", ".tk", ".ml", ".cf", ".ga"
}

CLICKBAIT_KEYWORDS = [
    "breaking", "viral", "shocking", "exposed", "truth", "secret", "leaked",
    "urgent", "alert", "banned", "censored", "real-news", "uncensored"
]


def analyze(url: str) -> dict:
    flags = []
    score = 100

    extracted = _EXTRACT(url)
    domain = extracted.domain.lower()
    suffix = f".{extracted.suffix.lower()}" if extracted.suffix else ""
    subdomain = extracted.subdomain.lower()

    if suffix in SUSPICIOUS_TLDS:
        score -= 40
        flags.append(f"Suspicious TLD: {suffix}")

    hyphen_count = domain.count("-")
    if hyphen_count >= 2:
        score -= 25
        flags.append(f"Suspicious domain: {hyphen_count} hyphens in domain name")
    elif hyphen_count == 1:
        score -= 10

    if subdomain and subdomain not in ("www", "m", "mobile"):
        sub_parts = subdomain.split(".")
        if len(sub_parts) > 1:
            score -= 20
            flags.append(f"Unusual subdomain structure: {subdomain}")

    url_lower = url.lower()
    found_kw = [kw for kw in CLICKBAIT_KEYWORDS if kw in url_lower]
    if found_kw:
        score -= 20
        flags.append(f"Clickbait keywords in URL: {', '.join(found_kw[:2])}")

    if re.search(r"[a-z]\d|\d[a-z]", domain):
        score -= 15
        flags.append("Numbers mixed into domain name (e.g. reuter5)")

    main_flag = flags[0] if flags else None
    return {"sub_score": max(0, score), "flag": main_flag, "all_flags": flags}
