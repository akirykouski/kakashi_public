"""Conditions C* (hand parse -> core) and C (model parse -> core): a thin adapter, no change to core logic.

    python eval/tools/run_core.py --conditions Cstar,C --worlds M,A --out eval/results/<run> --raw-tag <tag>

Request side: eval/parses/<world>_hand.jsonl (C*) or one model parse per request (C) -> core ChangeRequest.
Core side: core.check.run(request, record=False) on the world's own fact log (worlds never pooled).
Output side: Card.findings -> gold format (rule_u, key, kind, sources) per eval/MAPPING.md.

The C parser is called through the subscription CLI with the same model as A, A', B (methodology §3), using the
core parser's own system prompt and schema when core/parse.py exposes them.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]
REPO = EVAL.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

RULE_U = {"R1a": "U_SUPPLIER_STANDING", "R1b": "U_SOURCE_RELEASE", "R2": "U_CUSTOMER_APPROVAL",
          "R3": "U_OPEN_ISSUE", "R5": "U_RESTRICTED_SUBSTANCE", "R6": "U_MATERIAL", "R7": "U_MISSING_EVIDENCE",
          "R8": "U_SUBTIER"}
# R7 questions that are the question form of another unified rule (A's Q_SOURCE_RELEASE_UNKNOWN)
QUESTION_RULE_U = {"source_release": "U_SOURCE_RELEASE"}
SKIP_SEVERITIES = {"info"}  # notifications are not findings in either gold

# world A: core ids (eval/worlds/A/core/facts.jsonl) -> the entity names the A gold uses as keys
A_KEY_NAMES = {}


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def first(ids, pattern):
    for value in ids:
        if re.match(pattern, value):
            return value
    return None


def question_kind(ids):
    found = first(ids, r"^Q-")
    return found[2:] if found else None


def key_of(world, rule, ids, change):
    """Gold key for a core finding, by rule; ids are Finding.entities in the order the rule wrote them."""
    part = change.get("part")
    customer = first(ids, r"^CUST-")
    if rule == "R1a":
        key = ids[0] if ids else None
        return A_KEY_NAMES.get(key, key) if world == "A" else key
    if rule == "R1b":
        return part if world == "A" else f"{ids[0]}|{part}|{customer}"
    if rule == "R2":
        return customer[len("CUST-"):] if world == "A" and customer else customer
    if rule == "R3":
        return first(ids, r"^(8D|NCR)-")
    if rule == "R5":
        return ids[1] if len(ids) > 1 else (ids[0] if ids else None)
    if rule == "R6":
        return part if world == "A" else first(ids, r"^MAT-")
    if rule == "R7":
        kind = question_kind(ids)
        if kind in QUESTION_RULE_U:
            return part if world == "A" else f"{ids[0]}|{part}|{customer}"
        return kind
    return "|".join(ids)


def leaves(step):
    if not step.get("inferred"):
        return [step]
    result = []
    for premise in step.get("premises", []):
        result.extend(leaves(premise))
    return result


def to_gold_format(world, card, change):
    findings = []
    for finding in card["findings"]:
        if finding["severity"] in SKIP_SEVERITIES:
            continue
        rule, ids = finding["rule"], finding.get("entities", [])
        rule_u = RULE_U.get(rule, f"U_{rule}")
        if rule == "R7" and question_kind(ids) in QUESTION_RULE_U:
            rule_u = QUESTION_RULE_U[question_kind(ids)]
        kind = "question" if finding["severity"] == "question" else "blocker"
        sources = [{"doc_id": leaf.get("source"), "quote": leaf.get("quote") or ""}
                   for step in finding.get("evidence", []) for leaf in leaves(step) if leaf.get("source")]
        findings.append({"rule_u": rule_u, "key": str(key_of(world, rule, ids, change)), "kind": kind,
                         "rule_native": rule, "severity": finding["severity"], "entities": ids, "sources": sources})
    unique = {}
    for item in findings:
        unique.setdefault((item["rule_u"], item["key"].lower()), item)
    return list(unique.values())


ALIASES = {}


def use_world(world, as_of_dates):
    """Point the core at this world's facts. Reads only; no core file is changed.

    check.run projects from check._LOG, and rules.covered() (decision row R0) projects from a per-date cache
    that otherwise loads the default data/ world: both are set to this world's log, so worlds never mix.
    World M also loads the core's policy facts (rules_data/, written for world M); world A has its own policy
    facts inside eval/worlds/A/core/facts.jsonl (eval/tools/encode_A.py)."""
    from core import check, factlog, rules
    from core.project import Projection
    data_dir = EVAL / "worlds" / world / "core"
    log = factlog.default_log(data_dir=str(data_dir))
    if world == "M":
        log = rules.extend_log(log)
    check._LOG = log
    rules._projections.clear()
    for as_of in sorted(set(as_of_dates)):
        rules._projections[as_of] = Projection(log, as_of)
    A_KEY_NAMES.clear()
    ALIASES.clear()
    if world == "A":
        A_KEY_NAMES.update(json.load(open(data_dir / "key_names.json")))
        ALIASES.update(json.load(open(data_dir / "aliases.json")))
    return str(data_dir)


def resolve(change):
    """Names as said -> world ids, by the world's alias table (exact match only; unknown names stay names)."""
    return {key: ALIASES.get(value, value) if isinstance(value, str) else value for key, value in change.items()}


