"""Render the mini-company into files.

Outputs (all under data/):
  registry/<name>.csv      one table per registry
  docs/<id>.md             documents with a YAML header
  meetings/<id>.json       past meeting transcripts with decisions
  facts.jsonl              every fact with its source, quote and valid time (input of core/)
  corpus.jsonl             every source as plain text (input of the retrieval and full-context baselines)

Usage: python data/build.py
"""
import csv
import io
import json
import os
import sys

import yaml

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DATA_DIR)

from world import DOCUMENTS, REGISTRIES  # noqa: E402
from meetings import MEETINGS  # noqa: E402

LITERAL_COLUMNS = {"status", "role", "drawing_rev", "typical_yield_mpa", "min_yield_mpa"}
DOC_TYPE_CLASS = {
    "customer_requirement": "CustomerRequirement", "law": "Law", "standard": "Standard",
    "internal_procedure": "InternalProcedure", "contract": "Document", "part_card": "Document",
    "fmea": "Document", "8d": "EightD", "ncr": "NCR", "deviation": "Deviation", "email": "Document",
}
# Authority rank of a fact (core/contracts.py, docs/architecture.md): 1 law or customer requirement,
# 2 controlled record (procedure, standard, registry, 8D, NCR, deviation, part card), 3 informal (meeting, e-mail).
FACT_RANK = {"law": 1, "customer_requirement": 1, "internal_procedure": 2, "contract": 2, "standard": 2,
             "part_card": 2, "fmea": 2, "8d": 2, "ncr": 2, "deviation": 2, "registry": 2, "meeting": 3, "email": 3}
# Informal documents only restate what other records say: their content facts are mentions, never asserts.
MENTION_TYPES = {"email"}
DOC_RANK = {"law": 1, "customer_requirement": 2, "internal_procedure": 3, "contract": 3, "standard": 4,
            "part_card": 5, "fmea": 5, "8d": 5, "ncr": 5, "deviation": 5, "registry": 5, "meeting": 6,
            "email": 7}


def csv_line(values):
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="").writerow(values)
    return buffer.getvalue()


def new_fact(subject, predicate, obj, source, quote, valid_from=None, valid_to=None, kind="evidence",
             author=None, rank=2, assertion="assert"):
    # kind: assert | mention (contract field). epistemic: the older evidence/decision/constraint label.
    return {"s": subject, "p": predicate, "o": obj, "source": source, "quote": quote,
            "valid_from": valid_from, "valid_to": valid_to, "kind": assertion, "epistemic": kind,
            "rank": rank, "author": author}


def registry_facts(name, registry):
    facts = []
    columns = registry["columns"]
    source = f"REG-{name.upper()}"
    for row in registry["rows"]:
        record = dict(zip(columns, row))
        quote = csv_line(row)
        subject = record["id"]
        valid_from = record.get("valid_from") or None
        valid_to = record.get("valid_to") or None
        author = record.get("approved_by") or None
        kind = "decision" if name in ("asl", "supplier_qualification") else "evidence"
        class_name = registry["class"] or record.get("class")
        facts.append(new_fact(subject, "type", class_name, source, quote, valid_from, valid_to, kind, author))
        label = record.get("name") or record.get("description")
        if label:
            facts.append(new_fact(subject, "label", json.dumps(label), source, quote, valid_from, valid_to,
                                  kind, author))
        for column, predicate in registry["map"].items():
            value = record.get(column, "")
            if not value or value == "none":
                continue
            for item in value.split(";"):
                obj = json.dumps(item) if column in LITERAL_COLUMNS else item
                facts.append(new_fact(subject, predicate, obj, source, quote, valid_from, valid_to, kind, author))
        if record.get("supersedes"):
            facts.append(new_fact(subject, "supersedes", record["supersedes"], source, quote, valid_from,
                                  valid_to, kind, author))
    return facts


def document_facts(document):
    source = document["id"]
    kind = "constraint" if document["type"] in ("customer_requirement", "law", "internal_procedure") else "evidence"
    first_line = document["body"].splitlines()[0]
    rank = FACT_RANK[document["type"]]
    facts = [new_fact(source, "type", DOC_TYPE_CLASS[document["type"]], source, first_line,
                      document["valid_from"], document["valid_to"], kind, document["author"], rank)]
    if document.get("supersedes"):
        facts.append(new_fact(source, "supersedes", document["supersedes"], source, first_line,
                              document["valid_from"], document["valid_to"], kind, document["author"], rank))
    default_assertion = "mention" if document["type"] in MENTION_TYPES else "assert"
    for item in document["facts"]:
        subject, predicate, obj, quote = item[:4]
        assertion = item[4] if len(item) > 4 else default_assertion
        facts.append(new_fact(subject, predicate, obj, source, quote, document["valid_from"],
                              document["valid_to"], kind, document["author"], rank, assertion))
    return facts


