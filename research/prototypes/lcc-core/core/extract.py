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
from rdflib import OWL, RDF, Graph

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CORE_DIR)
sys.path.insert(0, CORE_DIR)
sys.path.insert(0, os.path.join(ROOT, "bench"))
sys.path.insert(0, os.path.join(ROOT, "data"))

from project import LCC, ONTOLOGY_PATH  # noqa: E402

CHUNK_CHARS = 20000
OVERLAP_CHARS = 2000
STATUS_VALUES = {"open", "closed", "valid", "expired", "rejected", "approved", "conditional", "revoked"}
# Derived by the reasoner. An extractor must never assert them.
INFERRED_PREDICATES = {"subjectTo", "subjectToLaw", "deliveredTo", "madeOfAlloy", "madeOfSeries",
                       "containsSubstanceVia", "hasIssue", "hasLaw", "supersededBy"}
DOCUMENT_PREDICATES = {
    "requiresCustomerApprovalFor": "requirement -> change type that needs written customer approval (PPAP)",
    "requiresNotificationFor": "requirement -> change type that needs only a notification to the customer",
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

SYSTEM = ("You extract facts from one company document into a fixed ontology. Output only facts that this "
          "document states as currently in force for its own record. Copy each quote character for character "
          "from the text: the shortest span that states the fact.")
FACTS_SCHEMA = {
    "type": "object",
    "properties": {"facts": {"type": "array", "items": {
        "type": "object",
        "properties": {"s": {"type": "string"}, "p": {"type": "string"}, "o": {"type": "string"},
                       "quote": {"type": "string"}},
        "required": ["s", "p", "o", "quote"]}}},
    "required": ["facts"],
}


def ontology_predicates():
    graph = Graph()
    graph.parse(ONTOLOGY_PATH, format="turtle")
    names = set()
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for subject in graph.subjects(RDF.type, kind):
            text = str(subject)
            if text.startswith(str(LCC)):
                names.add(text[len(str(LCC)):])
    return names


def known_ids(registries, document_ids):
    ids = set(document_ids)
    for registry in registries.values():
        for row in registry["rows"]:
            ids.add(row[0])
    ids |= {"SourceChange", "MaterialChange", "ProcessChange", "CoatingChange", "ScheduleChange",
            "PackagingChange", "CrVI", "CrIII", "Lead", "Cadmium", "Mercury", "Zinc", "Nickel"}
    return ids


def glossary(registries):
    lines = ["Ids you may use (anything else is unknown):"]
    for name in ("customers", "markets", "parts", "suppliers", "materials", "coatings"):
        entries = "; ".join(f"{row[0]} = {row[1]}" for row in registries[name]["rows"])
        lines.append(f"{name}: {entries}")
    lines.append("Use ALY-* for an alloy named without temper (e.g. EN AW-6082), MAT-* for a named temper.")
    lines.append("substances: CrVI = hexavalent chromium; CrIII = trivalent chromium; Lead; Cadmium; Mercury; "
                 "Zinc; Nickel")
    lines.append("change types: SourceChange; MaterialChange; ProcessChange; CoatingChange; ScheduleChange; "
                 "PackagingChange")
    lines.append("predicates:")
    for predicate, meaning in DOCUMENT_PREDICATES.items():
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


def normalise_object(predicate, obj):
    if predicate == "status":
        value = obj.strip().strip('"').lower()
        return json.dumps(value)
    return obj.strip()


def grounding_names(registries):
    """Part and supplier id -> words that must appear in a quote that names it (its id, or the supplier's name)."""
    names = {}
    for row in registries["parts"]["rows"]:
        names[row[0]] = [row[0]]
    for row in registries["suppliers"]["rows"]:
        names[row[0]] = [row[0], " ".join(row[1].split()[:2])]
    return names


def grounded(entity, quote, names):
    if entity not in names:
        return True
    lowered = quote.lower()
    return any(name.lower() in lowered for name in names[entity])


def check_fact(fact, document_text, predicates, ids, names=None):
    """Return (fact_with_document_quote, None) or (fact, reason)."""
    quote = find_quote(document_text, fact["quote"])
    if quote is None:
        return fact, "quote not found in document"
    checked = {**fact, "quote": quote}
    if fact["p"] not in predicates or fact["p"] in INFERRED_PREDICATES:
        return checked, f"predicate {fact['p']} not allowed"
    if fact["s"] not in ids:
        return checked, f"unknown subject {fact['s']}"
    if fact["p"] == "status":
        if json.loads(fact["o"]) not in STATUS_VALUES:
            return checked, f"unknown status {fact['o']}"
    elif fact["o"] not in ids:
        return checked, f"unknown object {fact['o']}"
    if names and not grounded(fact["o"], quote, names):
        return checked, f"ungrounded: quote does not name {fact['o']}"
    return checked, None


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
    context = (f"Document id: {header['id']} (type {header['type']})\nTitle: {header['title']}\n"
               f"Valid from {header['valid_from']} to {header['valid_to'] or 'open end'}\n"
               f"Replaces: {header['supersedes'] or 'nothing'}")
    instructions = GUARDED_INSTRUCTIONS if guarded else PLAIN_INSTRUCTIONS
    accepted, review, seen = [], [], set()
    tokens_in = tokens_out = 0
    started = time.time()
    pieces = chunks(body)
    for index, piece in enumerate(pieces, start=1):
        prompt = (f"{glossary(registries)}\n\n{context}\n{instructions}\n\n"
                  f"Part {index} of {len(pieces)} of the document:\n<<<\n{piece}\n>>>")
        output, usage, _, _ = call(model, SYSTEM, prompt, FACTS_SCHEMA)
        tokens_in += usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) \
            + usage.get("cache_read_input_tokens", 0)
        tokens_out += usage.get("output_tokens", 0)
        for raw in output.get("facts", []):
            fact = {"s": raw["s"].strip(), "p": raw["p"].strip(), "o": normalise_object(raw["p"], raw["o"]),
                    "quote": raw["quote"]}
            key = (fact["s"], fact["p"], fact["o"])
            if key in seen:
                continue
            seen.add(key)
            checked, reason = check_fact(fact, body, predicates, ids, names)
            if reason:
                review.append({**checked, "reason": reason})
            else:
                accepted.append(checked)
    return {"header": header, "accepted": accepted, "review": review, "tokens_in": tokens_in,
            "tokens_out": tokens_out, "seconds": time.time() - started, "chunks": len(pieces)}


def to_log_facts(result, kind_of_type):
    header = result["header"]
    facts = []
    for index, fact in enumerate(result["accepted"]):
        facts.append({"id": f"X-{header['id']}-{index:03d}", "s": fact["s"], "p": fact["p"], "o": fact["o"],
                      "source": header["id"], "quote": fact["quote"], "valid_from": header["valid_from"],
                      "valid_to": header["valid_to"], "kind": kind_of_type(header["type"]),
                      "author": header["author"]})
    return facts


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
    if args.accept:
        log.accept_proposed(result["header"]["id"], reviewer="bench")
    for fact in result["accepted"]:
        print(f"OK     {fact['s']} {fact['p']} {fact['o']}  \"{fact['quote'][:70]}\"")
    for fact in result["review"]:
        print(f"REVIEW {fact['s']} {fact['p']} {fact['o']}  ({fact['reason']})")
    print(f"{result['chunks']} chunks, {result['tokens_in']} tokens in, {result['seconds']:.0f} s")


if __name__ == "__main__":
    main()
