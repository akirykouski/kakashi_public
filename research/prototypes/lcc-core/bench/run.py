"""Run the benchmark conditions (see bench/PREREGISTRATION.md).

  python bench/run.py --conditions gold,ontology,retrieval,full [--limit 5] [--model sonnet]

Writes bench/results/<condition>.jsonl (one line per request: findings as (rule, key), tokens, seconds).
"""
import argparse
import csv
import io
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BENCH_DIR)
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "data"))

from rank_bm25 import BM25Okapi  # noqa: E402

import llm  # noqa: E402
from factlog import default_log  # noqa: E402
from project import Projection  # noqa: E402
from rules import check  # noqa: E402
from world import REGISTRIES  # noqa: E402

RESULTS_DIR = os.path.join(BENCH_DIR, "results")
ENGINE_LOCK = threading.Lock()  # rdflib's SPARQL parser is not thread-safe
RULES = ["R1a", "R1b", "R2", "R3", "R5", "R6", "R7"]
MISSING_KINDS = ["supplier_record", "coating_substances", "material_data", "material_certificate"]

RULE_CATALOGUE = """Rule catalogue. Report every finding that applies, and nothing else.
R1a  The new supplier's company-level qualification is currently "conditional" (no new parts allowed).
     key = supplier id
R1b  The new supplier has no current approval in the approved supplier list for this part, at the receiving
     site, for the customer of the part. (Approval is per supplier x part x our site x customer.)
     key = "supplier|part|customer" (use the supplier name as said if it has no id)
R2   The change needs written customer approval (PPAP resubmission) before shipping, under the customer's
     current requirements, and no valid deviation covers it and the new source is not already approved.
     key = customer id (one finding per customer of the part)
R3   The new supplier has an OPEN quality issue (8D, NCR) on the material or alloy of this part.
     key = issue id
R5   The new coating contains a substance restricted by law for vehicles sold in the part's market.
     key = substance id
R6   Source change: the new supplier is not qualified to deliver the part's drawing material (key = drawing
     material id). Material change: the new material is below the part's special characteristic
     (key = new material id).
R7   Evidence is missing, so a person must answer a question. key = one of: supplier_record (supplier not in
     our records), coating_substances (coating not in catalogue), material_data (material not in master),
     material_certificate (no 3.1 certificate from the new supplier for the drawing material).
Changes of delivery date, quantity or packaging alone need no finding unless a rule above applies."""

FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {"findings": {"type": "array", "items": {
        "type": "object",
        "properties": {"rule": {"type": "string", "enum": RULES}, "key": {"type": "string"},
                       "sources": {"type": "array", "items": {"type": "string"}},
                       "why": {"type": "string"}},
        "required": ["rule", "key", "sources", "why"]}}},
    "required": ["findings"],
}

CHANGE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["SourceChange", "MaterialChange", "ProcessChange", "CoatingChange",
                                            "ScheduleChange", "PackagingChange"]},
        "part": {"type": "string"}, "to_supplier": {"type": ["string", "null"]},
        "from_supplier": {"type": ["string", "null"]}, "site": {"type": ["string", "null"]},
        "new_material": {"type": ["string", "null"]}, "new_coating": {"type": ["string", "null"]}},
    "required": ["type", "part", "to_supplier", "from_supplier", "site", "new_material", "new_coating"],
}

SYSTEM_REVIEW = ("You review proposed engineering changes at Valsangone Componenti, a tier-1 automotive supplier. "
                 "Use only the company documents given. Never approve anything: list findings with the ids of the "
                 "documents that support each one. Documents can be outdated or replaced by newer ones.")
SYSTEM_PARSE = ("You turn a sentence said in an engineering change meeting into a structured change. Use the ids "
                "from the glossary. If a supplier, coating or material is not in the glossary, write its name "
                "exactly as said. site is null unless a receiving site is named. Moving deliveries to another of "
                "our sites is a SourceChange with that site.")


def load_jsonl(path):
    with open(path) as file:
        return [json.loads(line) for line in file]


def glossary():
    lines = ["Glossary of ids (names only, no relations):"]
    for name in ("parts", "suppliers", "customers", "sites", "materials", "coatings", "people"):
        registry = REGISTRIES[name]
        entries = "; ".join(f"{row[0]} = {row[1]}" for row in registry["rows"])
        lines.append(f"{name}: {entries}")
    lines.append("substances: CrVI = hexavalent chromium; CrIII = trivalent chromium; Lead; Cadmium; Mercury; "
                 "Zinc; Nickel")
    return "\n".join(lines)


# ---- documents visible on a date -------------------------------------------------------------------------

def registry_rows_visible(registry, as_of):
    columns = registry["columns"]
    if "valid_from" not in columns:
        return registry["rows"]
    index = columns.index("valid_from")
    return [row for row in registry["rows"] if not row[index] or row[index] <= as_of]


def csv_line(values):
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="").writerow(values)
    return buffer.getvalue()


def visible_sources(corpus, as_of):
    """(id, text) of every source a reader could see on as_of. Registries keep only rows that existed."""
    sources = []
    for item in corpus:
        if item["type"] == "registry":
            name = item["id"][len("REG-"):].lower()
            registry = REGISTRIES[name]
            rows = registry_rows_visible(registry, as_of)
            text = "\n".join([registry["title"], ",".join(registry["columns"])] + [csv_line(row) for row in rows])
            sources.append({"id": item["id"], "text": text, "registry": registry, "rows": rows})
        elif not item["valid_from"] or item["valid_from"] <= as_of:
            sources.append({"id": item["id"], "text": item["text"]})
    return sources