def meeting_facts(meeting):
    facts = []
    source = meeting["id"]
    for decision in meeting["decisions"]:
        quote = decision["quote"]
        common = {"source": source, "quote": quote, "valid_from": meeting["date"], "valid_to": None,
                  "kind": "assert", "epistemic": "decision", "rank": FACT_RANK["meeting"], "author": decision["by"]}
        facts.append({"s": decision["id"], "p": "type", "o": "Decision", **common})
        facts.append({"s": decision["id"], "p": "decidedIn", "o": meeting["id"], **common})
        facts.append({"s": decision["id"], "p": "decidedBy", "o": decision["by"], **common})
        facts.append({"s": decision["id"], "p": "reason", "o": json.dumps(decision["reason"]), **common})
        for entity in decision["about"]:
            facts.append({"s": decision["id"], "p": "about", "o": entity, **common})
    return facts


def render_registry_text(name, registry):
    lines = [registry["title"], ",".join(registry["columns"])]
    lines += [csv_line(row) for row in registry["rows"]]
    return "\n".join(lines)


def render_meeting_text(meeting, names):
    lines = [f"{meeting['title']}, {meeting['date']}"]
    for speaker, text in meeting["utterances"]:
        lines.append(f"{names[speaker]}: {text}")
    return "\n".join(lines)


def main(out_dir=DATA_DIR, registries=REGISTRIES, documents=DOCUMENTS, meetings=MEETINGS):
    for folder in ("registry", "docs", "meetings"):
        os.makedirs(os.path.join(out_dir, folder), exist_ok=True)
    names = {row[0]: row[1] for row in registries["people"]["rows"]}
    facts = []
    corpus = []

    for name, registry in registries.items():
        with open(os.path.join(out_dir, "registry", f"{name}.csv"), "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(registry["columns"])
            writer.writerows(registry["rows"])
        facts += registry_facts(name, registry)
        corpus.append({"id": f"REG-{name.upper()}", "type": "registry", "title": registry["title"],
                       "date": None, "valid_from": None, "valid_to": None, "supersedes": None,
                       "rank": DOC_RANK["registry"], "text": render_registry_text(name, registry)})

    for document in documents:
        header = {key: document.get(key) for key in
                  ("id", "type", "title", "date", "author", "valid_from", "valid_to", "supersedes", "mentions")}
        header["facts"] = [{"s": item[0], "p": item[1], "o": item[2], "quote": item[3]} for item in document["facts"]]
        with open(os.path.join(out_dir, "docs", f"{document['id']}.md"), "w") as file:
            file.write("---\n" + yaml.safe_dump(header, sort_keys=False, allow_unicode=True) + "---\n")
            file.write(document["body"].strip() + "\n")
        facts += document_facts(document)
        corpus.append({"id": document["id"], "type": document["type"], "title": document["title"],
                       "date": document["date"], "valid_from": document["valid_from"],
                       "valid_to": document["valid_to"], "supersedes": document.get("supersedes"),
                       "rank": DOC_RANK[document["type"]], "text": document["body"].strip()})

    for meeting in meetings:
        with open(os.path.join(out_dir, "meetings", f"{meeting['id']}.json"), "w") as file:
            json.dump(meeting, file, indent=2, ensure_ascii=False)
        facts += meeting_facts(meeting)
        corpus.append({"id": meeting["id"], "type": "meeting", "title": meeting["title"],
                       "date": meeting["date"], "valid_from": meeting["date"], "valid_to": None,
                       "supersedes": None, "rank": DOC_RANK["meeting"],
                       "text": render_meeting_text(meeting, names)})

    for index, fact in enumerate(facts):
        fact["id"] = f"F{index:04d}"
    with open(os.path.join(out_dir, "facts.jsonl"), "w") as file:
        for fact in facts:
            file.write(json.dumps(fact, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "registries.json"), "w") as file:
        json.dump(registries, file, ensure_ascii=False)
    with open(os.path.join(out_dir, "corpus.jsonl"), "w") as file:
        for item in corpus:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")
    record_count = sum(len(registry["rows"]) for registry in registries.values())
    print(f"{record_count} registry rows, {len(documents)} documents, {len(meetings)} meetings, "
          f"{len(facts)} facts, {len(corpus)} corpus items")


if __name__ == "__main__":
    main()
