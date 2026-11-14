"""Exploratory latency benchmark (not pre-registered): per-request check time, full vs request-scoped closure.

    python eval/tools/latency.py --units 0,300,1000 --full-limit 3 --out /tmp/lcc_latency.json

For each size: data/ itself (units 0) or data/scale.py with N distractor units in a temp dir (data/ is never
written). Every scenario of data/scenarios.json is checked cold (closure cache cleared before each request, as for
a request with a new as_of): once with the full closure (LCC_SCOPED=0 path), once scoped. At each size the two
cards must be equal (same comparison as tests/test_scoped_equivalence.py); a difference is reported.
--full-limit caps how many scenarios run the slow full path at the large sizes (minutes per request).
"""
import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "data"))

from core import check, factlog, project, rules  # noqa: E402

project.REUSE_FULL = False   # measure the cold path of every request (a new as_of), never the warm closure

VOLATILE = ("timings_ms", "record_id")


def strip(card):
    return json.loads(json.dumps({key: value for key, value in card.items() if key not in VOLATILE},
                                 sort_keys=True, default=str))


CONFIGS = {"before": (False, "owlrl"),        # main: whole snapshot, owlrl
           "scoped_owlrl": (True, "owlrl"),   # request scope only
           "after": (True, "rl")}            # request scope + core/rl.py (the default now)


def timed(request, config):
    scoped, reasoner = CONFIGS[config]
    project.REASONER = reasoner
    project.clear_cache()
    started = time.perf_counter()
    card, _, projection = check.evaluate(dict(request), record=False, scoped=scoped)
    elapsed = (time.perf_counter() - started) * 1000
    return elapsed, strip(card), projection


def p95(values):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]


def summary(values):
    return {"n": len(values), "median_ms": round(statistics.median(values), 1), "p95_ms": round(p95(values), 1)} \
        if values else {"n": 0}


def run_size(units, full_limit):
    if units == 0:
        data_dir = str(REPO / "data")
    else:
        import scale
        data_dir = scale.build_scaled(units, tempfile.mkdtemp(prefix=f"lcc_scale_{units}_"))
    log = rules.extend_log(factlog.default_log(data_dir=data_dir))
    check._LOG = log
    rules._projections.clear()
    scenarios = [item["id"] for item in json.load(open(REPO / "data" / "scenarios.json"))]
    times = {config: [] for config in CONFIGS}
    closure = {config: [] for config in CONFIGS}
    differing, scope_sizes, facts_in_force = [], [], None
    for index, scenario_id in enumerate(scenarios):
        request = check.scenario(scenario_id)
        cards = {}
        for config in CONFIGS:
            if config == "before" and index >= full_limit:
                continue
            elapsed, cards[config], projection = timed(request, config)
            times[config].append(elapsed)
            closure[config].append(projection.closure_ms)
            if config == "after":
                scope_sizes.append(projection.scoped_count)
                facts_in_force = projection.asserted_count
        if any(card != cards["after"] for card in cards.values()):
            differing.append(scenario_id)
        print(f"units {units} {scenario_id}: " + ", ".join(f"{config} {times[config][-1]:.0f} ms"
              for config in cards), flush=True)
    return {"units": units, "facts_in_force": facts_in_force, "scope_facts_median": statistics.median(scope_sizes),
            "check": {config: summary(values) for config, values in times.items()},
            "closure": {config: summary(values) for config, values in closure.items()},
            "compared": len(times["before"]), "differing": differing}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--units", default="0,300,1000")
    parser.add_argument("--full-limit", type=int, default=99)
    parser.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "lcc_latency.json"))
    args = parser.parse_args()
    results = []
    for units in [int(value) for value in args.units.split(",")]:
        limit = args.full_limit if units >= 1000 else 99
        results.append(run_size(units, limit))
        json.dump(results, open(args.out, "w"), indent=1)
        print(json.dumps(results[-1]), flush=True)


if __name__ == "__main__":
    main()
