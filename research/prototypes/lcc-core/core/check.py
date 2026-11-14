"""Command line: check a change against company memory.

  python core/check.py --part BR-220 --type SourceChange --to SUP-C [--at SUP-I] [--as-of 2026-11-14] [--json]
  python core/check.py --scenario main      (scenarios in data/scenarios.json)

Never prints "approved": either blockers with sources, or "no blocker found in memory".
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from explain import render  # noqa: E402
from factlog import default_log  # noqa: E402
from project import ROOT, Projection  # noqa: E402
from rules import check, not_checked  # noqa: E402


def print_not_checked(items):
    if not items:
        return
    print("\nNOT CHECKED (stated in the documents, no ontology predicate for it; a person must read these):")
    for item in items:
        print(f"  - [{item['source']}] \"{item['quote'].replace(chr(10), ' ')}\"")
        if item.get("summary"):
            print(f"    obligation: {item['summary']}")


def print_report(projection, change, findings, elapsed_ms):
    print(f"Change: {json.dumps(change)}")
    print(f"Memory as of {projection.as_of}: {projection.asserted_count} facts, "
          f"{len(projection.graph)} triples after reasoning ({projection.reasoning_ms:.0f} ms); check {elapsed_ms:.0f} ms")
    counted = [item for item in findings if item["severity"] != "info"]
    if not counted:
        print("No blocker found in memory. This is not an approval.")
    for item in findings:
        owner = f"  owner: {projection.label(item['owner'])}" if item.get("owner") else ""
        print(f"\n[{item['severity'].upper()}] {item['rule']}: {item['title']}{owner}")
        if item.get("note"):
            print(f"  note: {item['note']}")
        for step in item["evidence"]:
            print(render(step, 1))
        grouped = {}
        for consequence in item.get("consequences", []):  # one line per quote, however many types it names
            grouped.setdefault((consequence["source"], consequence["quote"]), []).append(consequence["label"])
        for (source, quote), labels in grouped.items():
            print(f"  Consequence if shipped: {'; '.join(labels)}  [{source}: \"{quote}\"]")
    print_not_checked(not_checked(projection, change))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario")
    parser.add_argument("--part")
    parser.add_argument("--type", default="SourceChange")
    parser.add_argument("--to", dest="to_supplier")
    parser.add_argument("--at", dest="at_supplier", help="sub-tier supplier that makes the change (R8)")
    parser.add_argument("--site")
    parser.add_argument("--material", dest="new_material")
    parser.add_argument("--coating", dest="new_coating")
    parser.add_argument("--as-of", default="2026-11-14")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.scenario:
        with open(os.path.join(ROOT, "data", "scenarios.json")) as file:
            scenarios = {item["id"]: item for item in json.load(file)}
        change = dict(scenarios[args.scenario]["change"])
        as_of = scenarios[args.scenario].get("as_of", args.as_of)
    else:
        change = {key: getattr(args, key) for key in ("type", "part", "to_supplier", "at_supplier", "site", "new_material",
                                                       "new_coating") if getattr(args, key)}
        as_of = args.as_of
    log = default_log()
    projection = Projection(log, as_of)
    started = time.time()
    findings = check(projection, change)
    elapsed_ms = (time.time() - started) * 1000
    if args.json:
        print(json.dumps({"change": change, "as_of": as_of, "findings": findings,
                          "not_checked": [{key: item[key] for key in ("id", "source", "quote", "summary")}
                                          for item in not_checked(projection, change)]}, indent=2))
    else:
        print_report(projection, change, findings, elapsed_ms)


if __name__ == "__main__":
    main()
