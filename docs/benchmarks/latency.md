# Core latency on large companies (branch ws/fast-reasoning)

**Exploratory, not pre-registered.** Measured on 14 Nov 2026, one machine (Apple M1, 8 cores, Python 3.12.13,
rdflib 7.6.0, owlrl 7.6.2), with nothing else heavy running during the final run. The method was not fixed in
advance. Do not read these numbers as a claim about another machine or another company.

## What changed

1. **Request-scoped reasoning** (`core/project.py`: `Projection(log, as_of, scope=entities)`, `scope_facts`).
   The snapshot is still taken over every fact, so what is in force, contested, history and provenance stay the
   same. Only the graph that is closed shrinks to the request's bounded neighbourhood:
   forward closure from the request's entities (every chain in `lcc.ttl`, plus transitive `suppliesTo` / `feedsInto` /
   `supersedes`, runs forward), one step backward into it (approvals, qualifications, capabilities,
   certificates, 8Ds/NCRs, laws via `appliesInMarket`), then forward again. Shared entities (plants, customers,
   markets, materials, people, documents) are never walked backward, except along `appliesInMarket`. Readers that
   scan a class globally always get all of it: policies, completeness statements, decisions, commitments,
   deviations and `Q-*` keys. The source documents of the facts in scope are included too. `check.evaluate` is
   scoped by default; `LCC_SCOPED=0` gives the old path.
2. **`core/rl.py`**: the ontology is closed once by owlrl and cached. After that only the instance rules the
   ontology can trigger run, semi-naively: subclass, domain/range, subproperty, inverse, symmetric, transitive,
   property chains and eq-ref. If the ontology uses a construct that is not implemented, or a functional property
   gets two values (owl:sameAs), it falls back to owlrl. `LCC_REASONER=owlrl` gives the old reasoner.
3. **Warm cache**: `project.warm(log, as_of)` computes the full closure for today when the server starts
   (`web/server.py`). It is computed again on every fact-log commit (`FactLog.on_commit`: acceptance, a record
   written by a person, a review). When a scoped check finds the full closure of its snapshot in the cache, it
   uses that instead. Scoped closures are cached by (snapshot hash, facts in scope).

## Latency: per-request check time, cold

`python eval/tools/latency.py --units 0,300,1000 --full-limit 11`. Each request is timed from `check.evaluate`
to the finished card (snapshot, closure, rules, decision, OIDA, memory). The closure cache is cleared before
every request, as for a request with a new `as_of`, and the warm path is off (`REUSE_FULL = False`). The
requests are the 11 scenarios in `data/scenarios.json`. Distractor units come from `data/scale.py`, ported from
`research/prototypes/lcc-core/data/scale.py` and written to a temp dir, never to `data/`. Each unit adds a
supplier, a program, 2 parts, 2 approvals, a qualification, a capability, often a certificate, an 8D, 2 part
cards and a meeting. Units share the real hubs: customers, MKT-EU, plants, materials and people.

| size | facts in force | facts closed per request (after) | before: whole snapshot, owlrl (= main) | scoped, owlrl | **after: scoped, rl.py** |
|---|---|---|---|---|---|
| product data | 569 | 505 | median 510 ms, p95 683 ms | 466 / 534 ms | **50 / 204 ms** |
| +300 units | 14,600 | 505 | median 7,669 ms, p95 8,355 ms | 756 / 956 ms | **339 / 453 ms** |
| +1000 units | 47,326 | 505 | median 22,707 ms, p95 24,482 ms | 1,452 / 1,611 ms | **1,175 / 1,317 ms** |

Closure time alone (median), before → after: 480 → 29 ms (product data), 7,293 → 79 ms (+300),
21,513 → 85 ms (+1000). The scope stays at about 505 facts whatever the size of the company. At 1000 units
most of what remains (~1.1 s) is outside the closure: the snapshot over 47k facts, building the scope, and the
memory/OIDA passes over all facts in force. That is the next thing to optimise; this branch does not touch it.

At every size, all 11 scenario cards were identical across the three configurations (`differing: []`,
11 scenarios x 3 configurations per size). Arseniy's 127 s at 47k facts came from a different machine; on this one the same
size takes 22.7 s before.

With the warm cache, a check on today's snapshot never closes anything; the closure was computed at server
start or at the last acceptance.

