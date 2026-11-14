"""Meeting remark -> ChangeRequest.

  python -m core.parse "Bormida is late, let's take the BR-220 blanks from Chisone, same alloy"

The model only reads: one structured-output call returns the change type and the names as they are written in
the remark (surface strings). Code then maps every name to a registry id, deterministically:

  1. the exact id ("SUP-C"), case-insensitive;
  2. one registry id written as a whole word inside the name ("BR-220 blanks" -> BR-220);
  3. the registry name or a confirmed alias (registry key `aliases`, fix/5), equal to the name;
  4. a confirmed alias written as a whole word inside the name;
  5. every word of the name appears as a whole word in one registry name ("Chisone" -> Meccanica Chisone S.r.l.).

A stage that finds exactly one id resolves the name. A stage that finds two or more stops: the name is ambiguous.
A name that resolves to nothing, is ambiguous, or is not written in the remark goes to `unresolved` with the
reason and the candidates. Nothing is guessed. The remark is kept verbatim in `utterance`.

parse_form(dict) is the typed-form path for the UI fallback: the same validation and resolution, no model.

Model access: Vercel AI Gateway (OpenAI-compatible), key in env AI_GATEWAY_API_KEY, server side only. Every model
answer is cached as a fixture in tests/fixtures/parse/, keyed by a hash of model, prompts and schema. Without the
key, parse() answers from fixtures and raises FixtureMissing for a remark it has not seen.

Written 14 Nov 2026 (workstream P). New code; the whole-word alias match follows fix/5 (core/aliases.py).
"""
import datetime
import json
import os
import re
import sys

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CORE_DIR)
sys.path.insert(0, CORE_DIR)

import llm  # noqa: E402
from contracts import CHANGE_TYPES, ChangeRequest  # noqa: E402
from llm import FixtureMissing, load_dotenv  # noqa: E402,F401  (re-exported for callers and tests)

REGISTRIES_PATH = os.path.join(ROOT, "data", "registries.json")
FIXTURES_DIR = os.path.join(ROOT, "tests", "fixtures", "parse")
PARSE_MODEL = "anthropic/claude-haiku-5.5"

# ChangeRequest field -> registry table its id comes from.
FIELD_TABLES = {
    "part": "parts",
    "to_supplier": "suppliers",
    "from_supplier": "suppliers",
    "site": "sites",
    "new_material": "materials",
    "new_coating": "coatings",
}
FORM_FIELDS = set(FIELD_TABLES) | {"type", "scope", "as_of", "utterance", "speaker"}
SCOPES = ("series", "service")
# Words that never identify an entity on their own (legal forms, articles).
NOISE_WORDS = {"the", "a", "an", "our", "s", "r", "l", "p", "srl", "spa", "ab", "ltd", "gmbh"}

CHANGE_TYPE_GUIDE = {
    "SourceChange": "another supplier company makes or delivers the part, a supplier is added (second source), or "
                    "a supplier delivers the part to another of our plants",
    "SubTierSupplierChange": "our supplier changes ITS own supplier of a material, part or service",
    "LocationChange": "the same company moves production of the part to another of its plants",
    "ShippingLocationChange": "the same supplier ships the part from another of its own places (ship-from point)",
    "MaterialChange": "the part is made from another material or alloy",
    "CoatingChange": "another coating, plating or surface treatment on the part",
    "SpecialProcessChange": "a change to heat treatment, plating or welding process parameters",
    "ProcessChange": "a change to the manufacturing process or method (e.g. CNC program, line, sequence)",
    "EquipmentChange": "new or different production machines",
    "ToolingChange": "new or modified tools, dies, moulds or fixtures only",
    "TestMethodChange": "a change of test or inspection method",
    "SoftwareChange": "a change of process or product software",
    "DesignChange": "a change of drawing, design record or specification",
    "PackagingChange": "a change of packaging or labelling",
    "ProductionResumptionChange": "production restarts after a long stop (tooling inactive for 12 months or more)",
    "ScheduleChange": "a change of delivery date, slot or quantity only",
    "PriceChange": "a change of price only",
}

