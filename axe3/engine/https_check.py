from urllib.parse import urlparse

import requests


def analyze(url: str) -> dict:
    parsed = urlparse(url)

    if parsed.scheme.lower() == "http":
        return {"sub_score": 0, "flag": "No HTTPS - plain HTTP in 2025"}

    try:
        response = requests.get(
            url,
            timeout=5,
            verify=True,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
        )

        if len(response.history) > 4:
            return {
                "sub_score": 40,
                "flag": f"Excessive redirects ({len(response.history)}) before reaching final URL",
            }

        return {"sub_score": 100, "flag": None}

    except requests.exceptions.SSLError:
        return {"sub_score": 10, "flag": "Invalid or self-signed SSL certificate"}
    except requests.exceptions.ConnectionError:
        return {"sub_score": 20, "flag": "Could not connect to domain"}
    except requests.exceptions.Timeout:
        return {"sub_score": 30, "flag": "Domain timed out (may be down or blocking)"}
    except Exception:
        return {"sub_score": 30, "flag": "HTTPS check failed"}
