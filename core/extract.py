"""Document -> proposed facts for the fact log. The model reads; code checks every fact before it is proposed.

  python core/extract.py tests/fixtures/docs/CSR-AUR-R4.md [--live] [--json]

1. Split the document into overlapping, paragraph-aligned chunks.
2. Ask the model for facts (s, p, o, quote, context_quote) using only the document predicates below and ids from a
   glossary built from the registries (the 17 change types of core/contracts.py), plus `unclassified` items: rules
   about changes that fit no predicate or change type (fix/1).
3. Check each fact, the checks of the prototype unchanged:
   - quote: verbatim in the document (whitespace may differ; the stored quote is the document's own text);
   - context_quote (fix/3, two-span quotes): verbatim too, starts before the quote, the quote starts at most
     1500 characters after it ends, both inside the chunk the model saw;
   - predicate: one of the document predicates (and in ontology/lcc.ttl when that file exists), never inferred;
   - ids: subject and object are known ids (registries, document ids, change types, substances);
   - grounding: a part or supplier object must be named in the quote by its id, its name, or an alias a person
     confirmed (registry key `aliases`; fix/5, case-insensitive whole word, no fuzzy match).
   A blanket rule ("any change to products or processes") gives one fact per covered change type, each with the
   same quote (fix/7). Unclassified items keep a verbatim quote, checked the same way (fix/1).
4. Output plain dicts. Facts that pass are PROPOSALS for the fact log (core/factlog.py, workstream F): they count
   only after a person accepts them. Facts that fail go to `review` with the reason, never to the log.

Ported from research/prototypes/core/extract.py (night-shift/2026-11-13-kva-plan) with fix/3-two-span-quotes,
fix/5-aliases, fix/7-blanket-rule and fix/1-catchall; change types from fix/2-change-types (level 3, 17 types).
"""
import argparse
import json
import os
import re
import sys
import time

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CORE_DIR)
sys.path.insert(0, CORE_DIR)

import llm  # noqa: E402
from contracts import CHANGE_TYPES  # noqa: E402

REGISTRIES_PATH = os.path.join(ROOT, "data", "registries.json")
ONTOLOGY_PATH = os.path.join(ROOT, "ontology", "lcc.ttl")
FIXTURES_DIR = os.path.join(ROOT, "tests", "fixtures", "extract")
EXTRACT_MODEL = os.environ.get("KVA_EXTRACT_MODEL", "anthropic/claude-haiku-5.5")

CHUNK_CHARS = 20000
OVERLAP_CHARS = 2000
CONTEXT_MAX_GAP = 1500  # context_quote must end at most this many characters before the quote starts
STATUS_VALUES = {"open", "closed", "valid", "expired", "rejected", "approved", "conditional", "revoked"}
SUBSTANCES = {"CrVI": "hexavalent chromium", "CrIII": "trivalent chromium", "Lead": "lead", "Cadmium": "cadmium",
              "Mercury": "mercury", "Zinc": "zinc", "Nickel": "nickel"}
# Derived by the reasoner. An extractor must never assert them.
INFERRED_PREDICATES = {"subjectTo", "subjectToLaw", "deliveredTo", "madeOfAlloy", "madeOfSeries",
                       "containsSubstanceVia", "hasIssue", "hasLaw", "supersededBy"}
LITERAL_PREDICATES = {"status", "leadTimeDays"}
DOCUMENT_PREDICATES = {
    "requiresCustomerApprovalFor": "requirement -> change type that needs written customer approval (PPAP)",
    "requiresNotificationFor": "requirement -> change type that needs only a notification to the customer",
    "requiresNoticeFor": "requirement -> change type that must be announced to the customer before it is made "
                         "(advance notice; may come on top of an approval)",
    "leadTimeDays": "requirement -> literal: days of advance notice, one quoted integer such as \"180\"; only "
                    "when the notice clause gives a single number",
    "appliesInMarket": "law -> market where it applies",
    "restricts": "law -> substance it bans or restricts",
    "concernsSupplier": "issue, NCR or deviation -> supplier",
    "concernsMaterial": "issue, NCR or deviation -> material or alloy",
    "concernsPart": "issue, NCR or deviation -> part",
    "concernsCoating": "issue -> coating",
    "permitsChangeType": "deviation -> change type it permits",
    "permitsCoating": "deviation -> coating it permits",
    "status": "issue or deviation -> literal status: open, closed, valid, expired, rejected",
}
# rdfs:label of the 17 change types (ontology/lcc.ttl of fix/2-change-types).
CHANGE_TYPE_LABELS = {
    "SourceChange": "Change of supplier (source)",
    "MaterialChange": "Change of material",
    "ProcessChange": "Change of manufacturing process",
    "CoatingChange": "Change of coating / surface treatment",
    "ScheduleChange": "Change of delivery date or quantity",
    "PackagingChange": "Change of packaging",
    "LocationChange": "Change of manufacturing site",
    "ToolingChange": "Change of tooling",
    "DesignChange": "Change of design or specification",
    "SubTierSupplierChange": "Change of sub-tier supplier",
    "TestMethodChange": "Change of test or inspection method",
    "ShippingLocationChange": "Change of shipping location",
    "EquipmentChange": "Change of production equipment",
    "SoftwareChange": "Change of process or product software",
    "ProductionResumptionChange": "Resumption after a long production stop",
    "PriceChange": "Change of price",
    "SpecialProcessChange": "Change of a special process (heat treat, plating, welding)",
}
assert set(CHANGE_TYPE_LABELS) == set(CHANGE_TYPES)