def cli_call(model_arg, usage_box):
    """A `call` for core.llm.cached_call that answers through the subscription CLI with the baselines' model."""
    import subprocess
    from run_baselines import CLI

    def call(_core_model, system, prompt, schema):
        command = CLI + ["--model", model_arg, "--system-prompt", system, "--json-schema", json.dumps(schema)]
        started = time.time()
        completed = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=300, cwd="/tmp")
        usage_box["seconds"] = time.time() - started
        raw = completed.stdout
        response = json.loads(raw[raw.find("{"):]) if "{" in raw else {"is_error": True, "result": completed.stderr}
        if response.get("is_error"):
            raise RuntimeError(str(response.get("result"))[:300])
        usage_box["model_id"] = ",".join(sorted(response.get("modelUsage", {})))
        usage = response.get("usage", {})
        usage_box["tokens_in"] = sum(usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                                "cache_read_input_tokens"))
        usage_box["tokens_out"] = usage.get("output_tokens", 0)
        output = response.get("structured_output") or json.loads(response.get("result") or "{}")
        return output, {**usage, "model_id": usage_box["model_id"], "seconds": usage_box["seconds"]}
    call.recorded_by = f"claude -p --model {model_arg} (eval track, subscription CLI)"
    return call


def model_parse(item, model, raw_dir, world):
    """C: the core's own parser (prompt, schema, name resolution) with its model call routed to the CLI.
    Raw answers are recorded as fixtures under eval/raw/<tag>/C_parse/<world>/, not in the core's tests."""
    from core import parse
    parse.FIXTURES_DIR = str(raw_dir)
    registries = json.load(open(EVAL / "worlds" / world / ("core/registries.json" if world == "A" else "registries.json")))
    box = {"seconds": 0.0, "tokens_in": 0, "tokens_out": 0, "model_id": None}
    change = parse.parse(item["request_text"], as_of=item["as_of"], registries=registries, live=True,
                         call=cli_call(model, box))
    return change, box["seconds"], box["tokens_in"], box["tokens_out"], box["model_id"]


def run_one(world, condition, item, hand, model, raw_dir):
    from core import check
    result = {"id": item["id"], "condition": condition, "world": world, "findings": [], "error": None,
              "seconds": 0.0, "tokens_in": 0, "tokens_out": 0, "model_id": None}
    try:
        if condition == "Cstar":
            change = resolve(dict(hand[item["id"]]["change"]))
            result["schema_gap"] = hand[item["id"]].get("schema_gap")
        else:
            change, seconds, tokens_in, tokens_out, model_id = model_parse(item, model, raw_dir, world)
            result.update(seconds=seconds, tokens_in=tokens_in, tokens_out=tokens_out, model_id=model_id)
        result["parsed"] = change
        if not change.get("type"):
            result["error"] = "no change type the core accepts"
            return result
        started = time.time()
        card, _ = check.run(change, record=False)
        result["seconds"] = round(result["seconds"] + time.time() - started, 3)
        result["core_verdict"] = card["verdict"]
        result["decision_row"] = (card.get("decision") or {}).get("row_id")
        result["findings"] = to_gold_format(world, card, change)
        # R0 "no rule covers this": a verdict, not a finding (scorer reads `not_covered`)
        result["not_covered"] = card["verdict"] == "not_covered" and not result["findings"]
    except Exception as error:  # reported per request; a crash is an empty prediction for the scorer
        result["error"] = f"{type(error).__name__}: {error}"[:400]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", default="Cstar,C")
    parser.add_argument("--worlds", default="M,A")
    parser.add_argument("--out", required=True)
    parser.add_argument("--raw-tag", required=True)
    parser.add_argument("--model", default="sonnet")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    commit = __import__("subprocess").run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                                          text=True).stdout.strip()
    for world in args.worlds.split(","):
        gold = load_jsonl(EVAL / "gold" / f"{world}.jsonl")
        data_dir = use_world(world, [item["as_of"] for item in gold])
        hand = {row["id"]: row for row in load_jsonl(EVAL / "parses" / f"{world}_hand.jsonl")}
        for condition in args.conditions.split(","):
            raw_dir = EVAL / "raw" / args.raw_tag / "C_parse" / world
            started = time.time()
            results = [run_one(world, condition, item, hand, args.model, raw_dir) for item in gold]
            with open(out / f"{world}_{condition}.jsonl", "w") as file:
                for row in results:
                    file.write(json.dumps(row, ensure_ascii=False) + "\n")
            meta = {"condition": condition, "world": world, "core_commit": commit, "facts": data_dir,
                    "model_arg": args.model if condition == "C" else None,
                    "model_ids": sorted({row["model_id"] for row in results if row.get("model_id")}),
                    "n": len(results), "errors": sum(1 for row in results if row["error"]),
                    "wall_seconds": round(time.time() - started, 1),
                    "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            json.dump(meta, open(out / f"{world}_{condition}.meta.json", "w"), indent=1)
            print(json.dumps(meta), file=sys.stderr)


if __name__ == "__main__":
    main()
