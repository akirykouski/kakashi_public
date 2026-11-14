"""Tests for core/rules.py and core/explain.py (workstream R).

Prototype scenarios keep their findings; new tests cover: change-class keying of R2 and the certificate
question (item 2), open 8D at series level with the feature gate (item 3), completeness-scoped source release
(item 4), material vs drawing (item 5), covered() and proof-chain integrity.
"""
import json
import os
import sys
from collections import Counter

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.contracts import EvidenceStep, Finding  # noqa: E402
from core.explain import Explainer, leaves, valid_step  # noqa: E402
from core.factlog import FactLog, default_log  # noqa: E402
from core.project import Projection  # noqa: E402
from core.rules import RULES_DATA, check, covered, extend_log  # noqa: E402

SCENARIOS = {item["id"]: item for item in json.load(open(os.path.join(ROOT, "data", "scenarios.json")))}

# (rule, severity) multisets the prototype (night-shift + fix/1,2,4,8) produced for each scenario.
EXPECTED = {
    "main": [("R1a", "blocker"), ("R1b", "blocker"), ("R6", "blocker"), ("R2", "blocker"), ("R3", "warning"),
             ("R7", "question")],
    "main_after_audit": [("R1b", "blocker"), ("R6", "blocker"), ("R2", "blocker"), ("R3", "warning"),
                         ("R7", "question"), ("R4", "info")],
    "elv": [("R2", "blocker"), ("R2", "blocker"), ("R5", "blocker")],
    "silence": [],
    "subtier": [("R8", "blocker")],
}

FINDING_KEYS = set(Finding.__dataclass_fields__)
STEP_KEYS = set(EvidenceStep.__dataclass_fields__) - {"epistemic"}  # leaf badge is set by check.run (core/oida.py)


def fact(s, p, o, source="TEST", quote=None, literal=False, valid_from=None, fact_id=None):
    fact.counter += 1
    return {"s": s, "p": p, "o": json.dumps(o) if literal else o, "source": source,
            "quote": quote or f"{s} {p} {o}", "valid_from": valid_from, "valid_to": None, "kind": "assert", "rank": 2,
            "author": None, "id": fact_id or f"T{fact.counter:04d}"}


fact.counter = 0


def make_log(tmp_path, extra=(), drop=None):
    """Default data + rules policy facts (minus rows `drop` matches) + extra fixture facts."""
    log = default_log()
    rows = [json.loads(line) for line in open(os.path.join(RULES_DATA, "facts.jsonl"))]
    rows = [row for row in rows if not (drop and drop(row))] + list(extra)
    path = tmp_path / "facts.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    log.load_jsonl(str(path))
    log._rules_data_loaded = True
    return log


@pytest.fixture(scope="module")
def log():
    return extend_log(default_log())


def run(log, change, as_of="2026-11-14"):
    projection = Projection(log, as_of)
    return projection, check(projection, change)


def pairs(findings):
    return Counter((item["rule"], item["severity"]) for item in findings)


def assert_contract(findings):
    for item in findings:
        assert set(item) == FINDING_KEYS
        assert isinstance(item["entities"], list)
        if item["consequence"] is not None:
            assert {"type", "source", "quote"} <= set(item["consequence"])
        for step in item["evidence"]:
            assert valid_step(step), step
            stack = [step]
            while stack:
                current = stack.pop()
                assert set(current) == STEP_KEYS
                stack.extend(current["premises"])
        if item["severity"] in ("blocker", "question", "warning"):
            assert item["evidence"], f"{item['rule']} {item['title']} has no evidence"


# ---- prototype scenarios ---------------------------------------------------------------------------------

@pytest.mark.parametrize("scenario", sorted(EXPECTED))
def test_prototype_scenarios_keep_their_findings(log, scenario):
    item = SCENARIOS[scenario]
    _, findings = run(log, item["change"], item["as_of"])
    assert pairs(findings) == Counter(EXPECTED[scenario])
    assert_contract(findings)


def test_main_details(log):
    item = SCENARIOS["main"]
    _, findings = run(log, item["change"], item["as_of"])
    r2 = next(item for item in findings if item["rule"] == "R2")
    assert "CSR-AUR-R4" in r2["entities"]
    assert r2["consequence"] and r2["consequence"]["source"] == "CSR-AUR-R4"  # fix/4
    question = next(item for item in findings if item["rule"] == "R7")
    assert question["owner"] == "PER-GALLO"  # read from data, not code
    sources = {leaf["source"] for step in question["evidence"] for leaf in leaves(step)}
    assert "QP-11" in sources


def test_superseded_requirement_never_cited(log):
    item = SCENARIOS["main"]
    _, findings = run(log, item["change"], item["as_of"])
    cited = {leaf["source"] for finding in findings for step in finding["evidence"] for leaf in leaves(step)}
    assert "CSR-AUR-R3" not in cited


# ---- item 2: keyed on change class, not on a new supplier -----------------------------------------------

def test_coating_change_without_supplier_gets_customer_approval(log):
    _, findings = run(log, {"type": "CoatingChange", "part": "BR-220"})
    assert ("R2", "blocker") in pairs(findings)


