"""Extract facts from a document with a model, then check every fact before it may enter the fact log.

  python core/extract.py data_long/docs/CSR-AUR-R4.md [--accept]

1. Split the document into overlapping chunks.
2. Ask the model for facts (s, p, o, quote), using only ontology predicates and ids from a glossary.
3. Check each fact: the quote is literally in the document (whitespace may differ, the stored quote is the
   document's own text), the predicate exists in lcc.ttl and is not an inferred one, and every id is known.
   Facts that fail go to a review list with the reason, never into the log.
4. Write accepted facts as *proposed* (proposed_by="extractor"). They count only after a person accepts them.
   --accept auto-accepts them; that is for the benchmark only.
"""
import argparse
import json
import os
import re
import sys
import time

import yaml
from rdflib import OWL, RDF, RDFS, Graph

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CORE_DIR)
sys.path.insert(0, CORE_DIR)
sys.path.insert(0, os.path.join(ROOT, "bench"))
sys.path.insert(0, os.path.join(ROOT, "data"))

from project import LCC, ONTOLOGY_PATH  # noqa: E402

CHUNK_CHARS = 20000
OVERLAP_CHARS = 2000
# Vocabulary size offered to the model: 1 = the original 6 change types, 2 = 11, 3 = 17 (lcc:vocabLevel in
# ontology/lcc.ttl). Set with CHANGE_VOCAB=1|2|3; the default is the size chosen in bench/results/FIX_2.md.
VOCAB_LEVEL = int(os.environ.get("CHANGE_VOCAB", "1"))
LEVEL2_PREDICATES = {"requiresNoticeFor", "leadTimeDays"}
# CHANGE_NOTICE=0 withholds the two notice predicates at any level (diagnostic: types without them).
NOTICE_PREDICATES = os.environ.get("CHANGE_NOTICE", "1") != "0"
STATUS_VALUES = {"open", "closed", "valid", "expired", "rejected", "approved", "conditional", "revoked"}
# Derived by the reasoner. An extractor must never assert them.
INFERRED_PREDICATES = {"subjectTo", "subjectToLaw", "deliveredTo", "madeOfAlloy", "madeOfSeries",
                       "containsSubstanceVia", "hasIssue", "hasLaw", "supersededBy", "feedsInto"}
DOCUMENT_PREDICATES = {
    "requiresCustomerApprovalFor": "requirement -> change type that needs written customer approval (PPAP)",
    "requiresNotificationFor": "requirement -> change type that needs only a notification to the customer",
    "requiresNoticeFor": "requirement -> change type that must be announced to the customer before it is made "
                         "(advance notice; may come on top of an approval)",
    "leadTimeDays": "requirement -> literal: days of advance notice, one quoted integer such as \"180\"; only "
                    "when the notice clause gives a single number",
    "hasConsequence": "customer requirement -> consequence its own text names for shipping a change without "
                      "the required approval or notification: NewBusinessHold (new business hold), "
                      "RegistrarNotification (customer informs the IATF registrar or certification body), "
                      "Chargeback (chargebacks, costs or financial consequences), ControlledShipping (controlled "
                      "shipping or containment imposed on the supplier). Only when the quote states it",
    "appliesInMarket": "law -> market where it applies",
    "restricts": "law -> substance it bans or restricts",
    "concernsSupplier": "issue, NCR or deviation -> supplier",
    "concernsMaterial": "issue, NCR or deviation -> material or alloy",
    "concernsPart": "issue, NCR or deviation -> part",
    "concernsCoating": "issue -> coating",
    "permitsChangeType": "deviation -> change type it permits",
    "permitsCoating": "deviation -> coating it permits",
    "requiresCustomerApprovalForSubTier": "requirement -> change type that needs customer approval when a "
                                          "SUB-TIER supplier (tier 2, 3, ...) of the supplier makes it",
    "requiresNotificationForSubTier": "requirement -> change type that needs only a notification when a "
                                      "SUB-TIER supplier makes it",
    "suppliesTo": "supplier -> the supplier it delivers to, one tier up. Subject is the LOWER tier, object the "
                  "HIGHER tier (a Tier 3 supplier suppliesTo the Tier 2 supplier). Only when the text says or "
                  "clearly states who delivers to whom; one fact per link",
    "status": "issue or deviation -> literal status: open, closed, valid, expired, rejected",
}

