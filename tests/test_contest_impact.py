"""#28 contested records side by side, #29 "a document changed: what is affected".

All contradicting values here are test-only facts (source TEST-*); nothing is added to data/.
Run: python -m pytest tests/test_contest_impact.py -q
"""
import json
import os
import subprocess
import sys

import pytest

from core import check, impact, rules
from core.factlog import CONTRADICTS_WEIGHT, ConflictError, FactLog, default_log
from core.project import Projection
from core.snapshot import snapshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AS_OF = "2026-11-14"


def owner_fact(owner="PER-TEST-SQE"):
    return {"id": "T-OWNER", "s": "Q-contradiction", "p": "questionOwner", "o": owner, "source": "TEST-POLICY",
            "quote": "test-only: contradictions are decided by the test SQE", "rank": 2}


def small_log(with_owner=True):
    log = FactLog()
    with log._transaction():
        if with_owner:
            log._insert(owner_fact(), recorded_at="2026-01-01T00:00:00", review="accepted")
    log.write_record("QS-T-1", "SupplierQualification", {"qualifiedSupplier": "SUP-T", "status": '"approved"'},
                     source="TEST-AUDIT-1", quote="test-only: SUP-T approved", valid_from="2026-01-01",
                     author="PER-A", rank=2)
    return log


def write_contradiction(log, rank=2, on_conflict="contest"):
    return log.write_record("QS-T-2", "SupplierQualification",
                            {"qualifiedSupplier": "SUP-T", "status": '"conditional"'},
                            source="TEST-AUDIT-2", quote="test-only: SUP-T conditional", valid_from="2026-02-01",
                            author="PER-B", rank=rank, on_conflict=on_conflict)


# ---- #28 (a) fact log: third write path ----------------------------------------------------------------------

def test_refuse_stays_the_default():
    log = small_log()
    with pytest.raises(ConflictError) as raised:
        write_contradiction(log, on_conflict="refuse")
    assert raised.value.current == "QS-T-1"
    assert log.facts_about("QS-T-2", review="contested") == []


def test_contest_stores_record_not_in_force_with_link_and_question():
    log = small_log()
    written = write_contradiction(log)
    assert written
    assert {fact["review"] for fact in log.all_facts(review=None) if fact["s"] == "QS-T-2"} == {"contested"}
    current = {fact["s"] for fact in snapshot(log.all_facts(), "2026-03-01")["facts"]}
    assert "QS-T-1" in current and "QS-T-2" not in current           # the current record stays in force
    links = log.links("CONTRADICTS")
    assert links == [dict(links[0], s="QS-T-2", kind="CONTRADICTS", o="QS-T-1", weight=CONTRADICTS_WEIGHT)]
    [question] = log.open_questions()
    assert question["owner"] == "PER-TEST-SQE"                         # owner read from data, not hard-coded
    assert question["owner_source"] == "TEST-POLICY"
    assert (question["contested_record"], question["current_record"]) == ("QS-T-2", "QS-T-1")


def test_question_owner_is_none_when_no_policy_names_one():
    log = small_log(with_owner=False)
    write_contradiction(log)
    assert log.open_questions()[0]["owner"] is None


def test_more_authoritative_write_must_supersede_not_contest():
    log = small_log()
    with pytest.raises(ConflictError):
        write_contradiction(log, rank=1)


def test_only_the_owner_decides_and_both_outcomes_work():
    log = small_log()
    write_contradiction(log)
    question_id = log.open_questions()[0]["id"]
    with pytest.raises(PermissionError):
        log.resolve_contradiction(question_id, "take_contested", decided_by="PER-SOMEONE")
    assert log.resolve_contradiction(question_id, "take_contested", decided_by="PER-TEST-SQE") == "took_contested"
    current = {fact["s"] for fact in snapshot(log.all_facts(), "2026-03-01")["facts"]}
    assert "QS-T-2" in current and "QS-T-1" not in current
    assert log.open_questions() == []

    other = small_log()
    write_contradiction(other)
    other.resolve_contradiction(other.open_questions()[0]["id"], "keep_current", decided_by="PER-TEST-SQE")
    assert {fact["review"] for fact in other.all_facts(review=None) if fact["s"] == "QS-T-2"} == {"rejected"}


# ---- #28 (b), (c) rules and the card ---------------------------------------------------------------------------

def full_log():
    return rules.extend_log(default_log())


def add_facts(log, *facts):
    with log._transaction():
        for fact in facts:
            log._insert(dict({"rank": 2, "kind": "assert"}, **fact), recorded_at="2026-01-01T00:00:00",
                        review="accepted")
    return log


FMEA_240 = {"id": "T-FMEA-240", "s": "SC-BR220-YS", "p": "minYieldMPa", "o": '"240"', "source": "TEST-FMEA",
            "quote": "test-only: FMEA minimum yield 240 MPa"}
MATERIAL_CHANGE = {"type": "MaterialChange", "part": "BR-220", "new_material": "MAT-6061-T6", "as_of": AS_OF}


def test_contested_value_becomes_a_question_with_both_sources():
    projection = Projection(add_facts(full_log(), FMEA_240), AS_OF)
    findings = rules.check(projection, MATERIAL_CHANGE)
    questions = [item for item in findings if item["title"].startswith("Two current values")]
    assert len(questions) == 1
    question = questions[0]
    assert question["severity"] == "question" and question["rule"] == "R7"
    assert "240 (TEST-FMEA" in question["title"] and "250 (REG-SPECIAL_CHARACTERISTICS" in question["title"]
    assert question["owner"] == "PER-GALLO"                            # QP-15 5.1 via rules_data
    assert any(step.get("source") == "QP-15" for step in question["evidence"])
    [pair] = rules.contested_pairs(projection, MATERIAL_CHANGE)
    assert pair["key"] == ["SC-BR220-YS", "minYieldMPa"] and pair["reason"] == "same_rank_same_date"
    assert sorted(side["value"] for side in pair["sides"]) == ["240", "250"]
    assert all(side["quote"] and side["source"] for side in pair["sides"])


