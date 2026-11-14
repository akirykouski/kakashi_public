"""Speech-recognition forms: spoken part ids, sound-alike supplier names, from-supplier from records."""
import pytest

from core import parse

R = parse.load_registries()


@pytest.mark.parametrize("text", ["BR 220", "BR220", "B R 220", "br-220 blanks", "the BR 220 brackets"])
def test_spoken_part_ids(text):
    assert parse.resolve(R, "parts", text) == {"id": "BR-220"}


def test_unknown_part_stays_unknown():
    assert parse.resolve(R, "parts", "BR 22")["id"] is None


@pytest.mark.parametrize("text", ["kizon", "kisan", "chizone", "kizom"])
def test_chisone_sound_alikes(text):
    assert parse.resolve_sound_alike(R, "suppliers", text)[0] == "SUP-C"


@pytest.mark.parametrize("text", ["bermida", "pormina"])
def test_bormida_sound_alikes(text):
    assert parse.resolve_sound_alike(R, "suppliers", text)[0] == "SUP-B"


@pytest.mark.parametrize("text", ["Acme Tooling", "xyz", "Fonderia"])
def test_no_unique_match_is_none(text):
    assert parse.resolve_sound_alike(R, "suppliers", text) is None


def test_sound_alike_is_noted_not_silent():
    surface = {"part": "BR 220 blanks", "to_supplier": "kizon"}
    notes = []
    resolved, unresolved = parse.resolve_fields(R, surface, notes=notes)
    assert resolved == {"part": "BR-220", "to_supplier": "SUP-C"} and unresolved == []
    assert notes[0]["field"] == "to_supplier" and "heard “kizon”" in notes[0]["note"]
    assert "Meccanica Chisone" in notes[0]["note"] and "sound-alike" in notes[0]["note"]


def test_unknown_supplier_still_not_in_records():
    resolved, unresolved = parse.resolve_fields(R, {"to_supplier": "Zorblax"}, notes=[])
    assert resolved["to_supplier"] == "Zorblax" and "not in our records" in unresolved[0]["reason"]


def test_from_supplier_from_single_approved_source():
    resolved, notes = {"part": "BR-220", "to_supplier": "SUP-C"}, []
    parse.fill_from_records(R, resolved, notes, as_of="2026-11-14")
    assert resolved["from_supplier"] == "SUP-B" and notes[0]["note"] == "from records"


def test_from_supplier_not_filled_when_named_or_ambiguous():
    resolved, notes = {"part": "BR-220", "from_supplier": "SUP-X"}, []
    parse.fill_from_records(R, resolved, notes, as_of="2026-11-14")
    assert resolved["from_supplier"] == "SUP-X" and not notes
    resolved = {"part": "HS-410"}  # two approved sources
    parse.fill_from_records(R, resolved, notes, as_of="2026-11-14")
    assert "from_supplier" not in resolved
