"""Round-trip proof for the DMN export (core/dmn.py).

The exported XML is read back with a small FEEL reader written here, independent of core/decision.py: it knows
only the DMN 1.3 XML shape and the four unary-test forms the exporter emits ("-", true, false, a list of string
literals), and it refuses anything else. Every input set the coverage check enumerates (2^9 rule sets x 17
change classes) is evaluated with it under hit policy FIRST and compared with core.decision.match.
"""
import copy
import itertools
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from core import decision, dmn
from core.contracts import CHANGE_TYPES

NS = {"dmn": "https://www.omg.org/spec/DMN/20191111/MODEL/"}
STRING_LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')


# ---- an independent reader for the FEEL the exporter writes ----------------------------------------------

def parse_string(text):
    match = STRING_LITERAL.fullmatch(text.strip())
    if not match:
        raise ValueError(f"not a FEEL string literal: {text!r}")
    return re.sub(r"\\(.)", r"\1", match.group(1))


def parse_string_list(text):
    """A comma-separated sequence of FEEL string literals (no commas inside a literal are assumed)."""
    body = text.strip()
    if not body:
        return []
    items = []
    position = 0
    while position < len(body):
        match = STRING_LITERAL.match(body, position)
        if not match:
            raise ValueError(f"not a list of FEEL strings: {text!r}")
        items.append(parse_string(match.group(0)))
        position = match.end()
        rest = body[position:].lstrip()
        if rest.startswith(","):
            position = len(body) - len(rest) + 1
            while position < len(body) and body[position] == " ":
                position += 1
        elif rest:
            raise ValueError(f"unexpected text in {text!r}")
        else:
            break
    return items


def matches_any(value):
    return True


def unary_test(text, type_ref):
    """A predicate for one input entry. Only "-", true/false (boolean) and string disjunctions (string)."""
    text = text.strip()
    if text == "-":
        return matches_any
    if type_ref == "boolean":
        if text not in ("true", "false"):
            raise ValueError(f"unsupported boolean unary test {text!r}")
        expected = text == "true"

        def boolean_equals(value):
            return value is expected
        return boolean_equals
    if type_ref == "string":
        allowed = set(parse_string_list(text))

        def string_in(value):
            return value in allowed
        return string_in
    raise ValueError(f"unsupported typeRef {type_ref!r}")


def literal(text):
    text = text.strip()
    if text.startswith("["):
        if not text.endswith("]"):
            raise ValueError(f"bad list literal {text!r}")
        return parse_string_list(text[1:-1])
    return parse_string(text)


def load_dmn(xml_text):
    root = ET.fromstring(xml_text)
    decisions = root.findall("dmn:decision", NS)
    assert len(decisions) == 1
    table_node = decisions[0].find("dmn:decisionTable", NS)
    assert table_node.get("hitPolicy") == "FIRST"
    inputs = []
    for node in table_node.findall("dmn:input", NS):
        expression = node.find("dmn:inputExpression", NS)
        inputs.append((expression.find("dmn:text", NS).text, expression.get("typeRef")))
    outputs = [node.get("name") for node in table_node.findall("dmn:output", NS)]
    rules = []
    for node in table_node.findall("dmn:rule", NS):
        entries = [entry.find("dmn:text", NS).text for entry in node.findall("dmn:inputEntry", NS)]
        assert len(entries) == len(inputs)
        tests = [unary_test(text, type_ref) for text, (_, type_ref) in zip(entries, inputs)]
        values = [literal(entry.find("dmn:text", NS).text) for entry in node.findall("dmn:outputEntry", NS)]
        assert len(values) == len(outputs)
        rules.append({"id": node.get("id"), "tests": tests, "outputs": dict(zip(outputs, values))})
    return {"inputs": inputs, "rules": rules}


def evaluate(model, context):
    """Hit policy FIRST: outputs of the first rule whose every input entry holds; None when none does."""
    values = [context[name] for name, _ in model["inputs"]]
    for rule in model["rules"]:
        if all(test(value) for test, value in zip(rule["tests"], values)):
            return rule["outputs"]
    return None


def every_input_set(rule_ids):
    for change_class in CHANGE_TYPES:
        for size in range(len(rule_ids) + 1):
            for subset in itertools.combinations(rule_ids, size):
                yield change_class, subset


