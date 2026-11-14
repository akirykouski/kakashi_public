"""Model baselines A (BM25 top-8), A' (BM25 + dense top-8) and B (all documents dated <= request date).

    python eval/tools/run_baselines.py --conditions A,Aprime,B --worlds M,A --out eval/results/dryrun [--model sonnet]

Same system prompt, prompt template, rule catalogue and output schema for every condition and both worlds;
only the documents and the world's key formats differ. The model is Claude through the logged-in Claude Code
subscription CLI with tools, MCP servers and settings off (no API key). Every raw CLI response is saved under
eval/raw/<condition>/<world>/<request id>.json and reused when the prompt is unchanged.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]
RAW = EVAL / "raw"
RAW_DIR = RAW  # set from --raw-tag; dry runs use eval/raw/dryrun so reported runs never reuse them
TOP_K = 8
RRF_K = 60
DENSE_MODEL = "intfloat/multilingual-e5-small"  # world A mixes English and Italian
CLI = ["claude", "-p", "--strict-mcp-config", "--tools", "", "--setting-sources", "",
       "--disable-slash-commands", "--no-session-persistence", "--output-format", "json"]
TIMEOUT_S = 300

RULE_IDS = ["U_SUPPLIER_STANDING", "U_SOURCE_RELEASE", "U_CUSTOMER_APPROVAL", "U_OPEN_ISSUE",
            "U_RESTRICTED_SUBSTANCE", "U_MATERIAL", "U_MEASURED_VALUE", "U_DEVIATION_LIMIT", "U_MISSING_EVIDENCE"]

SYSTEM = ("You review proposed engineering changes at an automotive supplier. Use only the company documents "
          "given. Never approve anything: list findings, each with the documents and the verbatim quotes that "
          "support it. Documents can be outdated or replaced by newer ones.")

CATALOGUE = """Rule catalogue. Report every finding that applies, and nothing else. kind is "blocker" unless the rule says "question".
U_SUPPLIER_STANDING  The supplier as a whole may not receive new business or new parts now (qualification conditional, probation, blocked).
    key = {key_supplier}
U_SOURCE_RELEASE  The source has no current approval for this part (approval is per part x receiving plant x customer, and supplier location).
    If no controlled record covers that part, plant and customer, so absence cannot be read as "not approved", report kind "question" instead.
    key = {key_source}
U_CUSTOMER_APPROVAL  The change falls under a customer requirement in force (part -> program -> customer requirement), so written customer approval or notification is needed before shipment, and nothing in force already covers it.
    key = {key_customer}
U_OPEN_ISSUE  The supplier has an OPEN quality issue (8D, NCR) on the material or alloy of this part.
    key = issue id
U_RESTRICTED_SUBSTANCE  The new coating or material contains a substance restricted by law in the part's market.
    key = substance id
U_MATERIAL  The material offered or requested does not meet the material the drawing in force requires (grade, or capability against the special characteristic).
    key = {key_material}
U_MEASURED_VALUE  A measured value fails a special characteristic of the drawing and control plan in force.
    key = special characteristic id
U_DEVIATION_LIMIT  A deviation request exceeds the limits of the deviation procedure in force.
    key = procedure id
U_MISSING_EVIDENCE  kind "question": evidence a decision needs is not in the documents, so a person must answer.
    key = one of: {key_missing}
