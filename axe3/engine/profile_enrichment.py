import re
from urllib.parse import urlparse

import requests

_SOCIAL_HOSTS = {
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "x.com": "x",
    "www.x.com": "x",
    "twitter.com": "x",
    "www.twitter.com": "x",
    "tiktok.com": "tiktok",
    "www.tiktok.com": "tiktok",
}


def _safe_get(url: str, timeout: int = 3) -> str | None:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
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


def _extract_handle_from_path(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None

    blocked = {"p", "reel", "tv", "explore", "i", "status", "video"}
    first = parts[0].lower()
    if first in blocked:
        return None

    return first


def _extract_int(text: str, patterns: list[str]) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            digits = re.sub(r"[^0-9]", "", match.group(1))
            if digits:
                return int(digits)
    return None


def _extract_instagram_handle_from_reel_html(html: str) -> str | None:
    patterns = [
        r'"owner"\s*:\s*\{[^}]*"username"\s*:\s*"([a-zA-Z0-9._-]+)"',
        r'"alternateName"\s*:\s*"@([a-zA-Z0-9._-]+)"',
        r'"username"\s*:\s*"([a-zA-Z0-9._-]+)"',
        r'@([a-zA-Z0-9._-]+)\s*</a>',
        r'>@([a-zA-Z0-9._-]+)<',
        r'\"([a-zA-Z0-9._-]+)\"\s*:\s*\{\s*\".*?\".*?\"followers_count\"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            handle = match.group(1)
            if handle and 2 <= len(handle) <= 30:
                return handle
    return None


def _estimate_account_age_from_handle(handle: str) -> int | None:
    """Heuristic: common patterns in new accounts."""
    if re.search(r'\d{6,}', handle):
        return 30
    if handle.count('_') >= 2:
        return 60
    return None

def _instagram_profile_stats(handle: str) -> dict:
    url = f"https://www.instagram.com/{handle}/"
    html = _safe_get(url)
    if not html:
        return {"account": None, "texts": None, "flags": ["Could not fetch Instagram profile page"]}

    followers = _extract_int(
        html,
        [
            r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'"followers"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'>([0-9,]+)</span>\s*Followers',
            r'Followers.*?>([0-9,]+)<',
        ],
    )
    following = _extract_int(
        html,
        [
            r'"edge_follow"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'"following"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'>([0-9,]+)</span>\s*Following',
        ],
    )
    posts = _extract_int(
        html,
        [
            r'"edge_owner_to_timeline_media"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'"posts"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'>([0-9,]+)</span>\s*Posts',
        ],
    )

    verified = bool(re.search(r'"is_verified"\s*:\s*true', html, re.IGNORECASE))
    
    account_age = _estimate_account_age_from_handle(handle)

    captions = re.findall(r'"accessibility_caption"\s*:\s*"([^"]+)"', html)
    texts = [re.sub(r"\\u[0-9a-fA-F]{4}", " ", c).strip() for c in captions[:8] if c.strip()]

    account = {
        "followers_count": followers,
        "following_count": following,
        "posts_count": posts,
        "verified": verified,
        "account_age_days": account_age,
    }

    flags = []
    if followers is None and following is None and posts is None:
        flags.append("Instagram profile stats unavailable (public scraping limits)")
    else:
        flags.append("Instagram stats auto-extracted (handle confidence mode)")

    return {"account": account, "texts": texts if texts else None, "flags": flags}


def _x_profile_stats(handle: str) -> dict:
    # X blocks most unauthenticated profile metadata scraping; keep graceful fallback.
    return {
        "account": None,
        "texts": None,
        "flags": [f"X profile scraping limited without auth for @{handle}"],
    }


def _tiktok_profile_stats(handle: str) -> dict:
    url = f"https://www.tiktok.com/@{handle}"
    html = _safe_get(url)
    if not html:
        return {"account": None, "texts": None, "flags": ["Could not fetch TikTok profile page"]}

    followers = _extract_int(html, [
        r'"followerCount"\s*:\s*(\d+)',
        r'>([0-9M.K]+)\s*Followers',
        r'follower.*?>([0-9,]+)<',
    ])
    following = _extract_int(html, [
        r'"followingCount"\s*:\s*(\d+)',
        r'>([0-9M.K]+)\s*Following',
    ])
    posts = _extract_int(html, [
        r'"videoCount"\s*:\s*(\d+)',
        r'>([0-9,]+)\s*Videos',
    ])

    verified = bool(re.search(r'"verified"\s*:\s*true', html, re.IGNORECASE))
    account_age = _estimate_account_age_from_handle(handle)

    account = {
        "followers_count": followers,
        "following_count": following,
        "posts_count": posts,
        "verified": verified,
        "account_age_days": account_age,
    }

    flags = []
    if followers is None and following is None and posts is None:
        flags.append("TikTok profile stats unavailable (public scraping limits)")
    else:
        flags.append("TikTok stats auto-extracted")

    return {"account": account, "texts": None, "flags": flags}


def enrich(url: str, handle: str | None = None) -> dict:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    platform = _SOCIAL_HOSTS.get(host)

    if not platform:
        return {"platform": None, "handle": handle, "account": None, "texts": None, "flags": []}

    resolved_handle = handle or _extract_handle_from_path(url)
    flags = []

    if platform == "instagram" and not resolved_handle:
        html = _safe_get(url)
        if html:
            resolved_handle = _extract_instagram_handle_from_reel_html(html)
        if not resolved_handle:
            flags.append("Could not infer Instagram publisher handle from URL")

    if not resolved_handle:
        return {
            "platform": platform,
            "handle": None,
            "account": None,
            "texts": None,
            "flags": flags,
        }

    if platform == "instagram":
        data = _instagram_profile_stats(resolved_handle)
    elif platform == "x":
        data = _x_profile_stats(resolved_handle)
    elif platform == "tiktok":
        data = _tiktok_profile_stats(resolved_handle)
    else:
        data = {"account": None, "texts": None, "flags": []}

    return {
        "platform": platform,
        "handle": resolved_handle,
        "account": data.get("account"),
        "texts": data.get("texts"),
        "flags": flags + data.get("flags", []),
    }
