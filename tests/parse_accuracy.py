"""Parser accuracy on the 36 benchmark utterances (data/requests.jsonl).

  python tests/parse_accuracy.py               # recorded fixtures only (default, no key, no cost)
  python tests/parse_accuracy.py --live        # call the model through the Vercel AI Gateway (AI_GATEWAY_API_KEY)
  python tests/parse_accuracy.py --record-cli  # record missing fixtures with the local `claude -p --model haiku`

Exact match per field. A gold name that is not an id (the "missing" cases, e.g. "Viteria Lanzo") counts as a match
when the parser left the field empty and listed that name in `unresolved` for the same field: it must not guess.
"core" = type, part and to_supplier all match. "all" = every field of the gold change matches and the parser set
no field the gold leaves empty.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))

import parse as parser_module  # noqa: E402

REQUESTS_PATH = os.path.join(ROOT, "data", "requests.jsonl")
FIELDS = ("type", "part", "to_supplier", "from_supplier", "site", "new_material", "new_coating")
CORE_FIELDS = ("type", "part", "to_supplier")


def cli_call(model, system, prompt, schema):
    """Record a fixture with the local Claude Code CLI (subscription; does not use the team key)."""
    command = ["claude", "-p", "--model", "haiku", "--strict-mcp-config", "--tools", "", "--setting-sources", "",
               "--disable-slash-commands", "--no-session-persistence", "--system-prompt", system,
               "--output-format", "json", "--json-schema", json.dumps(schema)]
    completed = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=300, cwd="/tmp")
    raw = completed.stdout
    try:
        payload = json.loads(raw[raw.find("{"):])
    except json.JSONDecodeError:
        payload = [item for item in json.loads(raw) if item.get("type") == "result"][-1]
    if payload.get("is_error"):
        raise RuntimeError(str(payload.get("result"))[:300])
    output = payload.get("structured_output") or json.loads(payload.get("result", "{}"))
    return output, payload.get("usage", {})


cli_call.recorded_by = "claude-cli haiku (local subscription, not the gateway)"


def load_requests(path=REQUESTS_PATH):
    with open(path) as file:
        return [json.loads(line) for line in file if line.strip()]


def field_matches(field, gold_value, request, ids):
    got = request.get(field)
    if gold_value is None:
        return got is None and not any(item.get("field") == field for item in request.get("unresolved", []))
    if field != "type" and gold_value not in ids:  # a name, not an id: must be left unresolved
        return got is None and any(item.get("field") == field and item.get("text", "").lower() == gold_value.lower()
                                   for item in request.get("unresolved", []))
    return got == gold_value


def score(cases, outputs, ids):
    totals = {field: 0 for field in FIELDS}
    core = strict = 0
    rows = []
    for case, request in zip(cases, outputs):
        gold = case["change"]
        hits = {field: field_matches(field, gold.get(field), request, ids) for field in FIELDS}
        for field, hit in hits.items():
            totals[field] += hit
        core += all(hits[field] for field in CORE_FIELDS)
        strict += all(hits.values())
        rows.append((case, request, hits))
    return {"n": len(cases), "fields": totals, "core": core, "all": strict}, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="call the gateway model (needs AI_GATEWAY_API_KEY)")
    parser.add_argument("--record-cli", action="store_true", help="record missing fixtures with `claude -p`")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    parser_module.load_dotenv()  # from core/llm.py
    if args.live and not os.environ.get("AI_GATEWAY_API_KEY"):
        sys.exit("--live needs AI_GATEWAY_API_KEY in the environment")
    cases = load_requests()
    registries = parser_module.load_registries()
    outputs, sources = [], set()
    for case in cases:
        call = cli_call if args.record_cli else None
        surface, meta = parser_module.call_model(case["utterance"], live=args.live, call=call)
        sources.add(meta["recorded_by"] if meta["source"] == "fixture" else f"live: {meta['recorded_by']}")
        outputs.append(parser_module.parse(case["utterance"], as_of=case.get("as_of"), registries=registries))
    ids = {row[0] for table in registries.values() for row in table.get("rows", [])}
    result, rows = score(cases, outputs, ids)
    print(f"mode: {'live' if args.live else 'fixtures'}; answers from: {sorted(sources)}")
    print(f"core (type+part+to_supplier exact): {result['core']}/{result['n']}")
    print(f"all fields exact:                   {result['all']}/{result['n']}")
    for field in FIELDS:
        print(f"  {field:14s} {result['fields'][field]}/{result['n']}")
    for case, request, hits in rows:
        if args.verbose or not all(hits.values()):
            wrong = [field for field, hit in hits.items() if not hit]
            shown = {k: v for k, v in request.items() if k in FIELDS or k == "unresolved"}
            print(f"{case['id']} miss={wrong}\n   gold={case['change']}\n   got ={shown}")
    return result


if __name__ == "__main__":
    main()
