from typing import List, Optional

from pydantic import BaseModel


class AccountSignals(BaseModel):
    account_age_days: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None
    verified: Optional[bool] = None
    engagement_rate: Optional[float] = None
    posting_frequency_per_day: Optional[float] = None


class SourceRequest(BaseModel):
    url: str
    # Optional: if omitted, scorer attempts to infer handle from social URL.
    handle: Optional[str] = None
    # Optional manual account stats; overrides auto-enriched values when provided.
    account: Optional[AccountSignals] = None
    # Optional recent posts/captions; overrides auto-enriched texts when provided.
    texts: Optional[List[str]] = None


class SourceResponse(BaseModel):
    score: int
    confidence: int
    verdict: str
    flags: List[str]
    axis: str
