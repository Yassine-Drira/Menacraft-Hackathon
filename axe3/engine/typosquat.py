import re
from difflib import SequenceMatcher

import tldextract

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())

KNOWN_BRANDS = [
    "bbc", "cnn", "reuters", "apnews", "aljazeera", "theguardian",
    "nytimes", "washingtonpost", "lemonde", "lefigaro", "franceinfo",
    "euronews", "dw", "france24", "sky", "nbcnews", "abcnews",
    "cbsnews", "foxnews", "huffpost", "buzzfeed", "vice", "vox",
    "theatlantic", "economist", "forbes", "businessinsider",
    "techcrunch", "wired", "politico"
]

SUSPICIOUS_TOKENS = {
    "breaking", "live", "update", "today", "now", "official", "media",
    "news", "report", "alerts", "channel", "feed", "world", "global",
    "secure", "verify", "support", "login", "help", "service", "promo",
}


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + cost,
            ))
        prev = curr
    return prev[-1]


def _best_brand_match(domain_name: str):
    compact = re.sub(r"[^a-z0-9]", "", domain_name)
    tokens = [t for t in re.split(r"[-_.]", domain_name) if t]

    best_brand = None
    best_score = 0.0
    for brand in KNOWN_BRANDS:
        scores = [_similarity(domain_name, brand), _similarity(compact, brand)]
        if tokens:
            scores.append(max(_similarity(t, brand) for t in tokens))
        candidate = max(scores)
        if candidate > best_score:
            best_score = candidate
            best_brand = brand

    return best_brand, best_score, tokens, compact


def analyze(url: str) -> dict:
    extracted = _EXTRACT(url)
    domain_name = extracted.domain.lower()

    if not domain_name:
        return {"sub_score": 50, "flag": None}

    if domain_name in KNOWN_BRANDS:
        return {"sub_score": 100, "flag": None}

    best_brand, best_score, tokens, compact = _best_brand_match(domain_name)

    strong_brand_cue = False
    if best_brand:
        if best_brand in compact:
            strong_brand_cue = True
        elif domain_name.startswith(best_brand) or domain_name.endswith(best_brand):
            strong_brand_cue = True
        elif any(t == best_brand for t in tokens):
            strong_brand_cue = True

    if not best_brand:
        return {"sub_score": 100, "flag": None}

    other_tokens = [t for t in tokens if t != best_brand]
    has_suspicious_token = any(t in SUSPICIOUS_TOKENS for t in other_tokens)
    compact_distance = _levenshtein_distance(compact, best_brand)

    # High-risk: one-edit brand copy (e.g., bbbc, reuterz) or brand+sensational token.
    if (compact_distance == 1 and abs(len(compact) - len(best_brand)) <= 1 and best_score >= 0.80) or (
        strong_brand_cue and has_suspicious_token and best_score >= 0.78
    ):
        return {
            "sub_score": 0,
            "flag": (
                f"Domain '{domain_name}' strongly mimics known brand '{best_brand}' "
                f"(similarity {int(best_score * 100)}%)"
            ),
        }

    # Medium risk: looks similar but weaker evidence than hard typosquat.
    if strong_brand_cue and best_score >= 0.74:
        return {
            "sub_score": 35,
            "flag": (
                f"Domain '{domain_name}' appears brand-like to '{best_brand}' "
                f"(similarity {int(best_score * 100)}%)"
            ),
        }

    return {"sub_score": 100, "flag": None}
