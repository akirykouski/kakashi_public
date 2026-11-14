"""Counterfactuals (core/counterfactual.py) and plain-words explanations (core/explain_text.py).

Every counterfactual kept on a card must clear its finding when the check is re-run with its edits; computing them
must leave the real fact log and the decision records untouched; the explanation names rules_version and the row.
"""
import hashlib
import json
import os

import pytest

from core import check, counterfactual, decision, explain_text, project

SCENARIOS = ("main", "main_after_audit", "elv", "subtier")


def log_digest(log):
    return hashlib.sha256(json.dumps(log.all_facts(review=None), sort_keys=True).encode()).hexdigest()


def records_size():
    path = decision.RECORDS_PATH
    return os.path.getsize(path) if os.path.exists(path) else 0


@pytest.fixture(scope="module")
def cards():
    log = check.memory()
    before, records_before, cache_before = log_digest(log), records_size(), set(project._closure_cache)
    found = {}
    for scenario_id in SCENARIOS:
        card, _, _ = check.evaluate(check.scenario(scenario_id), record=False, explain=True)
        found[scenario_id] = card
    return {"cards": found, "log_before": before, "log_after": log_digest(log),
            "records_before": records_before, "records_after": records_size(),
            "cache_added": set(project._closure_cache) - cache_before}


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_every_counterfactual_verified_by_rerun(cards, scenario_id):
    card = cards["cards"][scenario_id]
    targets = [item for item in card["findings"] if item["severity"] in counterfactual.SEVERITIES]
    assert len(card["counterfactuals"]) == len(targets)
    log, request = check.memory(), card["request"]
    for item, finding in zip(card["counterfactuals"], targets):
        assert item["hypothetical"] is True
        if not item["verified"]:
            assert item["reason"]
            continue
        for option in [item] + item["alternatives"]:
            assert option["verified"] is True
            assert all(edit["hypothetical"] for edit in option["edits"])
            candidate = {"edits": [rebuild(edit, request) for edit in option["edits"]],
                         "request": request_override(option["edits"])}
            hyp_log, hyp_request = counterfactual.apply(log, request, [candidate])
            result = counterfactual.run_rules(hyp_log, hyp_request)
            assert not counterfactual.still_there(finding, result["findings"], request["type"])
            assert result["row"]["row_id"] == option["row_if_applied"]


def rebuild(edit, request):
    """Re-create the hypothetical facts of a public edit from its triple text (independent of the module's ids)."""
    if edit["action"] == "remove":
        return {"fact_ids": edit["fact_ids"]}
    if edit["action"] == "change_request":
        return {}
    builder = counterfactual.Builder(request)
    text = edit["triple"]
    if " a " in text.split(":")[0]:
        record_id, rest = text.split(" a ", 1)
        class_name, body = rest.split(": ", 1)
        facts = [builder.fact(record_id, "type", class_name)]
        for part in body.split(", "):
            predicate, obj = part.split(" ", 1)
            literal = obj.startswith('"')
            facts.append(builder.fact(record_id, predicate, json.loads(obj) if literal else obj, literal))
        return {"facts": facts}
    subject, predicate, obj = text.split(" ", 2)
    literal = obj.startswith('"')
    return {"facts": [builder.fact(subject, predicate, json.loads(obj) if literal else obj, literal)]}


def request_override(edits):
    found = {}
    for edit in edits:
        if edit["action"] == "change_request":
            _, field, value = edit["triple"].split(" ", 2)
            found[field] = value
    return found


def test_real_log_and_records_untouched(cards):
    assert cards["log_before"] == cards["log_after"]
    assert cards["records_before"] == cards["records_after"]
    assert not any(fact["source"] == counterfactual.HYPOTHETICAL_SOURCE for fact in check.memory().all_facts(review=None))


def test_hypothetical_closures_not_cached(cards):
    for key in cards["cache_added"]:
        graph, provenance = project._closure_cache[key]
        assert not any(fact["source"] == counterfactual.HYPOTHETICAL_SOURCE
                       for facts in provenance.values() for fact in facts)


def test_main_examples(cards):
    card = cards["cards"]["main"]
    by_rule = {item["blocker_rule"]: item for item in card["counterfactuals"]}
    assert by_rule["R1b"]["verified"] and "HYP-APR-SUP-C-BR-220-PLT-BEI-CUST-AUR" in by_rule["R1b"]["edits"][0]["triple"]
    assert "R2" in by_rule["R1b"]["clears"]
    assert by_rule["R6"]["verified"] and "MAT-6082-T6" in by_rule["R6"]["edits"][0]["triple"]
    assert by_rule["R3"]["verified"] and [edit["action"] for edit in by_rule["R3"]["edits"]] == ["remove", "add"]
    combined = card["counterfactual_all"]
    assert combined["hypothetical"] is True
    assert "blocker" not in {item["severity"] for item in combined["remaining"]}
    assert combined["verdict"] != "blockers_found"


def test_subtier_has_no_fake_edit(cards):
    item = cards["cards"]["subtier"]["counterfactuals"][0]
    assert item["blocker_rule"] == "R8" and not item["verified"] and item["reason"]


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_explanation_names_rules_version_and_row(cards, scenario_id):
    card = cards["cards"]["main" if scenario_id is None else scenario_id]
    explanation = card["explanation"]
    assert explanation["rules_version"] == decision.rules_version()
    assert explanation["rules_version"] in explanation["auditor"]
    assert card["decision"]["row_id"] in explanation["auditor"]
    assert explanation["customer"] and card["decision"]["decider"] in explanation["customer"]
    assert explain_text.explain(card) == explain_text.explain(card)   # deterministic


def test_explain_past_record(tmp_path):
    path = tmp_path / "decisions.jsonl"
    card, _, projection = check.evaluate(check.scenario("main"), record=False)
    entry = decision.record(card["request"], card["request"]["as_of"], projection.fact_ids_in_force,
                            card["findings"], card["decision"], card["verdict"], path=path)
    result = explain_text.for_record(entry["record_id"], path=path)
    text = result["explanation"]["auditor"]
    assert entry["record_id"] in text and entry["rules_version"] in text and entry["decision_row"] in text
    assert result["explanation"]["re_run_matches"] is True


def test_budget(cards):
    for card in cards["cards"].values():
        assert card["timings_ms"]["counterfactuals"] < 1500 * 2   # budget 1.5 s; slack for a loaded CI box
