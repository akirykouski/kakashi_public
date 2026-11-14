"""Import the two synthetic eval worlds from the private repo and write one gold format.

Usage: python eval/tools/import_worlds.py <path to torino_kakashi checkout on night-shift/2026-11-13-kva-plan>

Data only: no engine code is copied. The two worlds are kept apart (same ids mean different things).
Native rule ids are kept; a unified id (rule_u) is added from eval/MAPPING.md.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]

# Unified rule ids. Justification per line in eval/MAPPING.md.
M_RULES = {
    "R1a": ("U_SUPPLIER_STANDING", "blocker"),
    "R1b": ("U_SOURCE_RELEASE", "blocker"),
    "R2": ("U_CUSTOMER_APPROVAL", "blocker"),
    "R3": ("U_OPEN_ISSUE", "blocker"),
    "R5": ("U_RESTRICTED_SUBSTANCE", "blocker"),
    "R6": ("U_MATERIAL", "blocker"),
    "R7": ("U_MISSING_EVIDENCE", "question"),
}
M_INFERRED_RULES = {"R2", "R3", "R5"}  # M's pre-registered definition (core PREREGISTRATION.md)

A_RULES = {
    "B_SUPPLIER_NOT_QUALIFIED": "U_SUPPLIER_STANDING",
    "B_NO_SOURCE_RELEASE": "U_SOURCE_RELEASE",
    "Q_SOURCE_RELEASE_UNKNOWN": "U_SOURCE_RELEASE",
    "B_CUSTOMER_APPROVAL_REQUIRED": "U_CUSTOMER_APPROVAL",
    "B_OPEN_8D_SAME_ALLOY": "U_OPEN_ISSUE",
    "B_MATERIAL_MISMATCH": "U_MATERIAL",
    "Q_NO_MATERIAL_CERT": "U_MISSING_EVIDENCE",
    "special_characteristic_violation": "U_MEASURED_VALUE",
    "deviation_limit_exceeded": "U_DEVIATION_LIMIT",
}
A_CATEGORY = {
    "direct_conflict": "direct",
    "inference_only": "inferred",
    "stale_rule_trap": "stale",
    "missing_data": "missing",
    "clean_control": "clean",
}
A_AS_OF = "2026-11-14"  # A's requests carry no date; every A document is dated on or before this day.


def a_key(rule, request):
    """One key per rule, read from the request; A's gold has at most one finding per rule per request."""
    part = request["part"]
    if rule in ("B_NO_SOURCE_RELEASE", "Q_SOURCE_RELEASE_UNKNOWN", "B_MATERIAL_MISMATCH"):
        return part
    if rule == "B_CUSTOMER_APPROVAL_REQUIRED":
        return CUSTOMER_OF[request["id"]]
    if rule == "B_OPEN_8D_SAME_ALLOY":
        return "8D-25-031"
    if rule == "Q_NO_MATERIAL_CERT":
        return "material_certificate"
    if rule == "special_characteristic_violation":
        return "SC-01"
    if rule == "deviation_limit_exceeded":
        return "PRC-DEV-007"
    if rule == "B_SUPPLIER_NOT_QUALIFIED":
        return "Meccanica C"
    raise KeyError(rule)


CUSTOMER_OF = {}


def verdict_from(findings):
    kinds = {finding["kind"] for finding in findings}
    if "blocker" in kinds:
        return "blockers_found"
    if "question" in kinds:
        return "needs_info"
    if "not_covered" in kinds:
        return "not_covered"
    return "no_blockers_found"


def copy(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def import_m(src):
    out = EVAL / "worlds" / "M"
    for name in ["docs", "meetings", "registries.json", "facts.jsonl", "corpus.jsonl"]:
        copy(src / "data" / name, out / name)
    copy(src / "bench" / "requests.jsonl", out / "requests_native.jsonl")
    gold = []
    for request in load_jsonl(src / "bench" / "requests.jsonl"):
        findings = []
        for item in request["gold"]:
            rule_u, kind = M_RULES[item["rule"]]
            findings.append({"rule": item["rule"], "rule_u": rule_u, "key": item["key"], "kind": kind,
                             "inferred": item["rule"] in M_INFERRED_RULES})
        gold.append({"id": request["id"], "world": "M", "category": request["category"],
                     "category_native": request["category"], "as_of": request["as_of"],
                     "request_text": request["utterance"], "change_hand_parse": request["change"],
                     "verdict": verdict_from(findings), "verdict_source": "derived",
                     "findings": findings, "must_not_cite": [], "cleared": []})
    return gold


def import_a(src):
    out = EVAL / "worlds" / "A"
    copy(src / "data" / "sources", out / "sources")
    for name in ["change_requests.jsonl", "gold.jsonl", "RULES.md", "canonical.json", "invariants.json", "dev.jsonl"]:
        copy(src / "data" / "eval" / name, out / name)
    requests = {row["id"]: row for row in load_jsonl(src / "data" / "eval" / "change_requests.jsonl")}
    gold = []
    for native in load_jsonl(src / "data" / "eval" / "gold.jsonl"):
        request = requests[native["id"]]
        for item in native["expected_blockers"]:
            if item["rule"] == "B_CUSTOMER_APPROVAL_REQUIRED":
                text = item["claim"] + " ".join(e["doc_id"] + e["quote"] for e in item["evidence"])
                found = sorted(set(re.findall(r"\b(STL|CLM)\b", text)))
                if len(found) != 1:
                    raise SystemExit(f"{native['id']}: customer not unique in claim: {found}")
                CUSTOMER_OF[native["id"]] = found[0]
        findings = []
        for item in native["expected_blockers"]:
            kind = {"blocker": "blocker", "inferred": "blocker", "question": "question"}[item["kind"]]
            findings.append({"rule": item["rule"], "rule_u": A_RULES[item["rule"]], "key": a_key(item["rule"], request),
                             "kind": kind, "inferred": item["kind"] == "inferred",
                             "claim": item["claim"], "evidence": item["evidence"]})
        cleared = [{"rule": item["rule"], "rule_u": A_RULES[item["rule"]], "key": a_key(item["rule"], request),
                    "claim": item["claim"], "evidence": item["evidence"]} for item in native.get("cleared") or []]
        derived = verdict_from(findings)
        if derived != native["expected_verdict"]:
            raise SystemExit(f"{native['id']}: verdict {native['expected_verdict']} != derived {derived}")
        gold.append({"id": native["id"], "world": "A", "category": A_CATEGORY[request["category"]],
                     "category_native": request["category"], "as_of": A_AS_OF,
                     "request_text": request["request_text"], "change_hand_parse": None,
                     "verdict": native["expected_verdict"], "verdict_source": "author",
                     "findings": findings, "must_not_cite": native["must_not_cite"], "cleared": cleared})
    return gold


def main():
    src = Path(sys.argv[1]).resolve()
    commit = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (EVAL / "gold").mkdir(parents=True, exist_ok=True)
    write_jsonl(EVAL / "gold" / "M.jsonl", import_m(src))
    write_jsonl(EVAL / "gold" / "A.jsonl", import_a(src))
    (EVAL / "worlds" / "SOURCE.txt").write_text(
        f"Imported from torino_kakashi (private), branch night-shift/2026-11-13-kva-plan, commit {commit}\n"
        "by eval/tools/import_worlds.py. Synthetic data only. Engine code and data_real/ are not imported.\n")


if __name__ == "__main__":
    main()