def chunks_of(source):
    if "registry" in source:
        registry = source["registry"]
        header = f"{registry['title']}\n{','.join(registry['columns'])}"
        return [{"id": source["id"], "text": f"{header}\n{csv_line(row)}"} for row in source["rows"]]
    lines = source["text"].split("\n")
    chunks, current = [], []
    for line in lines:
        current.append(line)
        if sum(len(item) for item in current) > 350:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return [{"id": source["id"], "text": "\n".join(chunk)} for chunk in chunks]


def tokenize(text):
    cleaned = "".join(character.lower() if character.isalnum() or character == "-" else " " for character in text)
    return cleaned.split()


def render_sources(items):
    return "\n\n".join(f"[{item['id']}]\n{item['text']}" for item in items)


# ---- conditions ------------------------------------------------------------------------------------------

def run_gold(item, log):
    started = time.time()
    findings = check(Projection(log, item["as_of"]), item["change"])
    return {"findings": engine_keys(findings, item["change"]), "seconds": time.time() - started,
            "tokens_in": 0, "tokens_out": 0, "parsed": item["change"]}


def run_ontology(item, log, model):
    prompt = f"{glossary()}\n\nMeeting date: {item['as_of']}\nSentence: {item['utterance']}"
    change, usage, seconds, _ = llm.call(model, SYSTEM_PARSE, prompt, CHANGE_SCHEMA)
    change = {key: value for key, value in change.items() if value}
    started = time.time()
    with ENGINE_LOCK:
        findings = check(Projection(log, item["as_of"]), change)
    return {"findings": engine_keys(findings, change), "seconds": seconds + time.time() - started,
            "tokens_in": llm.input_tokens(usage), "tokens_out": usage.get("output_tokens", 0), "parsed": change}


def run_reader(item, model, corpus, mode):
    sources = visible_sources(corpus, item["as_of"])
    if mode == "retrieval":
        chunks = [chunk for source in sources for chunk in chunks_of(source)]
        index = BM25Okapi([tokenize(chunk["text"]) for chunk in chunks])
        scores = index.get_scores(tokenize(item["utterance"]))
        ranked = sorted(range(len(chunks)), key=scores.__getitem__, reverse=True)[:8]
        context = render_sources([chunks[position] for position in ranked])
    else:
        context = render_sources(sources)
    prompt = (f"{RULE_CATALOGUE}\n\n{glossary()}\n\nCompany documents:\n{context}\n\n"
              f"Meeting date: {item['as_of']}\nProposed change, as said in the meeting: {item['utterance']}")
    output, usage, seconds, _ = llm.call(model, SYSTEM_REVIEW, prompt, FINDINGS_SCHEMA)
    findings = [{"rule": finding["rule"], "key": finding["key"].strip(), "sources": finding.get("sources", [])}
                for finding in output.get("findings", [])]
    return {"findings": findings, "seconds": seconds, "tokens_in": llm.input_tokens(usage),
            "tokens_out": usage.get("output_tokens", 0)}


def engine_keys(findings, change):
    keys = []
    for finding in findings:
        if finding["severity"] == "info":
            continue
        entities = finding["entities"]
        rule = finding["rule"]
        if rule == "R1a":
            key = entities["supplier"]
        elif rule == "R1b":
            key = f"{entities['supplier']}|{entities['part']}|{entities['customer']}"
        elif rule == "R2":
            key = entities["customer"]
        elif rule == "R3":
            key = entities["issue"]
        elif rule == "R5":
            key = entities["substance"]
        elif rule == "R6":
            key = entities["material"]
        else:
            key = entities["missing"]
        sources = sorted({leaf["source"] for step in finding["evidence"] for leaf in leaves(step)})
        keys.append({"rule": rule, "key": key, "sources": sources})
    unique = {(item["rule"], item["key"]): item for item in keys}
    return list(unique.values())


def leaves(step):
    if not step.get("inferred"):
        return [step]
    result = []
    for premise in step.get("premises", []):
        result.extend(leaves(premise))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", default="gold,ontology,retrieval,full")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--parallel", type=int, default=6)
    parser.add_argument("--data-dir", default=os.path.join(ROOT, "data"))
    parser.add_argument("--tag", default="", help="suffix for result files, e.g. _scale6")
    parser.add_argument("--ids", help="comma-separated request ids to run")
    args = parser.parse_args()
    requests = load_jsonl(os.path.join(BENCH_DIR, "requests.jsonl"))[: args.limit]
    if args.ids:
        wanted = set(args.ids.split(","))
        requests = [item for item in requests if item["id"] in wanted]
    corpus = load_jsonl(os.path.join(args.data_dir, "corpus.jsonl"))
    with open(os.path.join(args.data_dir, "registries.json")) as file:
        REGISTRIES.clear()
        REGISTRIES.update(json.load(file))
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log = default_log(args.data_dir)
    for condition in args.conditions.split(","):
        started = time.time()

        def run_one(item):
            try:
                if condition == "gold":
                    result = run_gold(item, log)
                elif condition == "ontology":
                    result = run_ontology(item, log, args.model)
                else:
                    result = run_reader(item, args.model, corpus, condition)
            except Exception as error:  # keep going, record the failure
                result = {"findings": [], "error": repr(error)[:300], "seconds": 0, "tokens_in": 0, "tokens_out": 0}
            return {"id": item["id"], **result}

        workers = 1 if condition == "gold" else args.parallel
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(run_one, requests))
        with open(os.path.join(RESULTS_DIR, f"{condition}{args.tag}.jsonl"), "w") as file:
            for row in rows:
                file.write(json.dumps(row) + "\n")
        errors = sum(1 for row in rows if row.get("error"))
        print(f"{condition}: {len(rows)} requests, {errors} errors, {time.time() - started:.0f} s", flush=True)


if __name__ == "__main__":
    main()