# Document type -> rank of its facts (docs/architecture.md: 1 law/customer, 2 controlled record, 3 informal).
RANK_1_TYPES = {"law", "customer_requirement", "contract", "standard"}
RANK_3_TYPES = {"email", "meeting", "meeting_note", "chat", "note", "call"}

SYSTEM = ("You extract facts from one company document into a fixed ontology. Output only facts that this "
          "document states as currently in force for its own record. Copy each quote character for character "
          "from the text: the shortest span that states the fact. When that span is a list item, table row or "
          "heading fragment that does not itself say what is required (for example \"Change in sub-supplier\"), "
          "also give context_quote: the sentence or heading above it that states the obligation (for example "
          "\"The following changes require Adient approval:\"), copied character for character, at most 400 "
          "characters, and no more than 1500 characters before the quote. Set context_quote to null when the "
          "quote already states the fact on its own.")
PLAIN_INSTRUCTIONS = ("Rules: the subject is usually this document's id. Return an empty list if this part states "
                      "no such fact.")
GUARDED_INSTRUCTIONS = ("Rules: the subject is usually this document's id. Ignore revision histories and quotes of "
                        "earlier revisions, drafts, statements about other documents, divisions or companies, and "
                        "other reports listed for reference. A status line of one action inside the report is not "
                        "the report's status. Return an empty list if this part states no such fact.")
BLANKET_RULE = (" A blanket rule covers several change types at once: emit one fact per covered change type, each "
                "with the same verbatim quote. Example: \"The supplier shall obtain written consent before any "
                "change to its products or processes\" gives requiresCustomerApprovalFor for every change type of "
                "a product or process, each with that quote.")
CATCH_ALL = ("Catch-all: if the text states an obligation or rule of the supplier towards the customer about "
             "changes, notice, approval or conditions that fits NO change type and NO predicate above, do not "
             "force it into a fact. List it under unclassified with a verbatim quote of the sentence that states "
             "it and a one-line summary of the obligation. Return an empty unclassified list if there is none.")
FACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {"type": "array", "items": {
            "type": "object",
            "properties": {"s": {"type": "string"}, "p": {"type": "string"}, "o": {"type": "string"},
                           "quote": {"type": "string"}, "context_quote": {"type": ["string", "null"]}},
            "required": ["s", "p", "o", "quote", "context_quote"],
            "additionalProperties": False}},
        "unclassified": {"type": "array", "items": {
            "type": "object",
            "properties": {"quote": {"type": "string"}, "summary": {"type": "string"}},
            "required": ["quote", "summary"],
            "additionalProperties": False}},
    },
    "required": ["facts", "unclassified"],
    "additionalProperties": False,
}


# ---- vocabulary ------------------------------------------------------------------------------------------

def load_registries(path=REGISTRIES_PATH):
    with open(path) as file:
        return json.load(file)


def ontology_predicates(path=ONTOLOGY_PATH):
    """Object and datatype properties of ontology/lcc.ttl, or None when the file is not there (yet)."""
    if not os.path.exists(path):
        return None
    from rdflib import OWL, RDF, Graph
    graph = Graph()
    graph.parse(path, format="turtle")
    names = set()
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for subject in graph.subjects(RDF.type, kind):
            text = str(subject)
            names.add(re.split(r"[#/]", text)[-1])
    return names


def allowed_predicates():
    predicates = set(DOCUMENT_PREDICATES)
    in_ontology = ontology_predicates()
    if in_ontology is not None:
        predicates &= in_ontology | LITERAL_PREDICATES
    return predicates - INFERRED_PREDICATES


def known_ids(registries, document_ids):
    ids = set(document_ids)
    for name, registry in registries.items():
        if name.startswith("_"):
            continue
        for row in registry.get("rows", []):
            ids.add(row[0])
    return ids | set(CHANGE_TYPES) | set(SUBSTANCES)


