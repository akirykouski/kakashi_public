# Fix 8: tier awareness (suppliesTo, rule R8)

## What changed
- `ontology/lcc.ttl`: `suppliesTo` (supplier -> the supplier it delivers to, one tier up), `feedsInto` (transitive super-property, so a tier-3 supplier reaches the tier-1 supplier through every hop), `requiresCustomerApprovalForSubTier` and `requiresNotificationForSubTier` (requirement -> change type, for changes made BY a sub-tier supplier). The R2 predicates are untouched, so R2 cannot fire on a sub-tier clause.
- `core/rules.py`: R8. Input `at_supplier` (the sub-tier supplier) plus `type` and `part`. It finds the approved suppliers of the part that the sub-tier feeds into, then per customer emits one finding: notice must travel up the chain to the plant (QP-14), blocker if a current customer requirement of the part (existing chain `usedIn o forCustomer o imposes`) says `requiresCustomerApprovalForSubTier` for the change type, warning if it says notification only or is silent. Evidence: one quote per tier hop (via `explain`), the approval record, the CSR clause, the QP-14 clauses. No chain on file: R7 `tier_link` question; unknown supplier: R7 `supplier_record` + `tier_link`. A change with `at_supplier` skips R2.
- `core/extract.py`: three new document predicates in the glossary (`suppliesTo` with direction spelled out, the two sub-tier requirement predicates), `feedsInto` is inferred-only, `suppliesTo` needs BOTH suppliers named in its quote, supplier grounding now uses the name before the first comma or bracket ("Autoliv, Tier 1 ..." -> "Autoliv").
- `data/world.py`: sub-tier suppliers SUP-I (heat treatment, delivers to Bormida), SUP-J (billets, delivers to Chisone), SUP-K (homogenisation, delivers to SUP-J, a 3-hop chain); documents `SUBLIST-B`, `SUBLIST-C` (sub-supplier lists, the quoted `suppliesTo` facts), `CSR-AUR-S1` (Aurelia annex on sub-suppliers, imposed via the customers registry), `QP-14` (internal procedure on sub-supplier changes). All quotes verbatim (`validate_world.py` 0 errors).
- `core/check.py --at SUP-I`, scenario `subtier`; `bench/requests.py` T01 to T03 appended (first 36 lines of `requests.jsonl` byte-identical to HEAD, so the pre-registration hash of that file no longer matches the 39-line file; the 36-line prefix does); `bench/run.py` parser gets `at_supplier` and an R8 key; `bench/score.py` gets category `subtier`; `bench/llm.py` tolerates the CLI's JSON array (take `type == "result"`).
- Tests: 7 new (22 total), including the recall pattern DEMO (tier 3) -> Eissmann (tier 2) -> Autoliv (tier 1) -> vehicle maker built as facts in memory, and the two-ended grounding check.

## Measure 1: real documents (fresh run, `bench/extract_real.py`, registry unchanged)
| Metric | Before (run A, EXTRACTION_real.md) | After |
|---|---|---|
| Facts proposed | 16 | 17 |
| Kept | 12 (Ford 0) | 13 (Adient manual 3, letter 5, Astemo 2, Ford 3) |
| Sent to review | 4 (25%) | 1 (6%): `concernsPart PART-AIRBAG-COVER`, the real text has no part id |
| Wrong facts, strict audit (mine, one auditor) | 0 | 0 |
| Partial | 1 | 2 (manual MaterialChange, Autoliv `concernsSupplier`) |
| Yes | 11 | 11 |
| Strict precision (yes / kept) | 0.92 | 0.85 (0.92 if partial counts half, both) |
| Recall, 10-rule list | 5 of 10 | 5 of 10 (same rules; the 5 misses are the same four ontology gaps plus rule 3) |

Ford tier chain: **1 of 2 links extracted, direction correct.** `SUP-DEMO suppliesTo SUP-EISSMANN`, quote "DEMO did not notify the Tier 2 supplier (Eissmann) of these adjustments." (Tier 3 delivers to Tier 2: correct direction; the quote implies the link, it does not say "delivers to".) `SUP-EISSMANN suppliesTo SUP-AUTOLIV` was not proposed: no sentence of the report names both. Plus `concernsSupplier SUP-DEMO` (the cause, yes) and `concernsSupplier SUP-AUTOLIV` (partial, it reported the anomaly). The recall report states tier numbers, not delivery relations, so the full chain needs the sub-supplier list a plant already holds (our `SUBLIST-*` shape), not the recall report.

What moved the numbers: the Ford review share fell from 4 to 1 mostly because of the grounding-name fix (the old rule needed the first two words of "Autoliv, Tier 1 airbag ..." in the quote), not because of the model. The new sub-tier requirement predicates were never used on the three requirement documents: "Change of Tier 2, 3 and subsequent suppliers" and "Change in sub-supplier" were mapped to `SourceChange` as before (they are the supplier changing its sub-supplier, which is the correct reading). Astemo kept 2 facts, run A kept 4; I cannot tell prompt effect from sampling variance with one run each. The strict precision drop comes from adding Ford facts (one partial), not from a new wrong fact.