SYSTEM = ("You extract facts from one company document into a fixed ontology. Output only facts that this "
          "document states as currently in force for its own record. Copy each quote character for character "
          "from the text: the shortest span that states the fact. When that span is a list item, table row or "
          "heading fragment that does not itself say what is required (for example \"Change in sub-supplier\"), "
          "also give context_quote: the sentence or heading above it that states the obligation (for example "
          "\"The following changes require Adient approval:\"), copied character for character, at most 400 "
          "characters, and no more than 1500 characters before the quote. Leave context_quote out when the "
          "quote already states the fact on its own.")
CONTEXT_MAX_GAP = 1500  # context_quote must end at most this many characters before quote starts
FACTS_SCHEMA = {
    "type": "object",
    "properties": {"facts": {"type": "array", "items": {
        "type": "object",
        "properties": {"s": {"type": "string"}, "p": {"type": "string"}, "o": {"type": "string"},
                       "quote": {"type": "string"},
                       "context_quote": {"type": "string"}},
        "required": ["s", "p", "o", "quote"]}}},
    "required": ["facts"],
}
FACTS_SCHEMA["properties"]["unclassified"] = {"type": "array", "items": {
    "type": "object",
    "properties": {"quote": {"type": "string"}, "summary": {"type": "string"}},
    "required": ["quote", "summary"]}}

CATCH_ALL = ("Catch-all: if the text states an obligation or rule of the supplier towards the customer about "
             "changes, notice, approval or conditions that fits NO change type and NO predicate above (for "
             "example a change of location or design, a lead time, a price), do not force it into a fact. List "
             "it under unclassified with a verbatim quote of the sentence that states it and a one-line summary "
             "of the obligation. Return an empty unclassified list if there is none.")


def ontology_predicates(level=None):
    level = VOCAB_LEVEL if level is None else level
    graph = Graph()
    graph.parse(ONTOLOGY_PATH, format="turtle")
    names = set()
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for subject in graph.subjects(RDF.type, kind):
            text = str(subject)
            if text.startswith(str(LCC)):
                names.add(text[len(str(LCC)):])
    if level < 2 or not NOTICE_PREDICATES:
        names -= LEVEL2_PREDICATES
    return names


def change_types(level=None):
    """Change types offered at a vocabulary level: {name: label}, ordered by level."""
    level = VOCAB_LEVEL if level is None else level
    graph = Graph()
    graph.parse(ONTOLOGY_PATH, format="turtle")
    found = []
    for subject in graph.subjects(RDF.type, LCC.ChangeType):
        minimum = int(graph.value(subject, LCC.vocabLevel))
        if minimum <= level:
            found.append((minimum, str(subject)[len(str(LCC)):], str(graph.value(subject, RDFS.label))))
    return {name: label for _, name, label in sorted(found)}


def known_ids(registries, document_ids, level=None):
    ids = set(document_ids)
    for registry in registries.values():
        for row in registry["rows"]:
            ids.add(row[0])
    ids |= set(change_types(level))
    ids |= {"NewBusinessHold", "RegistrarNotification", "Chargeback", "ControlledShipping"}
    ids |= {"CrVI", "CrIII", "Lead", "Cadmium", "Mercury", "Zinc", "Nickel"}
    return ids


