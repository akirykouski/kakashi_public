"""What would change the decision: verified counterfactuals for the blockers on a card.

    python -m core.counterfactual --scenario main

For each blocker (and warning) on a card, this module proposes the smallest change to the records the rule reads
(a record added, a record's status replaced, or, where no record can help, a different request) and keeps it only
if re-running the same check on a hypothetical copy of the snapshot clears that finding. Nothing here asks a model:
candidate edits come from a small table per rule id (CANDIDATES below), written from each rule's preconditions in
core/rules.py, and every kept edit is verified by running rules.check + decision.decide again.

Hypothetical facts live only in a `HypotheticalLog` view over the real fact log: the real log is never written, no
DecisionRecord is written for a hypothetical run, and the closure cache entries of hypothetical snapshots are
dropped afterwards. Every edit carries "hypothetical": true and source "HYPOTHETICAL".

Why: CJEU C-203/22 (Dun & Bradstreet Austria, 27 Feb 2025): an explanation describes the procedure and principles
actually applied, and saying how a change in the data would have changed the result may be appropriate.

Written 14 Nov 2026 (ws/counterfactual).
"""
import argparse
import datetime
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import decision, project, rules  # noqa: E402
from core.contracts import ChangeRequest  # noqa: E402
from core.project import Projection, request_entities  # noqa: E402

BUDGET_S = 1.5             # per card
SEVERITIES = ("blocker", "warning")   # findings we try to clear (questions have owners, not edits)
MAX_ALTERNATIVES = 2       # verified candidates kept per finding
HYPOTHETICAL_SOURCE = "HYPOTHETICAL"
SEVERITY_ORDER = {"blocker": 0, "warning": 1, "question": 2, "info": 3}
# Finding entities are a flat, ordered id list (rules.entity_ids keeps the order of the rule's entity dict).
# The leading ids name the finding's roles; they identify "the same finding" across runs (titles change with data).
ROLES = {
    "R1a": ("supplier", "record"),
    "R1b": ("supplier", "part", "site", "customer"),
    "R2": ("requirement", "change_type", "customer"),
    "R3": ("supplier", "issue"),
    "R5": ("coating", "substance", "law"),
    "R6:SourceChange": ("supplier", "material"),
    "R6:MaterialChange": ("part", "material", "drawing_material"),
    "R8": ("supplier", "part", "customer"),
}


# ---- a hypothetical view of the fact log -----------------------------------------------------------------

class HypotheticalLog:
    """Read-only view of a FactLog with some facts added and some removed. Never writes to the real log."""

    def __init__(self, log, added=(), removed_ids=()):
        self._log = log
        self._added = [dict(fact) for fact in added]
        self._removed = set(removed_ids)
        self.on_commit = []

    def all_facts(self, review="accepted"):
        facts = [fact for fact in self._log.all_facts(review=review) if fact["id"] not in self._removed]
        return facts + [dict(fact) for fact in self._added] if review in ("accepted", None) else facts

    def unclassified_items(self, *args, **kwargs):
        return self._log.unclassified_items(*args, **kwargs)

    def contested_records(self):
        return self._log.contested_records() if hasattr(self._log, "contested_records") else []


def severity_rank(finding):
    return SEVERITY_ORDER.get(finding["severity"], 9)


def normalise(request):
    known = set(ChangeRequest.__dataclass_fields__)
    known.discard("epistemic")
    return ChangeRequest(**{key: value for key, value in request.items() if key in known}).to_dict()


def run_rules(log, request, table=None):
    """The deciding part of core/check.evaluate (findings -> row, verdict) on any log, writing nothing."""
    request = normalise(request)
    as_of = request.get("as_of") or "2026-11-14"
    projection = Projection(log, as_of, known_at=request.get("known_at"), scope=request_entities(request))
    findings = sorted(rules.check(projection, request), key=severity_rank)
    fired = any(item["severity"] != "info" for item in findings)
    if fired or rules.covered(request, projection):
        row, verdict = decision.decide(findings, request, table)
    else:
        row, verdict = decision.to_decision_row((table or decision.load_table())["rows"][-1]), "not_covered"
    return {"findings": findings, "row": row, "verdict": verdict, "projection": projection}


# ---- hypothetical facts ----------------------------------------------------------------------------------

