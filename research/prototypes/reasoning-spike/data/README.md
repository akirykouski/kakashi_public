# KVA hackathon synthetic dataset

Fictional supplier-change scenario for the "AI brain for industry" hackathon (Turin, 14 Nov 2026). A Turin tier-1 supplier machines aluminium bracket BR-220 (drawing Rev C) for program STL-Torino-27 for the customer Stellantis. Billet supplier Alluminio B is two weeks late, and an engineer files ECN-26-0147: take the billet from Meccanica C.

## Provenance

Synthetic, authored by the team before the event. The customer is Stellantis by name. Its requirement document is an illustrative excerpt: the wording is invented, and each requirement is numbered by the real IATF 16949 clause it supplements. All other companies, people, part numbers and document numbers are fictional. No real company text is used. IATF 16949 clause numbers are referenced by number only, never quoted. Licence: CC BY 4.0.

## Layout

| path | content |
|---|---|
| `sources/*.md` | 10 documents. File name = `doc_id`. Header fields: doc_id, type, revision, effective_date, owner, status |
| `eval/change_requests.jsonl` | 20 requests: `id, category, request_text, part, change_type` |
| `eval/gold.jsonl` | one row per request: `id, expected_verdict, expected_blockers, must_not_cite`, optional `cleared` |
| `eval/dev.jsonl` | 4 development requests with gold in the same object, for harness tuning only (see Dev set) |
| `eval/RULES.md` | rule slugs used in the gold, with meaning and examples |
| `eval/invariants.json` | per-document regex invariants on the source facts the gold depends on |
| `eval/canonical.json` | every row pinned: verdict, part, change_type, request regexes, exact (kind, rule, evidence docs) multiset, cleared rules, must_not_cite quotes |
| `MANIFEST.lock` | sha256 of every file in `sources/`, `eval/` and `README.md` (tamper lock) |
| `validate.py` | stdlib-only integrity check |
| `test_validate.py` | mutation tests for the validator |

Categories: 5 `direct_conflict`, 6 `inference_only` (2 to 3 hop chain), 4 `stale_rule_trap`, 3 `missing_data`, 2 `clean_control`.

## Gold schema

- `expected_verdict`: `blockers_found` | `no_blockers_found` | `needs_info`
- `expected_blockers[]`: `{kind: blocker|inferred|question, rule, claim, evidence: [{doc_id, quote}], owner (questions only)}`
  - `blocker`: stated in a document. `inferred`: needs a chain across documents. `question`: data missing, an owner is named.
- `must_not_cite[]`: `{doc_id, quote}` superseded or non-authoritative statements. A system that uses them as support fails the case.
- `cleared[]`: `{claim, evidence}` blockers that must NOT be raised because a newer fact removed them.
- Every `quote` is an exact literal substring of `sources/<doc_id>.md`.
- Gold lists the core expected items. A system may find more. Extra items are judged on evidence validity.

## Dev set

`eval/dev.jsonl` holds 4 development rows (`DEV-01` direct_conflict, `DEV-02` inference_only, `DEV-03` clean_control, `DEV-04` missing_data). Use them ONLY to tune the harness (prompts, parsing, retrieval). Never report them as eval results and never tune against the frozen 20.

Each line is one JSON object, request fields and gold fields together:

- Request fields: `id` (`DEV-NN`), `category`, `request_text`, `part`, `supplier`, `change_type`. `supplier` is the supplier name as written in `request_text`; it exists so overlap with the frozen 20 can be checked.
- Gold fields, identical to `gold.jsonl`: `expected_verdict`, `expected_blockers[]`, `must_not_cite[]`, optional `cleared[]`.
- Every quote is a literal substring of `sources/<doc_id>.md`. Rule ids, claim fidelity and verdict consistency are checked by the same code path as the frozen gold.
- No overlap with the frozen 20: no identical `request_text`, and no `(part, supplier, change_type)` triple equal to a frozen request (the supplier of a frozen request is every known supplier name found in its text). The dev rows are not pinned in `canonical.json`; their integrity comes from the semantic checks and the lock.

## Source map

| doc_id | role | status |
|---|---|---|
| ASL-TO-2026-04 | approved supplier list, per part x plant x customer, declares itself complete | controlled |
| DWG-BR220-RevC | drawing, 6082-T6, yield >= 250 MPa, SC-01 | effective |
| DWG-BR220-RevB | drawing, 6061-T6, yield >= 240 MPa | superseded trap |
| CP-BR220-R3 | control plan, line 30 = SC-01 | controlled |
| CSR-STL-2026-02 | OEM requirements, source change clause 8.5.6.1 | controlled |
| 8D-25-031 | open 8D at Meccanica C, cracks at fastener holes, 6061-T6 | open |
| EML-SQ-2026-0814 | probation email | superseded by 1105 |
| EML-SQ-2026-1105 | audit passed (Italian), also restates stale 6061 value | informal |
| PRC-DEV-007 | deviation procedure, max 2000 pieces, 6 weeks | controlled |
| BOM-STL-TORINO-27 | links BR-220 and BR-180 to the program | controlled |

## Validation

