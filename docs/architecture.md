# Architecture of the product core

Written 14 Nov 2026 after 10:30. The product core in `core/` is new code written today. It consolidates two
research prototypes (`research/prototypes/`, made before 10:30 and improved by Arseniy after it); every
piece carried over from a prototype says so in its commit message ("ported from research/prototypes/…").
Design source: `docs/benchmarks/crossbench/REVIEW.md` §3. Contracts: `core/contracts.py`.

```
meeting remark ──► parse.py ──► ChangeRequest
                                    │
documents ──► extract.py ──► factlog.py (proposed → person accepts → in force)
                                    │
                         snapshot.py (what is in force at as_of: supersession, document rank)
                                    │
                         project.py  (RDF graph of the request's neighbourhood + OWL 2 RL closure by rl.py,
                                      cached per (snapshot, scope); full closure for today kept warm)
                                    │
                         rules.py + explain.py ──► Findings with proof chains and verbatim quotes
                                    │
                         decision.py (decision table → allowed actions + decider; R0; coverage check)
                                    │
                         check.py ──► Card + DecisionRecord (rules version, facts in force, rules fired)
```

The language model is used in two places only: `parse.py` (remark → ChangeRequest) and `extract.py`
(document → proposed facts). Everything from `factlog.py` down is deterministic: same facts, same rules, same
request give the same card.

## Modules and owners (build day)

| Module | What | Ported from | Workstream |
|---|---|---|---|
| `ontology/lcc.ttl`, `shapes.ttl` | One ontology: Maksim's classes + 17 change types (fix/2), consequences (fix/4), sub-tier chain (fix/8), OIDA epistemic type annotation | M prototype + fixes | F |
| `factlog.py` | Append-only bitemporal log; fact rows carry `kind` (assert/mention), `rank` (1 law/customer, 2 controlled record, 3 informal), `context_quote`; agent proposals; conflict check at acceptance inside one transaction; `unclassified` queue (fix/1) | M prototype + A spike + fixes | F |
| `snapshot.py` | Facts in force at (valid time, record time): record supersession + functional-predicate resolution by rank and date; lower rank never supersedes higher; contested pairs become questions | A spike `core.py` | F |
| `project.py` | Snapshot → RDF → OWL 2 RL closure, cached by (snapshot hash, scope); same query API as the prototype `Projection`. `Projection(log, as_of, scope=entities)` closes only the request's bounded neighbourhood (`scope_facts`); `warm(log, as_of)` keeps the full closure for today, recomputed on every fact-log commit. Scoped cards equal full cards: `tests/test_scoped_equivalence.py`; latency: `docs/benchmarks/latency.md` | M prototype + ws/fast-reasoning | F |
| `rl.py` | Instance-level OWL 2 RL rules (subclass, domain/range, subproperty, inverse, symmetric, transitive, property chains) over the ontology closed once by owlrl; falls back to owlrl when the ontology or facts need more (owl:sameAs). Same graph as owlrl, triple for triple (tested) | ws/fast-reasoning | F |
| `rules.py`, `explain.py` | R1a–R8 + not_checked (fix/1) + consequence (fix/4) + sub-tier R8 (fix/8); customer approval and certificate keyed on change class; open 8D at alloy-series level behind a policy flag; completeness scoped by list; owners and policy quotes read from data, not hard-coded | M prototype + fixes + A shapes | R |
| `decision.py`, `decision_table.yaml` | Declared decision model: change class × fired rules → allowed actions + decider + rests_on; R0 fallback; formal coverage check (enumerate input sets: uncovered → person, overlaps listed); DecisionRecord with `rules_version` hash | new | D |
| `parse.py` | Remark → ChangeRequest via one structured-output call (team key, server side); names → ids by code against the registries and confirmed aliases (fix/5); unresolved names returned, never guessed | new + fix/5 | P |
| `extract.py` | Document → proposed facts; verbatim quote and context quote checks (fix/3); aliases (fix/5); blanket rules (fix/7); unclassified items (fix/1); table-aware conversion (fix/6) | M prototype + fixes | P |
| `check.py` | Pipeline + CLI + JSON for the page: request → Card + DecisionRecord | new | integration |
| `oida.py` | OIDA epistemic type (`lcc:epistemicType` of the record's class) on the request (PLAN), every finding and every evidence leaf (#26) | new | integration |
| `oida.py`, `rules_data/oida_stakes.json` | Open questions get `blocks` {part, change_type} and `urgency` = clamp(age/30·0.3 + blockers·0.2 + stakes·0.5); stakes table is data; questions sorted by urgency (#27). Runs after the decision: never changes rules or the table | new | integration |

Data: `data/` holds the synthetic company (Valsangone, fictional customers). Real third-party documents are
never committed; `data_real/SOURCES.md` lists their public URLs.
