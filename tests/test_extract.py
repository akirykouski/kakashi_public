"""Extractor tests. Run: python -m pytest tests/ -q

Check tests need no model. The two document tests replay answers recorded live through the Vercel AI Gateway
(anthropic/claude-haiku-5.5) from tests/fixtures/extract/, so they run without AI_GATEWAY_API_KEY. Both documents
in tests/fixtures/docs/ are synthetic (fictional customers); no third-party text.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))

from extract import (CHANGE_TYPES, check_fact, extract_document, extract_text, grounded,  # noqa: E402
                     grounding_aliases, grounding_names, load_registries, to_proposals)

DOCS = os.path.join(ROOT, "tests", "fixtures", "docs")
REG = load_registries()

# ---- fix/3: two-span quotes (ported from research/prototypes/tests/test_context_quote.py) ----------------
DOC = "Intro.\n\nThe following changes   require Adient approval:\n- Change in sub-supplier\n- Change of site\n"
PREDICATES = {"requiresCustomerApprovalFor"}
IDS = {"DOC", "SourceChange"}


def fact(**extra):
    return {"s": "DOC", "p": "requiresCustomerApprovalFor", "o": "SourceChange",
            "quote": "Change in sub-supplier", **extra}


def test_context_and_quote_both_verbatim_pass():
    checked, reason = check_fact(fact(context_quote="The following changes require Adient approval:"),
                                 DOC, PREDICATES, IDS)
    assert reason is None
    assert checked["context_quote"] == "The following changes   require Adient approval:"  # document's own text


def test_invented_context_is_rejected():
    _, reason = check_fact(fact(context_quote="All changes require approval:"), DOC, PREDICATES, IDS)
    assert reason == "context quote not found in document"


def test_context_after_quote_is_rejected():
    _, reason = check_fact(fact(context_quote="Change of site"), DOC, PREDICATES, IDS)
    assert reason and reason.startswith("context quote not before quote")


def test_context_too_far_before_quote_is_rejected():
    doc = "Rule: approval needed.\n\n" + "filler. " * 400 + "\n- Change in sub-supplier\n"
    _, reason = check_fact(fact(context_quote="Rule: approval needed."), doc, PREDICATES, IDS)
    assert reason and reason.startswith("context quote not before quote")


def test_context_outside_chunk_is_rejected():
    scope = DOC[DOC.index("- Change in"):]
    _, reason = check_fact(fact(context_quote="The following changes require Adient approval:"),
                           DOC, PREDICATES, IDS, scope=scope)
    assert reason and reason.startswith("context quote not before quote")


def test_no_context_unchanged():
    checked, reason = check_fact(fact(), DOC, PREDICATES, IDS)
    assert reason is None and "context_quote" not in checked


def test_invented_quote_is_rejected():
    _, reason = check_fact(fact(quote="Change of supplier"), DOC, PREDICATES, IDS)
    assert reason == "quote not found in document"


def test_inferred_predicate_is_rejected():
    _, reason = check_fact({**fact(), "p": "subjectTo"}, DOC, PREDICATES | {"subjectTo"}, IDS)
    assert reason == "predicate subjectTo not allowed"


# ---- fix/5: alias grounding (ported from research/prototypes/tests/test_aliases.py) ----------------------
ALIAS_REG = {
    "parts": {"columns": ["id", "name"], "rows": [["PART-X", "Driver airbag cover"]]},
    "suppliers": {"columns": ["id", "name"], "rows": [["SUP-DEMO", "DEMO, Tier 3 supplier"]],
                  "aliases": {"SUP-DEMO": ["DEMO"]}},
}
QUOTE = "the Tier 3 supplier (DEMO) made adjustments"


def test_id_name_rule_unchanged_without_alias():
    names = grounding_names({k: {"rows": v["rows"]} for k, v in ALIAS_REG.items()})
    assert not grounded("SUP-DEMO", QUOTE, names)
    assert grounded("SUP-DEMO", "see SUP-DEMO here", names)


def test_alias_is_case_insensitive_whole_word_only():
    names, aliases = grounding_names(ALIAS_REG), grounding_aliases(ALIAS_REG)
    assert grounded("SUP-DEMO", QUOTE, names, aliases)
    assert grounded("SUP-DEMO", "demo made changes", names, aliases)
    assert not grounded("SUP-DEMO", "a demonstration run", names, aliases)
    assert not grounded("SUP-DEMO", "the Tier 3 supplier made changes", names, aliases)


def test_alias_does_not_ground_other_entities():
    assert not grounded("PART-X", QUOTE, grounding_names(ALIAS_REG), grounding_aliases(ALIAS_REG))


def test_ungrounded_supplier_goes_to_review():
    doc = "NCR 7: the supplier delivered parts with porosity."
    candidate = {"s": "NCR-7", "p": "concernsSupplier", "o": "SUP-D", "quote": "the supplier delivered parts"}
    _, reason = check_fact(candidate, doc, {"concernsSupplier"}, {"NCR-7", "SUP-D"}, grounding_names(REG))
    assert reason == "ungrounded: quote does not name SUP-D"


# ---- fix/7 + fix/1 with a fake model ---------------------------------------------------------------------

def fake_call(answer):
    def call(model, system, prompt, schema):
        return answer, {}
    call.recorded_by = "test"
    return call


def test_blanket_and_unclassified_checks(tmp_path, monkeypatch):
    import extract as extract_module
    monkeypatch.setattr(extract_module, "FIXTURES_DIR", str(tmp_path))
    body = "5.1 Written consent is needed before any change to products or processes.\n5.9 Price is per quote.\n"
    rule = "Written consent is needed before any change to products or processes."
    answer = {"facts": [{"s": "DOC-T", "p": "requiresCustomerApprovalFor", "o": change_type, "quote": rule,
                         "context_quote": None} for change_type in ("SourceChange", "MaterialChange")],
              "unclassified": [{"quote": "Price is per quote.", "summary": "price terms"},
                               {"quote": "Prices are fixed for 3 years.", "summary": "invented"}]}
    header = {"id": "DOC-T", "type": "customer_requirement", "valid_from": "2026-11-01", "valid_to": None}
    result = extract_text(header, body, registries=REG, call=fake_call(answer), live=True)
    assert [f["o"] for f in result["accepted"]] == ["SourceChange", "MaterialChange"]
    assert {f["quote"] for f in result["accepted"]} == {rule}
    assert result["unclassified"] == [{"quote": "Price is per quote.", "summary": "price terms"}]
    assert result["unclassified_rejected"][0]["reason"] == "quote not found in document"
    proposals = to_proposals(result)
    assert [p["kind"] for p in proposals] == ["assert", "assert", "unclassified"]
    assert all(p["rank"] == 1 and p["source"] == "DOC-T" and p["status"] == "proposed" for p in proposals)


# ---- recorded documents ----------------------------------------------------------------------------------

def test_csr_aur_r4_from_fixture():
    result = extract_document(os.path.join(DOCS, "CSR-AUR-R4.md"))
    assert all(source.startswith("fixture") for source in result["answers_from"])
    approvals = {f["o"]: f for f in result["accepted"] if f["p"] == "requiresCustomerApprovalFor"}
    assert set(approvals) == {"SourceChange", "MaterialChange", "ProcessChange", "CoatingChange"}
    assert approvals["SourceChange"]["quote"] == "a change of source"
    assert approvals["SourceChange"]["context_quote"].startswith("The supplier shall obtain written approval")
    assert result["unclassified"], "per-part approval scope fits no predicate and must be listed"
    body = open(os.path.join(DOCS, "CSR-AUR-R4.md")).read()
    for item in result["accepted"] + result["unclassified"]:
        assert item["quote"] in body and (item.get("context_quote") or "") in body


def test_blanket_rule_from_fixture():
    result = extract_document(os.path.join(DOCS, "CSR-NOR-SYN.md"))
    blanket = [f for f in result["accepted"] if f["p"] == "requiresCustomerApprovalFor"
               and f["quote"].startswith("The supplier shall obtain written consent")]
    assert len(blanket) >= 4 and all(f["o"] in CHANGE_TYPES for f in blanket)
    assert any(f["p"] == "requiresNotificationFor" and f["o"] == "PackagingChange" for f in result["accepted"])
    proposals = to_proposals(result)
    keys = {"source", "quote", "context_quote", "s", "p", "o", "kind", "rank"}
    assert all(keys <= set(p) for p in proposals)
    json.dumps(proposals)
