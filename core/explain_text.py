"""A plain-words explanation of one decision, in two registers, from the decision record and the card. No model.

    python -m core.explain_text --scenario main            # both registers for a fresh check (nothing recorded)
    python -m core.explain_text --record DR-0123456789abcdef

"customer" (for the customer or supplier): short, no internal ids beyond document ids.
"auditor": the procedure actually applied, with rule ids, rules_version, decision table row, fact ids and their
documents, and the verified counterfactuals (CJEU C-203/22, Dun & Bradstreet Austria, 27 Feb 2025: describe the
procedure and principles actually applied; how a change in the data would have changed the result).

Deterministic: fixed templates over the card and record fields. Written 14 Nov 2026 (ws/counterfactual).
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

VERDICT_TEXT = {
    "blockers_found": "the change cannot go ahead as proposed: at least one blocker was found",
    "needs_info": "no blocker was found, but open questions must be answered first",
    "no_blockers_found": "no blocker was found. This is not an approval: the change goes through normal change control",
    "not_covered": "no rule covers this change, so a person decides without a rule-based check",
}
REQUEST_FIELDS = (("part", "part"), ("to_supplier", "new supplier"), ("from_supplier", "current supplier"),
                  ("at_supplier", "at sub-tier supplier"), ("site", "plant"), ("new_material", "new material"),
                  ("new_coating", "new coating"), ("scope", "scope"))
SEVERITY_WORD = {"blocker": "Blocker", "warning": "Warning", "question": "Open question", "info": "Note"}


def leaves(steps):
    """Evidence leaves (quoted facts) of a proof chain, depth first."""
    for step in steps or []:
        if step.get("premises"):
            yield from leaves(step["premises"])
        if not step.get("inferred") and step.get("fact_id"):
            yield step


def facts_used(card):
    """(fact_id, source, triple, quote) of every quoted fact the findings rest on, first use first."""
    seen, found = set(), []
    for finding in card.get("findings") or []:
        for step in leaves(finding.get("evidence")):
            if step["fact_id"] in seen:
                continue
            seen.add(step["fact_id"])
            found.append({"fact_id": step["fact_id"], "source": step.get("source"), "triple": step.get("triple"),
                          "quote": (step.get("quote") or "").replace("\n", " "), "rule": finding["rule"]})
    return found


def documents_of(finding):
    return sorted({step.get("source") for step in leaves(finding.get("evidence")) if step.get("source")})


def asked(request):
    parts = [f"{name} {request[key]}" for key, name in REQUEST_FIELDS if request.get(key)]
    return f"{request.get('type', 'change')} ({', '.join(parts)})"


def plain_edits(edits, with_ids):
    shown = [edit for edit in edits if with_ids or not edit.get("replaced_by_next")]
    return "; ".join(edit["plain"] + (f" [{edit['action']} {edit['triple']}]" if with_ids else "") for edit in shown)


def counterfactual_lines(card, with_ids):
    lines, seen = [], {}
    for item in card.get("counterfactuals") or []:
        if not item.get("verified"):
            if with_ids:
                lines.append(f"- {item['blocker_rule']}: no verified change ({item.get('reason')}).")
            continue
        if with_ids:
            lines.append(f"- {item['blocker_rule']}: would clear if {plain_edits(item['edits'], True)} -> table row "
                         f"{item['row_if_applied']}, re-run verified.")
            continue
        text = plain_edits(item["edits"], False)
        if text in seen:
            continue
        seen[text] = True
        cleared = [other for other in card["counterfactuals"] if other.get("verified")
                   and plain_edits(other["edits"], False) == text]
        kinds = sorted({other["severity"] for other in cleared})
        lines.append(f"- If {text}: {len(cleared)} {' / '.join(kinds)}{'s' if len(cleared) > 1 else ''} would go.")
    for item in card.get("counterfactuals") or []:
        if not item.get("verified") and not with_ids:
            lines.append(f"- {item['title']}: no change to our records would clear this.")
    combined = card.get("counterfactual_all")
    if combined:
        from core.counterfactual import plain_all
        lines.append(plain_all(combined))
    return lines


def customer_text(card, record):
    request, row = card["request"], card["decision"]
    blockers = [item for item in card["findings"] if item["severity"] == "blocker"]
    questions = [item for item in card["findings"] if item["severity"] == "question"]
    lines = [f"You asked about: {asked(request)}, checked as of {record.get('as_of') or request.get('as_of')}.",
             f"Result: {VERDICT_TEXT.get(card['verdict'], card['verdict'])}."]
    if blockers:
        lines.append("What stops it:")
        lines += [f"- {item['title']} (documents: {', '.join(documents_of(item)) or 'none cited'})" for item in blockers]
    if questions:
        lines.append("Still to answer:")
        lines += [f"- {item['title']}" for item in questions]
    lines.append(f"Who decides: the {row['decider']}. The check does not approve anything.")
    if row.get("allowed_actions"):
        lines.append(f"Possible next steps: {', '.join(row['allowed_actions'])}.")
    what_if = counterfactual_lines(card, with_ids=False)
    if what_if:
        lines.append("What would change the result (hypothetical, each verified by re-running the same check):")
        lines += what_if
    return "\n".join(lines)


def auditor_text(card, record, row_meaning=""):
    request, row = card["request"], card["decision"]
    lines = [f"Decision record {record.get('record_id') or card.get('record_id') or '(not recorded)'}"
             f"{', created ' + record['created_at'] if record.get('created_at') else ''}.",
             f"Request: {json.dumps(request, ensure_ascii=False, sort_keys=True)}.",
             f"Valid time (as_of): {record.get('as_of') or request.get('as_of')}; record time (known_at): "
             f"{request.get('known_at') or 'all records'}.",
             f"rules_version: {record.get('rules_version', '(unknown)')} (sha256 of the ontology, the decision table "
             f"and the rules module).",
             (f"Facts in force in the snapshot: {len(record['facts_in_force'])} (listed in the record)."
              if record.get("facts_in_force") else "Facts in force: no record written for this check."),
             "Procedure applied: (1) the snapshot of facts in force at as_of (supersession, then document rank and "
             "date for single-valued facts); (2) OWL 2 RL closure of the change's neighbourhood; (3) the rules "
             "R1a-R8 in core/rules.py; (4) the decision table, hit policy FIRST, on the change class and the rules "
             "that fired at blocker, warning or question. No language model is used from the snapshot on.",
             f"Rules fired: {', '.join(record.get('rules_fired') or []) or 'none'}."]
    for finding in card["findings"]:
        lines.append(f"- {finding['rule']} [{finding['severity']}] {finding['title']}")
        facts = [f"{step['fact_id']}@{step.get('source')}" for step in leaves(finding.get("evidence"))]
        if facts:
            lines.append(f"    rests on: {', '.join(dict.fromkeys(facts))}")
        if finding.get("note"):
            lines.append(f"    note: {finding['note']}")
    lines.append(f"Decision table row {record.get('decision_row') or row['row_id']}"
                 f"{': ' + row_meaning if row_meaning else ''}")
    lines.append(f"    decider: {row['decider']}; allowed actions: {', '.join(row['allowed_actions']) or 'none'}; "
                 f"rests on: {', '.join(row.get('rests_on') or [])}.")
    lines.append(f"Verdict: {record.get('verdict') or card['verdict']} (never 'approved').")
    used = facts_used(card)
    if used:
        lines.append("Quoted facts used:")
        lines += [f"- {item['fact_id']} [{item['source']}] {item['triple']}: \"{item['quote'][:160]}\"" for item in used]
    for item in card.get("not_checked") or []:
        lines.append(f"Not checked (not expressible by the rules): {item.get('source')}: \"{item.get('quote')}\"")
    for pair in card.get("contested") or []:
        lines.append(f"Contested, not used as a value: {pair.get('key')} ({pair.get('reason')}).")
    what_if = counterfactual_lines(card, with_ids=True)
    if what_if:
        lines.append("Counterfactuals (HYPOTHETICAL records, source HYPOTHETICAL, never written to the fact log; each "
                     "kept only if re-running the check on a copy of the snapshot clears the finding):")
        lines += what_if
    return "\n".join(lines)


def explain(card, record=None, row_meaning=""):
    """{"customer": str, "auditor": str, "rules_version": str, "row_id": str, "record_id": str}."""
    from core import decision
    record = dict(record or {})
    if not record.get("rules_version"):
        record["rules_version"] = decision.rules_version()   # no record written: the current rules
    record.setdefault("rules_fired", decision.fired_rules(card["findings"]))
    record.setdefault("decision_row", card["decision"]["row_id"])
    record.setdefault("verdict", card["verdict"])
    return {"customer": customer_text(card, record), "auditor": auditor_text(card, record, row_meaning),
            "rules_version": record.get("rules_version"), "row_id": card["decision"]["row_id"],
            "record_id": record.get("record_id") or card.get("record_id")}


def for_record(record_id, path=None):
    """Explanation of a past decision record: re-runs the recorded request (nothing new recorded) and says whether
    the current rules still give the recorded answer."""
    from core import check, counterfactual, decision
    records = [item for item in decision.read_records(path) if item["record_id"] == record_id]
    if not records:
        raise KeyError(f"no decision record {record_id}")
    record = records[-1]
    request = dict(record["request"], as_of=record["as_of"])
    card, _, _ = check.evaluate(request, record=False)
    attach(card, record)
    same = (decision.fired_rules(card["findings"]) == sorted(record.get("rules_fired") or [])
            and card["decision"]["row_id"] == record["decision_row"])
    current = decision.rules_version()
    result = card["explanation"]
    notes = []
    if current != record.get("rules_version"):
        notes.append(f"The rules changed since this record (now {current}).")
    if not same:
        notes.append("Re-running the recorded request today gives a different result; the recorded rules fired, "
                     "row and verdict above are the ones from the record.")
    result["re_run_matches"] = same
    result["notes"] = notes
    if notes:
        result["auditor"] += "\n" + " ".join(notes)
    return {"record": record, "explanation": result, "card": card}


def attach(card, record=None, table=None, log=None, counterfactuals=True):
    """Add `counterfactuals`, `counterfactual_all` and `explanation` to a card in place (used by core/check.py)."""
    from core import check, counterfactual, decision
    if counterfactuals:
        result = counterfactual.compute(log or check.memory(), card["request"], table=table)
        card["counterfactuals"] = result["items"]
        card["counterfactual_all"] = result["all"]
        card.setdefault("timings_ms", {})["counterfactuals"] = result["ms"]
    card["explanation"] = explain(card, record, decision.row_meaning(card["decision"]["row_id"], table))
    return card


def main():
    from core import check
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario")
    parser.add_argument("--record")
    parser.add_argument("--register", choices=("customer", "auditor", "both"), default="both")
    args = parser.parse_args()
    if args.record:
        result = for_record(args.record)["explanation"]
    else:
        card, entry, _ = check.evaluate(check.scenario(args.scenario or "main"), record=False)
        result = attach(card, entry)["explanation"]
    for register in ("customer", "auditor"):
        if args.register in (register, "both"):
            print(f"==== for the {register} ====\n{result[register]}\n")


if __name__ == "__main__":
    main()