def glossary(registries, level=None):
    level = VOCAB_LEVEL if level is None else level
    lines = ["Ids you may use (anything else is unknown):"]
    for name in ("customers", "markets", "parts", "suppliers", "materials", "coatings"):
        entries = "; ".join(f"{row[0]} = {row[1]}" for row in registries[name]["rows"])
        lines.append(f"{name}: {entries}")
    lines.append("Use ALY-* for an alloy named without temper (e.g. EN AW-6082), MAT-* for a named temper.")
    lines.append("substances: CrVI = hexavalent chromium; CrIII = trivalent chromium; Lead; Cadmium; Mercury; "
                 "Zinc; Nickel")
    types = change_types(level)
    if level < 2:
        lines.append("change types: " + "; ".join(types))
    else:
        lines.append("change types (use the most specific one that fits):")
        for name, label in types.items():
            lines.append(f"  {name} = {label}")
    lines.append("consequence types: NewBusinessHold; RegistrarNotification; Chargeback; ControlledShipping")
    lines.append("predicates:")
    for predicate, meaning in DOCUMENT_PREDICATES.items():
        if (level < 2 or not NOTICE_PREDICATES) and predicate in LEVEL2_PREDICATES:
            continue
        lines.append(f"  {predicate}: {meaning}")
    return "\n".join(lines)


def read_document(path):
    with open(path) as file:
        raw = file.read()
    _, header_text, body = raw.split("---\n", 2)
    return yaml.safe_load(header_text), body


