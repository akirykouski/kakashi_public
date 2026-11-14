"""The pipeline: change request (or meeting remark) -> Card + DecisionRecord.

    python -m core.check --scenario main [--json]
    python -m core.check --remark "Bormida is late, take BR-220 from Chisone, same alloy" [--json]
    python -m core.check --type SourceChange --part BR-220 --to SUP-C [--as-of 2026-11-14] [--json]

Deterministic from the request on: the same facts, rules and request give the same card. The language model is
used only by core/parse.py when a remark is given. Written 14 Nov 2026 (integration); design in
docs/architecture.md, shapes in core/contracts.py.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import decision, oida, rules  # noqa: E402
from core import memory as decision_memory  # noqa: E402  (check.memory() is the fact log)
from core.contracts import Card, ChangeRequest  # noqa: E402
from core.factlog import default_log  # noqa: E402
from core.project import Projection, request_entities  # noqa: E402

DEFAULT_AS_OF = "2026-11-14"
# Request-scoped reasoning (core/project.py scope_facts): close only the change's neighbourhood. LCC_SCOPED=0 closes
# the whole snapshot as before; tests/test_scoped_equivalence.py proves both give the same card.
SCOPED = os.environ.get("LCC_SCOPED", "1") != "0"
SEVERITY_ORDER = {"blocker": 0, "warning": 1, "question": 2, "info": 3}
_LOG = None
_COVERAGE = None


def memory():
    """The fact log, loaded once per process."""
    global _LOG
    if _LOG is None:
        _LOG = default_log()
        rules.extend_log(_LOG)  # policy facts (QP-15): 8D level, completeness scope, owners
    return _LOG


def coverage():
    """Coverage check of the decision table, computed once per process."""
    global _COVERAGE
    if _COVERAGE is None:
        report = decision.coverage_check()
        _COVERAGE = {key: report[key] for key in ("input_sets", "to_person", "overlaps")}
    return _COVERAGE


def fallback_row():
    return decision.to_decision_row(decision.load_table()["rows"][-1])


def severity_rank(finding):
    return SEVERITY_ORDER.get(finding["severity"], 9)


def scenario(scenario_id):
    with open(os.path.join(ROOT, "data", "scenarios.json")) as file:
        scenarios = {item["id"]: item for item in json.load(file)}
    item = scenarios[scenario_id]
    request = dict(item["change"])
    request.setdefault("as_of", item.get("as_of", DEFAULT_AS_OF))
    if item.get("known_at"):
        request.setdefault("known_at", item["known_at"])
    return request


def from_remark(remark, as_of=None):
    from core import parse  # imported lazily: only this path calls a model
    return parse.parse(remark, as_of=as_of)


def run(request, record=True):
    """Check one change request. Returns (card, decision_record)."""
    card, entry, _ = evaluate(request, record=record)
    return card, entry


def evaluate(request, record=True, table=None, rules_version_value=None, coverage_value=None, scoped=None,
             explain=False):
    """The one pipeline. table / rules_version_value / coverage_value let the demo page re-check under an
    edited decision table without writing core/decision_table.yaml. explain=True adds the card keys
    counterfactuals / counterfactual_all / explanation (core/explain_text.py). Returns (card, record, projection)."""
    known = set(ChangeRequest.__dataclass_fields__)
    known.discard("epistemic")  # derived on the card, never an input
    request = ChangeRequest(**{key: value for key, value in request.items() if key in known}).to_dict()
    as_of = request.get("as_of") or DEFAULT_AS_OF
    started = time.time()
    scoped = SCOPED if scoped is None else scoped
    projection = Projection(memory(), as_of, known_at=request.get("known_at"),
                            scope=request_entities(request) if scoped else None)
    projected = time.time()
    findings = sorted(rules.check(projection, request), key=severity_rank)
    not_checked = rules.not_checked(projection, request) if hasattr(rules, "not_checked") else []
    checked = time.time()
    # A change is covered when a rule applies to it, and always when a rule actually fired.
    fired = any(item["severity"] != "info" for item in findings)
    if fired or rules.covered(request, projection):
        row, verdict = decision.decide(findings, request, table)
    else:
        rows = (table or decision.load_table())["rows"]
        row, verdict = decision.to_decision_row(rows[-1]), "not_covered"  # no rule applies: a person decides
    entry = None
    if record:
        entry = decision.record(request, as_of, getattr(projection, "fact_ids_in_force", []), findings, row,
                                verdict, rules_version_value=rules_version_value)
    card_request = dict(request)
    findings = oida.annotate(projection, card_request, findings)  # OIDA badges + question urgency (#26, #27)
    finished = time.time()
    timings = dict(projection.timings()) if hasattr(projection, "timings") else {}
    timings.update({"projection": round((projected - started) * 1000, 1),
                    "rules": round((checked - projected) * 1000, 1),
                    "total": round((finished - started) * 1000, 1)})
    card = Card(request=card_request, verdict=verdict, findings=findings,
                not_checked=[{key: item.get(key) for key in ("id", "source", "quote", "summary")}
                             for item in not_checked],
                decision=row, coverage=coverage_value or coverage(), record_id=entry["record_id"] if entry else "",
                timings_ms=timings, contested=contested_pairs(projection, request),
                **decision_memory.annotate(projection, card_request, findings)).__dict__
    if explain:
        from core import explain_text  # verified counterfactuals (hypothetical re-runs) + two-register text
        explain_text.attach(card, entry, table=table)
    return card, entry, projection


def contested_pairs(projection, request):
    """#28 card key `contested`: both versions with sources (rules.contested_pairs); [] when nothing is contested."""
    return rules.contested_pairs(projection, request)