## No degradation: merge gate (main bc0e6ab before, this branch after, same machine)

| world | requests | precision | recall | inferred recall | exact | verdict acc. | clean false alarm | must_not_cite hits | differing requests |
|---|---|---|---|---|---|---|---|---|---|
| M, C* (before = frozen run `eval/results/frozen/M_Cstar.jsonl`) | 36 | 1.00 → 1.00 | 0.976 → 0.976 | 1.00 → 1.00 | 34/36 → 34/36 | 0.972 → 0.972 | 0.00 → 0.00 | n/a | none |
| A, C* (before = frozen run `eval/results/frozen/A_Cstar.jsonl`) | 20 | 0.765 → 0.765 | 0.813 → 0.813 | 1.00 → 1.00 | 10/20 → 10/20 | 0.70 → 0.70 | 0.00 → 0.00 | 0.00 → 0.00 | none |
| M_scale (8x), C* (before = main bc0e6ab run here) | 36 | 1.00 → 1.00 | 0.976 → 0.976 | 1.00 → 1.00 | 34/36 → 34/36 | 0.972 → 0.972 | 0.00 → 0.00 | n/a | none |

"Differing" compares, per request, the scored findings, the core verdict, `not_covered` and errors. The
`run_core.py` C* latency (mean 0.02 s before and after) does not measure the closure: `use_world` builds the
full projection for each date before the requests are timed. The latency table above is the measurement.

- Scenario cards, main vs branch, with every card key except timings and the record id: 11/11 identical.
- pytest: main 175 passed, 1 skipped. Branch 293 passed, 1 skipped (the same 175 + 118 new).

## Equivalence proof (`tests/test_scoped_equivalence.py`)

The test compares whole cards, not only findings. The reference is the full snapshot closed by owlrl (the old
path). The candidate is the scoped projection closed by `core/rl.py` (the new default). The fields compared are
findings (rule, severity, title, entities, evidence leaves and premises with quotes), verdict, decision row,
not_checked, contested, past decisions and maintenance. Only `timings_ms` and `record_id` are excluded.

| request set | cards compared |
|---|---|
| `data/scenarios.json` | 11 |
| `data/requests.jsonl` | 36 |
| random requests over `data/registries.json` (seed 14: 9 change types, 4 dates, random sites, materials, coatings, from-suppliers) | 60 |
| `eval/parses/M_hand.jsonl` on eval world M | 36 |
| `eval/parses/A_hand.jsonl` on eval world A (4 schema-gap rows have no change type; the core is never called for them) | 16 |
| `eval/parses/M_hand.jsonl` on `eval/worlds/M_scale` (8x) | 36 |
| **total** | **195** |

Graph level: the closure from `core/rl.py` equals owlrl's triple for triple on world M at 4 dates and on eval
worlds M and A (6 tests). One more test checks the warm cache: a check is served from the warm closure, and
the closure is recomputed when a record is written. Each latency run also compares cards across the three
configurations: 11 scenarios per size, including +300 and +1000 units.

During development the test caught two scopes that were too small: (1) the sub-tier scenario, where the OIDA
badge of an evidence leaf reads the class of its source document, so source documents are now in scope;
(2) eq-ref `owl:sameAs` triples that owlrl writes, which rl.py now writes too. Both were fixed in the scope or
the engine. The test was not changed.

## `reasonable` (Rust OWL 2 RL), optional item

Tried `reasonable` from PyPI in a separate venv; not installed in the product. On the product data's full graph
(538 facts): owlrl 460 ms, reasonable 18 ms. The result is **not** the same: 77 instance triples owlrl derives
are missing, among them property-chain conclusions the rules read (`BK-330 subjectTo CSR-AUR-R3`,
`containsSubstanceVia`, `deliveredTo`). 58 triples differ in literal form (e.g. `status "open"`). It is not a
drop-in, so it is not used. `core/rl.py` gives the same graph as owlrl at about 25 ms on that graph.

## Not done

- The non-closure cost at large sizes (snapshot over all facts, memory/OIDA passes): ~1.1 s at 47k facts.
- The scope rules (hub classes, `appliesInMarket`) are written for `lcc.ttl` and today's readers. A new rule
  that reaches records through a plant, customer or material must extend `HUB_BACKWARD` in `core/project.py`.
  The equivalence test fails if it does not.