def chunks(text, size=CHUNK_CHARS, overlap=OVERLAP_CHARS):
    """Paragraph-aligned chunks; each one starts `overlap` characters before the previous one ended."""
    pieces = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind("\n\n", start + size // 2, end)
            if boundary > 0:
                end = boundary
        pieces.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return pieces


def find_quote(document_text, quote):
    """Return the document's own text for `quote` if it is there (whitespace may differ), else None."""
    words = quote.split()
    if not words:
        return None
    pattern = r"\s+".join(re.escape(word) for word in words)
    match = re.search(pattern, document_text)
    return match.group(0) if match else None


def find_spans(text, quote):
    """All (start, end) spans of `quote` in `text` (whitespace may differ)."""
    words = quote.split()
    if not words:
        return []
    pattern = r"\s+".join(re.escape(word) for word in words)
    return [match.span() for match in re.finditer(pattern, text)]


def find_context(scope, context_quote, quote):
    """Return (context_text, quote_text) if both are verbatim in `scope`, the context starts before the quote, and
    the quote starts at most CONTEXT_MAX_GAP characters after the context ends (a context that runs into the quote,
    as in "...after any of: a change of source", is fine); else None. The verbatim checks are never relaxed."""
    for c_start, c_end in find_spans(scope, context_quote):
        for q_start, q_end in find_spans(scope, quote):
            if c_start < q_start and q_start - c_end <= CONTEXT_MAX_GAP:
                return scope[c_start:c_end], scope[q_start:q_end]
    return None


def normalise_object(predicate, obj):
    if predicate == "status":
        value = obj.strip().strip('"').lower()
        return json.dumps(value)
    if predicate == "leadTimeDays":
        return json.dumps(obj.strip().strip('"'))
    return obj.strip()


def grounding_names(registries):
    """Part and supplier id -> words that must appear in a quote that names it (its id, or the supplier's name)."""
    names = {}
    for row in registries["parts"]["rows"]:
        names[row[0]] = [row[0]]
    for row in registries["suppliers"]["rows"]:
        names[row[0]] = [row[0], " ".join(row[1].split()[:2])]
    return names


def grounding_aliases(registries):
    """Entity id -> strings a person confirmed as the way documents write that entity (registry key `aliases`)."""
    aliases = {}
    for registry in registries.values():
        for entity, strings in registry.get("aliases", {}).items():
            aliases.setdefault(entity, []).extend(strings)
    return aliases


def has_alias(alias, quote):
    """Case-insensitive, whole-word match. No fuzzy matching: the alias must be written out in the quote."""
    return re.search(r"(?<!\w)" + re.escape(alias.strip()) + r"(?!\w)", quote, re.IGNORECASE) is not None


def grounded(entity, quote, names, aliases=None):
    if entity not in names:
        return True
    lowered = quote.lower()
    if any(name.lower() in lowered for name in names[entity]):
        return True
    return any(alias.strip() and has_alias(alias, quote) for alias in (aliases or {}).get(entity, []))


TWO_ENDED_PREDICATES = {"suppliesTo"}  # both ends are suppliers: the quote must name both


def check_fact(fact, document_text, predicates, ids, names=None, aliases=None, scope=None):
    """Return (fact_with_document_quote, None) or (fact, reason). `scope` is the chunk the model saw."""
    quote = find_quote(document_text, fact["quote"])
    if quote is None:
        return fact, "quote not found in document"
    checked = {**fact, "quote": quote}
    context = (fact.get("context_quote") or "").strip()
    if context:
        checked["context_quote"] = context
        if find_quote(document_text, context) is None:
            return checked, "context quote not found in document"
        pair = find_context(scope if scope is not None else document_text, context, fact["quote"])
        if pair is None:
            return checked, "context quote not before quote within 1500 characters in the same chunk"
        checked["context_quote"], checked["quote"] = pair
    else:
        checked.pop("context_quote", None)
    if fact["p"] not in predicates or fact["p"] in INFERRED_PREDICATES:
        return checked, f"predicate {fact['p']} not allowed"
    if fact["s"] not in ids:
        return checked, f"unknown subject {fact['s']}"
    if fact["p"] == "status":
        if json.loads(fact["o"]) not in STATUS_VALUES:
            return checked, f"unknown status {fact['o']}"
    elif fact["p"] == "leadTimeDays":
        text = fact["o"].strip('"')
        if not (text.isdigit() and 1 <= int(text) <= 730):
            return checked, f"bad lead time {fact['o']}"
    elif fact["o"] not in ids:
        return checked, f"unknown object {fact['o']}"
    if names and not grounded(fact["o"], quote, names, aliases):
        return checked, f"ungrounded: quote does not name {fact['o']}"
    if names and fact["p"] in TWO_ENDED_PREDICATES and not grounded(fact["s"], quote, names, aliases):
        return checked, f"ungrounded: quote does not name {fact['s']}"
    return checked, None


BLANKET_RULE = (" A blanket rule covers several change types at once: emit one fact per covered change type, each "
                "with the same verbatim quote. Example: \"The supplier shall obtain written consent before any "
                "change to its products or processes\" gives requiresCustomerApprovalFor for ProcessChange, "
                "MaterialChange, SourceChange, CoatingChange (all products and processes), each with that quote.")
PLAIN_INSTRUCTIONS = ("Rules: the subject is usually this document's id. Return an empty list if this part states "
                      "no such fact.")
GUARDED_INSTRUCTIONS = ("Rules: the subject is usually this document's id. Ignore revision histories and quotes of "
                        "earlier revisions, drafts, statements about other documents, divisions or companies, and "
                        "other reports listed for reference. A status line of one action inside the report is not "
                        "the report's status. Return an empty list if this part states no such fact.")


def extract_document(path, registries, document_ids, model="sonnet", call=None, guarded=True):
    """Return {"header", "accepted", "review", "tokens_in", "tokens_out", "seconds", "chunks"}."""
    if call is None:
        import llm
        call = llm.call
    header, body = read_document(path)
    predicates = ontology_predicates()
    ids = known_ids(registries, document_ids)
    names = grounding_names(registries)
    aliases = grounding_aliases(registries)
    context = (f"Document id: {header['id']} (type {header['type']})\nTitle: {header['title']}\n"
               f"Valid from {header['valid_from']} to {header['valid_to'] or 'open end'}\n"
               f"Replaces: {header['supersedes'] or 'nothing'}")
    instructions = (GUARDED_INSTRUCTIONS if guarded else PLAIN_INSTRUCTIONS) + BLANKET_RULE
    accepted, review, seen = [], [], set()
    unclassified, unclassified_rejected, seen_quotes = [], [], set()
    tokens_in = tokens_out = 0
    started = time.time()
    pieces = chunks(body)
    for index, piece in enumerate(pieces, start=1):
        prompt = (f"{glossary(registries)}\n\n{context}\n{instructions}\n{CATCH_ALL}\n\n"
                  f"Part {index} of {len(pieces)} of the document:\n<<<\n{piece}\n>>>")
        output, usage, _, _ = call(model, SYSTEM, prompt, FACTS_SCHEMA)
        tokens_in += usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) \
            + usage.get("cache_read_input_tokens", 0)
        tokens_out += usage.get("output_tokens", 0)
        for raw in output.get("facts", []):
            fact = {"s": raw["s"].strip(), "p": raw["p"].strip(), "o": normalise_object(raw["p"], raw["o"]),
                    "quote": raw["quote"]}
            if raw.get("context_quote"):
                fact["context_quote"] = raw["context_quote"]
            key = (fact["s"], fact["p"], fact["o"])
            if key in seen:
                continue
            seen.add(key)
            checked, reason = check_fact(fact, body, predicates, ids, names, aliases, scope=piece)
            if reason:
                review.append({**checked, "reason": reason})
            else:
                accepted.append(checked)
        for raw in output.get("unclassified", []):
            quote = find_quote(body, raw.get("quote", ""))  # the same quote check as for facts
            if quote is None:
                unclassified_rejected.append({**raw, "reason": "quote not found in document"})
            elif quote not in seen_quotes:
                seen_quotes.add(quote)
                unclassified.append({"quote": quote, "summary": raw.get("summary", "").strip()})
    return {"header": header, "accepted": accepted, "review": review, "unclassified": unclassified,
            "unclassified_rejected": unclassified_rejected, "tokens_in": tokens_in,
            "tokens_out": tokens_out, "seconds": time.time() - started, "chunks": len(pieces)}


