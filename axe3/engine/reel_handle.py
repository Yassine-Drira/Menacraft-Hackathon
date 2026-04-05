import re
from functools import lru_cache
from urllib.parse import urlparse

import requests

_INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}


@lru_cache(maxsize=512)
def _fetch_html(url: str, timeout: float) -> str | None:
    try:
        resp = requests.get(
            url,
            timeout=(1.0, timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        if resp.status_code >= 400:
            return None
        return resp.text
    except Exception:
        return None


def _extract_instagram_handle_from_html(html: str) -> str | None:
    patterns = [
        r'"owner"\s*:\s*\{[^}]*"username"\s*:\s*"([a-zA-Z0-9._-]+)"',
        r'"alternateName"\s*:\s*"@([a-zA-Z0-9._-]+)"',
        r'"username"\s*:\s*"([a-zA-Z0-9._-]+)"',
        r'@([a-zA-Z0-9._-]+)\s*</a>',
        r'>@([a-zA-Z0-9._-]+)<',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            handle = match.group(1)
            if handle and 2 <= len(handle) <= 30:
                return handle
    return None


def infer_handle(url: str, timeout: float = 1.4) -> dict:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path_parts = [p for p in parsed.path.split("/") if p]

    if host not in _INSTAGRAM_HOSTS:
        return {"handle": None, "flag": None}

    if not path_parts:
        return {"handle": None, "flag": "Instagram URL has no path to infer publisher"}

    first = path_parts[0].lower()
    if first not in {"reel", "p", "tv"}:
        # Profile URL: /<handle>/
        return {"handle": first, "flag": "Publisher handle inferred from Instagram profile path"}

    html = _fetch_html(url, float(timeout))
    if not html:
        return {"handle": None, "flag": "Could not fetch Instagram reel page for publisher handle"}

    handle = _extract_instagram_handle_from_html(html)
    if not handle:
        return {"handle": None, "flag": "Could not infer Instagram publisher handle from reel page"}

    return {"handle": handle, "flag": f"Publisher handle inferred from reel page: @{handle}"}
