"""Command line: check a change against company memory.

  python core/check.py --part BR-220 --type SourceChange --to SUP-C [--as-of 2026-11-14] [--json]
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
from rules import check  # noqa: E402


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario")
    parser.add_argument("--part")
    parser.add_argument("--type", default="SourceChange")
    parser.add_argument("--to", dest="to_supplier")
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
        change = {key: getattr(args, key) for key in ("type", "part", "to_supplier", "site", "new_material",
                                                       "new_coating") if getattr(args, key)}
        as_of = args.as_of
    log = default_log()
    projection = Projection(log, as_of)
    started = time.time()
    findings = check(projection, change)
    elapsed_ms = (time.time() - started) * 1000
    if args.json:
        print(json.dumps({"change": change, "as_of": as_of, "findings": findings}, indent=2))
    else:
        print_report(projection, change, findings, elapsed_ms)


if __name__ == "__main__":
    main()
