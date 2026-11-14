# One gold format for two worlds

Both worlds are synthetic. They are imported side by side and **never pooled as facts**: the same ids (8D-25-031, BR-180, BR-220, BR-310) mean different things in world M and world A. Scores are computed per world; a pooled number is only ever a sum of per-world counts over requests, never a run over merged facts.

Source: `eval/worlds/SOURCE.txt` (private repo commit). Re-import: `python eval/tools/import_worlds.py <torino_kakashi checkout>`.

## Files

| Path | What |
|---|---|
| `eval/worlds/M/` | World M (Valsangone): `docs/`, `meetings/`, `registries.json`, `facts.jsonl`, `corpus.jsonl` (the 46 sources the model baselines read), `requests_native.jsonl` (36 requests with the author's gold) |
| `eval/worlds/A/` | World A: `sources/` (10 documents), `change_requests.jsonl`, `gold.jsonl` (the author's gold), `RULES.md`, `canonical.json`, `invariants.json`, `dev.jsonl` (4 dev requests; the only set we may tune on) |
| `eval/gold/M.jsonl`, `eval/gold/A.jsonl` | The two golds in the one format below. These are the files that get re-golded and frozen. |

## Gold record

```json
{"id": "CR-01", "world": "A", "category": "direct", "category_native": "direct_conflict",
 "as_of": "2026-11-14", "request_text": "...", "change_hand_parse": null,
 "verdict": "blockers_found", "verdict_source": "author",
 "findings": [{"rule": "B_NO_SOURCE_RELEASE", "rule_u": "U_SOURCE_RELEASE", "key": "BR-220",
               "kind": "blocker", "inferred": false, "claim": "...", "evidence": [{"doc_id": "...", "quote": "..."}]}],
 "must_not_cite": [{"doc_id": "...", "quote": "..."}],
 "cleared": [{"rule": "B_SUPPLIER_NOT_QUALIFIED", "rule_u": "U_SUPPLIER_STANDING", "key": "Meccanica C"}]}
```

- `rule` is the author's native id, kept unchanged. `rule_u` is the unified id from the table below. **A finding matches on (`rule_u`, `key`)**, keys compared case-insensitively after trimming.
- `kind`: `blocker` | `question` | `not_covered`. A's `inferred` kind is a blocker with `inferred: true`.
- `verdict`: `blockers_found` (any blocker) | `needs_info` (no blocker, at least one question) | `no_blockers_found` | `not_covered` (no rule covers the request; no gold item uses it yet).
- `inferred`: the finding needs two or more documents combined. Feeds "recall on inferred findings" (methodology §5).
- `must_not_cite`: superseded or informal quotes that must not be used as authority. `cleared`: rules that must **not** fire because what triggered them was superseded.

## Rule vocabulary mapping

| Unified | World M | World A | Why they are the same check |
|---|---|---|---|
| `U_SUPPLIER_STANDING` | R1a supplier qualification (blocker) | `B_SUPPLIER_NOT_QUALIFIED` (only in `cleared`) | Both ask whether the supplier as a whole may receive new business (M: qualification status in the supplier register; A: probation by e-mail). Neither looks at the part. |
| `U_SOURCE_RELEASE` | R1b part approval (blocker), key `supplier|part|customer` | `B_NO_SOURCE_RELEASE` (blocker), `Q_SOURCE_RELEASE_UNKNOWN` (question); key = part | Both check approval of a source for one part (A adds plant and supplier location). A splits blocker/question by whether a complete controlled list covers the scope; M is closed-world everywhere and has no question form. Same check, so one id; `kind` carries the split. |
| `U_CUSTOMER_APPROVAL` | R2 customer approval (PPAP), key = customer id | `B_CUSTOMER_APPROVAL_REQUIRED`, key = customer code | Both: the change falls under a customer requirement reached through part → program/customer → clause, so written customer approval is needed before shipment. Inferred in both worlds. |
| `U_OPEN_ISSUE` | R3 open supplier issue on the part's alloy, key = 8D id | `B_OPEN_8D_SAME_ALLOY`, key = 8D id | Both: the supplier has an open 8D whose failure mode fits the part although no document links the 8D to the part. Inferred in both. M's core emits it as a "warning"; both golds count it as a finding, so it is scored as a blocker. |
| `U_RESTRICTED_SUBSTANCE` | R5 restricted substance (coating → substance → law → market), key = substance | — | No A counterpart: world A has no coating or law documents. |
| `U_MATERIAL` | R6 material capability / special characteristic, key = material id | `B_MATERIAL_MISMATCH`, key = part | Both: the offered or requested material does not meet the material the drawing in force requires. M compares capability and yield minimum; A compares grade designation. Keys differ by world (M names the material, A the part) because each world has at most one per request; matching is within a world only. |
| `U_MEASURED_VALUE` | — | `special_characteristic_violation` (NEW in A), key = SC id | A measured value fails a special characteristic. M has no measured-value rule. |
| `U_DEVIATION_LIMIT` | — | `deviation_limit_exceeded` (NEW in A), key = procedure id | A deviation request exceeds the procedure's limits. M has no deviation-cap rule. |
| `U_MISSING_EVIDENCE` | R7 missing evidence → question, key = what is missing (`material_certificate`, `supplier_record`, `coating_substances`, `material_data`) | `Q_NO_MATERIAL_CERT`, key `material_certificate` | Both are questions, not violations: required evidence is not in the documents. A only has the certificate case; M's other R7 keys have no A counterpart. |

## Decisions made while converting (mechanical, no gold content changed)

1. **M verdict is derived**, not authored: M's gold has no verdict field. Rule: any blocker → `blockers_found`; else any question → `needs_info`; else `no_blockers_found`. With M's kinds (R7 question, all others blocker) no M request is `needs_info`, because every M request with an R7 finding also has an R2 or R1b blocker. The same rule reproduces all 20 of A's authored verdicts (checked by the import script).
2. **M `inferred`** = rule in {R2, R3, R5}, M's own pre-registered definition (`docs/benchmarks/core/PREREGISTRATION.md`). **A `inferred`** = A's `kind: inferred`.
3. **A keys** are added by the eval owner (A's gold has rule and claim, no key), one entity per rule, read from the request or claim: source release and material → part; customer approval → customer code found in the claim (STL for all nine); open 8D → 8D id; certificate → `material_certificate`; measured value → `SC-01`; deviation → `PRC-DEV-007`; supplier standing → `Meccanica C`. A has at most one finding per rule per request, so the key changes nothing for the gold; it only stops a model finding with the right rule but a wrong entity from counting as a hit.
4. **A `as_of`** = 2026-11-14 (A's requests carry no date; every A document is dated on or before it).
5. **A categories** renamed to the methodology's five: direct_conflict → direct, inference_only → inferred, stale_rule_trap → stale, missing_data → missing, clean_control → clean. The native name stays in `category_native`.
6. **M has no `must_not_cite` or `cleared`** (not authored). The `must_not_cite` metric is computed on world A only. Adding them to M would be new gold and is for the re-gold step, not this import.
7. Not imported: engine code (`core/`, `ontology/`, `prep/spikes/`), `data_real/` (real third-party documents), M's generator `data/world.py`.

World A's `CSR-STL-2026-02` names the real OEM it imitates and states that its wording is invented. It is synthetic text; flagged here so the team can decide whether to rename before the pitch.
