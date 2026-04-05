import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AXE3_DIR = ROOT / "axe3"
if str(AXE3_DIR) not in sys.path:
    sys.path.insert(0, str(AXE3_DIR))

from scorer import compute


def run_benchmark(dataset_path: Path) -> None:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))

    rows = []
    counts = defaultdict(int)
    correct = 0

    for item in data:
        url = item["url"]
        expected = item["expected"]
        result = compute(url)
        predicted = result["verdict"]
        score = result["score"]
        confidence = result.get("confidence", 0)

        is_correct = predicted == expected
        correct += int(is_correct)
        counts[(expected, predicted)] += 1

        rows.append(
            {
                "url": url,
                "expected": expected,
                "predicted": predicted,
                "score": score,
                "confidence": confidence,
                "ok": is_correct,
            }
        )

    total = len(rows)
    accuracy = (correct / total) * 100 if total else 0.0

    print("=" * 78)
    print("ClipTrust Axe3 Benchmark")
    print("=" * 78)
    print(f"Samples: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.1f}%")
    print()

    print("Confusion counts (expected -> predicted):")
    labels = ["authentic", "suspicious", "fake"]
    for exp in labels:
        line = [f"{exp:10s}"]
        for pred in labels:
            line.append(f"{counts[(exp, pred)]:3d}")
        print(" ".join(line) + "   (to authentic/suspicious/fake)")

    print()
    print("Mismatches:")
    mismatch = [r for r in rows if not r["ok"]]
    if not mismatch:
        print("- None")
    else:
        for r in mismatch:
            print(
                f"- {r['url']} | expected={r['expected']} predicted={r['predicted']} "
                f"score={r['score']} confidence={r['confidence']}"
            )

    out_path = dataset_path.parent / "benchmark_results.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print()
    print(f"Detailed rows saved to: {out_path}")


if __name__ == "__main__":
    run_benchmark(Path("benchmark_urls.json"))
