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
    card = run(check.scenario("silence"))
    assert card["verdict"] == "not_covered"
    assert card["decision"]["row_id"] == "R0"


def test_never_approved():
    for scenario_id in ("main", "main_after_audit", "elv", "silence", "subtier"):
        assert run(check.scenario(scenario_id))["verdict"] != "approved"
