"""Memory of decisions and maintenance (core/memory.py, issue #19): every card item, scenarios end to end.

No model call: every scenario is a typed change request from data/scenarios.json.
"""
import json
import os

import pytest

from core import check

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = {}
with open(os.path.join(ROOT, "data", "corpus.jsonl")) as _file:
    for _line in _file:
        _item = json.loads(_line)
        CORPUS[_item["id"]] = _item["text"]
with open(os.path.join(ROOT, "data", "scenarios.json")) as _file:
    SCENARIO_IDS = [item["id"] for item in json.load(_file)]


def card_for(scenario_id, **override):
    request = check.scenario(scenario_id)
    request.update(override)
    card, _ = check.run(request, record=False)
    return card


def items(card, kind):
    return [item for item in card["maintenance"] if item["kind"] == kind]


def past(card, decision_id):
    found = [item for item in card["past_decisions"] if item["id"] == decision_id]
    assert found, f"{decision_id} not on the card: {[item['id'] for item in card['past_decisions']]}"
    return found[0]


def assert_verbatim(evidence):
    assert evidence, "every item needs evidence"
    for step in evidence:
        assert step["source"] and step["quote"]
        assert step["quote"] in CORPUS[step["source"]], (step["source"], step["quote"])


# ---- every scenario runs end to end, every item is sourced -----------------------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_scenario_end_to_end_with_sourced_memory(scenario_id):
    card = card_for(scenario_id)
    assert "past_decisions" in card and "maintenance" in card
    for item in card["maintenance"]:
        assert_verbatim(item["evidence"])
    for decision in card["past_decisions"]:
        assert decision["quote"] in CORPUS[decision["source"]]
        for reason in decision["reasons"]:
            assert_verbatim([reason])


def test_deterministic():
    assert card_for("main_after_audit")["maintenance"] == card_for("main_after_audit")["maintenance"]


# ---- past decisions ----------------------------------------------------------------------------------------------

def test_main_shows_dec031_rejected_by_conti_with_reasons_still_holding():
    card = card_for("main")
    first = card["past_decisions"][0]
    assert first["id"] == "DEC-031" and first["date"] == "2026-10-02" and first["by"] == "PER-CONTI"
    assert first["title"].startswith("Rejected.")
    assert first["status"] == "stands"
    states = {reason["record"]: reason["state"] for reason in first["reasons"]}
    assert states == {"CAP-C-01": "still holds", "CAP-C-02": "still holds", "8D-25-031": "still holds"}
    eight_d = [reason for reason in first["reasons"] if reason["record"] == "8D-25-031"][0]
    assert eight_d["quote"] == "Status: open"


def test_dec033_reason_superseded_today_but_holds_on_8_nov():
    today = past(card_for("main_after_audit"), "DEC-033")
    assert today["status"] == "review"
    reason = today["reasons"][0]
    assert reason["state"] == "superseded" and reason["by"] == "QS-C-2026" and reason["on"] == "2026-11-06"
    then = past(card_for("known_at_11_08"), "DEC-033")
    assert then["status"] == "stands" and then["reasons"][0]["state"] == "still holds"


def test_decision_after_as_of_is_not_shown():
    card = card_for("main")  # as of 2026-11-05: DEC-033 (8 Nov) and DEC-035 (10 Nov) did not exist yet
    assert {item["id"] for item in card["past_decisions"]} == {"DEC-031"}


# ---- record time (known_at) -------------------------------------------------------------------------------------

def test_known_at_11_08_chisone_still_conditional():
    card = card_for("known_at_11_08")
    assert card["request"]["known_at"] == "2026-11-08"
    assert any(finding["rule"] == "R1a" and finding["severity"] == "blocker" for finding in card["findings"])
    assert not items(card, "decision_review") and not items(card, "decided_before_known")


def test_same_valid_time_known_today_chisone_is_approved():
    card = card_for("known_at_11_08", known_at=None)
    assert not any(finding["rule"] == "R1a" and finding["severity"] == "blocker" for finding in card["findings"])


