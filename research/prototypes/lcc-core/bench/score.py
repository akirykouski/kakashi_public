"""Score bench/results/<condition>.jsonl against the gold in bench/requests.jsonl. No LLM judge.

  python bench/score.py [--conditions gold,ontology,retrieval,full]

Writes bench/results/RESULTS.md and prints it.
"""
import argparse
import json
import os

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BENCH_DIR, "results")
INFERRED_RULES = {"R2", "R3", "R5"}  # R8 findings are reported separately (bench/results/FIX_8.md)
CATEGORIES = ["direct", "inferred", "stale", "missing", "clean", "subtier"]
LABELS = {"gold": "C*. Gold parse → core (no model)", "ontology": "C. Model parses → core",
          "retrieval": "A. BM25 top-8 chunks → model", "full": "B. All documents → model"}


def load_jsonl(path):
    with open(path) as file:
        return [json.loads(line) for line in file]


def normalise(key):
    return key.strip().replace(" | ", "|").lower()


def pairs(findings):
    return {(finding["rule"], normalise(finding["key"])) for finding in findings}


def score(requests, rows):
    by_id = {row["id"]: row for row in rows}
    totals = {"tp": 0, "fp": 0, "fn": 0, "inferred_tp": 0, "inferred_total": 0}
    per_category = {category: {"exact": 0, "n": 0} for category in CATEGORIES}
    clean_alarms = 0
    misses = []
    for item in requests:
        row = by_id.get(item["id"], {"findings": []})
        gold = pairs(item["gold"])
        predicted = pairs(row["findings"])
        totals["tp"] += len(gold & predicted)
        totals["fp"] += len(predicted - gold)
        totals["fn"] += len(gold - predicted)
        inferred_gold = {pair for pair in gold if pair[0] in INFERRED_RULES}
        totals["inferred_total"] += len(inferred_gold)
        totals["inferred_tp"] += len(inferred_gold & predicted)
        per_category[item["category"]]["n"] += 1
        if gold == predicted:
            per_category[item["category"]]["exact"] += 1
        else:
            misses.append({"id": item["id"], "missed": sorted(gold - predicted), "extra": sorted(predicted - gold)})
        if item["category"] == "clean" and predicted:
            clean_alarms += 1
    precision = totals["tp"] / max(totals["tp"] + totals["fp"], 1)
    recall = totals["tp"] / max(totals["tp"] + totals["fn"], 1)
    n = len(requests)
    return {
        "precision": precision, "recall": recall,
        "inferred_recall": totals["inferred_tp"] / max(totals["inferred_total"], 1),
        "exact": {category: values["exact"] / max(values["n"], 1) for category, values in per_category.items()},
        "exact_all": sum(values["exact"] for values in per_category.values()) / n,
        "clean_alarm_rate": clean_alarms / max(per_category["clean"]["n"], 1),
        "tokens_in": sum(row.get("tokens_in", 0) for row in rows) / n,
        "tokens_out": sum(row.get("tokens_out", 0) for row in rows) / n,
        "seconds": sum(row.get("seconds", 0) for row in rows) / n,
        "errors": sum(1 for row in rows if row.get("error")),
        "misses": misses,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", default="gold,ontology,retrieval,full")
    parser.add_argument("--tag", default="")
    parser.add_argument("--ids")
    args = parser.parse_args()
    requests = load_jsonl(os.path.join(BENCH_DIR, "requests.jsonl"))
    if args.ids:
        wanted = set(args.ids.split(","))
        requests = [item for item in requests if item["id"] in wanted]
    results = {}
    for condition in args.conditions.split(","):
        path = os.path.join(RESULTS_DIR, f"{condition}{args.tag}.jsonl")
        if os.path.exists(path):
            results[condition] = score(requests, load_jsonl(path))
    lines = [f"# Results ({len(requests)} requests, {sum(len(item['gold']) for item in requests)} gold findings)", "",
             "| Condition | Precision | Recall | Recall, inferred (R2/R3/R5) | Exact match | False alarm on clean "
             "| Tokens in / request | Seconds / request | Errors |", "|---|---|---|---|---|---|---|---|---|"]
    for condition, result in results.items():
        lines.append(f"| {LABELS[condition]} | {result['precision']:.2f} | {result['recall']:.2f} | "
                     f"{result['inferred_recall']:.2f} | {result['exact_all']:.2f} | {result['clean_alarm_rate']:.2f} | "
                     f"{result['tokens_in']:.0f} | {result['seconds']:.1f} | {result['errors']} |")
    lines += ["", "## Exact match by category", "", "| Condition | " + " | ".join(CATEGORIES) + " |",
              "|---|" + "---|" * len(CATEGORIES)]
    for condition, result in results.items():
        lines.append(f"| {LABELS[condition]} | " + " | ".join(f"{result['exact'][category]:.2f}"
                                                            for category in CATEGORIES) + " |")
    if "ontology" in results and "full" in results:
        ontology, full = results["ontology"], results["full"]
        passed = ontology["inferred_recall"] >= full["inferred_recall"] + 0.20 and ontology["precision"] >= 0.90
        lines += ["", "## Pre-registered threshold", "",
                  f"C inferred recall {ontology['inferred_recall']:.2f} vs B {full['inferred_recall']:.2f} "
                  f"(needs +0.20); C precision {ontology['precision']:.2f} (needs ≥ 0.90): "
                  f"**{'PASSED' if passed else 'NOT PASSED'}**."]
    lines += ["", "## Misses per condition", ""]
    for condition, result in results.items():
        lines.append(f"### {LABELS[condition]}")
        for miss in result["misses"]:
            lines.append(f"- {miss['id']}: missed {miss['missed']} extra {miss['extra']}")
        lines.append("")
    text = "\n".join(lines) + "\n"
    with open(os.path.join(RESULTS_DIR, f"RESULTS{args.tag}.md"), "w") as file:
        file.write(text)
    print(text)


if __name__ == "__main__":
    main()
