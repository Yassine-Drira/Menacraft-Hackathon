import math
import re


def _features(text: str) -> dict:
    words = re.findall(r"[a-zA-Z']+", text)
    word_count = max(1, len(words))
    sentences = max(1, len(re.findall(r"[.!?]", text)))
    avg_sentence_len = word_count / sentences

    upper_chars = sum(1 for c in text if c.isupper())
    alpha_chars = max(1, sum(1 for c in text if c.isalpha()))
    upper_ratio = upper_chars / alpha_chars

    punct_count = len(re.findall(r"[!?.,;:]", text))
    punct_ratio = punct_count / max(1, len(text))

    vocab_richness = len(set(w.lower() for w in words)) / word_count

    return {
        "avg_sentence_len": avg_sentence_len,
        "upper_ratio": upper_ratio,
        "punct_ratio": punct_ratio,
        "vocab_richness": vocab_richness,
    }


def _coef_variation(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(var) / mean


def analyze(texts: list[str] | None) -> dict:
    if not texts:
        return {"sub_score": None, "flag": "Writing style unavailable", "available": False}

    cleaned = [t.strip() for t in texts if t and t.strip()]
    if len(cleaned) < 3:
        return {"sub_score": None, "flag": "Need at least 3 texts for style consistency", "available": False}

    feats = [_features(t) for t in cleaned]

    cv_sentence = _coef_variation([f["avg_sentence_len"] for f in feats])
    cv_upper = _coef_variation([f["upper_ratio"] for f in feats])
    cv_punct = _coef_variation([f["punct_ratio"] for f in feats])
    cv_vocab = _coef_variation([f["vocab_richness"] for f in feats])

    score = 100
    flags = []

    if cv_sentence > 0.65:
        score -= 20
        flags.append("Large variation in sentence style across posts")
    elif cv_sentence > 0.4:
        score -= 10

    if cv_upper > 0.9:
        score -= 15
        flags.append("Inconsistent uppercase usage across posts")

    if cv_punct > 0.9:
        score -= 15
        flags.append("Inconsistent punctuation style across posts")

    if cv_vocab > 0.45:
        score -= 10
        flags.append("Vocabulary pattern varies strongly across posts")

    clickbait_hits = 0
    for t in cleaned:
        if re.search(r"\b(shocking|urgent|must see|exposed|truth they hide)\b", t.lower()):
            clickbait_hits += 1
    if clickbait_hits >= max(2, len(cleaned) // 2):
        score -= 12
        flags.append("Frequent sensational wording in sampled texts")

    score = max(0, min(100, score))
    return {
        "sub_score": score,
        "flag": flags[0] if flags else None,
        "all_flags": flags,
        "available": True,
    }