def test_decided_before_we_knew():
    found = items(card_for("main_after_audit"), "decided_before_known")
    assert len(found) == 1
    assert found[0]["record"] == "DEC-033/QS-C-2026" and found[0]["owner"] == "PER-CONTI"
    assert "recorded 2026-11-10" in found[0]["title"]


def test_review_item_for_superseded_reason():
    found = items(card_for("main_after_audit"), "decision_review")
    assert [item["decision"] for item in found] == ["DEC-033"]
    assert found[0]["severity"] == "question"


# ---- promises (PLAN with a horizon) -----------------------------------------------------------------------------

def test_promise_before_horizon_is_a_plan_and_blockers_stay():
    card = card_for("main_after_audit")
    pending = items(card, "promise_pending")
    assert {item["record"] for item in pending} == {"PRM-C-8D-CLOSE", "PRM-C-6082T6"}
    assert all(item["epistemic"] == "PLAN" for item in pending)
    assert any(finding["rule"] == "R3" for finding in card["findings"])      # open 8D warning stays
    assert any(finding["rule"] == "R6" and finding["severity"] == "blocker" for finding in card["findings"])


def test_promise_past_horizon_becomes_question_with_owner_and_growing_urgency():
    early = items(card_for("main_after_audit", as_of="2026-11-25"), "promise_overdue")
    late = items(card_for("main_after_audit", as_of="2026-12-20"), "promise_overdue")
    assert [item["record"] for item in early] == ["PRM-C-8D-CLOSE"]
    assert early[0]["owner"] == "PER-GALLO" and early[0]["days_overdue"] == 5
    assert early[0]["severity"] == "question" and early[0]["epistemic"] == "QUESTION"
    late_8d = [item for item in late if item["record"] == "PRM-C-8D-CLOSE"][0]
    assert late_8d["urgency"] > early[0]["urgency"]
    assert {item["record"] for item in late} == {"PRM-C-8D-CLOSE", "PRM-C-6082T6"}


def test_promise_not_visible_before_the_email_was_recorded():
    card = card_for("main_after_audit", known_at="2026-11-11")
    assert not items(card, "promise_pending") and not items(card, "promise_overdue")


# ---- deviations ---------------------------------------------------------------------------------------------------

def test_deviation_expiring_in_47_days():
    found = items(card_for("main_after_audit"), "deviation_expiring")
    assert [(item["record"], item["days_left"]) for item in found] == [("DEV-121", 47)]
    assert "expires in 47 days" in found[0]["title"]
    assert "2026-12-31" in found[0]["evidence"][0]["quote"]


def test_deviation_expired_brings_its_blocker_back():
    card = card_for("dev_expired")
    found = items(card, "deviation_expired")
    assert [item["record"] for item in found] == ["DEV-121"]
    assert found[0]["severity"] == "blocker" and found[0]["blockers_back"] == ["R2"]
    assert card["verdict"] == "blockers_found"
    covered = card_for("dev_expired", as_of="2026-11-14")
    assert covered["verdict"] == "no_blockers_found"


# ---- contradiction ------------------------------------------------------------------------------------------------

def test_contradiction_side_by_side():
    card = card_for("contradiction")
    found = items(card, "contradiction")
    assert len(found) == 1
    item = found[0]
    assert item["record"] == "SC-BR220-YS/minYieldMPa" and sorted(item["values"]) == ["240", "250"]
    assert {step["source"] for step in item["evidence"]} == {"REG-SPECIAL_CHARACTERISTICS", "FMEA-BR220-B"}
    assert item["owner"] == "PER-ROMANO" and item["related"]
    assert card["maintenance"][0]["kind"] == "contradiction"   # related to BR-220: first on the strip


def test_contradiction_absent_before_fmea_rev_b():
    assert not items(card_for("main"), "contradiction")


# ---- rule change and R0 scenarios are unchanged by memory ---------------------------------------------------------

def test_rule_change_r3_vs_r4():
    assert card_for("rule_change_r3")["verdict"] == "no_blockers_found"
    assert card_for("rule_change_r4")["verdict"] == "blockers_found"


def test_no_rule_goes_to_a_person():
    card = card_for("no_rule")
    assert card["verdict"] == "not_covered" and card["decision"]["row_id"] == "R0"
