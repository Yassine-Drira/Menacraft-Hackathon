# ClipTrust Axe3 Judge Pitch

## 60-Second Version
We built the Source Credibility engine for ClipTrust.
Given any news URL or social post URL, we return a trust score from 0 to 100, a verdict, and explainable risk flags.

What is different in our system is that we do not only score the domain. For social links, we also enrich publisher profile evidence when available, then combine both domain and publisher behavior signals.

The output is transparent: score, confidence, verdict, and plain-language flags.
That means a user can see exactly why a source is suspicious or trusted.

We benchmarked on a labeled set of 24 URLs across authentic, suspicious, and fake examples.
Current accuracy is 95.8 percent, with stable response performance around 1 to 2 seconds.

So this is not a black-box classifier. It is fast, explainable, and production-ready for source-risk triage.

## 3-Minute Version
### 1) Problem
People share fast-moving content from links and reels.
Users need a quick, explainable way to judge source credibility before trusting the claim.

### 2) Approach
Our engine evaluates 7 weighted signals:
- Domain age
- Brand mimic / typosquat risk
- URL structure quality
- HTTPS and certificate posture
- Known bad-domain list match
- Publisher account behavior
- Writing style consistency where text is available

For social links, we attempt profile enrichment and gracefully degrade when platforms limit scraping.

### 3) Output Design
API response is practical and interpretable:
- score: overall trust estimate
- confidence: certainty based on evidence coverage
- verdict: authentic / suspicious / fake
- flags: human-readable reasons

This lets downstream systems or judges understand decisions quickly.

### 4) Validation
We built a labeled benchmark of 24 URLs with expected classes.
Measured result:
- Accuracy: 95.8 percent
- Confusion profile:
  - authentic: 11/11 correct
  - suspicious: 6/6 correct
  - fake: 6/7 correct

The one miss is currently conservative, fake predicted as suspicious.

### 5) Reliability and Demo Safety
We use one stable startup path via start_axe3.ps1.
The demo flow is deterministic with fixed URLs and expected outcomes.
If enrichment is partially unavailable, confidence drops and a clear flag explains why.

### 6) Impact
This engine is ready to plug into a broader misinformation detection pipeline.
It is transparent, fast, and operationally safe for real-world triage.

## Live Demo Sequence (90 seconds)
1. Run backend with start_axe3.ps1
2. Test authentic URL: https://bbc.com
3. Test social URL: https://instagram.com/instagram
4. Test suspicious URL: https://bbc-news-live.com
5. Show score, confidence, and top flags for each
6. Close with benchmark result: 95.8% on 24 labeled URLs
