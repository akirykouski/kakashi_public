# Fix 5: alias table for grounding (finding 5 of EXTRACTION_real.md)

Real text names entities as written ("DEMO", "Autoliv", "the Tier 3 supplier"). The grounding check required the entity id or the first two words of its registry name in the quote, so true Ford facts went to review.

## What changed
- `core/extract.py`: a registry table (`parts`, `suppliers`) may carry `"aliases": {entity_id: [strings]}`. `grounded()` accepts a fact if the id, the old name rule, or any alias appears in the quote. Alias match is case-insensitive and whole-word (`has_alias`). No fuzzy matching; without an alias nothing changes.
- `core/aliases.py` (onboarding helper). `list`: facts in review as "ungrounded", each with candidate aliases found in the quote (pieces of the registry name, ALL-CAPS tokens, "Tier N supplier", mid-sentence capitalised words). `accept ENTITY "alias" --by NAME`: refuses unless the alias is written in at least one pending quote of that entity, writes it to the registry, re-checks the queued facts and moves the now grounded ones to kept. Only a person's `accept` adds an alias.
- `bench/llm.py`: minimal fix, the CLI's JSON array of events is read by taking `type == "result"`.
- `tests/test_aliases.py` (4 tests): word boundary ("demo" in "demonstration" does not ground), alias scoped to its own entity, candidates, re-check.

## Aliases added (data_real/registries.json) and why
| Entity | Alias | Where it is written in the documents |
|---|---|---|
| SUP-AUTOLIV | `Autoliv` | FORD-573-18V806 "Autoliv Automotive Safety Products", "Autoliv, the non-AFS driver airbag module Tier 1 supplier" |
| SUP-DEMO | `DEMO` | "the Tier 3 supplier (DEMO)" |
| SUP-EISSMANN | `Eissmann` | "the Tier 2 supplier (Eissmann)" |
| PART-AIRBAG-COVER | `plastic cover` | "may contain a plastic cover that was improperly injection-molded". Judgement call by the person: the Ford quote never says "airbag cover" in the span the model chose. Weakest alias; it is only safe because no other part is named "plastic cover" in these four documents. |

Aliases were confirmed through the CLI after the first run (the person flow). `list` offered `Autoliv`, `DEMO`, `Tier 3 supplier`, `Eissmann` as candidates; for the part it offered `Driver airbag`, `airbag`, `cover` (no phrase "airbag cover" in that quote). A guard check: `accept SUP-DEMO "Acme"` is refused (not in any pending quote).

## 1. Real documents (fresh runs, 4 docs, Sonnet)
| Metric | Baseline run A | Run 1: original registry | After CLI alias accepts (re-check of run 1) | Run 2: fresh run with aliases |
|---|---|---|---|---|
| Kept | 12 | 12 | 16 | 16 |
| Review | 4 (25%) | 4 (25%), all `ungrounded` | 0 | 0 (0%) |
| Review by reason | 4 ungrounded | 4 ungrounded (Ford: part, Autoliv, DEMO, Eissmann) | none | none |

Run 1 reproduced baseline A exactly (Adient manual 3, letter 5, Astemo 4, Ford 0 kept). Re-check turned the 4 Ford review items into kept facts without a model call.

Strict audit of the 16 facts kept in run 2 (same auditor and team as the original, not independent):
- Yes 13, partial 3, wrong **0**. Strict precision 13/16 = 0.81 (partial = 0), 0.91 with partial at half. Baseline: 11/12 = 0.92 on run A, 12 yes / 3 partial / 0 wrong over A+B.
- Partials: Adient manual MaterialChange (sentence covers design/process/facility; same as before), Autoliv concernsSupplier (it reported the anomaly, not the cause), Eissmann concernsSupplier (the Tier 2 that was not informed, not the origin). Both Ford supplier partials were already known from run B; they are the price of the `concernsSupplier` predicate, not of aliases.
- Ford: DEMO yes (the cause), airbag cover yes (the part named in the Description of the Defect).
- Model variance between runs: run 2 kept a different Adient letter / Astemo set of change types (letter now MaterialChange too, Astemo Material/Process/Packaging/Source) with the same counts. All checked against the text; correct.

Recall on the 10 rules of EXTRACTION_real.md: **5 of 10**, unchanged (1, 4, 5, 7 partial, 9 found; 2, 3, 6, 8, 10 missed: location and lead-time are not in the ontology, #3 general rule not emitted). The fix touches grounding, not recall of change rules.

Net effect: Ford, previously 0 of 4 kept, is 4 of 4 kept; review share 25% to 0%; no wrong fact added.

## 2. Synthetic traps (bench/extract_eval.py, data_long, registries without aliases)
| | Baseline | This run |
|---|---|---|
| Precision | 0.97 | **0.97** (32/33 found correct; the one wrong is 8D-25-031, as before) |
| Recall | 0.91 | **0.94** (33 of 35 found; misses CSR-AUR-R4 and DEV-121, one each) |
| Traps taken | 0 of 15 | **0 of 15** |
| Sent to review | 0 | 0 |

Recall differs by model variance only (grounding is unchanged for these registries: no `aliases` keys). Part of the model calls were cached from an earlier identical attempt of the same run the same session (bench/cache, 39 entries, same code). Bench results files rewritten by the eval were reverted, not committed.

## 3. Tests and checks
- `pytest tests -q`: **19 passed** (15 old + 4 new), exit 0.
- `core/check.py --scenario main | main_after_audit | elv | silence`: exit 0, 0, 0, 0. Blockers: main R1a (supplier conditional), main_after_audit R1b (no approval for BR-220 at the plant) plus customer approval, elv R2 (CoatingChange on CL-115), silence "No blocker found". Same as README.

## Risks
- An alias is a free string a person adds; a too generic one ("cover", "supplier") would ground wrong facts. Guards: must appear in a pending quote, whole word, per entity. No check that an alias is unique across entities: two entities with alias "Tier 3 supplier" would both ground. `plastic cover` above is such a judgement call.
- Grounding accepts a mention, not a role: `concernsSupplier SUP-AUTOLIV` is grounded by any quote containing "Autoliv" (see the two partials). Aliases do not change that.
- The `accept` command rewrites registries.json in the standard JSON layout (the committed file is hand-compacted); aliases in the file were inserted inline to keep the diff small.
- Re-check works on the saved review lists (`data_real/out/*.json`). Facts already written to a factlog queue are not touched.
