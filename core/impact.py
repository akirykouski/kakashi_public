"""A document changed: what is affected (#29, docs/research/kva-oida-hooks.md 4.5).

    python -m core.impact CSR-AUR-R3            # text report
    python -m core.impact CSR-AUR-R3 --json

Given a document id that a newer revision supersedes (CSR-AUR-R4 supersedes CSR-AUR-R3), list everything that
rests on the old revision and mark it "review: source superseded":

  facts               every fact whose source is the old document, whose subject or object is the document
                      (CUST-AUR imposes CSR-AUR-R3), or whose literal value cites it by id. A registry row that
                      merely lists the id in its quote is not counted (it would flag every column of the row).
  table_rows          decision-table rows whose rests_on cites the document, or cites a rule that reads a
                      predicate the old document asserts (RULE_READS below)
  recorded_decisions  decision records (data/decisions.jsonl) whose facts_in_force use one of those facts or
                      whose request names the document
  past_decisions      past decision records in the data (Decision records in the fact log; meeting decisions;
                      records exposed by core/memory.py when present) whose source or reason cites the document

A report over the existing supersession chain: it reads, never writes. Deterministic for the same inputs.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REVIEW = "review: source superseded"
CHANGED = "review: source cited"   # the document is not superseded (yet): the report still lists what cites it

# Predicates each rule reads (core/rules.py). A table row resting on a rule is affected when the old document
# asserted one of the predicates that rule reads.
RULE_READS = {
    "R1a": {"qualifiedSupplier", "status"},
    "R1b": {"approvedSupplier", "approvedPart", "approvedSite", "approvedForCustomer", "status", "completeForPlant",
            "completeForCustomer", "completeForSeries", "completeForScope", "deliveredTo"},
    "R2": {"subjectTo", "imposes", "requiresCustomerApprovalFor", "requiresNotificationFor", "requiresNoticeFor",
           "leadTimeDays", "hasConsequence", "permitsChangeType", "permitsCoating"},
    "R3": {"hasIssue", "concernsMaterial", "concernsPart", "failureFeature", "policyValue", "policyFor"},
    "R5": {"containsSubstance", "restricts", "subjectToLaw"},
    "R6": {"madeOf", "minYieldMPa", "typicalYieldMPa", "capableMaterial", "capableSupplier",
           "hasSpecialCharacteristic"},
    "R7": {"questionOwner", "requiresCertificateFor", "certSupplier", "certMaterial"},
    "R8": {"requiresCustomerApprovalForSubTier", "requiresNotificationForSubTier", "feedsInto", "suppliesTo"},
}
DECISION_CLASSES = ("Decision", "PastDecision")


def cites(text, doc):
    """True when `text` names `doc` as a whole id (CSR-AUR-R3 does not match CSR-AUR-R30)."""
    if not isinstance(text, str) or not text:
        return False
    return re.search(rf"(?<![A-Za-z0-9-]){re.escape(doc)}(?![A-Za-z0-9])", text) is not None


def _deep_cites(value, doc):
    if isinstance(value, str):
        return cites(value, doc)
    if isinstance(value, dict):
        return any(_deep_cites(item, doc) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_deep_cites(item, doc) for item in value)
    return False


# ---- inputs ----------------------------------------------------------------------------------------------

def default_facts():
    from core import rules
    from core.factlog import default_log
    log = rules.extend_log(default_log())
    return log.all_facts(review=None)


def meeting_decisions(meetings_dir=None):
    folder = meetings_dir or os.path.join(ROOT, "data", "meetings")
    found = []
    if not os.path.isdir(folder):
        return found
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as handle:
            meeting = json.load(handle)
        for decision in meeting.get("decisions") or []:
            found.append(dict(decision, meeting=meeting.get("id"), source=meeting.get("id")))
    return found


def memory_records():
    """Past decision / maintenance records from core/memory.py, if that module exists. Read generically: any
    module-level list of dicts, and the result of any zero-argument function whose name says it lists records."""
    try:
        from core import memory
    except Exception:  # module absent (or broken): the report covers the other inputs
        return []
    found = []
    for name in sorted(dir(memory)):
        if name.startswith("_"):
            continue
        value = getattr(memory, name)
        if callable(value) and re.match(r"^(past_|all_|list_|load_)?(decisions|records|maintenance|items)", name):
            try:
                value = value()
            except TypeError:
                continue
            except Exception:
                continue
        if isinstance(value, (list, tuple)) and value and all(isinstance(item, dict) for item in value):
            for item in value:
                found.append(dict(item, _from=f"core.memory.{name}"))
    return found


# ---- the report ------------------------------------------------------------------------------------------

def _fact_item(fact, why, status):
    return {"fact_id": fact["id"], "s": fact["s"], "p": fact["p"], "o": fact["o"], "source": fact["source"],
            "quote": (fact.get("quote") or "").replace("\n", " "), "valid_from": fact.get("valid_from"),
            "valid_to": fact.get("valid_to"), "review_state": fact.get("review") or "accepted", "why": why,
            "status": status}


def impact(doc, facts=None, table=None, records=None, past=None):
    """The report for one document id. Inputs default to the repository's data; tests pass their own."""
    if facts is None:
        facts = default_facts()
    if table is None:
        from core import decision
        table = decision.load_table()
    if records is None:
        from core import decision
        records = decision.read_records()
    if past is None:
        past = meeting_decisions() + memory_records()

    supersession = [fact for fact in facts if fact["p"] == "supersedes" and fact["o"] == doc
                    and (fact.get("review") or "accepted") == "accepted"]
    replaced_by = sorted({fact["s"] for fact in supersession})
    status = REVIEW if replaced_by else CHANGED
    supersession_ids = {fact["id"] for fact in supersession}

    affected = []
    for fact in sorted(facts, key=lambda item: item["id"]):
        if fact["id"] in supersession_ids:
            continue
        if fact["source"] == doc:
            why = "source"
        elif fact["o"] == doc or fact["s"] == doc:
            why = "points to the document"
        elif fact["o"].startswith('"') and cites(fact["o"], doc):
            why = "value cites the document"
        else:
            continue
        affected.append(_fact_item(fact, why, status))
    fact_ids = {item["fact_id"] for item in affected}
    doc_predicates = {fact["p"] for fact in facts if fact["source"] == doc or fact["s"] == doc}

    rows = []
    for row in table.get("rows") or []:
        rests_on = row.get("rests_on") or []
        direct = [item for item in rests_on if cites(str(item), doc)]
        via = sorted(rule for rule in rests_on if rule in RULE_READS and RULE_READS[rule] & doc_predicates)
        if not direct and not via:
            continue
        reads = sorted(set().union(*(RULE_READS[rule] & doc_predicates for rule in via))) if via else []
        rows.append({"row_id": row["id"], "meaning": row.get("meaning"), "rests_on": rests_on,
                     "cites": direct, "via_rules": via, "reads": reads, "status": status})

    recorded = []
    for entry in records:
        used = sorted(set(entry.get("facts_in_force") or []) & fact_ids)
        named = _deep_cites(entry.get("request"), doc)
        if not used and not named:
            continue
        recorded.append({"record_id": entry.get("record_id"), "created_at": entry.get("created_at"),
                         "as_of": entry.get("as_of"), "request": entry.get("request"),
                         "verdict": entry.get("verdict"), "decision_row": entry.get("decision_row"),
                         "facts_used": used, "names_document": named, "status": status})

    past_items = []
    by_subject = {}
    for fact in facts:
        by_subject.setdefault(fact["s"], []).append(fact)
    for subject in sorted(by_subject):
        record_facts = by_subject[subject]
        if not any(fact["p"] == "type" and fact["o"] in DECISION_CLASSES for fact in record_facts):
            continue
        hits = [fact for fact in record_facts if fact["source"] == doc or fact["o"] == doc
                or cites(fact["o"], doc) or cites(fact.get("quote"), doc)]
        if hits:
            reason = next((fact["o"] for fact in record_facts if fact["p"] == "reason"), None)
            past_items.append({"id": subject, "from": "fact log", "source": record_facts[0]["source"],
                               "reason": reason, "cited_by": sorted(fact["id"] for fact in hits), "status": status})
    seen = {item["id"] for item in past_items}
    for item in past:
        identifier = item.get("id") or item.get("record_id")
        if identifier in seen or not _deep_cites(item, doc):
            continue
        seen.add(identifier)
        past_items.append({"id": identifier, "from": item.get("_from") or item.get("meeting") or "data",
                           "source": item.get("source"), "reason": item.get("reason") or item.get("text"),
                           "status": status})

    return {
        "doc": doc, "superseded": bool(replaced_by), "replaced_by": replaced_by, "status": status,
        "supersession": [_fact_item(fact, "supersedes", "in force") for fact in supersession],
        "facts": affected, "table_rows": rows, "recorded_decisions": recorded, "past_decisions": past_items,
        "counts": {"facts": len(affected), "table_rows": len(rows), "recorded_decisions": len(recorded),
                   "past_decisions": len(past_items)},
    }


