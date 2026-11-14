"""Meeting mode (issue #32): one transcript line -> is it a change proposal? -> card.

    python -m core.meeting "Let's take the BR-220 blanks from Chisone, same alloy."
    python -m core.meeting --demo            # every line of data/meetings/demo_meeting.jsonl

Two stages, so most lines cost nothing:

  1. prefilter(line), plain code: a line passes only when it names something the company tracks (a part id, a
     supplier, a material, a coating, a site, a process word) AND has a change verb ("switch", "move", "take ...
     from", "instead of" ...). Greetings, short lines and status talk stop here, no model call.
  2. one cheap structured-output call (anthropic/claude-haiku-5.5 through core/llm.py, cached as a fixture in
     tests/fixtures/meeting/ like the parser): {is_change_proposal, reason}. Reported past changes, hypotheticals
     and questions about status are not proposals.

Only a line the model flagged goes on to core.parse.parse -> core.check.evaluate (the server does that step, see
web/server.py /api/meeting/line). A line the model did not flag never gets a card; a line whose call failed is
reported as not classified, never guessed.

mentions(line) lists the registry ids a line names (parts, suppliers, materials, coatings, sites). The page uses
it to re-check an open card when a later line names the same supplier or part on a later date (e.g. "We
re-audited Chisone last week" on 14 Nov re-checks the 5 Nov card as of 14 Nov).

Written 14 Nov 2026 (issue #32).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import llm  # noqa: E402
from core.parse import load_registries, whole_word_in  # noqa: E402

FIXTURES_DIR = os.path.join(ROOT, "tests", "fixtures", "meeting")
DEMO_PATH = os.path.join(ROOT, "data", "meetings", "demo_meeting.jsonl")
CLASSIFY_MODEL = "anthropic/claude-haiku-5.5"
MIN_WORDS = 5

GREETING = re.compile(r"^\s*(hi|hello|good (morning|afternoon|evening)|morning|thanks|thank you|ok|okay|right|"
                      r"great|sure|yes|no|bye|see you|welcome|let's start|shall we start)\b", re.IGNORECASE)
# Words that, on their own, name something a change can be about (besides registry ids and names).
TOPIC_WORDS = (
    "supplier", "source", "alloy", "material", "steel", "aluminium", "aluminum", "coating", "anodising", "anodizing",
    "plating", "passivation", "chromate", "conversion", "zinc", "nickel", "paint", "heat treatment", "ageing", "aging",
    "inspection", "cmm", "gauge", "test", "machine", "line", "press", "tool", "tooling", "die", "mould", "mold",
    "fixture", "packaging", "label", "drawing", "software", "program", "plant", "site", "process", "blanks", "billet",
)
CHANGE_VERBS = re.compile(
    r"\b(switch\w*|mov(e|es|ed|ing)|tak(e|es|ing) .{0,40}\bfrom|us(e|ing) .{0,40}\binstead|instead of|chang(e|es|ing)|"
    r"replac\w*|swap\w*|transfer\w*|relocat\w*|outsourc\w*|re-?sourc\w*|second source|dual source|shift\w*|"
    r"adopt\w*|introduc\w*|go with|buy .{0,30}\bfrom|order .{0,30}\bfrom|bring .{0,30}\bin-house|drop\w*|"
    r"qualify .{0,30}\bfor|add\w* .{0,30}\bas (a )?(second|new) (source|supplier))\b",
    re.IGNORECASE)
# Generic words of supplier names that do not identify one supplier.
GENERIC_NAME_WORDS = {"alluminio", "meccanica", "fonderia", "galvanica", "plastiche", "minuterie", "trattamenti",
                      "termici", "billette", "omogeneizzazione", "s.r.l.", "s.p.a.", "srl", "spa"}
MENTION_TABLES = ("parts", "suppliers", "materials", "coatings", "sites")

SYSTEM = (
    "You listen to a supplier-quality meeting at an automotive parts maker. For ONE line of the transcript, decide "
    "whether the speaker proposes a change to how a part is made, sourced, coated, inspected, packed or where it "
    "is made, so that the change still has to be decided. A proposal is a suggestion, request or question that "
    "puts a concrete change on the table now (\"let's take BR-220 from Chisone\", \"can we switch the coating\"). "
    "NOT a proposal: status updates, reports of facts or audits, changes that already happened, hypotheticals "
    "that are explicitly put off, small talk. Give a one-sentence reason."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "is_change_proposal": {"type": "boolean"},
        "reason": {"type": "string", "description": "one short sentence"},
    },
    "required": ["is_change_proposal", "reason"],
    "additionalProperties": False,
}

_name_index = None


def name_index(registries=None):
    """[(id, [whole-word needles])] for the tables a line can mention: the id and distinctive name words."""
    global _name_index
    if _name_index is not None and registries is None:
        return _name_index
    registries = registries or load_registries()
    index = []
    for table in MENTION_TABLES:
        registry = registries.get(table, {})
        aliases = registry.get("aliases", {})
        for row in registry.get("rows", []):
            entity, name = row[0], (row[1] if len(row) > 1 else "")
            needles = [entity, *aliases.get(entity, [])]
            if table == "suppliers":
                needles += [word for word in name.split() if word.lower() not in GENERIC_NAME_WORDS and len(word) > 3]
            if table == "sites":
                needles += [name.split()[0]]  # "Beinasco plant ..." -> Beinasco
            index.append((entity, needles))
    _name_index = index
    return index


def mentions(line, registries=None):
    """Registry ids (parts, suppliers, materials, coatings, sites) the line names, in registry order."""
    return [entity for entity, needles in name_index(registries) if any(whole_word_in(n, line) for n in needles)]


def prefilter(line, registries=None):
    """Plain code, no model. Returns {"passed": bool, "reason": str, "mentions": [ids]}."""
    text = " ".join(str(line or "").split())
    found = mentions(text, registries) if text else []
    if len(text.split()) < MIN_WORDS:
        return {"passed": False, "reason": "short line", "mentions": found}
    if GREETING.match(text) and not found:
        return {"passed": False, "reason": "greeting or acknowledgement", "mentions": found}
    lowered = text.lower()
    topic = bool(found) or any(whole_word_in(word, lowered) for word in TOPIC_WORDS)
    if not topic:
        return {"passed": False, "reason": "names no part, supplier, material, coating, site or process",
                "mentions": found}
    if not CHANGE_VERBS.search(text):
        return {"passed": False, "reason": "no change verb", "mentions": found}
    return {"passed": True, "reason": "names a tracked item and a change verb", "mentions": found}


def call_model(line, live=False, call=None):
    prompt = f"Transcript line:\n<<<\n{line}\n>>>"
    return llm.cached_call(CLASSIFY_MODEL, SYSTEM, prompt, SCHEMA, FIXTURES_DIR, live=live, call=call, note=line,
                           max_tokens=200)


def classify(line, live=False, call=None, registries=None):
    """One line -> {is_change_proposal, reason, stage, mentions, model?}.

    stage "prefilter": stopped by code, no model call. stage "model": the model answered (meta in "model").
    Raises llm.FixtureMissing (or the gateway's error) when the model is needed and cannot answer: the caller
    reports the line as not classified; nothing is guessed.
    """
    gate = prefilter(line, registries)
    result = {"is_change_proposal": False, "reason": gate["reason"], "stage": "prefilter",
              "mentions": gate["mentions"]}
    if not gate["passed"]:
        return result
    output, meta = call_model(" ".join(str(line).split()), live=live, call=call)
    result.update({"is_change_proposal": bool(output.get("is_change_proposal")),
                   "reason": str(output.get("reason") or ""), "stage": "model",
                   "model": {"source": meta["source"], "key": meta["key"], "usage": meta.get("usage") or {}}})
    return result


def load_demo(path=DEMO_PATH):
    """The demo transcript: one JSON object per line {speaker, text, as_of, session?, expect?}."""
    with open(path, encoding="utf-8") as handle:
        return [json.loads(row) for row in handle if row.strip()]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Classify meeting lines as change proposals.")
    parser.add_argument("line", nargs="?")
    parser.add_argument("--demo", action="store_true", help="classify every line of the demo transcript")
    parser.add_argument("--live", action="store_true", help="call the model even if a fixture exists")
    args = parser.parse_args()
    lines = [item["text"] for item in load_demo()] if args.demo else [args.line]
    for line in lines:
        result = classify(line, live=args.live)
        flag = "FLAG" if result["is_change_proposal"] else "pass"
        print(f"{flag:4} [{result['stage']:9}] {line}\n      {result['reason']} {result['mentions']}")


if __name__ == "__main__":
    main()
