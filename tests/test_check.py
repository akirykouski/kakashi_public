"""End-to-end pipeline: request -> Card, including the R0 outcome decided by rules.covered()."""
from core import check


def run(request):
    card, _ = check.run(request, record=False)
    return card


def test_main_scenario_blocks_with_decision_row():
    card = run(check.scenario("main"))
    assert card["verdict"] == "blockers_found"
    assert card["decision"]["row_id"] == "D2"
    assert {item["rule"] for item in card["findings"]} >= {"R1a", "R1b", "R2", "R6"}


def test_uncovered_change_goes_to_a_person():
    # "Move BR-220 final inspection to the new CMM": no rule covers an equipment change on this part.
    card = run({"type": "EquipmentChange", "part": "BR-220", "as_of": "2026-11-14"})
    assert card["verdict"] == "not_covered"
    assert card["decision"]["row_id"] == "R0"


def test_schedule_change_is_checked_not_approved():
    # QP-15 4.1: delivery date changes are examined; nothing fires, which is not an approval.
    card = run(check.scenario("silence"))
    assert card["verdict"] == "no_blockers_found"
    assert card["decision"]["row_id"] == "D11"


def test_never_approved():
    for scenario_id in ("main", "main_after_audit", "elv", "silence", "subtier"):
        assert run(check.scenario(scenario_id))["verdict"] != "approved"
