import re


def analyze(account: dict | None, handle: str | None = None) -> dict:
    if not account and not handle:
        return {"sub_score": None, "flag": "Account behavior unavailable", "available": False}

    if not account and handle:
        flags = ["Account statistics unavailable; only handle-level signals found"]
        handle_l = handle.lower()
        score = 62
        if re.search(r"\d{4,}", handle_l):
            score -= 14
            flags.append("Handle contains long numeric sequence")
        elif re.search(r"\d{1,3}", handle_l):
            score -= 5
        if handle_l.count("_") >= 3:
            score -= 10
            flags.append("Handle pattern looks synthetic")
        elif handle_l.count("_") == 2:
            score -= 4

        if len(handle_l) < 4:
            score -= 8
            flags.append("Very short handle has low trust signal")
        elif len(handle_l) > 22:
            score -= 6
            flags.append("Very long handle can indicate low-quality identity")

        if re.search(r"(official|real|news|tv|media)", handle_l):
            score += 2

        score = max(0, min(100, score))
        return {
            "sub_score": score,
            "flag": flags[0],
            "all_flags": flags,
            "available": True,
        }

    score = 70
    flags = []

    if account:
        age_days = account.get("account_age_days")
        followers = account.get("followers_count")
        following = account.get("following_count")
        posts = account.get("posts_count")
        verified = account.get("verified")
        engagement = account.get("engagement_rate")
        freq = account.get("posting_frequency_per_day")

        if verified is True:
            score += 15
        if age_days is not None:
            if age_days < 30:
                score -= 30
                flags.append(f"Very new account: {age_days} days old")
            elif age_days < 180:
                score -= 15
                flags.append("Relatively new account profile")
            elif age_days > 365 * 3:
                score += 10

        if followers is not None and following is not None and following > 0:
            ratio = followers / following
            if followers > 500 and ratio < 0.05:
                score -= 20
                flags.append("Abnormal followers/following ratio")
            elif ratio < 0.15:
                score -= 10

        if posts is not None:
            if posts < 8:
                score -= 10
                flags.append("Low posting history")
            elif posts > 1000:
                score += 5

        if engagement is not None:
            if engagement > 0.25:
                score -= 15
                flags.append("Unusually high engagement rate")
            elif followers and followers > 5000 and engagement < 0.001:
                score -= 10
                flags.append("Very low engagement for follower size")

        if freq is not None:
            if freq > 50:
                score -= 20
                flags.append("Posting frequency appears automated")
            elif freq > 25:
                score -= 10

    if handle:
        handle_l = handle.lower()
        if re.search(r"\d{4,}", handle_l):
            score -= 8
            flags.append("Handle contains long numeric sequence")
        if handle_l.count("_") >= 3:
            score -= 6
            flags.append("Handle pattern looks synthetic")

    score = max(0, min(100, score))
    return {
        "sub_score": score,
        "flag": flags[0] if flags else None,
        "all_flags": flags,
        "available": True,
    }