def test_test_method_change_without_supplier_gets_r2_when_requirement_covers_it(tmp_path):
    extra = [fact("CSR-AUR-R4", "requiresCustomerApprovalFor", "TestMethodChange", source="CSR-AUR-R4",
                  quote="a change of test method", valid_from="2026-07-01")]
    log = make_log(tmp_path, extra)
    projection, findings = run(log, {"type": "TestMethodChange", "part": "BR-220"})
    r2 = [item for item in findings if item["rule"] == "R2" and item["severity"] == "blocker"]
    assert r2 and "CSR-AUR-R4" in r2[0]["entities"]
    assert covered({"type": "TestMethodChange", "part": "BR-220"}, projection)


def test_test_method_change_not_covered_without_requirement(log):
    projection, findings = run(log, {"type": "TestMethodChange", "part": "BR-220"})
    assert findings == []
    assert not covered({"type": "TestMethodChange", "part": "BR-220"}, projection)


def test_material_change_without_supplier_asks_for_certificate_of_current_source(log):
    _, findings = run(log, {"type": "MaterialChange", "part": "BR-220", "new_material": "MAT-6082-T5"})
    questions = [item for item in findings if item["rule"] == "R7"]
    assert any("SUP-B" in item["entities"] and "MAT-6082-T5" in item["entities"] for item in questions)
    assert all(item["owner"] == "PER-GALLO" for item in questions)


def test_certificate_classes_come_from_data(tmp_path):
    log = make_log(tmp_path, drop=lambda row: row["p"] == "requiresCertificateFor")
    _, findings = run(log, SCENARIOS["main"]["change"], "2026-11-05")
    assert ("R7", "question") not in pairs(findings)


# ---- item 3: open 8D at series level, feature gate, policy flag from data ---------------------------------

def supplier_with_8d(alloy, feature):
    return [fact("SUP-T", "type", "Supplier"), fact("SUP-T", "label", "Test Alu", literal=True),
            fact("8D-T-001", "type", "Issue"), fact("8D-T-001", "concernsSupplier", "SUP-T"),
            fact("8D-T-001", "status", "open", literal=True), fact("8D-T-001", "concernsMaterial", alloy),
            fact("8D-T-001", "failureFeature", feature)]


def policy_level(level):
    return [fact("POL-TEST", "type", "Policy"), fact("POL-TEST", "statedIn", "TEST"),
            fact("POL-TEST", "policyFor", "OpenIssueLevel"), fact("POL-TEST", "policyValue", level, literal=True)]


def r3(findings):
    return [item for item in findings if item["rule"] == "R3"]


