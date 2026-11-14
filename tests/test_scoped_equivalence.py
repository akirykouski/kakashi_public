"""Request-scoped reasoning must give the same card as closing the whole snapshot.

For every request we can find in the repo, the card from a scoped projection (core/project.py scope_facts) must
equal the card from the full projection: findings (rule, severity, title, evidence leaves and premises),
not_checked, contested, past decisions, maintenance, verdict and decision row. Only timings and record ids may
differ. A difference means the scope is too small: fix scope_facts, never this test.

Request sets
  * data/scenarios.json                          (world M, default fact log)
  * data/requests.jsonl                          (world M)
  * eval/parses/M_hand.jsonl, A_hand.jsonl       (C* requests on each eval world's own fact log)
  * RANDOM_REQUESTS random requests over data/registries.json (world M), fixed seed
"""
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "tools"))

from core import check, project, rules  # noqa: E402
from core.project import Projection  # noqa: E402

RANDOM_REQUESTS = 60
RANDOM_TYPES = ("SourceChange", "SubTierSupplierChange", "LocationChange", "MaterialChange", "CoatingChange",
                "SpecialProcessChange", "ProcessChange", "DesignChange", "PriceChange")
VOLATILE = ("timings_ms", "record_id")


def card_of(request, scoped):
    card, _, projection = check.evaluate(dict(request), record=False, scoped=scoped)
    assert (projection.scope is not None) == scoped
    if scoped:
        assert projection.scoped_count <= projection.asserted_count
    return json.loads(json.dumps({key: value for key, value in card.items() if key not in VOLATILE},
                                 sort_keys=True, default=str))


def assert_same(request_id, request):
    full = card_of(request, scoped=False)
    scoped = card_of(request, scoped=True)
    if full != scoped:
        keys = sorted(key for key in full if full.get(key) != scoped.get(key))
        pytest.fail(f"{request_id}: scoped card differs from full card in {keys}: request {request}")


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def scenario_requests():
    out = []
    for item in json.load(open(ROOT / "data" / "scenarios.json")):
        out.append((f"scenario:{item['id']}", check.scenario(item["id"])))
    return out


def file_requests():
    out = []
    for item in load_jsonl(ROOT / "data" / "requests.jsonl"):
        request = dict(item["change"])
        request.setdefault("as_of", item.get("as_of") or check.DEFAULT_AS_OF)
        out.append((f"requests:{item['id']}", request))
    return out


def random_requests(count=RANDOM_REQUESTS, seed=14):
    registries = json.load(open(ROOT / "data" / "registries.json"))

    def ids(name):
        return [row[0] for row in registries[name]["rows"]]

    parts, suppliers, sites = ids("parts"), ids("suppliers"), ids("sites")
    materials, coatings = ids("materials"), ids("coatings")
    generator = random.Random(seed)
    out = []
    for number in range(count):
        change_type = generator.choice(RANDOM_TYPES)
        request = {"type": change_type, "part": generator.choice(parts),
                   "as_of": generator.choice(["2026-11-14", "2026-10-01", "2026-12-20", "2027-03-01"])}
        if change_type in ("SourceChange", "LocationChange"):
            request["to_supplier"] = generator.choice(suppliers)
            if generator.random() < 0.5:
                request["from_supplier"] = generator.choice(suppliers)
        if change_type == "SubTierSupplierChange":
            request["at_supplier"] = generator.choice(suppliers)
            request["to_supplier"] = generator.choice(suppliers)
        if change_type == "MaterialChange":
            request["new_material"] = generator.choice(materials)
        if change_type == "CoatingChange":
            request["new_coating"] = generator.choice(coatings)
        if generator.random() < 0.4:
            request["site"] = generator.choice(sites)
        out.append((f"random:{number:02d}", request))
    return out


WORLD_M = scenario_requests() + file_requests() + random_requests()


@pytest.fixture(autouse=True)
def scoped_closures_really_scoped(monkeypatch):
    """Else a scoped check reuses the cached full closure of the same snapshot (the warm path) and proves nothing."""
    monkeypatch.setattr(project, "REUSE_FULL", False)


@pytest.fixture(scope="module")
def default_world():
    saved_log, saved = check._LOG, dict(rules._projections)
    check._LOG = None
    rules._projections.clear()
    yield
    check._LOG = saved_log
    rules._projections.clear()
    rules._projections.update(saved)


@pytest.mark.parametrize("request_id,request_", WORLD_M, ids=[item[0] for item in WORLD_M])
def test_scoped_card_equals_full_card(default_world, request_id, request_):
    assert_same(request_id, request_)


@pytest.mark.parametrize("world", ["M", "A"])
def test_scoped_card_equals_full_card_eval_worlds(world):
    import run_core
    saved_log, saved = check._LOG, dict(rules._projections)
    try:
        gold = load_jsonl(ROOT / "eval" / "gold" / f"{world}.jsonl")
        run_core.use_world(world, [item["as_of"] for item in gold])
        hand = {row["id"]: row for row in load_jsonl(ROOT / "eval" / "parses" / f"{world}_hand.jsonl")}
        typed = 0
        for item in gold:
            change = run_core.resolve(dict(hand[item["id"]]["change"]))
            if not change.get("type"):
                continue                         # schema gap: the core is never called (run_core does the same)
            assert_same(f"{world}:{item['id']}", change)
            typed += 1
        assert typed > 0
    finally:
        check._LOG = saved_log
        rules._projections.clear()
        rules._projections.update(saved)


def test_scope_is_smaller_than_the_snapshot():
    from core.project import request_entities
    request = check.scenario("main")
    full = Projection(check.memory(), request["as_of"])
    scoped = Projection(check.memory(), request["as_of"], scope=request_entities(request))
    assert scoped.scoped_count <= full.scoped_count
    assert scoped.current_facts == full.current_facts


def test_warm_full_closure_is_recomputed_on_acceptance(monkeypatch):
    from core import factlog
    monkeypatch.setattr(project, "REUSE_FULL", True)
    log = rules.extend_log(factlog.default_log())
    project.clear_cache()
    warmed = project.warm(log, "2026-11-14")
    assert Projection(log, "2026-11-14").cache_hit
    scoped = Projection(log, "2026-11-14", scope={"BR-220", "SUP-C"})
    assert scoped.cache_hit and scoped.graph is warmed.graph          # scoped check served by the warm closure
    log.write_record("NCR-WARM-1", "NCR", {"concernsSupplier": "SUP-C", "status": '"open"'}, source="TEST",
                     quote="NCR-WARM-1 open on SUP-C", valid_from="2026-11-01", author="PER-GALLO")
    after = Projection(log, "2026-11-14")
    assert after.snapshot_hash != warmed.snapshot_hash
    assert after.cache_hit                                               # recomputed at acceptance, not now
