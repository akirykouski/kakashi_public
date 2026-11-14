"""Core tests. Run: python -m pytest tests/ -q  (from the repo root)"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "data"))

from explain import flatten  # noqa: E402
from factlog import ConflictError, default_log  # noqa: E402
from integrity import run as run_shacl  # noqa: E402
from project import Projection  # noqa: E402
from rules import check, corpus  # noqa: E402


def rules_fired(findings, severity=None):
    return sorted({item["rule"] for item in findings if severity is None or item["severity"] == severity})


def counted(findings):
    return [item for item in findings if item["severity"] != "info"]


@pytest.fixture(scope="module")
def log():
    return default_log()


def test_main_scenario_before_audit(log):
    findings = check(Projection(log, "2026-11-05"), {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C"})
    assert rules_fired(findings, "blocker") == ["R1a", "R1b", "R2", "R6"]
    assert rules_fired(findings, "warning") == ["R3"]
    assert rules_fired(findings, "question") == ["R7"]


def test_main_scenario_after_audit_supplier_blocker_goes_customer_approval_stays(log):
    findings = check(Projection(log, "2026-11-14"), {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C"})
    assert "R1a" not in rules_fired(findings, "blocker")
    assert "R2" in rules_fired(findings, "blocker")
    assert any(item["rule"] == "R4" for item in findings)


def test_inferred_warning_reaches_part_through_alloy(log):
    findings = check(Projection(log, "2026-11-14"), {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C"})
    warning = next(item for item in findings if item["rule"] == "R3")
    assert warning["entities"]["issue"] == "8D-25-031"
    assert any(step["inferred"] and "madeOfAlloy" in step["triple"] for step in warning["evidence"])


def test_elv_coating_blocked(log):
    findings = check(Projection(log, "2026-11-14"), {"type": "CoatingChange", "part": "CL-115", "new_coating": "COAT-ZN-YELLOW"})
    restricted = [item for item in findings if item["rule"] == "R5"]
    assert restricted and restricted[0]["entities"]["substance"] == "CrVI"
    assert "R2" in rules_fired(findings, "blocker")


def test_silence_on_schedule_change(log):
    assert counted(check(Projection(log, "2026-11-14"), {"type": "ScheduleChange", "part": "BR-220"})) == []


def test_valid_deviation_covers_coating_change(log):
    findings = check(Projection(log, "2026-11-14"),
                     {"type": "CoatingChange", "part": "HS-410", "from_supplier": "SUP-E", "new_coating": "COAT-ZNNI"})
    assert counted(findings) == []
    assert any(item["entities"].get("deviation") == "DEV-121" for item in findings)


def test_old_csr_revision_only_needs_notification(log):
    findings = check(Projection(log, "2026-05-01"), {"type": "CoatingChange", "part": "BR-220", "new_coating": "COAT-TCP"})
    assert "R2" not in rules_fired(findings, "blocker")
    findings = check(Projection(log, "2026-11-14"), {"type": "CoatingChange", "part": "BR-220", "new_coating": "COAT-TCP"})
    assert "R2" in rules_fired(findings, "blocker")


def test_revoked_approval(log):
    findings = check(Projection(log, "2026-11-14"), {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-D"})
    assert {"R1a", "R1b"} <= set(rules_fired(findings, "blocker"))
    findings = check(Projection(log, "2026-08-01"), {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-D"})
    assert "R1b" not in rules_fired(findings, "blocker")


def test_every_quote_is_in_its_source(log):
    projection = Projection(log, "2026-11-14")
    sources = corpus()
    changes = [{"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C"},
               {"type": "CoatingChange", "part": "CL-115", "new_coating": "COAT-ZN-YELLOW"}]
    for change in changes:
        for item in check(projection, change):
            for step in item["evidence"]:
                for leaf in flatten(step):
                    assert leaf["quote"] in sources[leaf["source"]]["text"]


def test_conflicting_write_is_refused_until_it_supersedes():
    log = default_log()

    def current(as_of):
        return Projection(log, as_of, reason=False).current_records

    with pytest.raises(ConflictError):
        log.write_record("QS-C-LIVE", "SupplierQualification", {"qualifiedSupplier": "SUP-C", "status": '"conditional"'},
                         source="MTG-LIVE", quote="live", valid_from="2026-11-14", author="PER-GALLO",
                         current_records=current)
    log.write_record("QS-C-LIVE", "SupplierQualification", {"qualifiedSupplier": "SUP-C", "status": '"conditional"'},
                     source="MTG-LIVE", quote="live", valid_from="2026-11-14", author="PER-GALLO",
                     supersedes="QS-C-2026", current_records=current)
    projection = Projection(log, "2026-11-14")
    assert projection.value("QS-C-LIVE", "status") == "conditional"
    assert "QS-C-2026" in projection.replaced


def test_agent_proposal_counts_only_after_acceptance():
    log = default_log()
    log.write_record("QS-C-AGENT", "SupplierQualification", {"qualifiedSupplier": "SUP-C", "status": '"conditional"'},
                     source="MTG-LIVE", quote="agent", valid_from="2026-11-14", author="agent",
                     supersedes="QS-C-2026", proposed_by="extraction-agent")
    assert "QS-C-AGENT" not in Projection(log, "2026-11-14", reason=False).current_records
    log.review("QS-C-AGENT", "accepted", "PER-BIANCHI")
    assert "QS-C-AGENT" in Projection(log, "2026-11-14", reason=False).current_records


def test_transaction_time_hides_facts_learned_later():
    log = default_log()
    log.write_record("QS-C-LATE", "SupplierQualification", {"qualifiedSupplier": "SUP-C", "status": '"conditional"'},
                     source="MTG-LIVE", quote="late", valid_from="2026-11-01", author="PER-GALLO", supersedes="QS-C-2025")
    assert "QS-C-LATE" not in Projection(log, "2026-11-14", known_at="2026-11-13T12:00:00+00:00", reason=False).current_records


def test_shacl_catches_two_current_qualifications():
    log = default_log()
    log.write_record("QS-C-DUP", "SupplierQualification", {"qualifiedSupplier": "SUP-C", "status": '"approved"'},
                     source="MTG-LIVE", quote="dup", valid_from="2026-11-10", author="PER-GALLO")
    conforms, text, _ = run_shacl(Projection(log, "2026-11-14"))
    assert not conforms and "more than one current qualification" in text


def test_shacl_conforms_on_clean_memory(log):
    conforms, _, _ = run_shacl(Projection(log, "2026-11-14"))
    assert conforms


def test_extractor_quote_check_and_review_list(tmp_path):
    from extract import extract_document, find_quote
    from world import DOCUMENTS, REGISTRIES
    text = "Intro.\n\n5.2 A change of coating requires Nordhavn approval before\nthe first shipment.\n"
    assert find_quote(text, "requires Nordhavn approval before the first shipment") is not None
    assert find_quote(text, "requires Nordhavn notification") is None
    path = tmp_path / "CSR-NOR-R2.md"
    path.write_text("---\nid: CSR-NOR-R2\ntype: customer_requirement\ntitle: t\nvalid_from: '2025-03-01'\n"
                    "valid_to: null\nsupersedes: null\nauthor: a\n---\n" + text)

    def fake_call(model, system, prompt, schema):
        facts = [
            {"s": "CSR-NOR-R2", "p": "requiresCustomerApprovalFor", "o": "CoatingChange",
             "quote": "A change of coating requires Nordhavn approval"},
            {"s": "CSR-NOR-R2", "p": "requiresNotificationFor", "o": "CoatingChange",
             "quote": "coating needs only a notification"},           # invented quote
            {"s": "CSR-NOR-R2", "p": "subjectTo", "o": "CUST-NOR", "quote": "Intro."},   # inferred predicate
            {"s": "CSR-NOR-R2", "p": "requiresCustomerApprovalFor", "o": "PaintChange",
             "quote": "A change of coating"},                           # unknown id
            {"s": "CSR-NOR-R2", "p": "concernsPart", "o": "BR-220",
             "quote": "A change of coating requires Nordhavn approval"},  # quote does not name the part
        ]
        return {"facts": facts}, {"input_tokens": 10, "output_tokens": 5}, 0.0, True

    result = extract_document(str(path), REGISTRIES, [item["id"] for item in DOCUMENTS], call=fake_call)
    assert [(fact["p"], fact["o"]) for fact in result["accepted"]] == [("requiresCustomerApprovalFor", "CoatingChange")]
    reasons = sorted(fact["reason"].split(" ")[0] for fact in result["review"])
    assert reasons == ["predicate", "quote", "ungrounded:", "unknown"]
