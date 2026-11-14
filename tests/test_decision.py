"""Tests for the declared decision model (core/decision.py + core/decision_table.yaml).

Fixtures: tests/fixtures/scenario_findings.json holds the findings that `core/check.py --scenario <id> --json`
of the pre-event core printed for the scenarios main, main_after_audit, elv and silence (fictional company
Valsangone).
"""
import json
import shutil
from pathlib import Path

import pytest
import yaml

from core import decision
from core.contracts import VERDICTS

FIXTURES = Path(__file__).parent / "fixtures" / "scenario_findings.json"


@pytest.fixture(scope="module")
def scenarios():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def table():
    return decision.load_table()


def run(scenario, table):
    return decision.decide(scenario["findings"], scenario["change"], table)


# ---- the table itself -----------------------------------------------------------------------------------

def test_table_is_valid_and_ends_with_r0(table):
    assert table["hit_policy"] == "first"
    assert table["rows"][-1]["id"] == "R0"
    assert 10 <= len(table["rows"]) <= 15


def test_table_without_fallback_is_refused(table, tmp_path):
    broken = dict(table, rows=table["rows"][:-1])
    path = tmp_path / "table.yaml"
    path.write_text(yaml.safe_dump(broken))
    with pytest.raises(decision.TableError):
        decision.load_table(path)


def test_undeclared_action_is_refused(table, tmp_path):
    rows = [dict(row) for row in table["rows"]]
    rows[0]["actions"] = ["ship it anyway"]
    path = tmp_path / "table.yaml"
    path.write_text(yaml.safe_dump(dict(table, rows=rows)))
    with pytest.raises(decision.TableError):
        decision.load_table(path)


# ---- real scenarios -------------------------------------------------------------------------------------

def test_main_conditional_supplier_stops(scenarios, table):
    row, result = run(scenarios["main"], table)
    assert result == "blockers_found"
    assert row["row_id"] == "D2"
    assert "R1a" in row["rests_on"]
    assert row["decider"] == "supplier quality engineer"


def test_main_after_audit_goes_to_material_capability(scenarios, table):
    # After the re-audit R1a no longer fires; R6 (not qualified for 6082-T6) is the first blocker row.
    row, result = run(scenarios["main_after_audit"], table)
    assert result == "blockers_found"
    assert row["row_id"] == "D3"
    assert "R4" not in decision.fired_rules(scenarios["main_after_audit"]["findings"])


def test_elv_restricted_substance_is_a_stop(scenarios, table):
    row, result = run(scenarios["elv"], table)
    assert result == "blockers_found"
    assert row["row_id"] == "D1"
    assert row["allowed_actions"] == ["stop"]


def test_silence_schedule_change_goes_to_a_person(scenarios, table):
    # No rule examines a ScheduleChange: before today this read "no blockers found".
    row, result = run(scenarios["silence"], table)
    assert scenarios["silence"]["findings"] == []
    assert row["row_id"] == "R0"
    assert result == "not_covered"


def test_checked_class_with_no_findings_is_not_an_approval(table):
    row, result = decision.decide([], {"type": "ProcessChange"}, table)
    assert row["row_id"] == "D11"
    assert result == "no_blockers_found"


def test_verdict_values():
    blocker = [{"rule": "R2", "severity": "blocker"}]
    question = [{"rule": "R7", "severity": "question"}]
    assert decision.verdict(blocker, covered=False) == "not_covered"
    assert decision.verdict(blocker, covered=True) == "blockers_found"
    assert decision.verdict(question, covered=True) == "needs_info"
    assert decision.verdict([], covered=True) == "no_blockers_found"
    assert "approved" not in VERDICTS


def test_info_findings_do_not_decide(table):
    notify = [{"rule": "R2", "severity": "info"}, {"rule": "R4", "severity": "info"}]
    row, result = decision.decide(notify, {"type": "CoatingChange"}, table)
    assert row["row_id"] == "D11"
    assert result == "no_blockers_found"


# ---- coverage check -------------------------------------------------------------------------------------

