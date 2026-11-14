# Fix 3: two-span quotes (context_quote + quote)

Problem (EXTRACTION_real.md, finding 1): on real documents all 12 kept quotes were list fragments ("Change in sub-supplier"); the obligation sits in the lead-in sentence above. The quote proved the change type exists, not that approval is required.

## Change
- A fact may carry `context_quote` (the governing sentence or heading) plus `quote` (the item). `core/extract.py`: schema, prompt ("when the span is a list item, table row or heading fragment, also give the governing sentence, verbatim, <= 400 chars"), `find_context`, `check_fact`.
- Code checks, never relaxed: both spans are literally in the document (whitespace may differ; stored text is the document's own); both lie in the chunk the model saw; the context starts before the quote; the quote starts at most 1500 characters after the context ends (`CONTEXT_MAX_GAP`). A context that runs into the quote ("...after any of: a change of source") is accepted because both spans stay verbatim. Any failure sends the whole fact to review with its own reason.
- Storage: `facts.context_quote` (nullable) in `core/factlog.py`; `to_log_facts` and `bench/extract_eval.py` pass it through. `core/explain.py` renders `"...<context>..." -> "<quote>"`, so `core/check.py` shows both.
- `bench/llm.py`: takes the `type == "result"` element when the CLI prints a JSON array (the minimal fix).
- `bench/run_extract_real.sh` now `cd`s to its own repo (it was hard-wired to the main checkout). `bench/fix3.sh` wraps the uv python command.
- Tests: `tests/test_context_quote.py` (7 cases: both verbatim, invented context, context after quote, too far, outside the chunk, no context, context running into quote).

First attempt required the context to end before the quote starts. It sent the 4 CSR-AUR-R4 facts to review (the model gave the whole sentence "7.1 ... after any of: a change of source"), dropping recall to 0.80. The overlap relaxation fixed that; no verbatim check was touched.

## Measurements (all model calls fresh: caches cleared, prompt changed)

### 1. Real documents (`bench/run_extract_real.sh`, two fresh runs, model is not deterministic)
| Metric | Baseline | Run 1 | Run 2 |
|---|---|---|---|
| Kept | 12 | 8 | 10 |
| Review | 4 (all Ford ungrounded) | 4 (Ford) | 2 (Ford) |
| Review by reason | ungrounded 4 | ungrounded 4 | ungrounded 2 |
| Facts with context_quote | 0 | 6 of 8 | 7 of 10 |
| Wrong facts (strict audit) | 0 (1 partial) | 0 | 0 |
| Quote alone states the rule | 0 of 12 | 2 of 8 (Astemo) | 2 of 10 (Astemo) |
| context_quote + quote states the rule, strict (approval or application obligation explicit) | n/a | 5 of 8 | 4 of 10 |
| Same, lenient (a "will not make any change ... except" prohibition counts) | n/a | 8 of 8 | 10 of 10 |
| Recall on the 10 rules | 5 of 10 | 4 of 10 | 4 of 10 |

- Where the context fixes it: Adient manual, `"Examples of product and process changes, that require Adient approval, include (but are not limited to):"` -> `"Change in sub-supplier"`. This is exactly the target case; both runs.
- Adient letter: the context the model picks is a truncated opening ("(b) Seller will not make any change relating to Supplies - including without", or "prohibited changes include, without limitation, changing (i) any third"). It states a prohibition; the "without prior written approval" clause is further on. Counted partial under the strict rule.
- Recall: both runs lost rule #7 (manual 4.5.2, partial in baseline, MaterialChange only) and the manual's MaterialChange fact. Not caused by the check: no new context-related review item in run 2, and run 1's 8 kept came with 0 context rejections. Model variance in how many facts it emits per chunk (kept varied 8 to 10 over identical code). Treat 4 vs 5 of 10 as noise, not a regression signal.
- Ford is unchanged: all review items are grounding artefacts (registry names), not related to quotes.

### 2. Synthetic traps (data_long, extraction scoring only, `extract_eval.extract_one` + `score_document`; the downstream bench rerun was skipped)
| | Baseline | Fix 3 |
|---|---|---|
| Precision | 0.97 | 0.94 (32 of 34) |
| Recall | 0.91 | 0.91 (32 of 35) |
| Traps taken | 0 of 15 | 0 of 15 (0 proposed either) |
| Facts with context_quote | 0 | 7 of 34 |

The two extras (8D-25-031 concernsMaterial MAT-6082-T6, DEV-121 concernsCoating COAT-ZNNI) carry no context_quote and are over-assertions of the same kind as the baseline's one extra; extra count 1 -> 2 is within run-to-run noise on 35 gold facts, not caused by the new check. Review: 1 (BR-310 ungrounded, same class as baseline). An earlier run of the first (strict-order) variant gave 0.93 / 0.80; the loss was exactly the 4 R4 facts the overlap fix restored.

### 3. Tests and scenarios
- `pytest tests -q`: 22 passed (15 existing + 7 new; includes `test_every_quote_is_in_its_source`).
- `core/check.py --scenario main | main_after_audit | elv | silence`: exit 0 / 0 / 0 / 0. Blocker sets: main R1a R1b R6 R2 (+R3 warn, R7 question); main_after_audit R1b R6 R2; elv R2 x2 + R5; silence none. Unchanged (these use hand-written `data/facts.jsonl`, rules untouched; `test_core` asserts the same sets).

## Verdict
Mechanism works and is safe: on the target case (lead-in obligation + bullet item) the reviewer now sees the obligation sentence and the item, both code-verified. Real-document quote usefulness moves from 0 of 12 to 4-5 strict, 8-10 lenient. Net kept count and recall did not improve (and fell within noise); this fix addresses evidence quality, not recall.

## Risk
1. The model chooses a truncated context ("including without") that is verbatim but incomplete; the code cannot judge sufficiency. A prompt line asking for the full clause could fix it, not tried.
2. A context may be far from the item (up to 1500 chars) and from a different list; the reviewer reads both, but a wrong pairing is not detected.
3. Grounding still tests the quote alone, so Ford facts still go to review.
4. Model variance across runs is of the same size as the effect on kept count; 2 real runs, one auditor, same caveats as EXTRACTION_real.md.
