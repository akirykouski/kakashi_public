"""The declared decision model: decision table, verdict, coverage check, decision record.

The decision model is `core/decision_table.yaml`, not this file. This module only loads the table, checks it
is well formed, finds the first matching row (hit policy FIRST), proves which inputs fall to R0 ("no rule
covers this, a person decides"), and writes an append-only record of every decision with a hash of the rules
that produced it.

Input is plain Finding dicts (core/contracts.py); nothing here depends on how the findings were made.

Written 14 Nov 2026 after 10:30 (workstream D), new code.

CLI:
    python -m core.decision                 # coverage check of the table
    python -m core.decision --json          # same, as JSON
    python -m core.decision --version       # rules_version and the files it hashes
"""
import argparse
import datetime
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from core.contracts import CHANGE_TYPES, VERDICTS, DecisionRecord, DecisionRow

ROOT = Path(__file__).resolve().parent.parent
TABLE_PATH = ROOT / "core" / "decision_table.yaml"
RECORDS_PATH = ROOT / "data" / "decisions.jsonl"
FALLBACK_ROW = "R0"
CONDITION_KEYS = ("classes", "all", "any", "none")

# Files whose content defines "the rules". A missing file is skipped and listed, never an error.
RULES_VERSION_PATTERNS = (
    "ontology/*.ttl",
    "ontology/RULES.md",
    "core/decision_table.yaml",
    "core/rules.py",
    "rules_data/facts.jsonl",  # policy facts the rules read (8D level, completeness scope, owners)
)

# Findings at these severities enter the table. Info findings are shown, but decide nothing.
DECIDING_SEVERITIES = ("blocker", "warning", "question")


class TableError(ValueError):
    """The decision table is not well formed."""


# ---- load and validate ----------------------------------------------------------------------------------

def load_table(path=None):
    """Read the table, validate it, and return it with every group name expanded to a plain list."""
    table_path = Path(path) if path else TABLE_PATH
    with open(table_path, encoding="utf-8") as handle:
        table = yaml.safe_load(handle)
    validate_table(table)
    return table


def expand(value, groups, everything):
    """A condition value is a list, a group name, or "any". Return it as a list."""
    if value == "any":
        return list(everything)
    if isinstance(value, str):
        if value not in groups:
            raise TableError(f"unknown group name '{value}'")
        return list(groups[value])
    return list(value)


def validate_table(table):
    problems = []
    if table.get("hit_policy") != "first":
        problems.append("hit_policy must be 'first'")
    rule_ids = table.get("rules") or []
    actions = set(table.get("actions") or [])
    deciders = set(table.get("deciders") or [])
    class_groups = table.get("class_groups") or {}
    rule_groups = table.get("rule_groups") or {}
    for name, members in class_groups.items():
        for change_class in members:
            if change_class not in CHANGE_TYPES:
                problems.append(f"class group {name}: '{change_class}' is not in CHANGE_TYPES")
    for name, members in rule_groups.items():
        for rule_id in members:
            if rule_id not in rule_ids:
                problems.append(f"rule group {name}: '{rule_id}' is not in rules")
    rows = table.get("rows") or []
    seen = set()
    for index, row in enumerate(rows):
        row_id = row.get("id")
        if not row_id or row_id in seen:
            problems.append(f"row {index}: missing or duplicate id '{row_id}'")
        seen.add(row_id)
        when = row.get("when")
        if when is None or not isinstance(when, dict):
            problems.append(f"{row_id}: 'when' must be a mapping")
            continue
        for key in when:
            if key not in CONDITION_KEYS:
                problems.append(f"{row_id}: unknown condition key '{key}'")
        try:
            for change_class in expand(when.get("classes", "any"), class_groups, CHANGE_TYPES):
                if change_class not in CHANGE_TYPES:
                    problems.append(f"{row_id}: '{change_class}' is not in CHANGE_TYPES")
            for key in ("all", "any", "none"):
                for rule_id in expand(when.get(key, []), rule_groups, rule_ids):
                    if rule_id not in rule_ids:
                        problems.append(f"{row_id}: rule '{rule_id}' is not in rules")
        except TableError as error:
            problems.append(f"{row_id}: {error}")
        for action in row.get("actions") or []:
            if action not in actions:
                problems.append(f"{row_id}: action '{action}' is not declared")
        if row.get("decider") not in deciders:
            problems.append(f"{row_id}: decider '{row.get('decider')}' is not declared")
        if not isinstance(row.get("rests_on"), list):
            problems.append(f"{row_id}: rests_on must be a list")
    if not rows or rows[-1].get("id") != FALLBACK_ROW or rows[-1].get("when"):
        problems.append(f"the last row must be {FALLBACK_ROW} with an empty condition")
    for row in rows[:-1]:
        if row.get("id") == FALLBACK_ROW:
            problems.append(f"{FALLBACK_ROW} may appear only as the last row")
    if problems:
        raise TableError("; ".join(problems))


