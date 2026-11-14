# PREP spike: reasoning core

Written 13 November 2026, before the event. Throwaway code that checks whether the
design in `docs/plan/01-solution.md` holds on the BR-220 scenario. It is not the
product: no server, no extraction, no interface, no LLM call. Whether any of it is
reused on the day, and how that is disclosed, is open decision D1.

| File | What it checks |
|---|---|
| `core.py` `snapshot()` | "In force" is a pure function of the fact set: supersession, authority tiers, stale mentions, contested facts, time travel |
| `core.py` `closure()`, `check()` | OWL 2 RL closure plus SHACL shapes give blockers and questions |
| `core.py` `Explainer` | Any inferred triple gets a proof tree ending in quoted facts, with no per-axiom code |
| `run_scenario.py` | 53 assertions on the above, including that every quote of the scenario facts is a literal substring of its `data/sources` document |
| `crosscheck_gold.py` | Runs the reasoner on CR-01 and compares its blocker/question ids with `data/eval/gold.jsonl` CR-01 (set comparison, exit 1 on mismatch; out-of-scope gold ids are listed in the file) |

Run from the repo root:

```
uv run --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 \
    python prep/spikes/reasoning-core/run_scenario.py
```

```
uv run --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 \
    python prep/spikes/reasoning-core/crosscheck_gold.py
```

The scenario describes the frozen `data/` plant: doc ids DWG-BR220-RevC, CP-BR220-R3, BOM-STL-TORINO-27,
CSR-STL-2026-02, ASL-TO-2026-04, 8D-25-031, EML-SQ-2026-0814/1105, plant TO1, customer STL. The 8D is on
EN AW-6061-T6 and the part on 6082-T6, so `B_OPEN_8D_SAME_ALLOY` is derived by the named series-level rule
SERIES-8D (see `ontology/README.md`), not by an alloy match.

Result on 14 Nov 2026 (macOS arm64): `run_scenario.py` exit 0, 56 checks passed; `crosscheck_gold.py` exit 0,
5 ids equal the gold set for CR-01. State 1 has 40 facts in force, 980 triples after closure, and the
snapshot, closure and validation together take about 250-340 ms.

Not covered: contested facts are reported but the "evaluate both alternatives"
step from the design is not implemented; `owl:hasKey` is not exercised; nothing
here measures a realistic plant-sized graph (a separate test saw 33,214 triples
close in 4.2 s).