def glossary(registries):
    lines = ["Ids you may use (anything else is unknown):"]
    for name in ("customers", "markets", "parts", "suppliers", "materials", "coatings"):
        if name in registries:
            entries = "; ".join(f"{row[0]} = {row[1]}" for row in registries[name]["rows"])
            lines.append(f"{name}: {entries}")
    lines.append("Use ALY-* for an alloy named without temper (e.g. EN AW-6082), MAT-* for a named temper.")
    lines.append("substances: " + "; ".join(f"{key} = {value}" for key, value in SUBSTANCES.items()))
    lines.append("change types (use the most specific one that fits):")
    for name, label in CHANGE_TYPE_LABELS.items():
        lines.append(f"  {name} = {label}")
    lines.append("predicates:")
    for predicate, meaning in DOCUMENT_PREDICATES.items():
        lines.append(f"  {predicate}: {meaning}")
    return "\n".join(lines)


# ---- document text ---------------------------------------------------------------------------------------

def read_document(path):
    """Markdown with a YAML front matter header -> (header dict, body). Header keys other than the ones the
    extractor shows the model (id, type, title, valid_from, valid_to, supersedes, author) are ignored."""
    import yaml
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


def find_spans(text, quote):
    """All (start, end) spans of `quote` in `text` (whitespace may differ)."""
    words = quote.split()
    if not words:
        return []
    pattern = r"\s+".join(re.escape(word) for word in words)
    return [match.span() for match in re.finditer(pattern, text)]


def find_quote(document_text, quote):
    """Return the document's own text for `quote` if it is there (whitespace may differ), else None."""
    spans = find_spans(document_text, quote)
    return document_text[spans[0][0]:spans[0][1]] if spans else None


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
    if predicate in LITERAL_PREDICATES:
        value = obj.strip().strip('"')
        return json.dumps(value.lower() if predicate == "status" else value)
    return obj.strip()


# ---- grounding (fix/5) -----------------------------------------------------------------------------------

def grounding_names(registries):
    """Part and supplier id -> words that must appear in a quote that names it (its id, or the supplier's name)."""
    names = {}
    for row in registries.get("parts", {}).get("rows", []):
        names[row[0]] = [row[0]]
    for row in registries.get("suppliers", {}).get("rows", []):
        names[row[0]] = [row[0], " ".join(row[1].split()[:2])]
    return names


def grounding_aliases(registries):
    """Entity id -> strings a person confirmed as the way documents write that entity (registry key `aliases`)."""
    aliases = {}
    for name, registry in registries.items():
        if name.startswith("_"):
            continue
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


# ---- checks ----------------------------------------------------------------------------------------------

def check_fact(fact, document_text, predicates, ids, names=None, scope=None, aliases=None):
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
        if not json.loads(fact["o"]).isdigit():
            return checked, f"lead time is not a whole number of days: {fact['o']}"
    elif fact["o"] not in ids:
        return checked, f"unknown object {fact['o']}"
    if names and not grounded(fact["o"], quote, names, aliases):
        return checked, f"ungrounded: quote does not name {fact['o']}"
    return checked, None


def check_unclassified(item, document_text):
    """Return (item_with_document_quote, None) or (item, reason). The same verbatim check as for facts."""
    quote = find_quote(document_text, item.get("quote", ""))
    if quote is None:
        return item, "quote not found in document"
    return {"quote": quote, "summary": (item.get("summary") or "").strip()}, None


# ---- extraction ------------------------------------------------------------------------------------------

def document_context(header):
    return (f"Document id: {header['id']} (type {header.get('type')})\nTitle: {header.get('title', '')}\n"
            f"Valid from {header.get('valid_from')} to {header.get('valid_to') or 'open end'}\n"
            f"Replaces: {header.get('supersedes') or 'nothing'}")


