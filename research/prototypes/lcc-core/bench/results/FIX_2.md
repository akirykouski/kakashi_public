# Fix 2: a larger change-type vocabulary, and what it costs (exploratory, not pre-registered)

Finding 2 of `EXTRACTION_real.md`: four of the five missed rules were expressiveness gaps (location twice, lead times twice). The ontology had 6 change types (Source, Material, Process, Coating, Schedule, Packaging) and no lead-time predicate.

## What was built
- `ontology/lcc.ttl`: 11 new change types, each with an `rdfs:comment` that cites its public source in paraphrase (AIAG PPAP 4th ed. section 3.1 and Table 3.1 situations; IATF 16949 clauses 8.5.6 and 8.5.6.1; AIAG CQI-9/11/12 for special processes; three types are labelled as taken from the real documents, not from IATF). Annotation `lcc:vocabLevel` (1, 2, 3) says which size offers a type to the extractor. New predicates `requiresNoticeFor` (advance notice before the change; may sit on top of an approval) and `leadTimeDays` (one quoted integer per requirement).
- `core/extract.py`: `CHANGE_VOCAB=1|2|3` selects the size; the glossary, the allowed ids and the allowed predicates follow it. `CHANGE_NOTICE=0` withholds the two notice predicates (diagnostic). `leadTimeDays` is checked as an integer 1 to 730.
- `core/rules.py`: R2 covers all new approval types (they are in `APPROVAL_CHANGE_TYPES`) and prints an info line with the lead time when a requirement has `requiresNoticeFor`. No new rule.
- `bench/llm.py`: reads the CLI's JSON array of events (take the `result` element); cache directory overridable by `LLM_CACHE_DIR`. `bench/extract_real.py`, `bench/extract_eval.py`: env knobs for output location and an extraction-only mode. `bench/run_fix2.sh <size>` runs one size with a fresh cache; `bench/scenarios_fix2.sh` compares scenario results.

Vocabularies. A = 6 original. B = 11 (+ LocationChange, ToolingChange, DesignChange, SubTierSupplierChange, TestMethodChange) and the two notice predicates. C = 17 (+ ShippingLocationChange, EquipmentChange, SoftwareChange, ProductionResumptionChange, PriceChange, SpecialProcessChange) and the two notice predicates. From B on the glossary also lists a label per type; A keeps the names-only line of the baseline.

## Results (Sonnet via `claude -p`, fresh cache per size, 2026-11-14)

Real documents (4 documents, 9 calls each size). Wrong facts: my strict manual audit of every kept fact against the text, one auditor (see limits).

| Measure | A (6) | B (11) | C (17) | B types only | C types only |
|---|---|---|---|---|---|
| Kept facts | 10 | 21 | 25 | 17 | 26 |
| To review (all Ford grounding) | 3 (23%) | 2 (9%) | 3 (11%) | 3 (15%) | 4 (13%) |
| Wrong facts | **0** | **0** | **1** | **0** | **1** |
| Partial / weak facts | 1 | 3 | 3 | 3 | 4 |
| Recall of the 10-rule spot list (yes + partial) | 4 + 1 | 8 + 1 | 8 + 1 | 6 + 1 | 7 + 0 |
| Spot-list rules still missing | 2, 3, 6, 8, 10 | 10 | 10 | 3, 8, 10 | 3, 8, 10 |

Synthetic traps (`bench/extract_eval.py` on `data_long`, 8 documents, 15 traps; extraction scoring only):

| Measure | A (6) | B (11) | C (17) | B types only | C types only |
|---|---|---|---|---|---|
| Precision | **0.97** | **0.84** | **0.85** | **0.97** | **0.97** |
| Recall | 0.91 | 0.91 | 0.94 | 0.94 | 0.94 |
| Traps taken | 0 of 15 | 0 of 15 | 0 of 15 | 0 of 15 | 0 of 15 |
| Sent to review | 2 | 1 | 0 | 1 | 1 |