def test_lower_rank_newer_value_keeps_head_and_still_asks():
    newer = dict(FMEA_240, id="T-FMEA-NEWER", rank=3, valid_from="2026-10-01")
    projection = Projection(add_facts(full_log(), newer), AS_OF)
    assert projection.value("SC-BR220-YS", "minYieldMPa") == "250"
    rules.check(projection, MATERIAL_CHANGE)
    [pair] = rules.contested_pairs(projection, MATERIAL_CHANGE)
    statuses = {side["value"]: side["status"] for side in pair["sides"]}
    assert statuses == {"250": "in force", "240": "contested, not in force"}


def test_card_carries_contested_key(monkeypatch):
    monkeypatch.setattr(check, "_LOG", add_facts(full_log(), FMEA_240))
    card, _, _ = check.evaluate(MATERIAL_CHANGE, record=False)
    assert [pair["key"] for pair in card["contested"]] == [["SC-BR220-YS", "minYieldMPa"]]
    monkeypatch.setattr(check, "_LOG", full_log())
    card, _, _ = check.evaluate(MATERIAL_CHANGE, record=False)
    assert card["contested"] == []


def test_contested_record_from_the_log_shows_on_the_card(monkeypatch):
    log = full_log()
    log.write_record("APR-T-REVOKE", "PartApproval",
                     {"approvedSupplier": "SUP-B", "approvedPart": "BR-220", "approvedSite": "PLT-BEI",
                      "approvedForCustomer": "CUST-AUR", "status": '"revoked"'},
                     source="TEST-EMAIL", quote="test-only: BR-220 approval of SUP-B revoked", valid_from="2026-11-01",
                     author="PER-X", rank=2, on_conflict="contest")
    monkeypatch.setattr(check, "_LOG", log)
    card, _, _ = check.evaluate({"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C", "as_of": AS_OF},
                                record=False)
    pairs = [pair for pair in card["contested"] if pair["reason"] == "contested_record"]
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["records"] == ["APR-001", "APR-T-REVOKE"] and pair["owner"] == "PER-GALLO"
    assert {side["value"]: side["status"] for side in pair["sides"]} == {
        "approved": "in force", "revoked": "contested, not in force"}
    assert any(item["title"].startswith("Two current values for APR-001 status") for item in card["findings"])


# ---- #29 impact ------------------------------------------------------------------------------------------------

def test_impact_of_superseded_csr_lists_facts_rows_records_and_past():
    records = [{"record_id": "DR-T1", "as_of": "2026-05-01", "facts_in_force": ["F0396", "F0001"],
                "request": {"type": "SourceChange"}, "verdict": "blockers_found", "decision_row": "D5"},
               {"record_id": "DR-T2", "as_of": AS_OF, "facts_in_force": ["F0001"], "request": {}}]
    past = [{"id": "PD-T1", "reason": "test-only: accepted under CSR-AUR-R3 section 7", "source": "TEST-MTG"},
            {"id": "PD-T2", "reason": "test-only: cites CSR-AUR-R30, a different id", "source": "TEST-MTG"}]
    facts = full_log().all_facts(review=None)
    facts.append({"id": "T-DEC-1", "s": "DEC-T", "p": "type", "o": "Decision", "source": "TEST-MTG", "quote": "q"})
    facts.append({"id": "T-DEC-2", "s": "DEC-T", "p": "reason", "o": '"Per CSR-AUR-R3 approval is enough."',
                  "source": "TEST-MTG", "quote": "q"})
    report = impact.impact("CSR-AUR-R3", facts=facts, records=records, past=past)
    assert report["superseded"] and report["replaced_by"] == ["CSR-AUR-R4"]
    assert report["status"] == impact.REVIEW == "review: source superseded"
    fact_ids = {item["fact_id"] for item in report["facts"]}
    assert {"F0395", "F0396", "F0397", "F0398", "F0399", "F0002"} <= fact_ids
    assert all(item["status"] == impact.REVIEW for item in report["facts"])
    assert "F0401" not in fact_ids                                      # the supersedes fact itself
    assert {row["row_id"] for row in report["table_rows"]} >= {"D5", "D6"}
    assert all("R2" in row["via_rules"] for row in report["table_rows"] if row["row_id"] in ("D5", "D6"))
    assert [entry["record_id"] for entry in report["recorded_decisions"]] == ["DR-T1"]
    assert report["recorded_decisions"][0]["facts_used"] == ["F0396"]
    assert {item["id"] for item in report["past_decisions"]} == {"DEC-T", "PD-T1"}


def test_impact_of_current_document_is_not_marked_superseded():
    report = impact.impact("CSR-AUR-R4", records=[], past=[])
    assert not report["superseded"] and report["status"] == impact.CHANGED
    assert report["counts"]["facts"] > 0


def test_impact_cli_json():
    result = subprocess.run([sys.executable, "-m", "core.impact", "CSR-AUR-R3", "--json"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    report = json.loads(result.stdout)
    assert report["doc"] == "CSR-AUR-R3" and report["replaced_by"] == ["CSR-AUR-R4"]


def test_impact_route():
    from web import server
    response = server.handle_impact({"doc": ["CSR-AUR-R3"]})
    assert response["impact"]["superseded"] and response["impact"]["counts"]["facts"] >= 6
    with pytest.raises(ValueError):
        server.handle_impact({})
