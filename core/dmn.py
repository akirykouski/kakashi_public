"""Export the declared decision table (core/decision_table.yaml) as a standard OMG DMN 1.3 model.

Why: a buyer can open the same rules in Camunda Modeler, Drools, Trisotech or any DMN 1.3 tool. The rules are
data in an open standard, not locked in this product.

What is written (one decision, "Change decision", hit policy FIRST):
- inputs:  the change class (string), then one boolean input per rule id the table reads ("R1a fired", ...);
- outputs: row id, allowed actions (FEEL list of strings), decider, rests_on (FEEL list of strings);
- one DMN rule per table row, in table order; the row meaning is the rule's description (the "Annotations"
  column in DMN editors). A row with an "any" condition becomes one DMN rule per listed rule id, placed next to
  each other with the same outputs: under FIRST that is the same table.
- a text annotation on the decision with the table's version note and the rules_version hash.

Cells are FEEL unary tests, and only these four forms are emitted:
  "-"                       any value
  true / false              a boolean equals
  "A","B"                   the change class is one of these strings
Outputs are FEEL literals: a string ("D1") or a list of strings (["stop", "re-audit supplier"]).

tests/test_dmn.py evaluates the exported XML with its own small FEEL reader and compares every input set the
coverage check enumerates (2^9 rule sets x 17 change classes) with core.decision.

Written 14 Nov 2026 (workstream DMN), new code.

CLI:
    python -m core.dmn --out decision.dmn     # write the file
    python -m core.dmn                        # print the XML
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from core import decision
from core.contracts import CHANGE_TYPES

DMN_NS = "https://www.omg.org/spec/DMN/20191111/MODEL/"
DMNDI_NS = "https://www.omg.org/spec/DMN/20191111/DMNDI/"
DC_NS = "http://www.omg.org/spec/DMN/20180521/DC/"
DI_NS = "http://www.omg.org/spec/DMN/20180521/DI/"
MODEL_NAMESPACE = "https://github.com/akirykouski/kakashi_public/decision"

DEFINITIONS_ID = "Definitions_change_check"
DECISION_ID = "Decision_change"
DECISION_NAME = "Change decision"
TABLE_ID = "DecisionTable_change"
CLASS_INPUT = "change_class"


class ExportError(ValueError):
    """The table holds a condition the DMN export cannot write as one rule."""


def fired_variable(rule_id):
    """FEEL variable name of the boolean input for one rule id, e.g. fired_R1a."""
    return f"fired_{rule_id}"


def feel_string(text):
    escaped = str(text).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def feel_list(items):
    return "[" + ", ".join(feel_string(item) for item in items) + "]"


def element_id(prefix, raw):
    """A DMN id is an XML NCName: letters, digits, _ - . and not starting with a digit."""
    cleaned = "".join(char if char.isalnum() or char in "_-." else "_" for char in str(raw))
    return f"{prefix}_{cleaned}"


# ---- rows -> DMN rules -----------------------------------------------------------------------------------

def class_cell(when, table):
    classes = decision.expand(when.get("classes", "any"), table.get("class_groups") or {}, CHANGE_TYPES)
    if set(classes) == set(CHANGE_TYPES):
        return "-"
    ordered = [name for name in CHANGE_TYPES if name in set(classes)]
    return ",".join(feel_string(name) for name in ordered)


def rule_cells(row, table):
    """One {rule_id: "true"|"false"|"-"} map per DMN rule the row becomes (more than one only for "any")."""
    when = row.get("when") or {}
    rule_ids = table["rules"]
    groups = table.get("rule_groups") or {}
    required = decision.expand(when.get("all", []), groups, rule_ids)
    excluded = decision.expand(when.get("none", []), groups, rule_ids)
    alternatives = decision.expand(when.get("any", []), groups, rule_ids)
    clash = set(required) & set(excluded)
    if clash:
        raise ExportError(f"{row['id']}: rule(s) {sorted(clash)} are both required and excluded")
    base = {rule_id: "-" for rule_id in rule_ids}
    for rule_id in required:
        base[rule_id] = "true"
    for rule_id in excluded:
        base[rule_id] = "false"
    if not alternatives:
        return [base]
    if any(rule_id in required for rule_id in alternatives):
        return [base]  # one alternative is already required: the "any" holds whenever the row can match
    variants = []
    for rule_id in alternatives:
        if rule_id in excluded:
            continue
        variant = dict(base)
        variant[rule_id] = "true"
        variants.append(variant)
    if not variants:
        raise ExportError(f"{row['id']}: every 'any' rule is also excluded, the row can never match")
    return variants


def dmn_rules(table):
    """The table rows as DMN rules: [{"id", "row_id", "description", "inputs": [...], "outputs": [...]}]."""
    result = []
    for row in table["rows"]:
        variants = rule_cells(row, table)
        outputs = [feel_string(row["id"]), feel_list(row.get("actions") or []), feel_string(row["decider"]),
                   feel_list(row.get("rests_on") or [])]
        for index, cells in enumerate(variants):
            suffix = "" if len(variants) == 1 else f"_any{index + 1}"
            result.append({
                "id": element_id("Rule", row["id"] + suffix),
                "row_id": row["id"],
                "description": row.get("meaning", ""),
                "inputs": [class_cell(row.get("when") or {}, table)] + [cells[rule_id] for rule_id in table["rules"]],
                "outputs": outputs,
            })
    return result


# ---- XML ------------------------------------------------------------------------------------------------

def dmn(tag):
    return f"{{{DMN_NS}}}{tag}"


def sub(parent, tag, attributes=None, text=None, namespace=DMN_NS):
    node = ET.SubElement(parent, f"{{{namespace}}}{tag}", attributes or {})
    if text is not None:
        node.text = text
    return node


def annotation_text(table, rules_version_value):
    note = table.get("version_note") or ""
    return (f"Exported from core/decision_table.yaml ({note}). rules_version {rules_version_value}. "
            "Hit policy FIRST: the first matching row answers; the last row R0 means no rule covers the change "
            "and a person decides. Inputs: the change class and, per rule id, whether that rule fired at severity "
            "blocker, warning or question.")


def export(table=None, rules_version_value=None):
    """The table as a DMN 1.3 XML string."""
    table = table or decision.load_table()
    if table.get("hit_policy") != "first":
        raise ExportError("only hit policy 'first' is exported")
    version = rules_version_value or decision.rules_version()
    ET.register_namespace("", DMN_NS)
    ET.register_namespace("dmndi", DMNDI_NS)
    ET.register_namespace("dc", DC_NS)
    ET.register_namespace("di", DI_NS)

    definitions = ET.Element(dmn("definitions"), {
        "id": DEFINITIONS_ID, "name": "Change Check decision model", "namespace": MODEL_NAMESPACE,
        "exporter": "kakashi core.dmn", "exporterVersion": "1"})
    decision_node = sub(definitions, "decision", {"id": DECISION_ID, "name": DECISION_NAME})
    sub(decision_node, "description", text="What may be done about a proposed supplier change and who decides. "
        "Never an approval: the best outcome is 'proceed under standard change control'.")
    table_node = sub(decision_node, "decisionTable", {"id": TABLE_ID, "hitPolicy": "FIRST"})

    class_input = sub(table_node, "input", {"id": "Input_change_class", "label": "Change class"})
    sub(class_input, "inputExpression", {"id": "InputExpression_change_class", "typeRef": "string"}).append(
        _text(CLASS_INPUT))
    sub(class_input, "inputValues", {"id": "InputValues_change_class"}).append(
        _text(",".join(feel_string(name) for name in CHANGE_TYPES)))
    for rule_id in table["rules"]:
        node = sub(table_node, "input", {"id": element_id("Input", rule_id), "label": f"{rule_id} fired"})
        sub(node, "inputExpression", {"id": element_id("InputExpression", rule_id), "typeRef": "boolean"}).append(
            _text(fired_variable(rule_id)))

    sub(table_node, "output", {"id": "Output_row_id", "label": "Row", "name": "row_id", "typeRef": "string"})
    sub(table_node, "output", {"id": "Output_allowed_actions", "label": "Allowed actions",
                               "name": "allowed_actions"})
    sub(table_node, "output", {"id": "Output_decider", "label": "Decides", "name": "decider", "typeRef": "string"})
    sub(table_node, "output", {"id": "Output_rests_on", "label": "Rests on", "name": "rests_on"})

    for rule in dmn_rules(table):
        rule_node = sub(table_node, "rule", {"id": rule["id"]})
        sub(rule_node, "description", text=rule["description"])
        for index, cell in enumerate(rule["inputs"]):
            entry = sub(rule_node, "inputEntry", {"id": f"{rule['id']}_in{index}"})
            sub(entry, "text", text=cell)
        for index, value in enumerate(rule["outputs"]):
            entry = sub(rule_node, "outputEntry", {"id": f"{rule['id']}_out{index}"})
            sub(entry, "text", text=value)

    sub(definitions, "textAnnotation", {"id": "Annotation_rules_version"}).append(
        _text(annotation_text(table, version)))
    association = sub(definitions, "association", {"id": "Association_rules_version"})
    sub(association, "sourceRef", {"href": "#Annotation_rules_version"})
    sub(association, "targetRef", {"href": f"#{DECISION_ID}"})

    dmndi = sub(definitions, "DMNDI", namespace=DMNDI_NS)
    diagram = sub(dmndi, "DMNDiagram", {"id": "DMNDiagram_change"}, namespace=DMNDI_NS)
    shape = sub(diagram, "DMNShape", {"id": "DMNShape_decision", "dmnElementRef": DECISION_ID}, namespace=DMNDI_NS)
    sub(shape, "Bounds", {"height": "80", "width": "180", "x": "160", "y": "100"}, namespace=DC_NS)
    shape = sub(diagram, "DMNShape", {"id": "DMNShape_annotation", "dmnElementRef": "Annotation_rules_version"},
                namespace=DMNDI_NS)
    sub(shape, "Bounds", {"height": "160", "width": "420", "x": "420", "y": "60"}, namespace=DC_NS)
    edge = sub(diagram, "DMNEdge", {"id": "DMNEdge_association", "dmnElementRef": "Association_rules_version"},
               namespace=DMNDI_NS)
    sub(edge, "waypoint", {"x": "420", "y": "140"}, namespace=DI_NS)
    sub(edge, "waypoint", {"x": "340", "y": "140"}, namespace=DI_NS)

    ET.indent(definitions, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(definitions, encoding="unicode") + "\n"


def _text(value):
    node = ET.Element(dmn("text"))
    node.text = value
    return node


def dmn_rule_id(row_id, table=None):
    """The DMN rule id(s) a table row is written as (for highlighting a matched row in a viewer)."""
    table = table or decision.load_table()
    return [rule["id"] for rule in dmn_rules(table) if rule["row_id"] == row_id]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export the decision table as an OMG DMN 1.3 file")
    parser.add_argument("--out", default=None, help="file to write (default: print to stdout)")
    parser.add_argument("--table", default=None, help="decision table YAML (default: core/decision_table.yaml)")
    args = parser.parse_args(argv)
    xml_text = export(decision.load_table(args.table))
    if args.out:
        Path(args.out).write_text(xml_text, encoding="utf-8")
        print(f"wrote {args.out} (DMN 1.3, {xml_text.count('<rule ')} rules)", file=sys.stderr)
    else:
        sys.stdout.write(xml_text)


if __name__ == "__main__":
    main()