SYSTEM = (
    "You read one remark from a supplier-quality meeting at an automotive parts maker and fill a form. You do not "
    "judge whether the change is allowed. Copy names exactly as they are written in the remark (surface strings): "
    "never translate a name into an id you have not seen in the remark, never add words that are not in it. "
    "Leave a field null when the remark does not say it."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": list(CHANGE_TYPES)},
        "part": {"type": ["string", "null"], "description": "part number or part name as written"},
        "to_supplier": {"type": ["string", "null"],
                        "description": "a supplier company that will newly make, deliver or do the work; null "
                                       "when the remark names only the supplier that already does it"},
        "from_supplier": {"type": ["string", "null"],
                          "description": "the supplier company that does it now, only if the remark names it "
                                         "(a company, never a plant)"},
        "site": {"type": ["string", "null"], "description": "our receiving plant, only if the remark names it"},
        "new_material": {"type": ["string", "null"],
                         "description": "the new material, only for a change of material"},
        "new_coating": {"type": ["string", "null"],
                        "description": "the new coating, only for a change of coating; the coating's name without "
                                       "opinions such as 'cheap' or 'new'"},
    },
    "required": ["type", "part", "to_supplier", "from_supplier", "site", "new_material", "new_coating"],
    "additionalProperties": False,
}


# ---- registries and resolution ---------------------------------------------------------------------------

def load_registries(path=REGISTRIES_PATH):
    with open(path) as file:
        return json.load(file)


def words(text):
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in NOISE_WORDS]


def whole_word_in(needle, haystack):
    """Case-insensitive whole-word match (fix/5 rule): the needle is written out in the haystack."""
    needle = needle.strip()
    if not needle:
        return False
    return re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", haystack, re.IGNORECASE) is not None


def table_entries(registries, table):
    """[(id, name, [aliases])] of one registry table."""
    registry = registries.get(table, {})
    aliases = registry.get("aliases", {})
    return [(row[0], row[1] if len(row) > 1 else "", aliases.get(row[0], [])) for row in registry.get("rows", [])]


def _one_stage(matches):
    """Return ('ok', id), ('ambiguous', ids) or None when the stage found nothing."""
    unique = sorted(set(matches))
    if len(unique) == 1:
        return "ok", unique[0]
    if len(unique) > 1:
        return "ambiguous", unique
    return None


def resolve(registries, table, text):
    """Map one surface string to an id of `table`. Return {"id": ..} or {"id": None, "reason", "candidates"}."""
    text = (text or "").strip()
    if not text:
        return {"id": None, "reason": "empty", "candidates": []}
    entries = table_entries(registries, table)
    lowered = " ".join(text.lower().split())
    text_words = set(words(text))
    stages = (
        [entity for entity, _, _ in entries if entity.lower() == lowered],
        [entity for entity, _, _ in entries if whole_word_in(entity, text)],
        [entity for entity, name, aliases in entries
         if lowered in {" ".join(n.lower().split()) for n in [name, *aliases] if n}],
        [entity for entity, _, aliases in entries if any(whole_word_in(alias, text) for alias in aliases)],
        [entity for entity, name, _ in entries if text_words and text_words <= set(words(name))],
    )
    for matches in stages:
        outcome = _one_stage(matches)
        if outcome is None:
            continue
        status, value = outcome
        if status == "ok":
            return {"id": value}
        return {"id": None, "reason": "ambiguous", "candidates": value}
    return {"id": None, "reason": f"not in {table}", "candidates": []}


# Fields where an unknown name is passed on to the rules (they ask "not in our supplier master / coating catalogue
# / material master"). Ambiguous names and names not written in the remark are never passed on.
UNKNOWN_NAME_FIELDS = ("to_supplier", "from_supplier", "new_material", "new_coating")


def resolve_fields(registries, surface, utterance=None):
    """Surface strings -> ({field: id}, [unresolved entries]). With an utterance, each name must be written in it."""
    resolved, unresolved = {}, []
    for field, table in FIELD_TABLES.items():
        text = surface.get(field)
        if text is None or not str(text).strip():
            continue
        text = str(text).strip()
        if utterance is not None and not whole_word_in(text, utterance):
            unresolved.append({"field": field, "text": text, "reason": "not written in the remark",
                               "candidates": []})
            continue
        outcome = resolve(registries, table, text)
        if outcome["id"] is not None:
            resolved[field] = outcome["id"]
        elif outcome["reason"].startswith("not in ") and field in UNKNOWN_NAME_FIELDS:
            # A name said in the meeting that is in none of our records is information, not noise: pass it to
            # the rules verbatim so they raise "not in our records" with an owner, instead of dropping it.
            resolved[field] = text
            unresolved.append({"field": field, "text": text, "reason": "not in our records: passed to the rules",
                               "candidates": []})
        else:
            unresolved.append({"field": field, "text": text, "reason": outcome["reason"],
                               "candidates": outcome["candidates"]})
    return resolved, unresolved


