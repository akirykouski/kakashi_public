# Fact extraction on real public documents (exploratory, not pre-registered)

Question: on real text, how often are kept facts correct, how often are quotes verbatim, and what share goes to review? The synthetic long-document result was precision 0.97, recall 0.91, 0 of 15 traps (`EXTRACTION.md`).

## Setup
- `core/extract.py` unchanged (checks, prompt, ontology predicates, 20k-char chunks, Sonnet via `claude -p`). Wrapper: `bench/extract_real.py`, run by `bench/run_extract_real.sh` (exit 0). The wrapper carries its own `claude -p` adapter with the same command as `bench/llm.py`, because the installed CLI now prints a JSON array of events and `bench/llm.py` fails to parse it (`JSONDecodeError: Extra data`). `bench/llm.py` was not touched; it needs the same fix before the main bench is rerun.
- Registry: `data_real/registries.json`, written by us as onboarding input: 3 customers, generic classes (`PART-ANY`, `SUP-ANY`, `SUP-SUBTIER`, `MAT-ANY`, `COAT-ANY`) and the named parties of the Ford recall. The ontology and the six change types (Source, Material, Process, Coating, Schedule, Packaging) are the product's, unchanged.
- Documents (sources, URLs, terms: `data_real/SOURCES.md`). Tokens are chars/4.

| Doc | Type | Chars | ~Tokens | Chunks | Seconds |
|---|---|---|---|---|---|
| ADIENT-SSM-Q-R10 (supplier manual, Quality) | requirement | 55,035 | 13.8k | 4 | 170 |
| ADIENT-LTR-UC (unauthorized changes letter) | requirement | 2,960 | 0.7k | 1 | 16 |
| ASTEMO-SCM-R4 (change management guidebook) | requirement | 48,029 | 12.0k | 3 | 104 |
| FORD-573-18V806 (recall report) | evidence | 5,665 | 1.4k | 1 | 83 |
| **Total** | | 111,689 | **~28k** | 9 | |

## Numbers (run A, the registry as first written)

