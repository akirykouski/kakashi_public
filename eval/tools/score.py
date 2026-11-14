"""Score prediction files against the gold. Code only, no LLM judge (methodology §5).

    python eval/tools/score.py --runs eval/results/<run> [--gold eval/gold]

Reads <run>/<world>_<condition>.jsonl (one row per request: id, findings[{rule_u, key, kind, sources[{doc_id, quote}]}],
tokens_in, tokens_out, seconds, error) and writes <run>/scores.json and <run>/REPORT.md.

Definitions
- A finding matches on (rule_u, key), keys compared case-insensitively after trimming. Micro precision and recall.
- Inferred recall: recall over gold findings with inferred = true.
- Exact match: the predicted set of (rule_u, key) equals the gold set, nothing missing, nothing extra.
- Verdict: derived from predicted kinds by the same rule as the gold (any blocker -> blockers_found; else any
  question -> needs_info; else not_covered if any; else no_blockers_found).
- False alarm on clean: a clean request with at least one predicted finding.
- must_not_cite hit: a predicted finding cites (same doc_id and a matching quote) a gold must_not_cite quote.
  Rate over requests that have must_not_cite items.
- Cleared fired: a predicted finding with the (rule_u, key) of a gold `cleared` item. Rate over requests with one.
- Rates carry 95% Wilson intervals. Conditions are compared on the same requests with McNemar's exact test
  (two-sided binomial on discordant pairs) for exact match and verdict.
- A request whose model call failed counts as an empty prediction (and is listed under errors).
"""
import argparse
import json
import math
import re
from itertools import combinations
from pathlib import Path

