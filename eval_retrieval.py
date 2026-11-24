"""Measure SEARCH quality with RAGAS context precision & recall (no AI calls, no quota)."""
import json
import sys
import warnings

warnings.filterwarnings("ignore")

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall

from safebank_bot import retrieve

precision_metric = IDBasedContextPrecision()
recall_metric = IDBasedContextRecall()

cases = json.load(open("golden.json", encoding="utf-8"))
scores = []

for case in cases:
    retrieved = [doc_id for doc_id, _ in retrieve(case["question"])]
    expected = case["expected_chunks"]
    shown = " ".join(retrieved) or "-"

    if not expected:  # out-of-scope question: the right result is "found nothing"
        verdict = "OK" if not retrieved else "JUNK FOUND"
        print(f'{case["id"]:<4} retrieved={shown:<6} expected=-    {verdict} (out of scope)')
        continue

    sample = SingleTurnSample(retrieved_context_ids=retrieved, reference_context_ids=expected)
    precision = precision_metric.single_turn_score(sample) if retrieved else 0.0
    recall = recall_metric.single_turn_score(sample)
    scores.append((precision, recall))
    print(f'{case["id"]:<4} retrieved={shown:<6} expected={" ".join(expected):<4} '
          f'precision={precision:.2f}  recall={recall:.2f}')

avg_precision = sum(p for p, _ in scores) / len(scores)
avg_recall = sum(r for _, r in scores) / len(scores)
print(f"\nAverage context precision: {avg_precision:.2f}  (how much of what we found was useful)")
print(f"Average context recall:    {avg_recall:.2f}  (how much of what we needed was found)")


MIN_RECALL = 0.85  # quality gate: the build fails below this
if avg_recall < MIN_RECALL:
    print(f"GATE FAILED: recall {avg_recall:.2f} is below {MIN_RECALL}")
    sys.exit(1)
print(f"GATE PASSED: recall {avg_recall:.2f} >= {MIN_RECALL}")