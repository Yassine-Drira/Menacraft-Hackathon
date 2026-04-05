from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import tldextract
import whois

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())
_WHOIS_POOL = ThreadPoolExecutor(max_workers=12)


def _whois_lookup(domain: str):
    return whois.whois(domain)


def _safe_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        txt = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(txt)
        except ValueError:
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(txt[:19], fmt)
                except ValueError:
                    continue
    return None


def analyze(url: str) -> dict:
    try:
        extracted = _EXTRACT(url)
        if not extracted.domain or not extracted.suffix:
            return {"sub_score": 20, "flag": "Domain registration date unavailable"}

        domain = f"{extracted.domain}.{extracted.suffix}".lower()

        future = _WHOIS_POOL.submit(_whois_lookup, domain)
        try:
            w = future.result(timeout=3.5)
        except FutureTimeoutError:
            return {"sub_score": 20, "flag": "WHOIS unavailable (timeout)"}

        creation = w.creation_date

        if isinstance(creation, list):
            creation = creation[0] if creation else None

        creation = _safe_datetime(creation)
        if creation is None:
            return {"sub_score": 20, "flag": "Domain registration date unavailable"}

        if creation.tzinfo is None:
            creation = creation.replace(tzinfo=timezone.utc)

        age_days = (datetime.now(timezone.utc) - creation).days

        if age_days < 30:
            return {"sub_score": 0, "flag": f"Domain created {age_days} days ago"}
        if age_days < 180:
            return {"sub_score": 25, "flag": f"Domain only {max(1, age_days // 30)} months old"}
        if age_days < 365:
            return {"sub_score": 50, "flag": None}
        if age_days < 1825:
            return {"sub_score": 75, "flag": None}
        return {"sub_score": 100, "flag": None}
    except Exception:
        return {"sub_score": 20, "flag": "WHOIS unavailable"}