def test_coverage_check_enumerates_every_input_set(table):
    report = decision.coverage_check(table)
    assert report["input_sets"] == 2 ** len(table["rules"]) * 17
    assert report["to_person"] == report["to_person_class_not_checked"] + report["to_person_rule_combination"]
    assert sum(report["row_hits"].values()) == report["input_sets"]
    assert report["row_hits"]["R0"] == report["to_person"]
    # Every class that no check examines goes entirely to a person.
    assert report["to_person_by_class"]["ScheduleChange"] == 2 ** len(table["rules"])
    assert report["overlaps"] > 0
    assert set(report) >= {"input_sets", "to_person", "overlaps", "examples"}


# ---- rules version and records --------------------------------------------------------------------------

def test_rules_version_lists_missing_files(tmp_path):
    (tmp_path / "core").mkdir()
    shutil.copy(decision.TABLE_PATH, tmp_path / "core" / "decision_table.yaml")
    detail = decision.rules_version_detail(tmp_path)
    assert detail["files"] == ["core/decision_table.yaml"]
    assert "core/rules.py" in detail["missing"]
    assert len(detail["rules_version"]) == 64


def test_same_input_same_rules_same_answer(scenarios, table, tmp_path):
    scenario = scenarios["main"]
    log = tmp_path / "decisions.jsonl"
    version = decision.rules_version()
    facts = decision.facts_from_findings(scenario["findings"])
    entries = []
    for _ in range(2):
        row, result = decision.decide(scenario["findings"], scenario["change"], decision.load_table())
        entries.append(decision.record(scenario["change"], scenario["as_of"], facts, scenario["findings"],
                                       row, result, version, path=log))
    first, second = entries
    assert first["verdict"] == second["verdict"] == "blockers_found"
    assert first["decision_row"] == second["decision_row"] == "D2"
    assert first["rules_version"] == second["rules_version"] == version
    assert first["rules_fired"] == ["R1a", "R1b", "R2", "R3", "R6", "R7"]
    assert first["facts_in_force"] == facts and facts
    assert len(decision.read_records(log)) == 2


def test_changing_one_row_changes_answer_and_rules_version(scenarios, tmp_path):
    # Copy the table into a scratch root, edit one row, and decide the same main scenario again.
    root = tmp_path / "repo"
    (root / "core").mkdir(parents=True)
    table_copy = root / "core" / "decision_table.yaml"
    shutil.copy(decision.TABLE_PATH, table_copy)
    scenario = scenarios["main"]
    log = tmp_path / "decisions.jsonl"

    before_version = decision.rules_version(root)
    before_row, before_verdict = decision.decide(scenario["findings"], scenario["change"],
                                                 decision.load_table(table_copy))
    decision.record(scenario["change"], scenario["as_of"], [], scenario["findings"], before_row,
                    before_verdict, before_version, path=log)

    # The plant now lets a conditional supplier be handled by the customer deviation path instead:
    # row D2 (R1a) is narrowed to sub-tier changes only.
    edited = yaml.safe_load(table_copy.read_text())
    for row in edited["rows"]:
        if row["id"] == "D2":
            row["when"]["classes"] = ["SubTierSupplierChange"]
    table_copy.write_text(yaml.safe_dump(edited, sort_keys=False))

    after_version = decision.rules_version(root)
    after_row, after_verdict = decision.decide(scenario["findings"], scenario["change"],
                                               decision.load_table(table_copy))
    decision.record(scenario["change"], scenario["as_of"], [], scenario["findings"], after_row,
                    after_verdict, after_version, path=log)

    assert before_row["row_id"] == "D2"
    assert after_row["row_id"] == "D3"
    assert before_version != after_version
    records = decision.read_records(log)
    assert [item["decision_row"] for item in records] == ["D2", "D3"]
    assert records[0]["rules_version"] != records[1]["rules_version"]


def test_log_is_append_only(scenarios, table, tmp_path):
    log = tmp_path / "decisions.jsonl"
    scenario = scenarios["silence"]
    row, result = decision.decide(scenario["findings"], scenario["change"], table)
    first = decision.record(scenario["change"], scenario["as_of"], [], [], row, result, "v", path=log)
    lines_before = log.read_text().splitlines()
    decision.record(scenario["change"], scenario["as_of"], [], [], row, result, "v", path=log)
    lines_after = log.read_text().splitlines()
    assert lines_after[:1] == lines_before
    assert json.loads(lines_after[0])["record_id"] == first["record_id"]
    assert first["verdict"] == "not_covered" and first["decision_row"] == "R0"
