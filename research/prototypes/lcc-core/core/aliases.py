"""Onboarding helper: let a person confirm how documents write a part or supplier.

A fact whose object is a part or supplier is kept only if its quote names it. Real text names entities as
written ("DEMO", "Autoliv", "the Tier 3 supplier"), not by our ids, so such facts land in review as "ungrounded".
This tool lists them, proposes candidate aliases found in the quote, and on a person's confirmation writes the
alias into the registry (`aliases` key of its table) and re-checks the queued facts. Nothing is accepted
without a person: no fuzzy matching, and an alias must be written out in at least one pending quote.

  python core/aliases.py list   --registry data_real/registries.json --out data_real/out
  python core/aliases.py accept --registry data_real/registries.json --out data_real/out SUP-DEMO "DEMO" --by anna
"""
import argparse
import glob
import json
import os
import re
import sys

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CORE_DIR)

from extract import grounded, grounding_aliases, grounding_names, has_alias  # noqa: E402

GROUNDED_TABLES = ("parts", "suppliers")
SKIP_WORDS = {"any", "the", "and", "of", "for", "supplier", "suppliers", "tier", "part", "product", "component",
              "delivering", "customer", "class", "generic", "delivered", "sub", "that"}


def load_registry(path):
    with open(path) as file:
        return json.load(file)


def tables(registry):
    return {k: v for k, v in registry.items() if not k.startswith("_")}


def entity_name(registry, entity):
    for table in GROUNDED_TABLES:
        for row in registry[table]["rows"]:
            if row[0] == entity:
                return row[1]
    return None


def candidates(registry, entity, quote, limit=8):
    """Strings in the quote that may be the entity's written name, best first. A person confirms; we never apply."""
    found = []

    def add(text):
        text = text.strip(" ,.;:()")
        if text and text.lower() not in {c.lower() for c in found} and has_alias(text, quote):
            found.append(text)

    name = entity_name(registry, entity) or ""
    words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9-]+", name) if w.lower() not in SKIP_WORDS]
    for size in (3, 2):  # phrases of the registry name that the quote repeats
        for start in range(len(words) - size + 1):
            add(" ".join(words[start:start + size]))
    for word in words:
        add(word)
    for match in re.finditer(r"\b[A-Z]{3,}\b|\bTier \d+ (?:supplier|sub-supplier)\b", quote):  # DEMO, Tier 3 supplier
        add(match.group(0))
    for match in re.finditer(r"(?<=[a-z,] )[A-Z][a-z]{3,}\b", quote):  # mid-sentence capitalised word
        add(match.group(0))
    return found[:limit]


def load_outputs(out_dir):
    items = []
    for path in sorted(glob.glob(os.path.join(out_dir, "*.json"))):
        with open(path) as file:
            items.append((path, json.load(file)))
    return items


def pending(outputs):
    """(path, result, index, fact) for every review fact that failed only on grounding."""
    for path, result in outputs:
        for index, fact in enumerate(result.get("review", [])):
            if fact.get("reason", "").startswith("ungrounded"):
                yield path, result, index, fact


def recheck(registry, outputs):
    """Move review facts that the (updated) registry now grounds into `accepted`. Return the moved facts."""
    names = grounding_names(tables(registry))
    aliases = grounding_aliases(tables(registry))
    moved = []
    for path, result in outputs:
        keep = []
        for fact in result.get("review", []):
            if fact.get("reason", "").startswith("ungrounded") and grounded(fact["o"], fact["quote"], names, aliases):
                fact = {k: v for k, v in fact.items() if k != "reason"}
                result["accepted"].append(fact)
                moved.append((path, fact))
            else:
                keep.append(fact)
        result["review"] = keep
    return moved


def save_outputs(outputs):
    for path, result in outputs:
        with open(path, "w") as file:
            json.dump(result, file, indent=1, default=str)


def cmd_list(args):
    registry = load_registry(args.registry)
    rows = list(pending(load_outputs(args.out)))
    if not rows:
        print("no ungrounded facts pending")
    for n, (path, result, _, fact) in enumerate(rows, start=1):
        print(f"[{n}] {result['header']['id']}  {fact['s']} {fact['p']} {fact['o']}")
        print(f"    quote: \"{fact['quote'][:160]}\"")
        print(f"    candidate aliases for {fact['o']}: {candidates(registry, fact['o'], fact['quote']) or 'none found'}")


def cmd_accept(args):
    registry = load_registry(args.registry)
    entity, alias = args.entity, args.alias.strip()
    table = next((t for t in GROUNDED_TABLES if any(r[0] == entity for r in registry[t]["rows"])), None)
    if table is None:
        sys.exit(f"{entity} is not a part or supplier in {args.registry}")
    outputs = load_outputs(args.out)
    supporting = [f for _, _, _, f in pending(outputs) if f["o"] == entity and has_alias(alias, f["quote"])]
    if not supporting:
        sys.exit(f"refused: \"{alias}\" is not written in any pending quote for {entity}")
    aliases = registry[table].setdefault("aliases", {})
    if alias.lower() not in {a.lower() for a in aliases.get(entity, [])}:
        aliases.setdefault(entity, []).append(alias)
    with open(args.registry, "w") as file:
        json.dump(registry, file, indent=1, ensure_ascii=False)
    moved = recheck(registry, outputs)
    save_outputs(outputs)
    print(f"alias \"{alias}\" -> {entity} confirmed by {args.by}; re-checked {len(moved)} queued fact(s):")
    for _, fact in moved:
        print(f"  now kept: {fact['s']} {fact['p']} {fact['o']}  \"{fact['quote'][:70]}\"")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("list", "accept"):
        p = sub.add_parser(name)
        p.add_argument("--registry", required=True)
        p.add_argument("--out", required=True)
        if name == "accept":
            p.add_argument("entity")
            p.add_argument("alias")
            p.add_argument("--by", default="reviewer")
    args = parser.parse_args()
    {"list": cmd_list, "accept": cmd_accept}[args.cmd](args)


if __name__ == "__main__":
    main()