```
python3 data/validate.py                              # exit 0 = all checks pass, 1 = failure
python3 data/validate.py <copy> [<ontology README>]   # validate another copy of the data dir
python3 data/validate.py --no-lock                    # semantic layer only (what the tests use)
python3 data/validate.py --relock                     # rewrite MANIFEST.lock, only after all semantic checks pass
python3 data/test_validate.py                         # mutation tests (or: python3 -m unittest data.test_validate)
```

`validate.py` (stdlib only) checks:

- Shape: 20 requests, category counts 5/6/4/3/2, ids match gold in order, source headers present, `doc_id` equals file name, verdicts consistent with blocker kinds.
- Quotes: every `doc_id` exists, every quote is a literal substring of its document and at least 20 characters long. A quote may not be both evidence and `must_not_cite`.
- Rule ids: every gold `rule` (blockers and cleared) is in the allowed set = ids parsed from `../ontology/README.md` (second CLI argument overrides the path; a missing file is an error) UNION the slugs in `eval/RULES.md`.
- Names: no real OEM or tier-1 name in any text file under `data/` (sources, eval, README, RULES, json), word-boundary, case-sensitive for short or common words. `validate.py` and `test_validate.py` are excluded because they must name them.
- Claim fidelity: every digit-bearing token of a claim (numbers, alloy designations, doc and part ids) must appear in one of that item's quotes, its doc ids or the request text.
- Source invariants: `eval/invariants.json` holds per-document `must_contain`, `must_not_match` and `exactly` (count) regexes for the facts the gold depends on (for example BR-220 has one ASL approval, Rev B is SUPERSEDED, the 8D is OPEN). Every source must have an entry.
- Canonical rows: `eval/canonical.json` pins EVERY gold row. Exact verdict, request `part` and `change_type`, regexes that `request_text` must match (supplier, part, quantity, weeks), the exact multiset of `(kind, rule, evidence doc_ids)` items, the exact cleared rules and the exact `must_not_cite` quote set. A missing or extra item fails.
- Pinned headers: each source's `doc_id`, `revision`, `status`, `effective_date` header lines are pinned in `invariants.json` (`header`), plus the 8D supplier, alloy, failure mode and status lines.
- Date and authority logic: `invariants.json` `_pairs` encodes that the superseded or informal document is older or lower-authority than the controlled one (Rev B vs Rev C, the 0814 vs 1105 emails, the informal emails vs the controlled records).
- Claim words: every claim shares at least 2 content words (4+ letters, not stopwords) with its quotes, the request text or its named owner. Cleared items need a rule, a claim and non-empty evidence.
- Dev set: 4 rows (one per category), same quote, rule, claim and verdict checks as the gold, no overlap with the frozen 20 by `request_text` or by `(part, supplier, change_type)`.
- Allowlist: only the known files may exist under `eval/` and `sources/` (one `sources/<doc_id>.md` per key of `invariants.json`).
- Tamper lock (layer 1, checked after the semantic layer so authoring errors keep meaningful messages): `MANIFEST.lock` is `{path: sha256}` over `README.md`, `sources/*`, `eval/*`. Any changed, missing or unlisted file fails. The semantic layer (layer 2) still catches authoring mistakes even after a relock.
- Anti-gaming: `inference_only` rows need an inferred item citing at least 2 distinct docs; positive evidence may not come from a doc whose header status is SUPERSEDED; `stale_rule_trap` rows need a non-empty `must_not_cite`.

### What the semantic layer does and does not prove

`eval/canonical.json` is derived from the frozen gold: it pins each row's verdict, rule ids, evidence doc ids and quote counts (not the claims or quotes themselves, except `must_not_cite`), plus request regexes, `part` and `change_type`. So the semantic checks guard the **internal consistency of a FROZEN set** (no silent drift, no quote that is not in a source, no claim unsupported by its quotes). They are NOT an independent oracle for whether the gold answers are correct: a wrong answer written into gold and canonical together would pass.

The independence guarantee is organisational, not computational: the gold was authored by a different agent than the one that authored the ontology (`../ontology/`). The only coupling between the two is the rule-id vocabulary parsed from `ontology/README.md`. Treat agreement between a system built on the ontology and this gold as evidence for that reason, not because `validate.py` passes.

Changing a source fact on purpose means updating `invariants.json` and `canonical.json` in the same commit.

### Relocking (human-reviewed step)

After an intentional edit run `python3 data/validate.py --relock`. It refuses to write unless every semantic check passes, prints one `relock diff: added|changed|removed <file>` line per file, then rewrites `MANIFEST.lock`. **Any relock must be reviewed in the commit diff:** read the `MANIFEST.lock` hunks against the files you meant to change, and reject the commit if a file changed that you did not touch. Never relock to silence a lock mismatch you cannot explain. The lock does not cover `validate.py` and `test_validate.py`, review those diffs directly.

## Known limits of the validator

- The semantic layer is lexical. It pins rule ids, evidence doc ids, quote counts, request patterns and source lines, but it does not understand claim polarity: a gold claim rewritten from "has no approval" to "has an approval" with the same words passes `--no-lock`. The byte lock (`MANIFEST.lock`) catches any such edit; a relock must be reviewed in the commit diff.
- The lock does not cover `validate.py` and `test_validate.py` themselves.
- Adversarial history: three falsifier rounds (59 + 20 mutations). Final state: lock layer 100%; semantic layer catches every mutation that changes a rule, a document fact, a date, an authority, a request or a quote, except the claim-polarity class above.