class Builder:
    """Makes hypothetical fact rows dated for the check (valid from as_of, recorded no later than known_at)."""

    def __init__(self, request):
        self.as_of = request.get("as_of") or "2026-11-14"
        known_at = request.get("known_at")
        day = min(self.as_of, known_at[:10]) if known_at else self.as_of
        self.recorded_at = f"{day}T00:00:00+00:00"
        self.count = 0

    def fact(self, subject, predicate, obj, literal=False):
        self.count += 1
        return {"id": f"HYP-{self.count:03d}", "s": subject, "p": predicate,
                "o": json.dumps(obj) if literal else obj, "source": HYPOTHETICAL_SOURCE,
                "quote": "hypothetical record, not in any document", "context_quote": None,
                "valid_from": self.as_of, "valid_to": None, "kind": "assert", "epistemic": None, "rank": 2,
                "supersedes": None, "author": None, "recorded_at": self.recorded_at, "review": "accepted",
                "proposed_by": None, "reviewed_by": None}

    def record(self, record_id, class_name, properties):
        facts = [self.fact(record_id, "type", class_name)]
        for predicate, obj, literal in properties:
            facts.append(self.fact(record_id, predicate, obj, literal))
        return facts


def triple_text(fact):
    obj = fact["o"]
    if obj.startswith('"'):
        obj = json.loads(obj)
        obj = f'"{obj}"'
    return f"{fact['s']} {fact['p']} {obj}"


def add_record(builder, record_id, class_name, properties, plain):
    facts = builder.record(record_id, class_name, properties)
    body = ", ".join(triple_text(fact)[len(record_id) + 1:] for fact in facts[1:])
    return {"action": "add", "triple": f"{record_id} a {class_name}: {body}", "plain": plain,
            "record": record_id, "facts": facts, "hypothetical": True}


def remove_facts(facts, plain):
    return {"action": "remove", "triple": "; ".join(triple_text(fact) for fact in facts), "plain": plain,
            "fact_ids": [fact["id"] for fact in facts], "sources": sorted({fact["source"] for fact in facts}),
            "hypothetical": True}


def replace_status(builder, projection, record, new_status, plain):
    """Remove the record's status fact(s) in force, add one with new_status: two edits."""
    old = projection.facts_for(record, "status")
    if not old:
        return None
    old_value = json.loads(old[0]["o"]) if old[0]["o"].startswith('"') else old[0]["o"]
    removal = remove_facts(old, f"{record}: status '{old_value}' replaced")
    removal["replaced_by_next"] = True   # the add below says it in words; readers may skip this one
    return [removal,
            {"action": "add", "triple": f'{record} status "{new_status}"', "plain": plain, "record": record,
             "facts": [builder.fact(record, "status", new_status, literal=True)], "hypothetical": True}]


def label(projection, name):
    return projection.label(name) if name else name


# ---- candidate edits per rule id (from the preconditions in core/rules.py) ----------------------------------
# Each builder returns a list of candidates; a candidate = {"edits": [...]} (fact edits) or
# {"request": {...overrides}, "edits": [...]} (a different request). Order = preference.

def cand_r1a(projection, request, finding, builder):
    """R1a fires while the supplier's qualification in force is conditional / disqualified (POL-QP11-4.3)."""
    record, supplier = roles(finding, request["type"]).get("record"), roles(finding, request["type"]).get("supplier")
    edits = replace_status(builder, projection, record, "approved",
                           f"the qualification {record} of {label(projection, supplier)} reads 'approved' "
                           f"(for example after a passed re-audit)")
    return [{"edits": edits}] if edits else []


def approval_edit(projection, request, builder, supplier, part, site, customer):
    record_id = f"HYP-APR-{supplier}-{part}-{site}-{customer}"
    return add_record(builder, record_id, "PartApproval",
                      [("approvedSupplier", supplier, False), ("approvedPart", part, False),
                       ("approvedSite", site, False), ("approvedForCustomer", customer, False),
                       ("status", "approved", True)],
                      f"a part approval (PPAP) {supplier} x {part} x {site} x {customer}, status approved: "
                      f"{label(projection, customer)} has released {label(projection, supplier)} for {part} at {site}")


def cand_r1b(projection, request, finding, builder):
    """R1b fires when no approved PartApproval supplier x part x site x customer exists (POL-QP11-4.2)."""
    entities = roles(finding, request["type"])
    if not all(entities.get(key) for key in ("supplier", "part", "site", "customer")):
        return []
    return [{"edits": [approval_edit(projection, request, builder, entities["supplier"], entities["part"],
                                     entities["site"], entities["customer"])]}]


