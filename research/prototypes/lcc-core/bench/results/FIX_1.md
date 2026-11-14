# FIX 1: catch-all for requirements the ontology cannot express

Finding 1 of `EXTRACTION_real.md`: obligations that fit no change type or predicate were silently dropped (4 of the 5 recall misses).

## What changed
- `core/extract.py`: the model may return an `unclassified` list (verbatim quote + one-line summary) besides `facts`. Each quote goes through the same `find_quote` check as a fact; a quote not in the document is discarded and counted in `unclassified_rejected`. Facts, predicate check, id check and grounding check are untouched.
- `core/factlog.py`: new table `unclassified` (review queue, status `proposed`). `core/project.py` keeps the rows in `projection.unclassified`; they are never added to the graph, so the reasoner never sees them. `data/unclassified.jsonl`, if present, is loaded by `default_log`.
- `core/rules.py::not_checked`: items whose source document the part is subject to (the scope R2 uses) and that is not superseded. `check()` is unchanged.
- `core/check.py`: a NOT CHECKED section (document, quote, obligation) after the findings, and `not_checked` in `--json`.
- `bench/llm.py`: reads the `result` event when the CLI prints a JSON array.
- `tests/test_core.py`: one test (listed for the scope, never reasoned, empty for an unknown part).

## Measure 1: real documents (fresh cache, same registry, Sonnet via `claude -p`)

| | Before (fresh rerun of old code) | After |
|---|---|---|
| Facts proposed | 16 | 16 |
| Kept | 12 | 12 (identical set, same quotes) |
| Wrong (strict audit vs quote and document) | 0 wrong, 1 partial | 0 wrong, 1 partial (same facts) |
| Review (facts) | 4 of 16 (25%), all "ungrounded" (Ford) | 4 of 16 (25%), all "ungrounded" (Ford) |
| Unclassified items, all with a verbatim quote | 0 | 10 (Adient manual 3, Adient letter 2, Astemo 5, Ford 0); 0 rejected by the quote check |
| Items needing a person | 4 | 14 |

Review by reason (facts): ungrounded 4; quote not found, unknown id, bad predicate 0. Unclassified: all 10 quotes verbatim.

Recall on the 10-rule spot list (rule numbers as in `EXTRACTION_real.md`):

| # | Rule | Kept fact | Catch-all item |
|---|---|---|---|
| 1 | Adient letter: third-party supplier change | yes | no |
| 2 | Adient letter: facility change | no | **no** (letter line 39 "(ii) any facility" not surfaced) |
| 3 | Manual 4.2: notification + approval for all product or process changes | no | **no** (general sentence not emitted) |
| 4 | Manual: sub-supplier | yes | no |
| 5 | Manual: process change | yes | no |
| 6 | Manual: manufacturing or shipping location | no | **yes** "Change in manufacturing or shipping location" |
| 7 | Manual 4.5.2 PPAP for design, material, process, facility | yes (partial) | no |
| 8 | Manual: SCR 180 days before | no | **yes** "at least 180 days prior to planned changes" |
| 9 | Astemo: Tier 2/3 suppliers | yes | no |
| 10 | Astemo: 6 months before start of production | no | **yes** "6 months prior to the start of production" |

Covered by a kept fact: **5 of 10** (unchanged). Covered by a catch-all item: **3 of 10** (#6, #8, #10). Together **8 of 10**. Still missed: #2, #3 (both expressible-sentence misses, not ontology gaps).

Audit of the 10 unclassified items: 10 of 10 quotes are real obligations in the document. Weaknesses: 1 quote duplicates a kept fact's quote (letter "packing, marking, shipping, price or date or place of delivery", summary adds "design/specifications", which the quote does not contain); 1 summary overreaches (Adient "Discovery that a supplier has not notified", summary adds MQR escalation); 1 Astemo item is a record-keeping rule, not a change rule.

## Measure 2: synthetic traps (`data_long`, 8 documents, 35 gold facts, fresh cache, extraction only; bench conditions not rerun)

| | Documented baseline | Fresh baseline | After run 1 | After run 2 |
|---|---|---|---|---|
| Precision | 0.97 | 0.971 (33/34) | 0.943 (33/35) | 0.943 (33/35) |
| Recall | 0.91 | 0.943 (33/35) | 0.943 | 0.943 |
| Traps taken | 0 of 15 | 0 | 0 | 0 |
| Review | | 1 | 0 | 0 |

The one extra false positive in both after-runs is `DEV-121 concernsCoating COAT-ZNNI` (deviation mentions the coating; not in gold); the fresh baseline did not produce it. Unclassified items on the synthetic set: 6 (CSR-AUR-R3 1, CSR-AUR-R4 3, LAW-ELV 1, NCR-26-017 1), 0 rejected; 2 of 6 are change-related (90 days notice before a planned change, deviation limits), 4 are general statements (sub-supplier responsibility, approval per part and site, answer time of 10 working days, hardness data per delivery).

## Measure 3: tests and scenarios

| Command | Exit |
|---|---|
| `pytest tests -q` (after, 16 tests) | **0** (16 passed) |
| `core/check.py --scenario main` | **0** |
| `core/check.py --scenario main_after_audit` | **0** |
| `core/check.py --scenario elv` | **0** |
| `core/check.py --scenario silence` | **0** |

The old code gives exit 0 for all four scenarios. Output diff against the old code: `main`, `main_after_audit`, `silence` identical (apart from timings); `elv` has the same two R2 blockers in swapped order (order of equal-severity findings is not stable). No NOT CHECKED section appears in the scenarios because `data/unclassified.jsonl` does not exist; the section is exercised by the new test.

## Honest limits
- One run per condition on real documents; the model is not deterministic, so 8 of 10 has no interval.
- The 0 wrong audit is by the same author as before; kept facts are byte-identical to the baseline, so the audit is inherited.
- The catch-all raises review load from 4 to 14 items on 4 documents (about 3.5 per document); a person must dismiss or classify them. No UI for dismissing exists yet (`review='dismissed'` is only a status value).
- Scope in `not_checked` is "documents the part is subject to"; for the real Adient and Astemo documents there is no part in memory, so the card section is not demonstrated on real data.
- Precision on the synthetic set dropped 0.971 to 0.943 in two runs (one extra fact); small n, may be the prompt change.
