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

VOLATILE = ("timings_ms", "record_id")


def strip(card):
    return json.loads(json.dumps({key: value for key, value in card.items() if key not in VOLATILE},
                                 sort_keys=True, default=str))


def timed(request, scoped):
    project.clear_cache()
    started = time.perf_counter()
    card, _, projection = check.evaluate(dict(request), record=False, scoped=scoped)
    return (time.perf_counter() - started) * 1000, strip(card), projection


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
    full_times, scoped_times, differing, scope_sizes = [], [], [], []
    facts_in_force = None
    for index, scenario_id in enumerate(scenarios):
        request = check.scenario(scenario_id)
        scoped_ms, scoped_card, projection = timed(request, True)
        scoped_times.append(scoped_ms)
        scope_sizes.append(projection.scoped_count)
        facts_in_force = projection.asserted_count
        if index < full_limit:
            full_ms, full_card, _ = timed(request, False)
            full_times.append(full_ms)
            if full_card != scoped_card:
                differing.append(scenario_id)
        print(f"units {units} {scenario_id}: scoped {scoped_ms:.0f} ms ({projection.scoped_count} facts)"
              + (f", full {full_times[-1]:.0f} ms" if index < full_limit else ""), flush=True)
    return {"units": units, "facts_in_force": facts_in_force, "scope_facts_median": statistics.median(scope_sizes),
            "full": summary(full_times), "scoped": summary(scoped_times),
            "scoped_same_subset": summary(scoped_times[:len(full_times)]),
            "compared": len(full_times), "differing": differing}


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
