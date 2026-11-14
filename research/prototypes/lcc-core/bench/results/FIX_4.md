# Fix 4: consequence of an unapproved change, quoted from the customer's own document

Real manuals name what happens if a change ships without approval (Adient: New Business Hold, notification to the IATF registrar, financial consequences). The card now says so, in the customer's words, and only when such a fact exists.

## What changed
- `ontology/lcc.ttl`: class `ConsequenceType`, individuals `NewBusinessHold`, `RegistrarNotification`, `Chargeback`, `ControlledShipping`, object property `hasConsequence` (CustomerRequirement to ConsequenceType). It is not an inferred predicate; the extractor may assert it.
- `core/extract.py`: `hasConsequence` in the predicate list given to the model, the four types in the glossary and in the known ids. The code checks are unchanged (quote verbatim, predicate in ontology, id known).
- `core/rules.py`: R2 blocker carries `consequences` (type, label, source, verbatim quote, fact id), read from asserted facts only. Empty list when the requirement states none.
- `core/check.py`: "Consequence if shipped: ... [DOC: "quote"]" under the R2 blocker, one line per distinct quote.
- Synthetic world: `data/world.py` CSR-AUR-R4 gets clause 7.5 and three facts, quotes literally in the text. `data/build.py` rerun, `data/validate_world.py` passes (513 facts, 0 errors). `data_long/docs/CSR-AUR-R4.md` got the same clause spliced in (filler untouched, so the baseline documents stay comparable).
- `bench/llm.py`: JSON-array output of the CLI handled (take `type=="result"`).
- `tests/test_core.py`: one new test (consequence quotes are in the source; nothing for non-R2 findings).

## Card (main scenario, as of 2026-11-05)
```
[BLOCKER] R2: SourceChange on BR-220 needs written customer approval (PPAP resubmission) before shipping, per CSR-AUR-R4
  ...
  - CSR-AUR-R4 requiresCustomerApprovalFor SourceChange  [CSR-AUR-R4: "a change of source"]
  Consequence if shipped: Chargeback or financial consequences  [CSR-AUR-R4: "will charge back all resulting costs"]
  Consequence if shipped: New business hold  [CSR-AUR-R4: "may place the supplier on New Business Hold"]
  Consequence if shipped: Notification to the IATF registrar  [CSR-AUR-R4: "may notify the supplier's IATF registrar"]
```
`main_after_audit` shows the same three lines under the R2 blocker that stays.

## 1. Real documents (fresh run, `data_real`, Sonnet)
| Metric | Value |
|---|---|
| Facts kept | 13 (Adient manual 6, Adient letter 5, Astemo 2, Ford 0) |
| Sent to review | 2 of 15 = 13% (Ford, both "ungrounded": part id and supplier name not in quote; as in EXTRACTION_real.md) |
| Wrong facts, strict audit | **0** |
| Partial | 1 (manual MaterialChange: the sentence also covers design, process, facility) |
| Recall on the 10 rules | **6 of 10** (rules 1, 3, 4, 5, 7, 9; misses 2, 6 location, 8, 10 lead times). Was 5 of 10: rule 3 ("advance notification and written approval prior to all product or process changes") was found this run. Run-to-run variance is real: Astemo gave 2 facts this run, 4 before. |
| Consequence facts found | **3**, all from one sentence, ADIENT-SSM-Q-R10 "Failure to do so will result in the supplier being placed on New Business Hold Status (respectively MQR 2 level), a formal notification to the IATF16949 or ISO 9001 registrar, and/or potential financial consequences." |
| Consequence facts correct | 3 of 3: NewBusinessHold yes, RegistrarNotification yes, Chargeback partial (the text says "financial consequences", not chargebacks; the label reads "Chargeback or financial consequences"). The sentence follows "Adient requires advance notification and written approval prior to all product or process changes", so it is the unapproved-change consequence. |
| Consequence facts missed | at least 2 in the same manual: line 1269 "Any charges incurred from Adient customers due to supplier issues will be communicated and passed on to the supplier in the form of a supplier chargeback" (not change-specific, correctly not taken) and 4.13 MQR 3 / New Business Hold criteria (KPI escalation, not change control, correctly not taken). The two Adient letter and Astemo documents state none. |

One quote carries three facts, so on a real customer the card prints three types in one line when the quote is shared (the check.py grouping), not three copies.

## 2. Synthetic traps (`bench/extract_eval.py`, data_long, fresh)
| | Baseline | This run |
|---|---|---|
| Precision | 0.97 | 0.95 (35 found, 2 wrong extras: 8D-25-031 concernsMaterial MAT-6082-T6, DEV-121 concernsCoating COAT-ZNNI; neither touches the new predicate) |
| Recall | 0.91 | 0.92 (38 gold, 3 missed: 8D-25-031 concernsPart BR-310, CSR-AUR-R4 requiresNotificationFor SourceChange, DEV-121 permitsChangeType CoatingChange) |
| Traps taken | 0 of 15 | **0 of 15** |
| New R4 consequence facts | n/a | 3 of 3 extracted, none wrong; the filler already contains "New business hold" and "Chargebacks" sections about KPI escalation and complaints, and no fact was taken from them |

The two extras are model variance on facts that were already in the gold set; the gold is now 38 facts (was 35) because of the three new ones. Result files in `bench/results/` were left at the pre-fix baseline; this table is the record.

## 3. Checks
- `pytest tests -q`: 16 passed.
- `data/validate_world.py`: exit 0, 513 facts, 0 errors.
- `core/check.py --scenario main | main_after_audit | elv | silence`: exit 0, 0, 0, 0.

## Not done
- No lead-time predicate and no location change type: 4 of the 5 real-doc recall misses are these, untouched here.
- `ControlledShipping` exists in the ontology and glossary but no document in either set states it, so it is unmeasured.
- The consequence is tied to the requirement, not to a change type. An unapproved material change and an unapproved source change show the same lines.
- Real-document audit is one reader, as in EXTRACTION_real.md.
