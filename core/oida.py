"""OIDA vocabulary on the card: epistemic type badges (#26) and question urgency with BLOCKS edges (#27).

Post-processing only: runs after rules.check and decision.decide, adds fields, never changes a finding's rule,
severity, evidence or the decision row. Design: docs/research/kva-oida-hooks.md sections 4.1 and 4.2.

  epistemic  CONSTRAINT | DECISION | EVIDENCE | PLAN | QUESTION, read from the `lcc:epistemicType` annotation of
             the record's class in ontology/lcc.ttl (Projection.epistemic_type). None when no class says.
  blocks     {"part", "change_type"}: the change an open question holds up.
  urgency    h = clamp(age_days/30*0.3 + blocking_edges*0.2 + stakes*0.5, 0, 1); stakes from
             rules_data/oida_stakes.json (policy data, not code).

Written 14 Nov 2026 (issues #26, #27).
"""
import json
import os
from datetime import date

try:
    from .project import ROOT
except ImportError:  # core/ on sys.path
    from project import ROOT

STAKES_PATH = os.path.join(ROOT, "rules_data", "oida_stakes.json")
QUESTION = "QUESTION"
_stakes_table = {}


def stakes_table():
    if not _stakes_table:
        with open(STAKES_PATH) as file:
            _stakes_table.update(json.load(file))
    return _stakes_table


# ---- #26 epistemic type ------------------------------------------------------------------------------------

def triple_parts(step):
    """Subject and object ids of a proof step's triple ("s p o")."""
    parts = (step.get("triple") or "").split(" ", 2)
    if len(parts) < 3:
        return parts[:1], None
    return [parts[0], parts[2]], parts[1]


def leaf_type(projection, step):
    """Type of the record the leaf is about (its subject's class), else of the document it quotes."""
    ids, _ = triple_parts(step)
    found = projection.epistemic_type(ids[0]) if ids else None
    if found is None and step.get("source"):
        found = projection.epistemic_type(step["source"])
    return found


def annotate_steps(projection, steps):
    """Set `epistemic` on every leaf (non-inferred step), recursively. Returns the leaf types in order."""
    found = []
    for step in steps:
        if step.get("inferred"):
            found += annotate_steps(projection, step.get("premises") or [])
        else:
            step["epistemic"] = leaf_type(projection, step)
            found.append(step["epistemic"])
    return found


def finding_type(projection, finding, leaf_types):
    """QUESTION for a question; otherwise the class of the first entity that has one, else of the first leaf."""
    if finding["severity"] == "question":
        return QUESTION
    for entity in finding.get("entities") or []:
        found = projection.epistemic_type(entity)
        if found:
            return found
    return next((item for item in leaf_types if item), None)


# ---- #27 urgency -------------------------------------------------------------------------------------------

def leaf_steps(steps):
    for step in steps:
        if step.get("inferred"):
            yield from leaf_steps(step.get("premises") or [])
        else:
            yield step


def age_days(projection, finding, as_of):
    """Days since the most recent dated evidence behind the question (valid_from of its leaf facts), else 0."""
    by_id = {fact["id"]: fact for fact in projection.current_facts}
    dates = [by_id[step["fact_id"]]["valid_from"] for step in leaf_steps(finding["evidence"])
             if step.get("fact_id") in by_id and by_id[step["fact_id"]].get("valid_from")]
    if not dates or not as_of:
        return 0
    days = (date.fromisoformat(as_of[:10]) - date.fromisoformat(max(dates)[:10])).days
    return max(days, 0)


def question_scope(projection, finding, request, table):
    """Ids the question touches: its entities, its proof steps, the change it blocks; one hop along expand_via."""
    scope = set(finding.get("entities") or [])
    for step in leaf_steps(finding["evidence"]):
        ids, _ = triple_parts(step)
        scope.update(item for item in ids if item)
    scope.update(request[key] for key in table.get("scope_from_change", []) if request.get(key))
    for item in list(scope):
        for predicate in table.get("expand_via", []):
            scope.update(projection.objects(item, predicate))
    return scope


def stakes(projection, finding, request):
    table = stakes_table()
    scope = question_scope(projection, finding, request, table)
    best = table.get("default", 0.3)
    for entry in table.get("stakes", []):
        if "when_class" in entry:
            hit = any(projection.is_a(item, entry["when_class"]) for item in scope)
        elif "when_requires_for_change" in entry:
            predicate = entry["when_requires_for_change"]
            hit = any(request.get("type") in projection.objects(item, predicate) for item in scope)
        else:
            hit = False
        if hit:
            best = max(best, entry["stakes"])
    return best


def urgency(age, blocking_edges, stakes_value, window=30):
    """OIDA question urgency: clamp(age_days/30*0.3 + blocking_edges*0.2 + stakes*0.5, 0, 1)."""
    value = age / window * 0.3 + blocking_edges * 0.2 + stakes_value * 0.5
    return round(min(max(value, 0.0), 1.0), 3)


# ---- card ----------------------------------------------------------------------------------------------------

def annotate(projection, request, findings):
    """Add epistemic / blocks / urgency to findings in place; return them sorted for the card (severity order
    kept, questions by urgency, highest first). Adds `epistemic` to the request dict too (a ChangeRequest is a
    PLAN)."""
    request["epistemic"] = projection.epistemic_type("ChangeRequest")
    blockers = sum(1 for item in findings if item["severity"] == "blocker")
    window = stakes_table().get("age_window_days", 30)
    as_of = request.get("as_of")
    for finding in findings:
        finding["epistemic"] = finding_type(projection, finding, annotate_steps(projection, finding["evidence"]))
        if finding["severity"] == "question":
            finding["blocks"] = {"part": request.get("part"), "change_type": request.get("type")}
            finding["stakes"] = stakes(projection, finding, request)
            finding["age_days"] = age_days(projection, finding, as_of)
            finding["blocking_edges"] = blockers
            finding["urgency"] = urgency(finding["age_days"], blockers, finding["stakes"], window)
    return sorted(findings, key=card_order)


SEVERITY_ORDER = {"blocker": 0, "warning": 1, "question": 2, "info": 3}


def card_order(finding):
    """Severity first (as rules.py sorts), then the most urgent question first."""
    return SEVERITY_ORDER.get(finding["severity"], 9), -(finding.get("urgency") or 0)