def cand_r2(projection, request, finding, builder):
    """R2 blocker clears when the new source is already approved for the part and customer (SourceChange), or a
    valid deviation covers the part, the change class and the supplier (covering_deviation)."""
    entities, part, change_type = roles(finding, request["type"]), request["part"], request["type"]
    customer = entities.get("customer")
    found = []
    supplier = request.get("to_supplier")
    if change_type == "SourceChange" and supplier and customer:
        sites = rules.target_sites(projection, request, customer)
        if sites:
            found.append({"edits": [approval_edit(projection, request, builder, supplier, part, sites[0], customer)]})
    suppliers = [item for item in (request.get("to_supplier"), request.get("from_supplier")) if item]
    if not suppliers:
        suppliers = sorted({item["supplier"] for item in rules.approvals(projection, part=part)
                            if item["status"] == "approved"})
    if suppliers:
        record_id = f"HYP-DEV-{part}-{change_type}"
        properties = [("status", "valid", True), ("concernsPart", part, False),
                      ("permitsChangeType", change_type, False), ("concernsSupplier", suppliers[0], False)]
        # no permitsCoating: the deviation covers the change class on the part (rules.covering_deviation), so it
        # also covers the request when another counterfactual changes the coating
        found.append({"edits": [add_record(builder, record_id, "Deviation", properties,
                                           f"a valid deviation granted by the customer for {change_type} on {part} "
                                           f"(supplier {suppliers[0]})")]})
    return found


def cand_r3(projection, request, finding, builder):
    """R3 fires while the supplier's 8D is open (open_issues reads status 'open')."""
    issue = roles(finding, request["type"]).get("issue")
    edits = replace_status(builder, projection, issue, "closed",
                           f"8D {issue} is closed (effectiveness of the corrective action verified)")
    return [{"edits": edits}] if edits else []


def cand_r5(projection, request, finding, builder):
    """R5 reads the law and the coating's substances: no record of ours clears it. The only change is a different
    request: a catalogue coating without a substance the part's laws restrict (verified by re-running)."""
    part = request["part"]
    restricted = set()
    for law in projection.objects(part, "subjectToLaw"):
        restricted |= set(projection.objects(law, "restricts"))
    found = []
    for coating in projection.instances("Coating"):
        if coating == request.get("new_coating"):
            continue
        if set(projection.objects(coating, "containsSubstance")) & restricted:
            continue
        found.append({"request": {"new_coating": coating},
                      "edits": [{"action": "change_request", "triple": f"request new_coating {coating}",
                                 "plain": f"the request asks for {label(projection, coating)} ({coating}) instead of "
                                          f"{label(projection, request.get('new_coating'))} (the rules check restricted substances only, not whether the coating suits the base material)",
                                 "hypothetical": True}]})
    return found


def cand_r6(projection, request, finding, builder):
    """R6 on a SourceChange: no SupplierCapability supplier x drawing material. On a MaterialChange: the new
    material is not the drawing designation (change the drawing first, POL-QP15-3.5)."""
    entities = roles(finding, request["type"])
    if request["type"] == "SourceChange" and entities.get("supplier") and entities.get("material"):
        supplier, material = entities["supplier"], entities["material"]
        return [{"edits": [add_record(builder, f"HYP-CAP-{supplier}-{material}", "SupplierCapability",
                                      [("capableSupplier", supplier, False), ("capableMaterial", material, False)],
                                      f"a capability record: {label(projection, supplier)} is qualified for "
                                      f"{label(projection, material)}")]}]
    if request["type"] == "MaterialChange" and entities.get("drawing_material"):
        part, drawing, new = request["part"], entities["drawing_material"], entities["material"]
        old = projection.facts_for(part, "madeOf", drawing)
        if not old:
            return []
        return [{"edits": [remove_facts(old, f"the drawing of {part} no longer designates {label(projection, drawing)}"),
                           {"action": "add", "triple": f"{part} madeOf {new}", "record": part,
                            "plain": f"the drawing of {part} is revised to designate {label(projection, new)}",
                            "facts": [builder.fact(part, "madeOf", new)], "hypothetical": True}]}]
    return []


