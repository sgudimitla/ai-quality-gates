"""Run the golden dataset against the SafeBank bot and print a scorecard."""
import csv
import json
import sys
import time
from datetime import datetime

from safebank_bot import answer

DELAY_SECONDS = 3  # pause between calls to avoid 503 "high demand" errors


def normalize(text):
    return text.lower().replace("\u2019", "'")  # curly apostrophe -> straight


def check(case, result):
    ans = normalize(result["answer"])
    has_expected = any(normalize(x) in ans for x in case["must_contain_any"])
    has_forbidden = any(normalize(x) in ans for x in case["must_not_contain"])
    answer_ok = has_expected and not has_forbidden
    search_ok = all(c in result["chunk_ids"] for c in case["expected_chunks"])
    if answer_ok:
        blame = "-"
    elif search_ok:
        blame = "AI"
    else:
        blame = "Search"
    return answer_ok, search_ok, blame


def main():
    cases = json.load(open("golden.json", encoding="utf-8"))
    rows = []
    for case in cases:
        try:
            result = answer(case["question"])
            answer_ok, search_ok, blame = check(case, result)
            verdict = "PASS" if answer_ok else "FAIL"
        except Exception as e:  # an API error is NOT a quality failure
            result = {"answer": f"{type(e).__name__}: {e}"[:80], "chunk_ids": []}
            search_ok, blame, verdict = False, "-", "ERROR"
        rows.append({
            "id": case["id"], "category": case["category"], "verdict": verdict,
            "search_ok": "yes" if search_ok else "no", "blame": blame,
            "retrieved": " ".join(result["chunk_ids"]),
            "answer": result["answer"].replace("\n", " "),
        })
        print(f'{case["id"]:<4} {verdict:<5} search_ok={rows[-1]["search_ok"]:<3} '
              f'blame={blame:<6} retrieved={rows[-1]["retrieved"]:<6} | {rows[-1]["answer"][:70]}')
        time.sleep(DELAY_SECONDS)

    passed = sum(r["verdict"] == "PASS" for r in rows)
    errors = sum(r["verdict"] == "ERROR" for r in rows)
    scored = len(rows) - errors
    print(f"\nScore: {passed}/{scored} passed" + (f"  ({errors} errors, rerun them)" if errors else ""))

    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    filename = f"results_{label}_{datetime.now():%Y%m%d_%H%M}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {filename}")


if __name__ == "__main__":
    main()