"""PREP SPIKE oracle cross-check: scenario reasoner vs the frozen gold, CR-01.

Runs the reasoner on the CR-01 request (ECN-26-0147, valid 2026-11-10) and
compares the produced blocker and question ids with the rule ids that
data/eval/gold.jsonl expects for CR-01 (set comparison). Also fails if any
evidence quote the card would cite is one of the gold's must_not_cite quotes.
Exit 0 on a match, 1 on any mismatch.

  uv run --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 \
      python prep/spikes/reasoning-core/crosscheck_gold.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import (DATA, Explainer, check, closure, functional_predicates, leaves,  # noqa: E402
                  load_scenario, load_shapes, load_tbox, snapshot)

CASE = "CR-01"
VALID_AT, KNOWN_AT = "2026-11-10", "2026-11-10T23:59"

# Gold rule ids the ontology does not model (data/eval/RULES.md marks them NEW,
# provisional slugs). Listed here on purpose: they are skipped by name, never silently.
OUT_OF_SCOPE = {
    "special_characteristic_violation": "RULES.md NEW: measured value fails a special characteristic; no measurement model",
    "deviation_limit_exceeded": "RULES.md NEW: PRC-DEV-007 quantity/duration caps are not modelled (ontology README, Not done)",
}

gold = next(r for r in map(json.loads, (DATA / "eval" / "gold.jsonl").read_text().splitlines()) if r["id"] == CASE)
expected = {b["rule"] for b in gold["expected_blockers"]}
skipped = {r: OUT_OF_SCOPE[r] for r in sorted(expected & OUT_OF_SCOPE.keys())}
expected -= set(skipped)

tbox, shapes = load_tbox(), load_shapes()
snap = snapshot(load_scenario(), functional_predicates(tbox), VALID_AT, KNOWN_AT)
g, asserted = closure(snap["facts"], tbox)
items = check(g, shapes)
produced = {i["type"] for i in items if i["severity"] in ("Blocker", "Question")}

print(f"{CASE} verdict in gold: {gold['expected_verdict']}")
print(f"expected (gold):   {sorted(expected)}")
print(f"produced (reason): {sorted(produced)}")
for rule, why in skipped.items():
    print(f"skipped out-of-scope gold id {rule}: {why}")
missing, extra = sorted(expected - produced), sorted(produced - expected)
print(f"diff: missing from reasoner = {missing}, extra in reasoner = {extra}")
failed = bool(missing or extra)

# the card must not rest on what the gold calls non-authoritative or superseded
ex = Explainer(tbox, g, asserted)
banned = {(m["doc_id"], m["quote"]) for m in gold["must_not_cite"]}
cited = set()
for item in items:
    for t in item["evidence"]:
        proof = ex.explain(t)
        cited |= {(leaf["doc"], leaf["quote"]) for leaf in leaves(proof) if leaf["source"] == "fact"}
hits = sorted(cited & banned)
print(f"must_not_cite hits in cited evidence: {hits}")
failed |= bool(hits)

print("MISMATCH" if failed else f"MATCH: {len(produced)} ids equal the gold set for {CASE}")
sys.exit(1 if failed else 0)