| Metric | Value |
|---|---|
| Facts proposed | 16 |
| Kept (passed the code checks) | 12 (Adient manual 3, Adient letter 5, Astemo 4, Ford 0) |
| Sent to review | 4 (25%), all "ungrounded" (Ford, see below) |
| Quote verbatim in source | 16 of 16 (the check is the code's; I spot-read all 12 kept quotes against the text) |
| Precision, strict, my audit: kept facts semantically correct | 11 of 12 yes, 1 partial = **0.92** (0.96 if partial counts half) |
| Predicate appropriate | 12 of 12 (all `requiresCustomerApprovalFor`; no notification-only rule was found in these documents) |
| Quote alone states the rule | **0 of 12 yes, 12 partial** (see Finding 1) |
| Recall spot check, 10 rules | **5 of 10** |
| Traps (old revisions, drafts, other divisions) | not measured; these documents carry none we could identify |

Run B (Ford only, supplier names in the registry cut to the single token the text uses): 3 kept, 1 in review. Audit: DEMO yes (the cause), Autoliv partial (it only reported the anomaly), Eissmann partial (the supplier that was not informed). That is 1 of 3 yes. Over runs A and B, 15 kept facts: 12 yes, 3 partial (manual Material in A; Autoliv, Eissmann in B), 0 wrong.

## Review by reason (run A)

| Reason | Count | Why |
|---|---|---|
| ungrounded: quote does not name `SUP-AUTOLIV` / `SUP-DEMO` / `SUP-EISSMANN` | 3 | Our registry names ("Autoliv, Tier 1 ...") did not match the grounding rule (first two words of the name must appear in the quote). Registry artefact; run B removes it. |
| ungrounded: quote does not name `PART-AIRBAG-COVER` | 1 | The check requires a part id in the quote; real text never contains our id. Inherent: parts must be onboarded by their real part numbers, which this recall report does not give. |
| quote not found / unknown id / bad predicate | 0 | |

No fact was hallucinated, and the model never reached outside the glossary.

## Recall spot check (10 change-control rules chosen before reading the output, from the sections that state them)

| # | Rule in the document | Extracted? |
|---|---|---|
| 1 | Adient letter: changing a third-party supplier needs written approval | yes (SourceChange) |
| 2 | Adient letter: changing a facility of the seller or its supplier | **no**: no change type for location |
| 3 | Adient manual 4.2: "advance notification and written approval prior to all product or process changes" | **no**: general rule, not emitted |
| 4 | Adient manual: change in sub-supplier | yes |
| 5 | Adient manual: manufacturing process change, temporary or permanent | yes |
| 6 | Adient manual: change in manufacturing or shipping location | **no**: no location type |
| 7 | Adient manual 4.5.2: PPAP and customer approval before first saleable shipment for planned design, material, process or facility changes | yes, mapped only to MaterialChange (partial) |
| 8 | Adient manual: SCR at least 180 days before the change | **no**: no lead-time predicate |
| 9 | Astemo: change of Tier 2, 3 and later suppliers | yes |
| 10 | Astemo: application 6 months before start of production | **no**: no lead-time predicate |

5 of 10. Of the 5 misses, 3 cannot be expressed in the ontology (location change twice, lead times twice: 4 of 5 are expressiveness gaps); 1 (#3) is expressible and was missed. Every rule the ontology can state was found.

## Findings
1. **Quotes are list items, not the rule.** All 12 quotes are a fragment ("Change in sub-supplier", "(iv) the nature, type or quality", a table cell of Astemo's matrix). The obligation sits one sentence above ("require Adient approval, include..."). The quote proves the change type exists, not that approval is required. A reviewer clicking the quote sees a bullet. The prompt asks for "the shortest span", which produces this.
2. **Precision holds on what is kept, but the kept set is thin.** 12 facts from 28k tokens; the Adient manual gave 3 from 14k tokens.
3. **Ontology, not model, limits recall.** Real documents regulate location, tooling, design, price, lead times, sub-supplier cascade, deviation authorisation. The six change types and the 11 predicates cover roughly the first half of the rules we sampled.
4. **Grounding check fits ids in text, not real names.** Generic part and supplier classes never appear in a quote, so facts about them need review by construction, and names must be onboarded as they are written in the document.
5. **Astemo's rule lives in a matrix.** `pdftotext` drops the marker column, so the extractor read rows as requirements. They are correct here (the matrix is the list of change points), but it is a reading the text alone cannot prove.
6. **Cost**: 9 calls, ~62k input tokens, ~4.6k output tokens, about 6 minutes wall (4 in parallel; Ford alone took 83 s on its first call).

## Five good facts
1. ADIENT-SSM-Q-R10 requiresCustomerApprovalFor SourceChange. "Change in sub-supplier" (listed under changes that require Adient approval).
2. ADIENT-LTR-UC requiresCustomerApprovalFor SourceChange. "prohibited changes include, without limitation, changing (i) any third" (party supplier ...).
3. ASTEMO-SCM-R4 requiresCustomerApprovalFor SourceChange. "Change of Tier 2, 3 and subsequent suppliers (including trading companies, suppliers of subsidiary materials)".
4. ADIENT-LTR-UC requiresCustomerApprovalFor ProcessChange. "method, or any process or software, or any production equipment used in".
5. FORD-573-18V806 concernsSupplier SUP-DEMO (run B). "the Tier 3 supplier (DEMO) made adjustments to the cover injection-molding process."

## Bad or weak facts (all of them)
| Fact | Verdict | Why |
|---|---|---|
| ADIENT-SSM-Q-R10 requiresCustomerApprovalFor MaterialChange, quote "other planned changes to design, material, process or facility" | partial | The sentence covers design, process and facility too; only the material slice is stored. Not wrong, incomplete. |
| FORD-573-18V806 concernsSupplier SUP-AUTOLIV (run B) | partial | Autoliv reported the anomaly; it is not the cause. |
| FORD-573-18V806 concernsSupplier SUP-EISSMANN (run B) | partial | Eissmann is the Tier 2 that was not informed, not the origin. |
| ADIENT-LTR-UC requiresCustomerApprovalFor ScheduleChange, quote "packing, marking, shipping, price or date or place of delivery" | yes, weak quote | Same quote as the PackagingChange fact; "date of delivery" is the schedule part, "price" has no type. |
| All 12 quotes, see Finding 1 | partial evidence | Fragment, not the obligation sentence. |

No fact was semantically wrong (0 of 15 across runs A and B). Four Ford proposals were blocked in run A by the grounding check.

## Honest limits
- One auditor, from the same team that wrote the extractor, the registry extension and the sampling of the 10 rules. No second reader; the 0 wrong is not independent.
- The registry extension was written by us after reading the documents. An onboarded real customer would supply real part numbers; run A's Ford review items show what happens without them.
- 4 documents, 16 facts: the confidence interval on 0.92 is wide (12 kept; one more bad fact moves it 8 points).
- Recall is 10 hand-picked rules, not an exhaustive gold set.
- No trap measurement; these documents hold no revision-history or draft traps we could find.
- Run B changed the Ford registry after seeing run A's result; it is a diagnostic, not a clean second run.
- Three of the four documents are copyright or marked confidential; see `data_real/SOURCES.md` before publishing any of them.
