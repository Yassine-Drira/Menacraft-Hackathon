# Judge-Ready Checklist

## Before presenting
1. Start backend once:
   - Run start_axe3.ps1
2. Confirm health endpoint:
   - GET http://127.0.0.1:8002/health
3. Run benchmark evidence:
   - python run_benchmark.py
4. Run deterministic live demo:
   - judge_demo.ps1

## What to show on stage
1. One authentic source result (bbc.com)
2. One social source result (instagram.com/instagram)
3. One fake or typosquat source result (bbc-news-live.com)
4. Confidence + top flags for explainability
5. Benchmark summary: accuracy and confusion counts

## Safe claim language
- Use: "95.8% accuracy on our 24-URL labeled benchmark set"
- Use: "confidence score reflects evidence coverage"
- Use: "system degrades safely when enrichment is partial"
- Avoid: unsupported large percentage improvement claims without before/after dataset proof