def round_trip(table):
    """Compare the DMN export with core.decision.match on every enumerated input set. Returns (compared, diffs)."""
    model = load_dmn(dmn.export(table, rules_version_value="test"))
    compared = 0
    diffs = []
    for change_class, subset in every_input_set(table["rules"]):
        context = {dmn.CLASS_INPUT: change_class}
        context.update({dmn.fired_variable(rule_id): rule_id in subset for rule_id in table["rules"]})
        got = evaluate(model, context)
        findings = [{"rule": rule_id, "severity": "warning"} for rule_id in subset]
        want = decision.match(findings, change_class, table)
        compared += 1
        expected = {"row_id": want["row_id"], "allowed_actions": want["allowed_actions"],
                    "decider": want["decider"], "rests_on": want["rests_on"]}
        if got != expected:
            diffs.append((change_class, subset, got, expected))
    return compared, diffs


# ---- tests ----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    return decision.load_table()


def test_round_trip_every_input_set_equals_decision_match(table):
    compared, diffs = round_trip(table)
    assert compared == 2 ** len(table["rules"]) * len(CHANGE_TYPES) == 8704
    assert diffs == [], diffs[:5]


def test_export_shape(table):
    xml_text = dmn.export(table, rules_version_value="abc123")
    root = ET.fromstring(xml_text)
    assert root.tag == "{https://www.omg.org/spec/DMN/20191111/MODEL/}definitions"
    decision_node = root.find("dmn:decision", NS)
    assert decision_node.get("name") == "Change decision"
    table_node = decision_node.find("dmn:decisionTable", NS)
    labels = [node.get("label") for node in table_node.findall("dmn:input", NS)]
    assert labels == ["Change class"] + [f"{rule_id} fired" for rule_id in table["rules"]]
    rule_nodes = table_node.findall("dmn:rule", NS)
    assert [node.get("id") for node in rule_nodes] == [f"Rule_{row['id']}" for row in table["rows"]]
    assert rule_nodes[0].find("dmn:description", NS).text == table["rows"][0]["meaning"]
    note = root.find("dmn:textAnnotation/dmn:text", NS).text
    assert "rules_version abc123" in note and table["version_note"] in note


def test_any_condition_and_edited_table_round_trip(table):
    edited = copy.deepcopy(table)
    edited["rows"].insert(0, {"id": "DX", "meaning": "test row", "when": {"classes": "source", "any": ["R3", "R7"],
                                                                          "none": ["R5"]},
                              "actions": ["stop"], "decider": "customer", "rests_on": ["R3"]})
    edited["rows"] = [row for row in edited["rows"] if row["id"] != "D2"]
    decision.validate_table(edited)
    assert dmn.dmn_rule_id("DX", edited) == ["Rule_DX_any1", "Rule_DX_any2"]
    compared, diffs = round_trip(edited)
    assert compared == 8704
    assert diffs == [], diffs[:5]


def test_contradictory_row_is_refused(table):
    edited = copy.deepcopy(table)
    edited["rows"][0]["when"] = {"all": ["R5"], "none": ["R5"]}
    with pytest.raises(dmn.ExportError):
        dmn.export(edited, rules_version_value="x")


def test_cli_writes_file(tmp_path):
    out = tmp_path / "decision.dmn"
    dmn.main(["--out", str(out)])
    model = load_dmn(out.read_text(encoding="utf-8"))
    assert len(model["rules"]) == len(decision.load_table()["rows"])


def test_committed_offline_export_has_the_same_rules(table):
    """web/static/dmn/decision.dmn (the offline copy the page shows) must hold the current table's rules.

    Only the rules are compared, not the rules_version note, so a change in core/rules.py alone does not fail
    this test. If it fails: python -m core.dmn --out web/static/dmn/decision.dmn
    """
    committed = Path(__file__).resolve().parent.parent / "web" / "static" / "dmn" / "decision.dmn"
    root = ET.fromstring(committed.read_text(encoding="utf-8"))
    fresh = ET.fromstring(dmn.export(table, rules_version_value="x"))
    path = "dmn:decision/dmn:decisionTable"
    assert ET.tostring(root.find(path, NS)) == ET.tostring(fresh.find(path, NS))