CHANGE_T = {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-T"}


def test_series_and_feature_default_fires(tmp_path):
    log = make_log(tmp_path, supplier_with_8d("ALY-6061", "FEAT-FASTENING-HOLE"))
    _, findings = run(log, CHANGE_T)
    found = r3(findings)
    assert len(found) == 1 and "Series6xxx" in found[0]["entities"] and "FEAT-FASTENING-HOLE" in found[0]["entities"]
    assert_contract(findings)
    sources = {leaf["source"] for step in found[0]["evidence"] for leaf in leaves(step)}
    assert {"QP-15", "FMEA-BR220", "REG-MATERIALS"} <= sources


def test_series_without_shared_feature_is_gated(tmp_path):
    log = make_log(tmp_path, supplier_with_8d("ALY-6061", "FEAT-OTHER"))
    _, findings = run(log, CHANGE_T)
    assert not r3(findings)


def test_policy_series_only_drops_the_gate(tmp_path):
    log = make_log(tmp_path, supplier_with_8d("ALY-6061", "FEAT-OTHER") + policy_level("series"),
                   drop=lambda row: row["p"] in ("policyValue", "policyFor"))
    _, findings = run(log, CHANGE_T)
    assert len(r3(findings)) == 1


def test_policy_alloy_keeps_exact_alloy_only(tmp_path):
    log = make_log(tmp_path, supplier_with_8d("ALY-6061", "FEAT-FASTENING-HOLE") + policy_level("alloy"),
                   drop=lambda row: row["p"] in ("policyValue", "policyFor"))
    _, findings = run(log, CHANGE_T)
    assert not r3(findings)


def test_exact_alloy_still_matches_under_any_policy(tmp_path):
    log = make_log(tmp_path, supplier_with_8d("ALY-6082", "FEAT-OTHER") + policy_level("alloy"),
                   drop=lambda row: row["p"] in ("policyValue", "policyFor"))
    _, findings = run(log, CHANGE_T)
    assert len(r3(findings)) == 1


# ---- item 4: completeness-scoped source release -----------------------------------------------------------

def narrow_scope():
    """Replace the data's statement (series parts, both plants, all customers and commodities) by a narrow one:
    Beinasco x Aurelia x 6xxx aluminium x series."""
    extra = [fact("CS-NARROW", "type", "CompletenessStatement"), fact("CS-NARROW", "completeForPlant", "PLT-BEI"),
             fact("CS-NARROW", "completeForCustomer", "CUST-AUR"),
             fact("CS-NARROW", "completeForSeries", "Series6xxx"),
             fact("CS-NARROW", "completeForScope", "series", literal=True)]
    return extra, (lambda row: row["s"] == "CS-ASL-SERIES")


def test_release_blocker_inside_declared_scope(log):
    _, findings = run(log, {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-D", "site": "PLT-BEI"})
    blockers = [item for item in findings if item["rule"] == "R1b"]
    assert blockers and blockers[0]["severity"] == "blocker" and "CS-ASL-SERIES" in blockers[0]["entities"]


def test_release_blocker_inside_narrow_scope(tmp_path):
    extra, drop = narrow_scope()
    _, findings = run(make_log(tmp_path, extra, drop),
                      {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-D", "site": "PLT-BEI"})
    blockers = [item for item in findings if item["rule"] == "R1b"]
    assert blockers and "CS-NARROW" in blockers[0]["entities"]
    sources = {leaf["source"] for step in blockers[0]["evidence"] for leaf in leaves(step)}
    assert "REG-MATERIALS" in sources  # commodity proven via madeOfSeries


def test_release_question_for_service_parts(log):
    _, findings = run(log, {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-D", "site": "PLT-BEI",
                            "scope": "service"})
    assert not [item for item in findings if item["rule"] == "R1b"]
    asked = [item for item in findings if "Q-source_release" in item["entities"]]
    assert asked and asked[0]["severity"] == "question" and asked[0]["owner"] == "PER-GALLO"


def test_release_question_outside_plant(tmp_path):
    extra, drop = narrow_scope()
    _, findings = run(make_log(tmp_path, extra, drop), {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-D", "site": "PLT-PIN"})
    assert not [item for item in findings if item["rule"] == "R1b"]
    assert [item for item in findings if "Q-source_release" in item["entities"]]


def test_release_question_outside_commodity(tmp_path):
    # CL-115 is spring steel: the narrow list is complete only for 6xxx aluminium.
    extra, drop = narrow_scope()
    _, findings = run(make_log(tmp_path, extra, drop), {"type": "SourceChange", "part": "CL-115", "to_supplier": "SUP-C", "site": "PLT-BEI"})
    assert not [item for item in findings if item["rule"] == "R1b"]
    assert [item for item in findings if "Q-source_release" in item["entities"]]


# ---- item 5: material vs drawing designation -------------------------------------------------------------

def test_material_change_off_drawing_is_blocker(log):
    _, findings = run(log, {"type": "MaterialChange", "part": "BR-220", "new_material": "MAT-6061-T6"})
    drawing = [item for item in findings if item["rule"] == "R6" and "MAT-6082-T6" in item["entities"]]
    assert drawing and drawing[0]["severity"] == "blocker"
    assert_contract(findings)


def test_material_change_to_drawing_material_has_no_drawing_blocker(log):
    _, findings = run(log, {"type": "MaterialChange", "part": "BR-220", "new_material": "MAT-6082-T6"})
    assert not [item for item in findings if item["rule"] == "R6"]


def test_unknown_material_is_question_with_owner(log):
    _, findings = run(log, {"type": "MaterialChange", "part": "BR-220", "new_material": "MAT-UNOBTAINIUM"})
    asked = [item for item in findings if "Q-material_data" in item["entities"]]
    assert asked and asked[0]["owner"] == "PER-ROSSI" and asked[0]["evidence"]


# ---- covered() -------------------------------------------------------------------------------------------

def test_covered(log):
    projection = Projection(log, "2026-11-14")
    assert covered(SCENARIOS["main"]["change"], projection)
    assert covered(SCENARIOS["elv"]["change"], projection)
    assert covered(SCENARIOS["subtier"]["change"], projection)
    assert covered(SCENARIOS["silence"]["change"], projection)  # QP-15 4.1
    assert not covered({"type": "EquipmentChange", "part": "BR-220"}, projection)
    assert not covered({"type": "PriceChange", "part": "BR-220"}, projection)


# ---- explain.py ------------------------------------------------------------------------------------------

def test_explainer_leaf_carries_context_quote(log):
    # projection.graph and provenance are shared and cached: never mutate them; use a view.
    from types import SimpleNamespace
    projection = Projection(log, "2026-11-14")
    triple, rows = sorted(projection.provenance.items(), key=lambda item: str(item[0]))[0]
    view = SimpleNamespace(graph=projection.graph,
                           provenance={triple: [dict(rows[0], context_quote="governing sentence")]})
    step = Explainer(view).explain(triple)
    assert step["context_quote"] == "governing sentence" and step["quote"]


def test_explainer_returns_none_without_proof():
    from types import SimpleNamespace
    from rdflib import Graph, URIRef
    triple = (URIRef("https://lcc.example/id/X"), URIRef("https://lcc.example/ont#madeOf"),
              URIRef("https://lcc.example/id/Y"))
    graph = Graph()
    graph.add(triple)  # in the closure, but no fact and no axiom produced it
    assert Explainer(SimpleNamespace(graph=graph, provenance={})).explain(triple) is None
