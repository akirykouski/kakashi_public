"""Parser tests. Run: python -m pytest tests/ -q

Id resolution and the typed-form path need no model. The accuracy test replays recorded model answers from
tests/fixtures/parse/ (recorded live through the Vercel AI Gateway, anthropic/claude-haiku-5.5), so it runs without
AI_GATEWAY_API_KEY; to call the model again use `python tests/parse_accuracy.py --live`.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from parse import FixtureMissing, load_registries, parse, parse_form, resolve, resolve_fields  # noqa: E402

REG = load_registries()


@pytest.mark.parametrize("table,text,expected", [
    ("suppliers", "SUP-C", "SUP-C"),
    ("suppliers", "sup-c", "SUP-C"),
    ("suppliers", "Chisone", "SUP-C"),
    ("suppliers", "Meccanica Chisone", "SUP-C"),
    ("suppliers", "Meccanica Chisone S.r.l.", "SUP-C"),
    ("suppliers", "alluminio bormida", "SUP-B"),
    ("parts", "BR-220", "BR-220"),
    ("parts", "BR-220 blanks", "BR-220"),
    ("sites", "Pinerolo", "PLT-PIN"),
    ("materials", "EN AW-6061-T6", "MAT-6061-T6"),
    ("coatings", "zinc flake", "COAT-ZNFLAKE"),
    ("coatings", "zinc-nickel", "COAT-ZNNI"),
    ("coatings", "yellow chromate passivation", "COAT-ZN-YELLOW"),
    ("coatings", "yellow chromate conversion coating", "COAT-CCC-YELLOW"),
    ("coatings", "trivalent conversion coating", "COAT-TCP"),
])
def test_resolves(table, text, expected):
    assert resolve(REG, table, text) == {"id": expected}


@pytest.mark.parametrize("table,text,reason", [
    ("suppliers", "Viteria Lanzo", "not in suppliers"),
    ("suppliers", "Fonderia", "ambiguous"),          # Fonderia Dora and Fonderia Pellice
    ("suppliers", "Chis", "not in suppliers"),       # no substring / fuzzy match
    ("coatings", "Nanoceram", "not in coatings"),
    ("coatings", "zinc", "ambiguous"),
    ("materials", "EN AW-7075", "not in materials"),
    ("materials", "6061", "ambiguous"),              # alloy and temper
    ("suppliers", "", "empty"),
])
def test_unresolved_never_guessed(table, text, reason):
    outcome = resolve(REG, table, text)
    assert outcome["id"] is None and outcome["reason"] == reason


def test_ambiguous_lists_candidates():
    assert resolve(REG, "suppliers", "Fonderia")["candidates"] == ["SUP-D", "SUP-H"]


def test_confirmed_alias_whole_word_only():
    registries = {**REG, "suppliers": {**REG["suppliers"], "aliases": {"SUP-C": ["MecChis"]}}}
    assert resolve(registries, "suppliers", "mecchis") == {"id": "SUP-C"}
    assert resolve(registries, "suppliers", "MecChis plant 2") == {"id": "SUP-C"}
    assert resolve(registries, "suppliers", "MecChisone")["id"] is None


def test_name_must_be_written_in_remark():
    resolved, unresolved = resolve_fields(REG, {"part": "BR-220", "to_supplier": "Meccanica Chisone"},
                                          utterance="Take the BR-220 blanks from Chisone")
    assert resolved == {"part": "BR-220"}
    assert unresolved[0]["field"] == "to_supplier" and unresolved[0]["reason"] == "not written in the remark"


def fake_call(answer):
    def call(model, system, prompt, schema):
        return answer, {}
    call.recorded_by = "test"
    return call


def test_parse_with_fake_model(tmp_path, monkeypatch):
    import parse as parse_module
    monkeypatch.setattr(parse_module, "FIXTURES_DIR", str(tmp_path))
    remark = "Viteria Lanzo quoted 20% less for the CL-115 clips, let's switch."
    answer = {"type": "SourceChange", "part": "CL-115", "to_supplier": "Viteria Lanzo", "from_supplier": None,
              "site": None, "new_material": None, "new_coating": None}
    request = parse(remark, as_of="2026-11-14", call=fake_call(answer), live=True)
    assert request["utterance"] == remark
    assert request["part"] == "CL-115" and "to_supplier" not in request
    assert request["unresolved"] == [{"field": "to_supplier", "text": "Viteria Lanzo", "reason": "not in suppliers",
                                      "candidates": []}]
    assert request["parse_confidence"] == 0.5


def test_bad_type_from_model_is_unresolved(tmp_path, monkeypatch):
    import parse as parse_module
    monkeypatch.setattr(parse_module, "FIXTURES_DIR", str(tmp_path))
    answer = {"type": "Teleport", "part": "BR-220"}
    request = parse("Teleport BR-220", call=fake_call(answer), live=True)
    assert "type" not in request and request["unresolved"][0]["field"] == "type"


def test_no_key_no_fixture_raises(tmp_path, monkeypatch):
    import parse as parse_module
    monkeypatch.setattr(parse_module, "FIXTURES_DIR", str(tmp_path))
    import llm
    monkeypatch.setattr(llm, "load_dotenv", lambda: None)
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    with pytest.raises(FixtureMissing):
        parse("Something nobody said before about BR-220")


def test_form_path():
    request = parse_form({"type": "SourceChange", "part": "BR-220", "to_supplier": "Chisone",
                          "from_supplier": "SUP-B", "as_of": "2026-11-14"})
    assert request == {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C", "from_supplier": "SUP-B",
                       "scope": "series", "as_of": "2026-11-14"}


@pytest.mark.parametrize("form", [
    {"type": "Teleport", "part": "BR-220"},
    {"type": "SourceChange"},
    {"type": "SourceChange", "part": "BR-220", "colour": "red"},
    {"type": "SourceChange", "part": "BR-220", "scope": "prototype"},
    {"type": "SourceChange", "part": "BR-220", "as_of": "14/11/2026"},
])
def test_form_rejects(form):
    with pytest.raises(ValueError):
        parse_form(form)


def test_form_unknown_name_is_unresolved():
    request = parse_form({"type": "SourceChange", "part": "BR-220", "to_supplier": "Viteria Lanzo"})
    assert "to_supplier" not in request and request["unresolved"][0]["text"] == "Viteria Lanzo"


def test_accuracy_on_fixtures():
    """All 36 benchmark utterances replay from fixtures; floor guards against regressions in resolution code."""
    import parse_accuracy
    cases = parse_accuracy.load_requests()
    outputs = [parse(case["utterance"], as_of=case.get("as_of"), registries=REG) for case in cases]
    ids = {row[0] for table in REG.values() for row in table.get("rows", [])}
    result, _ = parse_accuracy.score(cases, outputs, ids)
    assert result["n"] == 36
    assert result["fields"]["part"] == 36
    assert result["core"] >= 30
