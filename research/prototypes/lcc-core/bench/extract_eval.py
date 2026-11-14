"""Evaluate fact extraction on the long documents, then rerun the benchmark on extracted facts.

  python data/longdocs.py              # once: builds data_long/docs/*.md and data_long/traps.json
  python bench/extract_eval.py         # extraction scores + data_long/facts.jsonl + bench conditions gold,ontology

Gold = the hand-written facts of each document in data/world.py. Hand facts of the long documents are replaced
by the extracted (auto-accepted) facts; everything else in memory stays the same. requests.jsonl is untouched.
Writes bench/results/extraction_long.json and prints a table.
"""
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BENCH_DIR)
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "data"))
sys.path.insert(0, BENCH_DIR)

from extract import document_kind, extract_document, read_document, to_log_facts  # noqa: E402
from factlog import FactLog  # noqa: E402
from world import DOCUMENTS, REGISTRIES  # noqa: E402

LONG_DIR = os.path.join(ROOT, "data_long")
GUARDED = "--plain" not in sys.argv
OUT_DIR = LONG_DIR if GUARDED else os.path.join(ROOT, "data_long_plain")
DATA_DIR = os.path.join(ROOT, "data")
RESULTS_DIR = os.path.join(BENCH_DIR, "results")
PYTHON = sys.executable
TAG = "_long" if GUARDED else "_long_plain"


def gold_facts(doc_id):
    document = next(item for item in DOCUMENTS if item["id"] == doc_id)
    return {(s, p, o) for s, p, o, _ in document["facts"]}


def score_document(doc_id, result, traps):
    gold = gold_facts(doc_id)
    accepted = {(fact["s"], fact["p"], fact["o"]) for fact in result["accepted"]}
    proposed = accepted | {(fact["s"], fact["p"], fact["o"]) for fact in result["review"]}
    trap_set = {tuple(fact) for fact in traps.get(doc_id, [])}
    reasons = {}
    for fact in result["review"]:
        reason = fact["reason"].split(" ")[0]  # quote | predicate | unknown
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "id": doc_id, "chars": result["chars"], "chunks": result["chunks"], "gold": len(gold),
        "tp": len(gold & accepted), "fp": len(accepted - gold), "fn": len(gold - accepted),
        "missed": sorted(map(list, gold - accepted)), "extra": sorted(map(list, accepted - gold)),
        "trap_hits_accepted": sorted(map(list, trap_set & accepted)),
        "trap_hits_proposed": sorted(map(list, trap_set & proposed)),
        "review": [{key: fact[key] for key in ("s", "p", "o", "reason")} for fact in result["review"]],
        "review_reasons": reasons, "tokens_in": result["tokens_in"], "tokens_out": result["tokens_out"],
        "seconds": result["seconds"],
    }


def extract_one(doc_id):
    path = os.path.join(LONG_DIR, "docs", f"{doc_id}.md")
    result = extract_document(path, REGISTRIES, [item["id"] for item in DOCUMENTS], guarded=GUARDED)
    _, body = read_document(path)
    result["chars"] = len(body)
    return doc_id, result


def load_jsonl(path):
    with open(path) as file:
        return [json.loads(line) for line in file]


def build_long_memory(results):
    """data_long/facts.jsonl = data/facts.jsonl without the hand facts of the long documents + extracted facts."""
    replaced = set(results)
    base = [fact for fact in load_jsonl(os.path.join(DATA_DIR, "facts.jsonl"))
            if not (fact["source"] in replaced and fact["p"] not in ("type", "supersedes"))]
    log = FactLog()
    for fact in base:
        log._insert(fact, recorded_at="2026-11-13T00:00:00+00:00", review="accepted")
    for doc_id, result in results.items():
        for fact in to_log_facts(result, document_kind):
            log.propose_fact(fact, proposed_by="extractor")
        log.accept_proposed(doc_id, reviewer="bench-auto-accept")
    columns = ("id", "s", "p", "o", "source", "quote", "valid_from", "valid_to", "kind", "author")
    with open(os.path.join(OUT_DIR, "facts.jsonl"), "w") as file:
        for fact in log.all_facts():
            file.write(json.dumps({key: fact[key] for key in columns}, ensure_ascii=False) + "\n")
    shutil.copy(os.path.join(DATA_DIR, "registries.json"), os.path.join(OUT_DIR, "registries.json"))
    corpus = load_jsonl(os.path.join(DATA_DIR, "corpus.jsonl"))
    with open(os.path.join(OUT_DIR, "corpus.jsonl"), "w") as file:
        for item in corpus:
            if item["id"] in replaced:
                _, body = read_document(os.path.join(LONG_DIR, "docs", f"{item['id']}.md"))
                item = {**item, "text": body.strip()}
            file.write(json.dumps(item, ensure_ascii=False) + "\n")
    return len(base)


def main():
    with open(os.path.join(LONG_DIR, "traps.json")) as file:
        traps = json.load(file)
    doc_ids = sorted(name[:-3] for name in os.listdir(os.path.join(LONG_DIR, "docs")) if name.endswith(".md"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = dict(pool.map(extract_one, doc_ids))
    rows = [score_document(doc_id, results[doc_id], traps) for doc_id in doc_ids]
    os.makedirs(OUT_DIR, exist_ok=True)
    build_long_memory(results)
    with open(os.path.join(RESULTS_DIR, f"extraction{TAG}.json"), "w") as file:
        json.dump(rows, file, indent=1)

    lines = ["| Document | ~tokens | Chunks | Gold | Found | Wrong extra | Missed | Precision | Recall | Traps taken "
             "| Sent to review | Tokens in |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    totals = {"gold": 0, "tp": 0, "fp": 0, "fn": 0, "traps": 0, "review": 0, "tokens_in": 0}
    for row in rows:
        precision = row["tp"] / max(row["tp"] + row["fp"], 1)
        recall = row["tp"] / max(row["gold"], 1)
        lines.append(f"| {row['id']} | {row['chars'] // 4:,} | {row['chunks']} | {row['gold']} | {row['tp']} | "
                     f"{row['fp']} | {row['fn']} | {precision:.2f} | {recall:.2f} | "
                     f"{len(row['trap_hits_accepted'])} | {len(row['review'])} | {row['tokens_in']:,} |")
        totals["gold"] += row["gold"]
        totals["tp"] += row["tp"]
        totals["fp"] += row["fp"]
        totals["fn"] += row["fn"]
        totals["traps"] += len(row["trap_hits_accepted"])
        totals["review"] += len(row["review"])
        totals["tokens_in"] += row["tokens_in"]
    lines.append(f"| **Total** | | | {totals['gold']} | {totals['tp']} | {totals['fp']} | {totals['fn']} | "
                 f"{totals['tp'] / max(totals['tp'] + totals['fp'], 1):.2f} | "
                 f"{totals['tp'] / max(totals['gold'], 1):.2f} | {totals['traps']} | {totals['review']} | "
                 f"{totals['tokens_in']:,} |")
    print("\n".join(lines))
    with open(os.path.join(RESULTS_DIR, f"extraction{TAG}_table.md"), "w") as file:
        file.write("\n".join(lines) + "\n")

    subprocess.run([PYTHON, os.path.join(BENCH_DIR, "run.py"), "--conditions", "gold,ontology", "--data-dir",
                    OUT_DIR, "--tag", TAG], check=True)
    subprocess.run([PYTHON, os.path.join(BENCH_DIR, "score.py"), "--conditions", "gold,ontology", "--tag", TAG],
                   check=True)


if __name__ == "__main__":
    main()
