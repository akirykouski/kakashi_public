"""Decide H1–H4 of docs/methodology.md §1 from a scores.json, with the pre-registered thresholds.

    python eval/tools/hypotheses.py eval/results/<run>/scores.json > eval/results/<run>/HYPOTHESES.md

Decision on the two worlds together (per-world scores summed over requests; CHANGES.md); per-world shown beside.
"""
import json
import sys

THRESHOLDS = {
    "H1": "Recall on inferred findings, C > A' by at least 20 points",
    "H2": "Exact match on the stale and missing categories, C > B",
    "H3": "Exact match at 8x company size: C drops <= 3 points, B drops more than C",
    "H4": "Exact match, C >= B - 5 points",
}


def rate(metric):
    return None if metric is None else metric["rate"]


def show(metric):
    if metric is None:
        return "–"
    return f"{metric['rate']:.2f} [{metric['lo']:.2f}–{metric['hi']:.2f}], n = {metric['n']}"


def stale_missing(metrics):
    k = n = 0
    for category in ("stale", "missing"):
        entry = metrics["exact_by_category"][category]
        if entry:
            k += entry["k"]
            n += entry["n"]
    if n == 0:
        return None
    from score import wilson
    return wilson(k, n)


def decide(block):
    conditions = block["conditions"]
    c, a_prime, b = (conditions.get(name, {}).get("metrics") for name in ("C", "Aprime", "B"))
    rows = {}
    if c and a_prime:
        diff = rate(c["inferred_recall"]) - rate(a_prime["inferred_recall"])
        rows["H1"] = (diff >= 0.20, f"C {show(c['inferred_recall'])} vs A' {show(a_prime['inferred_recall'])}; diff {diff:+.2f}")
    if c and b:
        c_sm, b_sm = stale_missing(c), stale_missing(b)
        rows["H2"] = (rate(c_sm) > rate(b_sm), f"C {show(c_sm)} vs B {show(b_sm)}")
        diff = rate(c["exact"]) - rate(b["exact"])
        rows["H4"] = (diff >= -0.05, f"C {show(c['exact'])} vs B {show(b['exact'])}; diff {diff:+.2f}")
    rows.setdefault("H3", (None, "not run: needs the 8x company-size worlds for B and C"))
    return rows


def main():
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    scores = json.load(open(sys.argv[1]))
    lines = ["| Hypothesis | Pass if (pre-registered) | Scope | Result | Numbers |", "|---|---|---|---|---|"]
    order = ["both", "M", "A"]
    for hypothesis in ("H1", "H2", "H3", "H4"):
        for world in order:
            if world not in scores["worlds"]:
                continue
            outcome, numbers = decide(scores["worlds"][world]).get(hypothesis, (None, "missing condition"))
            verdict = {True: "PASS", False: "FAIL", None: "not decided"}[outcome]
            scope = "both worlds (decides)" if world == "both" else f"world {world}"
            lines.append(f"| {hypothesis} | {THRESHOLDS[hypothesis]} | {scope} | {verdict} | {numbers} |")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