def build_request(change_type, resolved, unresolved, as_of=None, utterance=None, speaker=None, scope="series",
                  confidence=None):
    if change_type not in CHANGE_TYPES:
        unresolved = [*unresolved, {"field": "type", "text": str(change_type), "reason": "not a change type",
                                    "candidates": []}]
        change_type = None
    request = ChangeRequest(type=change_type, part=resolved.get("part"),
                            to_supplier=resolved.get("to_supplier"), from_supplier=resolved.get("from_supplier"),
                            site=resolved.get("site"), new_material=resolved.get("new_material"),
                            new_coating=resolved.get("new_coating"), scope=scope,
                            as_of=as_of or datetime.date.today().isoformat(), utterance=utterance,
                            speaker=speaker, parse_confidence=confidence, unresolved=unresolved)
    return request.to_dict()


# ---- model call ------------------------------------------------------------------------------------------

def prompt_for(remark):
    guide = "\n".join(f"- {name}: {meaning}" for name, meaning in CHANGE_TYPE_GUIDE.items())
    return (f"Change types (pick the one that fits the change being proposed):\n{guide}\n\n"
            f"Remark:\n<<<\n{remark}\n>>>")


def call_model(remark, live=False, model=PARSE_MODEL, call=None):
    """Return (surface dict, meta). Fixture first unless live; a live answer is recorded as a fixture."""
    return llm.cached_call(model, SYSTEM, prompt_for(remark), SCHEMA, FIXTURES_DIR, live=live, call=call,
                           note=remark)


# ---- public API ------------------------------------------------------------------------------------------

def parse(remark, as_of=None, speaker=None, registries=None, live=False, call=None):
    """Meeting remark -> ChangeRequest dict. Names the registries do not confirm go to `unresolved`."""
    registries = registries or load_registries()
    surface, _ = call_model(remark, live=live, call=call)
    resolved, unresolved = resolve_fields(registries, surface, utterance=remark)
    named = sum(1 for field in FIELD_TABLES if surface.get(field))
    passed_on = sum(1 for item in unresolved if item["reason"] == "not in our records: passed to the rules")
    confidence = round((len(resolved) - passed_on) / named, 2) if named else 0.0
    if surface.get("type") not in CHANGE_TYPES:
        confidence = 0.0
    return build_request(surface.get("type"), resolved, unresolved, as_of=as_of, utterance=remark,
                         speaker=speaker, confidence=confidence)


def parse_form(form, registries=None):
    """Typed form (ids or registry names) -> ChangeRequest dict. Raises ValueError on a bad key, type or scope."""
    registries = registries or load_registries()
    unknown = set(form) - FORM_FIELDS
    if unknown:
        raise ValueError(f"unknown form fields: {sorted(unknown)}")
    if form.get("type") not in CHANGE_TYPES:
        raise ValueError(f"type must be one of CHANGE_TYPES, got {form.get('type')!r}")
    if not form.get("part"):
        raise ValueError("part is required")
    scope = form.get("scope") or "series"
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}, got {scope!r}")
    if form.get("as_of"):
        datetime.date.fromisoformat(form["as_of"])
    resolved, unresolved = resolve_fields(registries, form)
    return build_request(form["type"], resolved, unresolved, as_of=form.get("as_of"),
                         utterance=form.get("utterance"), speaker=form.get("speaker"), scope=scope)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Parse a meeting remark into a ChangeRequest.")
    parser.add_argument("remark")
    parser.add_argument("--as-of")
    parser.add_argument("--live", action="store_true", help="call the model even if a fixture exists")
    args = parser.parse_args()
    print(json.dumps(parse(args.remark, as_of=args.as_of, live=args.live), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
