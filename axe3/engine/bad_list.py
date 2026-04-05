import os

import pandas as pd
import tldextract

_DOMAINS = None
_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())


def _load_domains():
    global _DOMAINS
    if _DOMAINS is not None:
        return _DOMAINS

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "iffy.csv")

    try:
        df = pd.read_csv(csv_path, usecols=[0], header=0, names=["domain"])
        df["domain"] = df["domain"].astype(str).str.lower().str.strip()
        _DOMAINS = set(d for d in df["domain"].tolist() if d and d != "nan")
    except Exception:
        _DOMAINS = set()

    return _DOMAINS


def analyze(url: str) -> dict:
    domains = _load_domains()
    extracted = _EXTRACT(url)

    if not extracted.domain or not extracted.suffix:
        return {"sub_score": 100, "flag": None}

    domain = f"{extracted.domain}.{extracted.suffix}".lower()

    if domain in domains:
        return {
            "sub_score": 0,
            "flag": f"Domain '{domain}' is listed in iffy.news misinformation database",
        }

    return {"sub_score": 100, "flag": None}