def extract_text(header, body, registries=None, document_ids=(), model=EXTRACT_MODEL, live=False, call=None,
                 guarded=True):
    """Extract from one document already in text form. Return
    {"header", "accepted", "review", "unclassified", "unclassified_rejected", "tokens_in", "tokens_out",
     "seconds", "chunks", "answers_from"}."""
    registries = registries or load_registries()
    predicates = allowed_predicates()
    ids = known_ids(registries, [header["id"], *document_ids])
    names = grounding_names(registries)
    aliases = grounding_aliases(registries)
    instructions = (GUARDED_INSTRUCTIONS if guarded else PLAIN_INSTRUCTIONS) + BLANKET_RULE
    accepted, review, seen = [], [], set()
    unclassified, unclassified_rejected, seen_quotes = [], [], set()
    tokens_in = tokens_out = 0
    sources = set()
    started = time.time()
    pieces = chunks(body)
    for index, piece in enumerate(pieces, start=1):
        prompt = (f"{glossary(registries)}\n\n{document_context(header)}\n{instructions}\n{CATCH_ALL}\n\n"
                  f"Part {index} of {len(pieces)} of the document:\n<<<\n{piece}\n>>>")
        output, meta = llm.cached_call(model, SYSTEM, prompt, FACTS_SCHEMA, FIXTURES_DIR, live=live, call=call,
                                       note=f"{header['id']} part {index}/{len(pieces)}", max_tokens=8000)
        sources.add(f"{meta['source']}: {meta['recorded_by']}")
        usage = meta.get("usage") or {}
        tokens_in += usage.get("prompt_tokens", 0)
        tokens_out += usage.get("completion_tokens", 0)
        for raw in output.get("facts", []):
            fact = {"s": raw["s"].strip(), "p": raw["p"].strip(), "o": normalise_object(raw["p"], raw["o"]),
                    "quote": raw["quote"]}
            if raw.get("context_quote"):
                fact["context_quote"] = raw["context_quote"]
            key = (fact["s"], fact["p"], fact["o"])
            if key in seen:
                continue
            seen.add(key)
            checked, reason = check_fact(fact, body, predicates, ids, names, scope=piece, aliases=aliases)
            if reason:
                review.append({**checked, "reason": reason})
            else:
                accepted.append(checked)
        for raw in output.get("unclassified", []):
            item, reason = check_unclassified(raw, body)
            if reason:
                unclassified_rejected.append({**raw, "reason": reason})
            elif item["quote"] not in seen_quotes:
                seen_quotes.add(item["quote"])
                unclassified.append(item)
    return {"header": header, "accepted": accepted, "review": review, "unclassified": unclassified,
            "unclassified_rejected": unclassified_rejected, "tokens_in": tokens_in, "tokens_out": tokens_out,
            "seconds": round(time.time() - started, 2), "chunks": len(pieces), "answers_from": sorted(sources)}


def extract_document(path, registries=None, document_ids=(), **kwargs):
    header, body = read_document(path)
    return extract_text(header, body, registries=registries, document_ids=document_ids, **kwargs)


def document_rank(doc_type):
    if doc_type in RANK_1_TYPES:
        return 1
    if doc_type in RANK_3_TYPES:
        return 3
    return 2


def to_proposals(result):
    """Accepted facts and unclassified items as plain dicts for the fact log. All are proposals: a person accepts."""
    header = result["header"]
    common = {"source": header["id"], "rank": document_rank(header.get("type")),
              "valid_from": header.get("valid_from"), "valid_to": header.get("valid_to"),
              "author": header.get("author"), "proposed_by": "extractor", "status": "proposed"}
    proposals = []
    for index, fact in enumerate(result["accepted"]):
        proposals.append({"id": f"X-{header['id']}-{index:03d}", "s": fact["s"], "p": fact["p"], "o": fact["o"],
                          "quote": fact["quote"], "context_quote": fact.get("context_quote"), "kind": "assert",
                          **common})
    for index, item in enumerate(result.get("unclassified", [])):
        proposals.append({"id": f"U-{header['id']}-{index:03d}", "s": None, "p": None, "o": None,
                          "quote": item["quote"], "context_quote": None, "summary": item["summary"],
                          "kind": "unclassified", **common})
    return proposals


def main():
    parser = argparse.ArgumentParser(description="Extract proposed facts from one document.")
    parser.add_argument("path")
    parser.add_argument("--live", action="store_true", help="call the model even if a fixture exists")
    parser.add_argument("--json", action="store_true", help="print the proposals as JSON lines")
    args = parser.parse_args()
    result = extract_document(args.path, live=args.live)
    if args.json:
        for proposal in to_proposals(result):
            print(json.dumps(proposal, ensure_ascii=False, default=str))
        return
    for fact in result["accepted"]:
        context = f"  [under: \"{fact['context_quote'][:50]}\"]" if fact.get("context_quote") else ""
        print(f"OK     {fact['s']} {fact['p']} {fact['o']}  \"{fact['quote'][:70]}\"{context}")
    for fact in result["review"]:
        print(f"REVIEW {fact['s']} {fact['p']} {fact['o']}  ({fact['reason']})")
    for item in result["unclassified"]:
        print(f"UNCLASSIFIED (never checked by the reasoner)  \"{item['quote'][:70]}\"  {item['summary']}")
    print(f"{result['chunks']} chunks, {result['tokens_in']} tokens in, {result['seconds']:.1f} s, "
          f"answers from {result['answers_from']}")


if __name__ == "__main__":
    main()