# ---- match ----------------------------------------------------------------------------------------------

def fired_rules(findings):
    """Rule ids that fired at a severity that enters the table."""
    return sorted({item["rule"] for item in findings if item.get("severity") in DECIDING_SEVERITIES})


def change_class_of(change):
    if isinstance(change, str):
        return change
    return change.get("type")


def row_matches(row, change_class, fired, table):
    when = row.get("when") or {}
    class_groups = table.get("class_groups") or {}
    rule_groups = table.get("rule_groups") or {}
    rule_ids = table["rules"]
    if change_class not in expand(when.get("classes", "any"), class_groups, CHANGE_TYPES):
        return False
    required = expand(when.get("all", []), rule_groups, rule_ids)
    if not all(rule_id in fired for rule_id in required):
        return False
    alternatives = expand(when.get("any", []), rule_groups, rule_ids)
    if alternatives and not any(rule_id in fired for rule_id in alternatives):
        return False
    excluded = expand(when.get("none", []), rule_groups, rule_ids)
    if any(rule_id in fired for rule_id in excluded):
        return False
    return True


def matching_rows(change_class, fired, table):
    """Every row whose condition holds, in table order. The last one is always R0."""
    return [row for row in table["rows"] if row_matches(row, change_class, set(fired), table)]


def to_decision_row(row):
    return DecisionRow(row_id=row["id"], allowed_actions=list(row.get("actions") or []),
                       decider=row["decider"], rests_on=list(row.get("rests_on") or [])).__dict__


def match(findings, change, table=None):
    """First matching row for these findings and this change, as a DecisionRow dict."""
    table = table or load_table()
    rows = matching_rows(change_class_of(change), fired_rules(findings), table)
    return to_decision_row(rows[0])


def row_meaning(row_id, table=None):
    table = table or load_table()
    for row in table["rows"]:
        if row["id"] == row_id:
            return row.get("meaning", "")
    return ""


# ---- verdict --------------------------------------------------------------------------------------------

def verdict(findings, covered):
    """One of VERDICTS. Never "approved": the best outcome is "no blockers found"."""
    if not covered:
        result = "not_covered"
    elif any(item.get("severity") == "blocker" for item in findings):
        result = "blockers_found"
    elif any(item.get("severity") == "question" for item in findings):
        result = "needs_info"
    else:
        result = "no_blockers_found"
    assert result in VERDICTS
    return result


def decide(findings, change, table=None):
    """Row and verdict in one call. covered is False exactly when the row is R0."""
    row = match(findings, change, table)
    return row, verdict(findings, row["row_id"] != FALLBACK_ROW)


# ---- coverage check (Calvanese et al., BPM 2016, for a first-hit table over a finite input) --------------

def coverage_check(table=None, max_examples=12):
    """Enumerate every subset of the table's rule ids for every change class.

    Returns {"input_sets", "to_person", "overlaps", "examples"} plus a breakdown:
    - to_person: input sets whose first match is R0 (no rule covers them, a person decides);
    - overlaps: input sets matched by more than one non-fallback row (order decides; listed).
    """
    table = table or load_table()
    rule_ids = table["rules"]
    checked = set((table.get("class_groups") or {}).get("checked", []))
    input_sets = 0
    to_person = 0
    to_person_class_not_checked = 0
    to_person_by_class = {}
    overlap_count = 0
    overlap_pairs = {}
    row_hits = {row["id"]: 0 for row in table["rows"]}
    person_examples = []
    overlap_examples = []
    for change_class in CHANGE_TYPES:
        for size in range(len(rule_ids) + 1):
            for subset in itertools.combinations(rule_ids, size):
                input_sets += 1
                rows = matching_rows(change_class, subset, table)
                first = rows[0]["id"]
                row_hits[first] += 1
                if first == FALLBACK_ROW:
                    to_person += 1
                    to_person_by_class[change_class] = to_person_by_class.get(change_class, 0) + 1
                    if change_class not in checked:
                        to_person_class_not_checked += 1
                    elif len(person_examples) < max_examples:
                        person_examples.append({"class": change_class, "fired": list(subset)})
                real_rows = [row["id"] for row in rows if row["id"] != FALLBACK_ROW]
                if len(real_rows) > 1:
                    overlap_count += 1
                    for other in real_rows[1:]:
                        key = f"{real_rows[0]} over {other}"
                        overlap_pairs[key] = overlap_pairs.get(key, 0) + 1
                    if len(overlap_examples) < max_examples:
                        overlap_examples.append({"class": change_class, "fired": list(subset),
                                                 "rows": real_rows, "chosen": real_rows[0]})
    return {
        "input_sets": input_sets,
        "to_person": to_person,
        "overlaps": overlap_count,
        "examples": {"to_person": person_examples, "overlaps": overlap_examples},
        "to_person_class_not_checked": to_person_class_not_checked,
        "to_person_rule_combination": to_person - to_person_class_not_checked,
        "to_person_by_class": to_person_by_class,
        "overlap_rows": dict(sorted(overlap_pairs.items(), key=lambda item: -item[1])),
        "row_hits": row_hits,
        "rules": list(rule_ids),
        "change_classes": len(CHANGE_TYPES),
    }