def print_card(card):
    request = card["request"]
    print(f"Change: {json.dumps(request, ensure_ascii=False)}")
    print(f"Verdict: {card['verdict']}   (never 'approved': a person decides)")
    for finding in card["findings"]:
        print(f"\n[{finding['severity'].upper()}] {finding['rule']}: {finding['title']}")
        if finding.get("note"):
            print(f"  note: {finding['note']}")
        if finding.get("consequence"):
            consequence = finding["consequence"]
            print(f"  consequence if shipped: {consequence.get('type')} [{consequence.get('source')}: "
                  f"\"{consequence.get('quote')}\"]")
        for step in finding["evidence"]:
            print_step(step, "  ")
        if finding.get("owner"):
            print(f"  owner: {finding['owner']}")
    if card["not_checked"]:
        print("\nNOT CHECKED (requirements the ontology cannot express yet; a person reads them):")
        for item in card["not_checked"]:
            print(f"  - {item['source']}: \"{item['quote']}\"")
    for pair in card.get("contested") or []:
        print(f"\nCONTESTED {pair['key']} ({pair['reason']}), decides: {pair.get('owner') or 'a person'}")
        for side in pair["sides"]:
            print(f"  - {side['value']}  [{side.get('source')}: \"{side.get('quote')}\"] ({side.get('status')})")
    row = card["decision"]
    print(f"\nDecision table row {row['row_id']}: decided by {row['decider']}")
    for action in row["allowed_actions"]:
        print(f"  allowed: {action}")
    cover = card["coverage"]
    print(f"Table checked: {cover['input_sets']} input sets, {cover['to_person']} go to a person, "
          f"{cover['overlaps']} overlap")
    for item in card.get("past_decisions") or []:
        print(f"\nDECIDED BEFORE {item['id']} {item['date']} by {item['by']} ({item['status']}): \"{item['title']}\"")
        for reason in item["reasons"]:
            print(f"  reason {reason['record']}: {reason['detail']}  [{reason.get('source')}: \"{reason.get('quote')}\"]")
    for item in card.get("maintenance") or []:
        print(f"\nMAINTENANCE [{item['severity']}] {item['kind']}: {item['title']}"
              + (f"  owner {item['owner']}" if item.get("owner") else "")
              + (f"  urgency {item['urgency']}" if item.get("urgency") is not None else ""))
        for step in item["evidence"]:
            print(f"  [{step.get('source')}: \"{step.get('quote')}\"]")
    print(f"Record {card['record_id']}  timings {card['timings_ms']}")


def print_step(step, indent):
    source = f"  [{step.get('source')}: \"{step.get('quote')}\"]" if step.get("quote") else ""
    marker = "  (inferred" + (f": {step['rule']}" if step.get("rule") else "") + ")" if step.get("inferred") else ""
    print(f"{indent}- {step.get('triple')}{marker}{source}")
    for premise in step.get("premises") or []:
        print_step(premise, indent + "  ")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario")
    parser.add_argument("--remark")
    parser.add_argument("--type", default="SourceChange")
    parser.add_argument("--part")
    parser.add_argument("--to", dest="to_supplier")
    parser.add_argument("--site")
    parser.add_argument("--material", dest="new_material")
    parser.add_argument("--coating", dest="new_coating")
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--known-at", default=None)
    parser.add_argument("--no-record", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.scenario:
        request = scenario(args.scenario)
    elif args.remark:
        request = from_remark(args.remark, as_of=args.as_of)
    else:
        request = {key: getattr(args, key) for key in ("type", "part", "to_supplier", "site", "new_material",
                                                       "new_coating") if getattr(args, key)}
    if args.as_of:
        request["as_of"] = args.as_of
    if args.known_at:
        request["known_at"] = args.known_at
    card, _ = run(request, record=not args.no_record)
    if args.json:
        print(json.dumps(card, indent=2, ensure_ascii=False))
    else:
        print_card(card)


if __name__ == "__main__":
    main()