## Measure 2: synthetic long documents (`bench/extract_eval.py`, fresh, 8 docs, 35 gold facts)
| | Baseline | After |
|---|---|---|
| Precision | 0.97 | **0.94** (32 right, 2 wrong) |
| Recall | 0.91 | **0.91** (32 of 35) |
| Traps taken | 0 of 15 | **0 of 15** |
| Sent to review | 1 | 1 |

The two wrong extras: `8D-25-031 concernsMaterial MAT-6082-T6` (also in the baseline) and `DEV-121 concernsCoating COAT-ZNNI` (new; an unrelated predicate, most likely sampling variance, not shown to be caused by this fix). Raw: `FIX_8_extraction_long.json`, `FIX_8_extraction_long_table.md`. The tracked `*_long` result files were restored to HEAD after the run (the run overwrites them).

`data/validate_world.py`: 528 facts, 50 sources, **0 errors** (510 facts before). `data/validate.py` (the separate KVA dataset): OK. `core/integrity.py`: conforms.

## Measure 3: checks and tests
| Check | Result |
|---|---|
| `pytest tests -q` | 22 passed (15 before + 7) |
| `check.py --scenario` main / main_after_audit / elv / silence / subtier | exit 0 for all five |
| Blocker sets of the four old scenarios | unchanged (same rules, severities and entities as before the change; compared as JSON) |
| Bench, gold parse -> core, 39 requests | precision 1.00, recall 1.00, exact 1.00, clean alarms 0.00 (`RESULTS_fix8.md`) |
| Bench, model parses -> core, 39 requests | precision 0.98, recall 1.00, exact 0.97; subtier T01 to T03 exact 3 of 3; same as the 36-request result before (0.98 / 1.00 / 0.97) |
| Bench conditions A and B (readers) | not rerun: the corpus changed and the 36 old rows are from the old corpus; no R8 in their rule catalogue |

Caveat as before: the same person wrote data, rules and gold, so C* = 1.00 is an upper bound. A first version of the parser prompt made `from Galvanica Eporediese` an `at_supplier` (C02 regression); the final prompt says a supplier that delivers to us directly is never `at_supplier`. T01's first wording had no part number and failed to parse; it was reworded before the final run (the first run's failure is why).

## Subtier card (`python core/check.py --scenario subtier`)
```
Change: {"type": "ProcessChange", "part": "BR-220", "at_supplier": "SUP-I"}
[BLOCKER] R8: ProcessChange at Trattamenti Termici Sangone S.r.l. (2 tiers below the plant): notice must travel up
the chain and Aurelia Automobili S.p.A. must approve in writing before shipping, per CSR-AUR-S1.
Chain: Trattamenti Termici Sangone S.r.l. -> Alluminio Bormida S.r.l. -> plant PLT-BEI   owner: Elena Gallo
  - SUP-I feedsInto SUP-B  (inferred: suppliesTo subPropertyOf feedsInto)
    - SUP-I suppliesTo SUP-B  [SUBLIST-B: "Trattamenti Termici Sangone S.r.l. (SUP-I), which delivers the treated blanks to Alluminio Bormida"]
  - APR-001 approvedSupplier SUP-B  [REG-ASL: "APR-001,SUP-B,BR-220,PLT-BEI,CUST-AUR,approved,2024-02-10,,PER-BIANCHI,"]
  - APR-001 approvedPart BR-220  [REG-ASL: ...]
  - BR-220 deliveredTo CUST-AUR  (inferred: property chain usedIn o forCustomer) [REG-PARTS, REG-PROGRAMS quotes]
  - policy QP-14  ["4.2 The supplier passes every sub-supplier change notice to Valsangone before the change is implemented."]
  - policy QP-14  ["4.3 The plant checks the notice against the customer requirement for the part and informs the customer, or asks for written approval, before the first shipment."]
  - BR-220 subjectTo CSR-AUR-S1  (inferred: property chain usedIn o forCustomer o imposes) [3 quotes]
  - CSR-AUR-S1 requiresCustomerApprovalForSubTier ProcessChange  [CSR-AUR-S1: "a change of manufacturing process or a change of coating at a sub-supplier requires written approval from Aurelia"]
```
The 3-hop case (`--part BR-310 --type ProcessChange --at SUP-K`) gives a warning (Nordhavn has no sub-tier clause) with one quote per hop: SUP-K -> SUP-J -> SUP-C -> plant PLT-PIN.

## Limits
- Ford is representable (test above) but the report alone yields only one of its two links.
- R8 is prospective: it checks a planned sub-tier change. It does not detect an unnotified change that already happened (the Ford failure itself); that needs a change log fed by the sub-supplier.
- `CSR-AUR-S1` is our own invented annex; real customers phrase sub-supplier clauses in their own way, and the extractor never used the two new requirement predicates on the real manuals.
- Tier numbers: "N tiers below the plant" counts from the plant's direct suppliers (1) downward.
- The registry change adds SUP-I..K to the glossary of every extraction and parser prompt.