CATEGORIES = ["direct", "inferred", "stale", "missing", "clean"]
CONDITION_ORDER = ["A", "Aprime", "B", "C", "Cstar"]
LABEL = {"A": "A (BM25 top-8 → model)", "Aprime": "A' (BM25 + dense top-8 → model)",
         "B": "B (all documents → model)", "C": "C (model parse → core)", "Cstar": "C* (hand parse → core)"}


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def norm(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def finding_set(findings):
    return {(f["rule_u"], norm(f["key"])) for f in findings}


def verdict_of(findings):
    kinds = {f.get("kind", "blocker") for f in findings}
    for kind, verdict in (("blocker", "blockers_found"), ("question", "needs_info"), ("not_covered", "not_covered")):
        if kind in kinds:
            return verdict
    return "no_blockers_found"


def quote_tokens(text):
    return set(re.findall(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", norm(text)))


def quotes_match(cited, forbidden):
    a, b = quote_tokens(cited), quote_tokens(forbidden)
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= 0.6


def cites_forbidden(findings, must_not_cite):
    for finding in findings:
        for source in finding.get("sources", []):
            for item in must_not_cite:
                if norm(source.get("doc_id")) == norm(item["doc_id"]) and quotes_match(source.get("quote", ""), item["quote"]):
                    return True
    return False


def wilson(successes, n, z=1.96):
    if n == 0:
        return None
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return {"rate": round(p, 4), "k": successes, "n": n, "lo": round(max(0.0, centre - half), 4),
            "hi": round(min(1.0, centre + half), 4)}


def mcnemar(first, second):
    """Exact two-sided McNemar on paired booleans. b = first right only, c = second right only."""
    b = sum(1 for x, y in zip(first, second) if x and not y)
    c = sum(1 for x, y in zip(first, second) if y and not x)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "p": 1.0}
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return {"b": b, "c": c, "p": round(min(1.0, 2 * tail), 4)}


def score_condition(gold_rows, predictions):
    by_id = {row["id"]: row for row in predictions}
    tp = fp = fn = inferred_tp = inferred_total = 0
    kind_counts = {kind: {"tp": 0, "gold": 0, "pred": 0} for kind in ("blocker", "question")}
    per_request = []
    for gold in gold_rows:
        prediction = by_id.get(gold["id"], {"findings": [], "error": "missing"})
        predicted = prediction.get("findings") or []
        expected = finding_set(gold["findings"])
        got = finding_set(predicted)
        tp += len(expected & got)
        fp += len(got - expected)
        fn += len(expected - got)
        inferred = {(f["rule_u"], norm(f["key"])) for f in gold["findings"] if f.get("inferred")}
        inferred_total += len(inferred)
        inferred_tp += len(inferred & got)
        for kind in kind_counts:
            gold_kind = {(f["rule_u"], norm(f["key"])) for f in gold["findings"] if f["kind"] == kind}
            pred_kind = {(f["rule_u"], norm(f["key"])) for f in predicted if f.get("kind") == kind}
            kind_counts[kind]["tp"] += len(gold_kind & pred_kind)
            kind_counts[kind]["gold"] += len(gold_kind)
            kind_counts[kind]["pred"] += len(pred_kind)
        cleared = {(c["rule_u"], norm(c["key"])) for c in gold.get("cleared", [])}
        per_request.append({
            "id": gold["id"], "category": gold["category"],
            "exact": expected == got,
            "verdict_ok": verdict_of(predicted) == gold["verdict"],
            "verdict": verdict_of(predicted), "gold_verdict": gold["verdict"],
            "missed": sorted(expected - got), "extra": sorted(got - expected),
            "clean_alarm": gold["category"] == "clean" and bool(got),
            "mnc_applicable": bool(gold.get("must_not_cite")),
            "mnc_hit": bool(gold.get("must_not_cite")) and cites_forbidden(predicted, gold["must_not_cite"]),
            "cleared_applicable": bool(cleared), "cleared_fired": bool(cleared & got),
            "tokens_in": prediction.get("tokens_in", 0), "tokens_out": prediction.get("tokens_out", 0),
            "seconds": prediction.get("seconds", 0), "error": prediction.get("error"),
        })
    n = len(per_request)
    clean = [r for r in per_request if r["category"] == "clean"]
    mnc = [r for r in per_request if r["mnc_applicable"]]
    cleared_rows = [r for r in per_request if r["cleared_applicable"]]
    metrics = {
        "n_requests": n, "n_gold_findings": tp + fn,
        "precision": wilson(tp, tp + fp), "recall": wilson(tp, tp + fn),
        "inferred_recall": wilson(inferred_tp, inferred_total),
        "exact": wilson(sum(r["exact"] for r in per_request), n),
        "exact_by_category": {c: wilson(sum(r["exact"] for r in per_request if r["category"] == c),
                                        sum(1 for r in per_request if r["category"] == c)) for c in CATEGORIES},
        "verdict_accuracy": wilson(sum(r["verdict_ok"] for r in per_request), n),
        "verdict_by_category": {c: wilson(sum(r["verdict_ok"] for r in per_request if r["category"] == c),
                                          sum(1 for r in per_request if r["category"] == c)) for c in CATEGORIES},
        "clean_false_alarm": wilson(sum(r["clean_alarm"] for r in clean), len(clean)),
        "must_not_cite_hits": wilson(sum(r["mnc_hit"] for r in mnc), len(mnc)),
        "cleared_fired": wilson(sum(r["cleared_fired"] for r in cleared_rows), len(cleared_rows)),
        "by_kind": {kind: {"precision": wilson(v["tp"], v["pred"]), "recall": wilson(v["tp"], v["gold"])}
                    for kind, v in kind_counts.items()},
        "tokens_in_mean": round(sum(r["tokens_in"] for r in per_request) / max(n, 1)),
        "tokens_out_mean": round(sum(r["tokens_out"] for r in per_request) / max(n, 1)),
        "seconds_mean": round(sum(r["seconds"] for r in per_request) / max(n, 1), 2),
        "errors": [r["id"] for r in per_request if r["error"]],
        "counts": {"tp": tp, "fp": fp, "fn": fn, "inferred_tp": inferred_tp, "inferred_total": inferred_total},
    }
    return metrics, per_request


def fmt(rate):
    if rate is None:
        return "–"
    return f"{rate['rate']:.2f} [{rate['lo']:.2f}–{rate['hi']:.2f}] ({rate['k']}/{rate['n']})"


def report(scores, run_dir):
    lines = [f"# Scores: `{run_dir}`", "",
             "Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). "
             "Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).", ""]
    for world, block in scores["worlds"].items():
        lines += [f"## World {world}", "",
                  "| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for condition, entry in block["conditions"].items():
            m = entry["metrics"]
            lines.append(f"| {LABEL.get(condition, condition)} | {fmt(m['precision'])} | {fmt(m['recall'])} | "
                         f"{fmt(m['inferred_recall'])} | {fmt(m['exact'])} | {fmt(m['verdict_accuracy'])} | "
                         f"{fmt(m['clean_false_alarm'])} | {fmt(m['must_not_cite_hits'])} | {fmt(m['cleared_fired'])} | "
                         f"{m['tokens_in_mean']} / {m['tokens_out_mean']} | {m['seconds_mean']} | {len(m['errors'])} |")
        lines += ["", "Exact match by category:", "", "| Condition | " + " | ".join(CATEGORIES) + " |",
                  "|---|" + "---|" * len(CATEGORIES)]
        for condition, entry in block["conditions"].items():
            m = entry["metrics"]["exact_by_category"]
            lines.append(f"| {LABEL.get(condition, condition)} | " + " | ".join(fmt(m[c]) for c in CATEGORIES) + " |")
        lines += ["", "Findings by kind (precision / recall):", "", "| Condition | blocker P | blocker R | question P | question R |", "|---|---|---|---|---|"]
        for condition, entry in block["conditions"].items():
            k = entry["metrics"]["by_kind"]
            lines.append(f"| {LABEL.get(condition, condition)} | {fmt(k['blocker']['precision'])} | {fmt(k['blocker']['recall'])} | "
                         f"{fmt(k['question']['precision'])} | {fmt(k['question']['recall'])} |")
        if block["mcnemar"]:
            lines += ["", "Paired comparisons (McNemar exact; b = first right only, c = second right only):", "",
                      "| Pair | Exact match b / c, p | Verdict b / c, p |", "|---|---|---|"]
            for pair, test in block["mcnemar"].items():
                e, v = test["exact"], test["verdict"]
                lines.append(f"| {pair} | {e['b']} / {e['c']}, p = {e['p']} | {v['b']} / {v['c']}, p = {v['p']} |")
        lines += ["", "Per-request misses and extras:", ""]
        for condition, entry in block["conditions"].items():
            wrong = [r for r in entry["per_request"] if not r["exact"] or not r["verdict_ok"]]
            lines.append(f"- **{LABEL.get(condition, condition)}**: {len(wrong)} requests not exact or wrong verdict")
            for r in wrong:
                lines.append(f"  - {r['id']} ({r['category']}): verdict {r['verdict']} (gold {r['gold_verdict']}); "
                             f"missed {r['missed']} extra {r['extra']}" + (f"; ERROR {r['error']}" if r["error"] else ""))
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--gold", default=str(Path(__file__).resolve().parents[1] / "gold"))
    args = parser.parse_args()
    run_dir, gold_dir = Path(args.runs), Path(args.gold)
    scores = {"run": str(run_dir), "gold_dir": str(gold_dir), "worlds": {}}
    pooled = {}
    for world in ("M", "A"):
        gold_path = gold_dir / f"{world}.jsonl"
        if not gold_path.exists():
            continue
        gold_rows = load_jsonl(gold_path)
        conditions = {}
        for condition in CONDITION_ORDER:
            path = run_dir / f"{world}_{condition}.jsonl"
            if path.exists():
                metrics, per_request = score_condition(gold_rows, load_jsonl(path))
                conditions[condition] = {"metrics": metrics, "per_request": per_request}
                pooled.setdefault(condition, {})[world] = (gold_rows, load_jsonl(path))
        tests = {}
        for first, second in combinations(conditions, 2):
            one, two = conditions[first]["per_request"], conditions[second]["per_request"]
            tests[f"{first} vs {second}"] = {"exact": mcnemar([r["exact"] for r in one], [r["exact"] for r in two]),
                                             "verdict": mcnemar([r["verdict_ok"] for r in one], [r["verdict_ok"] for r in two])}
        scores["worlds"][world] = {"conditions": conditions, "mcnemar": tests}
    # both worlds: per-world scoring, then counts summed over requests (no pooling of facts)
    both = {}
    for condition, worlds in pooled.items():
        if len(worlds) == 2:
            gold_rows = [row for world in ("M", "A") for row in worlds[world][0]]
            predictions = [row for world in ("M", "A") for row in worlds[world][1]]
            metrics, per_request = score_condition(gold_rows, predictions)
            both[condition] = {"metrics": metrics, "per_request": per_request}
    if both:
        tests = {}
        for first, second in combinations(both, 2):
            one, two = both[first]["per_request"], both[second]["per_request"]
            tests[f"{first} vs {second}"] = {"exact": mcnemar([r["exact"] for r in one], [r["exact"] for r in two]),
                                             "verdict": mcnemar([r["verdict_ok"] for r in one], [r["verdict_ok"] for r in two])}
        scores["worlds"]["both"] = {"conditions": both, "mcnemar": tests}
    json.dump(scores, open(run_dir / "scores.json", "w"), indent=1, ensure_ascii=False, default=list)
    (run_dir / "REPORT.md").write_text(report(scores, run_dir))
    print(f"wrote {run_dir / 'scores.json'} and {run_dir / 'REPORT.md'}")


if __name__ == "__main__":
    main()
