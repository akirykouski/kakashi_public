# Fix 7: blanket rules in the extraction prompt

Change (`core/extract.py`, `BLANKET_RULE`, appended to both instruction variants): one generic invented example of a blanket rule ("written consent before any change to its products or processes") and the instruction to emit one fact per covered change type, each with the same verbatim quote. Checks untouched. `bench/llm.py`: parse the JSON-array CLI output (take type=="result").

## Real documents (fresh run, `bench/extract_real.py`)
| Metric | Before | After |
|---|---|---|
| Facts proposed / kept / review | 16 / 12 / 4 | 16 / 12 / 4 (Ford 4, all grounding artefacts) |
| Kept per doc (manual / letter / Astemo / Ford) | 3 / 5 / 4 / 0 | 4 / 5 / 3 / 0 |
| Strict audit, kept semantically correct | 11 yes, 1 partial = 0.92 | 11 yes, 1 partial = 0.92 |
| Recall, 10-rule list | 5 of 10 | **6 of 10** (#3 flipped to yes) |

- #3 flipped: manual emits Process, Material, Source, Coating, all quoting "Adient requires advance notification and written approval prior to all product or process ...".
- Over-generalisation: 1 partial, 0 wrong. Adient CoatingChange is inferred from "all product or process changes" (coating is not named). Partial, defensible.
- Side effect on quotes: the blanket quote now wins the dedupe key, so the specific list-item quotes for the manual's sub-supplier and for Astemo's "Tier 2, 3 suppliers" are gone. Astemo SourceChange/ProcessChange now quote "Application and approval must be made to Astemo." (the definition sentence, right under "changes in manufacturing/work methods, change of suppliers' contractors"). Those are the correct obligation sentences, arguably better evidence than the old fragments (Finding 1), but the quote alone is less specific per change type.
- Still missed: #2, #6 (location), #8, #10 (lead time), all ontology gaps. #7 still partial.

## Synthetic traps (`bench/extract_eval.py`, data_long)
| | Baseline | After |
|---|---|---|
| Precision | 0.97 | 0.94 (33 found, 2 wrong) |
| Recall | 0.91 | 0.94 (33 of 35 found, 2 missed) |
| Traps taken | 0 of 15 | 0 of 15 |

The 2 wrong extras are `concernsMaterial` (8D-25-031) and `concernsCoating` (DEV-121); neither is a requiresCustomerApprovalFor/notification fact, so not blanket over-generalisation. Misses: CSR-AUR-R4 requiresNotificationFor SourceChange, DEV-121 permitsChangeType CoatingChange. One sample per condition; Sonnet is not deterministic, so 0.97 to 0.94 is within a 1-fact swing (35 gold facts).

## Checks
pytest tests -q: 15 passed. core/check.py --scenario main, main_after_audit, elv, silence: all exit 0.

## Risk
- Single run each, one auditor (same as EXTRACTION_real.md). 
- Blanket example may push coating/packaging/schedule over-emission on documents with vague "all changes" wording; the quote is shared, so a reviewer sees one sentence behind several facts.