CANDIDATES = {
    "R1a": cand_r1a,   # supplier qualification status
    "R1b": cand_r1b,   # part approval supplier x part x site x customer
    "R2": cand_r2,     # customer approval: existing approval, or a valid deviation
    "R3": cand_r3,     # open 8D
    "R5": cand_r5,     # restricted substance: only a different coating
    "R6": cand_r6,     # material capability / drawing designation
    # R8 (sub-tier, customer approval required): rule_subtier has no exception a record could meet.
}
NO_EDIT_REASON = {
    "R8": "No record the rules read can clear this: R8 has no exception (no deviation or existing approval "
          "ends it). Only the customer's written approval, outside the fact log, answers it.",
}


# ---- verification ----------------------------------------------------------------------------------------

def role_names(finding, change_type):
    return ROLES.get(f"{finding['rule']}:{change_type}") or ROLES.get(finding["rule"])


def roles(finding, change_type):
    """{role: id} for a finding (see ROLES); {} when the rule has no role table."""
    names = role_names(finding, change_type) or ()
    return dict(zip(names, finding.get("entities") or []))


def finding_key(finding, change_type=None):
    names = role_names(finding, change_type)
    entities = finding.get("entities") or []
    return (finding["rule"],) + tuple(entities[:len(names)] if names else entities)


def still_there(finding, findings, change_type=None):
    key, level = finding_key(finding, change_type), SEVERITY_ORDER[finding["severity"]]
    return any(finding_key(item, change_type) == key and SEVERITY_ORDER.get(item["severity"], 9) <= level for item in findings)


def edit_signature(candidate):
    return json.dumps([candidate.get("request") or {},
                       [(edit["action"], edit["triple"]) for edit in candidate["edits"]]], sort_keys=True)


def apply(log, request, candidates):
    """Hypothetical log + request for a list of candidates applied together."""
    added, removed, overrides = [], set(), {}
    for candidate in candidates:
        overrides.update(candidate.get("request") or {})
        for edit in candidate["edits"]:
            added += edit.get("facts") or []
            removed |= set(edit.get("fact_ids") or [])
    return HypotheticalLog(log, added, removed), dict(request, **overrides)


def public_edit(edit):
    return {key: value for key, value in edit.items() if key != "facts"}


def summary(result):
    return {"row_id": result["row"]["row_id"], "verdict": result["verdict"], "decider": result["row"]["decider"],
            "allowed_actions": result["row"]["allowed_actions"], "rules_fired": decision.fired_rules(result["findings"]),
            "remaining": [{"rule": item["rule"], "severity": item["severity"], "title": item["title"]}
                          for item in result["findings"] if item["severity"] in ("blocker", "warning", "question")]}


