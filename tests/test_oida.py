"""OIDA on the card: epistemic type badges (#26) and question urgency + BLOCKS edges (#27). core/oida.py."""
import json

from core import check, oida
from core.contracts import EPISTEMIC_TYPES


def run(scenario_id):
    card, _ = check.run(check.scenario(scenario_id), record=False)
    return card


def leaves(steps):
    for step in steps:
        if step["inferred"]:
            yield from leaves(step["premises"])
        else:
            yield step


def by_rule(card, rule):
    return next(item for item in card["findings"] if item["rule"] == rule)


# ---- #26 epistemic type ------------------------------------------------------------------------------------

def test_request_is_plan():
    assert run("main")["request"]["epistemic"] == "PLAN"


def test_epistemic_input_is_ignored_and_not_recorded():
    request = dict(check.scenario("main"), epistemic="DECISION")
    card, entry = check.run(request, record=False)
    assert card["request"]["epistemic"] == "PLAN"


def test_every_finding_and_leaf_has_epistemic_field():
    for scenario_id in ("main", "main_after_audit", "elv", "subtier"):
        for finding in run(scenario_id)["findings"]:
            assert finding["epistemic"] in EPISTEMIC_TYPES
            for step in leaves(finding["evidence"]):
                assert "epistemic" in step
                assert step["epistemic"] in EPISTEMIC_TYPES + (None,)


def test_types_come_from_ontology_classes():
    card = run("main")
    assert by_rule(card, "R1a")["epistemic"] == "DECISION"      # SupplierQualification QS-C-2025
    assert by_rule(card, "R2")["epistemic"] == "CONSTRAINT"     # CustomerRequirement CSR-AUR-R4
    assert by_rule(card, "R3")["epistemic"] == "EVIDENCE"       # EightD 8D-25-031
    types = {step["triple"].split(" ")[0]: step["epistemic"]
             for finding in card["findings"] for step in leaves(finding["evidence"])}
    assert types["QS-C-2025"] == "DECISION"
    assert types["POL-QP11-4.3"] == "CONSTRAINT"                # lcc:Policy
    assert types["CAP-C-01"] == "EVIDENCE"                      # SupplierCapability


def test_questions_are_question():
    for finding in run("main")["findings"]:
        if finding["severity"] == "question":
            assert finding["epistemic"] == "QUESTION"


# ---- #27 urgency and blocks ----------------------------------------------------------------------------------

def test_urgency_formula():
    assert oida.urgency(0, 0, 0.3) == 0.15
    assert oida.urgency(30, 1, 0.5) == 0.75          # 0.3 + 0.2 + 0.25
    assert oida.urgency(10, 0, 0.3) == 0.25          # 0.1 + 0.15
    assert oida.urgency(90, 4, 1.0) == 1.0           # clamped
    assert oida.urgency(-5, 0, 0.0) == 0.0           # clamped


def test_question_blocks_change_and_has_urgency():
    card = run("main")
    question = by_rule(card, "R7")
    assert question["blocks"] == {"part": "BR-220", "change_type": "SourceChange"}
    blockers = sum(1 for item in card["findings"] if item["severity"] == "blocker")
    assert question["blocking_edges"] == blockers == 4
    assert question["stakes"] == 1.0                 # BR-220 has a special characteristic
    assert question["age_days"] == 0                 # policy evidence carries no date
    assert question["urgency"] == oida.urgency(0, blockers, 1.0)


def test_non_questions_have_no_urgency():
    for finding in run("main")["findings"]:
        if finding["severity"] != "question":
            assert finding["urgency"] is None and finding["blocks"] is None


def test_stakes_table_is_data():
    table = json.load(open(oida.STAKES_PATH))
    assert {entry["stakes"] for entry in table["stakes"]} == {1.0, 0.5}
    assert table["default"] == 0.3


def test_stakes_levels():
    projection = check.Projection(check.memory(), "2026-11-14")
    special = {"severity": "question", "entities": ["SC-BR220-YS"], "evidence": []}
    approval = {"severity": "question", "entities": ["CSR-AUR-R4"], "evidence": []}
    plain = {"severity": "question", "entities": ["SUP-C"], "evidence": []}
    no_part = {"type": "ScheduleChange"}
    assert oida.stakes(projection, special, no_part) == 1.0
    assert oida.stakes(projection, approval, {"type": "SourceChange"}) == 0.5
    assert oida.stakes(projection, plain, no_part) == 0.3


def test_questions_sorted_by_urgency_after_severity():
    findings = [
        {"severity": "question", "urgency": 0.2, "rule": "a"},
        {"severity": "blocker", "rule": "b"},
        {"severity": "question", "urgency": 0.9, "rule": "c"},
        {"severity": "info", "rule": "d"},
    ]
    assert [item["rule"] for item in sorted(findings, key=oida.card_order)] == ["b", "c", "a", "d"]


def test_decision_unchanged_by_annotation():
    card = run("main")
    assert card["verdict"] == "blockers_found"
    assert card["decision"]["row_id"] == "D2"