def to_log_facts(result, kind_of_type):
    header = result["header"]
    facts = []
    for index, fact in enumerate(result["accepted"]):
        facts.append({"id": f"X-{header['id']}-{index:03d}", "s": fact["s"], "p": fact["p"], "o": fact["o"],
                      "source": header["id"], "quote": fact["quote"],
                      "context_quote": fact.get("context_quote"), "valid_from": header["valid_from"],
                      "valid_to": header["valid_to"], "kind": kind_of_type(header["type"]),
                      "author": header["author"]})
    return facts


def to_log_unclassified(result):
    header = result["header"]
    return [{"id": f"U-{header['id']}-{index:03d}", "source": header["id"], "quote": item["quote"],
             "summary": item["summary"]} for index, item in enumerate(result.get("unclassified", []))]


def document_kind(doc_type):
    return "constraint" if doc_type in ("customer_requirement", "law", "internal_procedure") else "evidence"


def main():
    from factlog import default_log
    from world import DOCUMENTS, REGISTRIES
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--accept", action="store_true", help="auto-accept (benchmark only)")
    args = parser.parse_args()
    result = extract_document(args.path, REGISTRIES, [item["id"] for item in DOCUMENTS])
    log = default_log()
    for fact in to_log_facts(result, document_kind):
        log.propose_fact(fact, proposed_by="extractor")
    for item in to_log_unclassified(result):
        log.propose_unclassified(item, proposed_by="extractor")
    if args.accept:
        log.accept_proposed(result["header"]["id"], reviewer="bench")
    for fact in result["accepted"]:
        print(f"OK     {fact['s']} {fact['p']} {fact['o']}  \"{fact['quote'][:70]}\"")
    for fact in result["review"]:
        print(f"REVIEW {fact['s']} {fact['p']} {fact['o']}  ({fact['reason']})")
    for item in result["unclassified"]:
        print(f"UNCLASSIFIED (never checked by the reasoner)  \"{item['quote'][:70]}\"  {item['summary']}")
    print(f"{result['chunks']} chunks, {result['tokens_in']} tokens in, {result['seconds']:.0f} s")


if __name__ == "__main__":
    main()