def compute(log, request, findings=None, table=None, budget_s=BUDGET_S):
    """Counterfactuals for one card. Returns {"items": [...], "all": {...}, "ms": .., "runs": ..}.

    items: one per blocker / warning: {blocker_rule, severity, title, edits, verified, row_if_applied, clears,
    alternatives, side_effects} or {..., verified: false, reason}. all: the row and verdict with the first verified
    edit of every finding applied together."""
    started = time.perf_counter()
    deadline = started + budget_s
    request = normalise(request)
    cache_keys = set(project._closure_cache)
    try:
        base = run_rules(log, request, table)
        findings = base["findings"] if findings is None else findings
        projection = base["projection"]
        builder = Builder(request)
        targets = [item for item in findings if item["severity"] in SEVERITIES]
        runs, items, results, verified_candidates = 1, [], {}, []

        def verify(candidate):
            nonlocal runs
            signature = edit_signature(candidate)
            if signature not in results:
                hyp_log, hyp_request = apply(log, request, [candidate])
                results[signature] = run_rules(hyp_log, hyp_request, table)
                runs += 1
            return results[signature]

        for target in targets:
            item = {"blocker_rule": target["rule"], "severity": target["severity"], "title": target["title"],
                    "hypothetical": True, "verified": False, "edits": [], "alternatives": []}
            builder_fn = CANDIDATES.get(target["rule"])
            candidates = builder_fn(projection, request, target, builder) if builder_fn else []
            # an edit already verified for an earlier finding that also clears this one comes first (no new run)
            reused = [candidate for candidate in verified_candidates
                      if not still_there(target, results[edit_signature(candidate)]["findings"], request["type"])]
            signatures = {edit_signature(candidate) for candidate in reused}
            candidates = reused[:1] + [candidate for candidate in candidates if edit_signature(candidate) not in signatures]
            if not candidates:
                item["reason"] = NO_EDIT_REASON.get(target["rule"], "No candidate edit for this rule.")
            for candidate in candidates:
                if len(item["alternatives"]) + item["verified"] >= MAX_ALTERNATIVES:
                    break
                if time.perf_counter() > deadline:
                    item.setdefault("reason", "Time budget reached before this candidate was verified.")
                    break
                result = verify(candidate)
                if still_there(target, result["findings"], request["type"]):
                    continue
                verified = {"edits": [public_edit(edit) for edit in candidate["edits"]], "verified": True,
                            "row_if_applied": summary(result)["row_id"],
                            "verdict_if_applied": result["verdict"],
                            "clears": sorted({finding["rule"] for finding in targets
                                              if not still_there(finding, result["findings"], request["type"])}),
                            "side_effects": [{"rule": new["rule"], "severity": new["severity"], "title": new["title"]}
                                             for new in result["findings"] if new["severity"] in SEVERITIES
                                             and not any(finding_key(new, request["type"]) == finding_key(old, request["type"]) for old in findings)],
                            "_candidate": candidate}
                if candidate not in verified_candidates:
                    verified_candidates.append(candidate)
                if not item["verified"]:
                    item.update(verified)
                    item.pop("reason", None)
                else:
                    item["alternatives"].append({key: value for key, value in verified.items() if key != "_candidate"})
            if not item["verified"] and candidates and "reason" not in item:
                item["reason"] = "No candidate edit cleared this finding when the check was re-run."
            items.append(item)

        # all minimal edits together (first verified candidate of each finding, each distinct edit once)
        chosen, seen = [], set()
        for item in items:
            candidate = item.get("_candidate")
            if candidate and edit_signature(candidate) not in seen:
                seen.add(edit_signature(candidate))
                chosen.append(candidate)
        combined = None
        if chosen and time.perf_counter() <= deadline + budget_s:   # the combined run is always worth showing
            hyp_log, hyp_request = apply(log, request, chosen)
            result = run_rules(hyp_log, hyp_request, table)
            runs += 1
            combined = dict(summary(result), hypothetical=True,
                            edits=[public_edit(edit) for candidate in chosen for edit in candidate["edits"]],
                            changes=[[public_edit(edit) for edit in candidate["edits"]] for candidate in chosen])
        for item in items:
            item.pop("_candidate", None)
        return {"items": items, "all": combined, "runs": runs,
                "ms": round((time.perf_counter() - started) * 1000, 1), "budget_ms": budget_s * 1000}
    finally:
        for key in set(project._closure_cache) - cache_keys:   # hypothetical closures never stay cached
            project._closure_cache.pop(key, None)


def plain_all(combined):
    """One sentence about the combined counterfactual."""
    if not combined:
        return ""
    count = len(combined["changes"])
    verdict_text = {"blockers_found": "blockers found", "needs_info": "needs information",
                    "no_blockers_found": "no blockers found", "not_covered": "not covered by any rule"}
    text = (f"With these {count} hypothetical change{'s' if count != 1 else ''} the table row would be "
            f"{combined['row_id']}: {verdict_text.get(combined['verdict'], combined['verdict'])}")
    if combined["verdict"] == "no_blockers_found":
        text += " — still not an approval"
    left = [item["rule"] for item in combined["remaining"]]
    if left:
        text += f" (still open: {', '.join(sorted(set(left)))})"
    return text + "."


def main():
    from core import check
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="main")
    args = parser.parse_args()
    request = check.scenario(args.scenario)
    result = compute(check.memory(), request)
    for item in result["items"]:
        print(f"[{item['severity']}] {item['blocker_rule']}: {item['title']}")
        if item["verified"]:
            for edit in item["edits"]:
                print(f"   HYPOTHETICAL {edit['action']}: {edit['plain']}")
            print(f"   verified by re-run; clears {item['clears']}; row if applied {item['row_if_applied']}")
            for alternative in item["alternatives"]:
                print(f"   or: {'; '.join(edit['plain'] for edit in alternative['edits'])} "
                      f"(row {alternative['row_if_applied']})")
        else:
            print(f"   {item.get('reason')}")
    print(plain_all(result["all"]))
    print(f"{result['runs']} runs, {result['ms']} ms")


if __name__ == "__main__":
    main()