def coverage_summary(report):
    """The short form for the card."""
    return {key: report[key] for key in ("input_sets", "to_person", "overlaps")}


# ---- rules version --------------------------------------------------------------------------------------

def rules_version_detail(root=None, patterns=None):
    """sha256 over the files that define the rules. Missing files are skipped and listed."""
    base = Path(root) if root else ROOT
    digest = hashlib.sha256()
    hashed = []
    missing = []
    for pattern in patterns or RULES_VERSION_PATTERNS:
        matches = sorted(base.glob(pattern))
        if not matches:
            missing.append(pattern)
            digest.update(f"missing:{pattern}\n".encode())
            continue
        for path in matches:
            relative = path.relative_to(base).as_posix()
            digest.update(f"file:{relative}\n".encode())
            digest.update(path.read_bytes())
            digest.update(b"\n")
            hashed.append(relative)
    return {"rules_version": digest.hexdigest(), "files": hashed, "missing": missing}


def rules_version(root=None, patterns=None):
    return rules_version_detail(root, patterns)["rules_version"]


# ---- decision record ------------------------------------------------------------------------------------

def facts_from_findings(findings):
    """Fact ids cited anywhere in the findings' proof chains (leaves and premises)."""
    found = set()
    pending = [step for item in findings for step in item.get("evidence") or []]
    while pending:
        step = pending.pop()
        if step.get("fact_id"):
            found.add(step["fact_id"])
        pending.extend(step.get("premises") or [])
    return sorted(found)


def record(request, as_of, facts_in_force, findings, row, verdict_value, rules_version_value=None,
           path=None, decided_by=None, created_at=None):
    """Build a DecisionRecord, append it to the JSONL log, return it as a dict.

    The log is append-only: this function opens it in append mode and never rewrites a line.
    """
    if verdict_value not in VERDICTS:
        raise ValueError(f"verdict '{verdict_value}' is not one of {VERDICTS}")
    version = rules_version_value or rules_version()
    created = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    row_id = row["row_id"] if isinstance(row, dict) else row
    body = {
        "request": request,
        "as_of": as_of,
        "rules_version": version,
        "facts_in_force": sorted(facts_in_force or []),
        "rules_fired": fired_rules(findings),
        "verdict": verdict_value,
        "decision_row": row_id,
    }
    content = json.dumps(body, sort_keys=True, ensure_ascii=False)
    record_id = "DR-" + hashlib.sha256(f"{created}\n{content}".encode()).hexdigest()[:16]
    entry = DecisionRecord(record_id=record_id, created_at=created, decided_by=decided_by, **body).__dict__
    log_path = Path(path) if path else RECORDS_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_records(path=None):
    log_path = Path(path) if path else RECORDS_PATH
    if not log_path.exists():
        return []
    with open(log_path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


# ---- CLI ------------------------------------------------------------------------------------------------

def print_report(report, table):
    print(f"Decision table: {len(table['rows'])} rows, hit policy {table['hit_policy']}, "
          f"rules {', '.join(report['rules'])}")
    print(f"table checked: {report['input_sets']} input sets "
          f"(2^{len(report['rules'])} rule sets x {report['change_classes']} change classes), "
          f"{report['to_person']} go to a person, {report['overlaps']} overlap")
    print(f"  to a person because no check examines the change class: {report['to_person_class_not_checked']}")
    print(f"  to a person because no row covers the combination of fired rules: "
          f"{report['to_person_rule_combination']}")
    print("first-match hits per row:")
    for row_id, hits in report["row_hits"].items():
        print(f"  {row_id:4} {hits}")
    print("overlaps by row pair (input sets where the second row also matches; the first one wins):")
    for rows, count in report["overlap_rows"].items():
        print(f"  {rows:20} {count}")
    print("examples that go to a person in a checked class:")
    for example in report["examples"]["to_person"]:
        print(f"  {example['class']:24} fired {example['fired']}")


def main():
    parser = argparse.ArgumentParser(description="Decision table: coverage check and rules version")
    parser.add_argument("--table", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()
    if args.version:
        print(json.dumps(rules_version_detail(), indent=2))
        return
    table = load_table(args.table)
    report = coverage_check(table)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, table)


if __name__ == "__main__":
    main()