Changes of delivery date, quantity, expediting or packaging alone need no finding unless a rule above applies."""

KEYS = {
    "M": {"key_supplier": "supplier id",
          "key_source": '"supplier|part|customer" with ids (use the supplier name as said if it has no id)',
          "key_customer": "customer id (one finding per customer of the part)",
          "key_material": "source change: the drawing material id; material change: the new material id",
          "key_missing": "supplier_record (supplier not in our records), coating_substances (coating not in "
                         "catalogue), material_data (material not in master), material_certificate (no 3.1 "
                         "certificate for the material)"},
    "A": {"key_supplier": "supplier name as written in the documents (e.g. Meccanica C)",
          "key_source": "part number",
          "key_customer": "customer code (e.g. STL, CLM)",
          "key_material": "part number",
          "key_missing": "material_certificate (no certificate or test result for the material or lot)"},
}

SCHEMA = {
    "type": "object",
    "properties": {"findings": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "rule_u": {"type": "string", "enum": RULE_IDS},
            "key": {"type": "string"},
            "kind": {"type": "string", "enum": ["blocker", "question"]},
            "sources": {"type": "array", "items": {"type": "object", "properties": {
                "doc_id": {"type": "string"}, "quote": {"type": "string"}}, "required": ["doc_id", "quote"]}},
            "why": {"type": "string"}},
        "required": ["rule_u", "key", "kind", "sources", "why"]}}},
    "required": ["findings"],
}


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def csv_line(values):
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="").writerow(values)
    return buffer.getvalue()


# ---- worlds: sources visible on a date ------------------------------------------------------------------

M_DIR = EVAL / "worlds" / "M"  # --m-dir switches to eval/worlds/M_scale for H3


def m_sources(as_of):
    world = M_DIR
    registries = json.load(open(world / "registries.json"))
    sources = []
    for item in load_jsonl(world / "corpus.jsonl"):
        if item["type"] == "registry":
            registry = registries[item["id"][len("REG-"):].lower()]
            rows = registry["rows"]
            if "valid_from" in registry["columns"]:
                index = registry["columns"].index("valid_from")
                rows = [row for row in rows if not row[index] or row[index] <= as_of]
            header = f"{registry['title']}\n{','.join(registry['columns'])}"
            sources.append({"id": item["id"], "text": "\n".join([header] + [csv_line(row) for row in rows]),
                            "rows": [f"{header}\n{csv_line(row)}" for row in rows]})
        elif not item["valid_from"] or item["valid_from"] <= as_of:
            sources.append({"id": item["id"], "text": item["text"]})
    return sources


def m_glossary():
    registries = json.load(open(M_DIR / "registries.json"))
    lines = ["Glossary of ids (names only, no relations):"]
    for name in ("parts", "suppliers", "customers", "sites", "materials", "coatings", "people"):
        lines.append(f"{name}: " + "; ".join(f"{row[0]} = {row[1]}" for row in registries[name]["rows"]))
    lines.append("substances: CrVI = hexavalent chromium; CrIII = trivalent chromium; Lead; Cadmium; Mercury; "
                 "Zinc; Nickel")
    return "\n".join(lines)


def a_sources(as_of):
    sources = []
    for path in sorted((EVAL / "worlds" / "A" / "sources").glob("*.md")):
        text = path.read_text()
        match = re.search(r"^effective_date:\s*(\S+)", text, re.M)
        if match and match.group(1) <= as_of:
            sources.append({"id": path.stem, "text": text})
    return sources


WORLD = {"M": (m_sources, m_glossary), "A": (a_sources, lambda: "")}


def chunks_of(source):
    if "rows" in source:
        return [{"id": source["id"], "text": row} for row in source["rows"]]
    chunks, current = [], []
    for line in source["text"].split("\n"):
        current.append(line)
        if sum(len(item) for item in current) > 350:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return [{"id": source["id"], "text": "\n".join(chunk)} for chunk in chunks]


def tokenize(text):
    return "".join(c.lower() if c.isalnum() or c == "-" else " " for c in text).split()


_dense = None


def dense_model():
    global _dense
    if _dense is None:
        from sentence_transformers import SentenceTransformer
        _dense = SentenceTransformer(DENSE_MODEL)
    return _dense


def bm25_rank(chunks, query):
    from rank_bm25 import BM25Okapi
    scores = BM25Okapi([tokenize(chunk["text"]) for chunk in chunks]).get_scores(tokenize(query))
    return sorted(range(len(chunks)), key=lambda i: -scores[i])


def dense_rank(chunks, query):
    model = dense_model()
    passages = model.encode([f"passage: {chunk['text']}" for chunk in chunks], normalize_embeddings=True)
    question = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    scores = passages @ question
    return sorted(range(len(chunks)), key=lambda i: -scores[i])


def context_for(condition, sources, query):
    if condition == "B":
        return sources
    chunks = [chunk for source in sources for chunk in chunks_of(source)]
    if condition == "A":
        ranked = bm25_rank(chunks, query)[:TOP_K]
    else:  # Aprime: reciprocal rank fusion of BM25 and dense
        fused = {}
        for ranking in (bm25_rank(chunks, query), dense_rank(chunks, query)):
            for position, index in enumerate(ranking):
                fused[index] = fused.get(index, 0.0) + 1.0 / (RRF_K + position + 1)
        ranked = sorted(fused, key=lambda i: -fused[i])[:TOP_K]
    return [chunks[index] for index in ranked]


def build_prompt(world, item, context):
    sources_fn, glossary_fn = WORLD[world]
    documents = "\n\n".join(f"[{source['id']}]\n{source['text']}" for source in context)
    parts = [CATALOGUE.format(**KEYS[world]), glossary_fn(), f"Company documents:\n{documents}",
             f"Meeting date: {item['as_of']}\nProposed change, as said in the meeting: {item['request_text']}"]
    return "\n\n".join(part for part in parts if part)


def call_model(model, prompt, raw_path):
    key = hashlib.sha256(json.dumps([model, SYSTEM, prompt, SCHEMA]).encode()).hexdigest()
    if raw_path.exists():
        stored = json.load(open(raw_path))
        if stored.get("prompt_sha256") == key and not stored["response"].get("is_error"):
            return stored["response"], stored["seconds"]
    command = CLI + ["--model", model, "--system-prompt", SYSTEM, "--json-schema", json.dumps(SCHEMA)]
    started = time.time()
    completed = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=TIMEOUT_S, cwd="/tmp")
    seconds = time.time() - started
    raw = completed.stdout
    response = json.loads(raw[raw.find("{"):]) if "{" in raw else {"is_error": True, "result": completed.stderr}
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"prompt_sha256": key, "model_arg": model, "seconds": seconds, "response": response},
              open(raw_path, "w"), indent=1, ensure_ascii=False)
    return response, seconds


def run_one(condition, world, item, model):
    sources = WORLD[world][0](item["as_of"])
    context = context_for(condition, sources, item["request_text"])
    prompt = build_prompt(world, item, context)
    response, seconds = call_model(model, prompt, RAW_DIR / condition / world / f"{item['id']}.json")
    usage = response.get("usage", {})
    tokens_in = sum(usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    result = {"id": item["id"], "condition": condition, "world": world, "seconds": round(seconds, 2),
              "tokens_in": tokens_in, "tokens_out": usage.get("output_tokens", 0),
              "model_id": ",".join(sorted(response.get("modelUsage", {}))) or None,
              "context_ids": [source["id"] for source in context], "findings": [], "error": None}
    if response.get("is_error"):
        result["error"] = str(response.get("result"))[:300]
        return result
    output = response.get("structured_output") or json.loads(response.get("result") or "{}")
    result["findings"] = [{"rule_u": f["rule_u"], "key": f["key"].strip(), "kind": f["kind"],
                           "sources": f.get("sources", [])} for f in output.get("findings", [])]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", default="A,Aprime,B")
    parser.add_argument("--worlds", default="M,A")
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--raw-tag", required=True, help="e.g. dryrun or frozen")
    parser.add_argument("--m-dir", default="M", help="world-M directory under eval/worlds (M_scale for H3)")
    args = parser.parse_args()
    global RAW_DIR, M_DIR
    M_DIR = EVAL / "worlds" / args.m_dir
    RAW_DIR = RAW / args.raw_tag
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cli_version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    for world in args.worlds.split(","):
        gold = load_jsonl(EVAL / "gold" / f"{world}.jsonl")
        if args.limit:
            gold = gold[:args.limit]
        for condition in args.conditions.split(","):
            if condition == "Aprime":
                dense_model()  # load once before threads start
            started = time.time()
            with ThreadPoolExecutor(args.workers) as pool:
                results = list(pool.map(lambda item: run_one(condition, world, item, args.model), gold))
            with open(out / f"{world}_{condition}.jsonl", "w") as file:
                for row in results:
                    file.write(json.dumps(row, ensure_ascii=False) + "\n")
            model_ids = sorted({row["model_id"] for row in results if row["model_id"]})
            meta = {"condition": condition, "world": world, "model_arg": args.model, "model_ids": model_ids,
                    "cli": cli_version, "cli_flags": CLI, "top_k": TOP_K, "dense_model": DENSE_MODEL,
                    "rrf_k": RRF_K, "raw_dir": str(RAW_DIR.relative_to(EVAL.parent)), "temperature": "CLI default (not settable)", "n": len(results),
                    "errors": sum(1 for row in results if row["error"]), "wall_seconds": round(time.time() - started, 1),
                    "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            json.dump(meta, open(out / f"{world}_{condition}.meta.json", "w"), indent=1)
            print(json.dumps(meta), file=sys.stderr)


if __name__ == "__main__":
    main()