Regression (same commit tree against `git archive` of the parent): `pytest tests data/test_validate.py` 95 passed, 114 subtests (at default level 2 and again at the committed default 1; exit 0); `core/check.py --scenario main | main_after_audit | elv | silence` exit 0 for all four, sorted (severity, rule) sets identical to the unchanged tree, so the blocker sets are unchanged (main R1a R1b R2 R6; after audit R1b R2 R6; elv R2 R2 R5; silence none).

## Audit notes
- The one wrong fact at size C (and at C types only): ADIENT-LTR-UC `requiresCustomerApprovalFor ShippingLocationChange`, quote ending "date or place of delivery". Place of delivery is where goods go, the type means where they ship from. The same size got the Adient manual's "manufacturing or shipping location" right for both location types.
- Partials: ToolingChange from "any production equipment" (the letter, sizes B and B-only: no equipment type at that size); Astemo MaterialChange from "when changing material manufacturers" (really a source change); `leadTimeDays 180` stated in the Adient manual for the process-change steps, stored for the whole requirement; Astemo "Software input to parts" and the 12-month restart come from a matrix whose marker column `pdftotext` dropped, so approval is not provable from text alone (Finding 5 of the earlier report).
- Not fixed by any size: Astemo's "6 months before start of production" (rule 10) sits in the third chunk and was never emitted; the Ford grounding failures (names and part ids, Finding 4).
- Gain from the sizes: Adient letter went from 5 to 8-11 facts and the manual from 3 to 6-11, mostly new location, tooling, design, test-method and sub-tier facts. Sub-supplier changes now land on `SubTierSupplierChange` instead of `SourceChange`; the old `SourceChange` facts are gone for those quotes.
- The "wrong extra" facts at B and C on the synthetic set are all `requiresNoticeFor` and `leadTimeDays` (for example "notification at least 60 days before implementation"). They state what the document says, but the gold lists only `requiresNotificationFor`, so the scorer counts them as wrong. The model emits both predicates for one clause: the two predicates overlap by design. Without the notice predicates (B and C types only) precision is back to 0.97.

## Decision (rule fixed before the run)
Largest size with 0 wrong facts on real documents, synthetic precision at least 0.95, 0 traps, review share at most 30%.

| Size | Real wrong = 0 | Synthetic precision >= 0.95 | Traps = 0 | Review <= 30% | Passes |
|---|---|---|---|---|---|
| A (6) | yes | yes (0.97) | yes | yes (23%) | **yes** |
| B (11) | yes | **no (0.84)** | yes | yes (9%) | no |
| C (17) | **no (1)** | **no (0.85)** | yes | yes (11%) | no |

**Chosen: A (6 types), the committed default (`CHANGE_VOCAB=1`).** The ontology keeps all 17 types and both predicates; the extractor offers them only when `CHANGE_VOCAB` is 2 or 3.

Post-hoc reading, not part of the rule: the sizes B and C failed on the notice predicates, not on the types. The two extra runs (types only) show B types only (11 types, no notice predicates) passes every criterion (0 wrong, 0.97, 0 traps, 15% review) with recall 6 + 1 of 10 against 4 + 1 for A, and C types only fails on the one wrong fact. Following the rule on those runs would pick 11 types without notice predicates (`CHANGE_VOCAB=2 CHANGE_NOTICE=0`). That is a different experiment run after seeing the numbers, so it is a recommendation, one line to adopt.

## Limits
- One auditor, from the team that wrote the extractor, the vocabulary and the 10-rule list. No second reader.
- 4 documents, 10 to 26 kept facts per run: one fact moves precision 4 to 10 points. One run per size; model output varies between runs (size A here kept 10 facts where the earlier report kept 12).
- Rule 3 and rule 8 (the notice and lead-time rules) are only reachable with the notice predicates, which the synthetic scorer penalises.
- Gold for the synthetic set was written for the old predicates; it was not extended for this experiment.
- `leadTimeDays` is one value per requirement; documents with a different period per change type are a gap (the extractor was told to leave it out then).
- Raw outputs: `bench/results/fix2/` (`real_<size>/`, run logs), `bench/results/extraction_long_fix2_<size>*.json|md`. Real-document outputs quote copyrighted text, see `data_real/SOURCES.md`.