def print_report(report):
    doc = report["doc"]
    if report["superseded"]:
        print(f"{doc} is superseded by {', '.join(report['replaced_by'])}. Everything below: {report['status']}.")
    else:
        print(f"{doc} is not superseded by any record in force. Listing what cites it.")
    counts = report["counts"]
    print(f"\nFacts ({counts['facts']}):")
    for item in report["facts"]:
        print(f"  - {item['fact_id']}: {item['s']} {item['p']} {item['o']}  [{item['why']}; {item['source']}: "
              f"\"{item['quote'][:90]}\"]")
    print(f"\nDecision-table rows ({counts['table_rows']}):")
    for row in report["table_rows"]:
        how = ", ".join(filter(None, [f"cites {', '.join(row['cites'])}" if row["cites"] else "",
                                      f"via {', '.join(row['via_rules'])} reading {', '.join(row['reads'])}"
                                      if row["via_rules"] else ""]))
        print(f"  - {row['row_id']}: {row['meaning']}  ({how})")
    print(f"\nRecorded decisions ({counts['recorded_decisions']}):")
    for entry in report["recorded_decisions"]:
        print(f"  - {entry['record_id']} as of {entry['as_of']}: row {entry['decision_row']}, {entry['verdict']} "
              f"({len(entry['facts_used'])} facts from {doc})")
    print(f"\nPast decisions ({counts['past_decisions']}):")
    for item in report["past_decisions"]:
        print(f"  - {item['id']} ({item['from']}): {item.get('reason')}")


def main():
    parser = argparse.ArgumentParser(description="What does a document change affect?")
    parser.add_argument("doc", help="document id, e.g. CSR-AUR-R3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = impact(args.doc)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
