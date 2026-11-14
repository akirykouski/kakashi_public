# Maksim's core on Arseniy's frozen gold (20 requests)

Condition: gold parse (hand-written change JSON from `request_text` only, no LLM) -> Maksim's engine (`core/`, unchanged) -> rule-id mapping -> scored by code against `arseniy_core/data/eval/gold.jsonl`. As-of date 2026-11-14 for all requests. Rerun: `crossbench/run.sh`.

Files: `crossbench/encode_world.py` (world: 162 facts from the 10 sources, every quote checked as a literal substring), `crossbench/parsed_changes.json` (20 parses + mapping class), `crossbench/run_and_score.py` (engine run, rule mapping, scoring), `results.jsonl` (per request), `data/facts.jsonl`, `data/corpus.jsonl` (generated).

## Headline

| metric | value |
|---|---|
| exact rule-set match | **8 / 20** |
| verdict accuracy | **16 / 20** |
| rule-id precision / recall | **0.68 / 0.72** (tp 21, fp 10, fn 8) |
| must_not_cite violations | **0** (no superseded source cited in any non-info finding) |
| `cleared` rules that wrongly fire | **0** (B_SUPPLIER_NOT_QUALIFIED stays off in CR-03, CR-18) |
| requests with a direct parse | 11 (exact 2, verdict 10); 6 approximate parse; 3 unsupported |

## By category

| category | n | exact | verdict | tp | fp | fn |
|---|---|---|---|---|---|---|
| clean_control | 2 | 2 | 2 | 0 | 0 | 0 |
| direct_conflict | 5 | 0 | 4 | 10 | 3 | 3 |
| inference_only | 6 | 4 | 6 | 6 | 2 | 0 |
| missing_data | 3 | 1 | 1 | 1 | 3 | 2 |
| stale_rule_trap | 4 | 1 | 3 | 4 | 2 | 3 |

## Rule mapping (Maksim -> Arseniy)

| Maksim | Arseniy | why |
|---|---|---|
| R1a (supplier conditional) | B_SUPPLIER_NOT_QUALIFIED | same concept: company-level standing forbids new parts; probation encoded as status `conditional` |
| R1b (no approval supplier x part x site x customer) | B_NO_SOURCE_RELEASE | same key; but R1b is closed-world everywhere (no completeness scope) |
| R2 blocker (customer approval needed) | B_CUSTOMER_APPROVAL_REQUIRED | same chain part -> program -> customer -> clause |
| R3 (open 8D on part's material/alloy) | B_OPEN_8D_SAME_ALLOY | same intent; Maksim matches temper or alloy, not alloy series |
| R6 (supplier not capable of drawing material / new material below SC) | B_MATERIAL_MISMATCH | capability = billet grade on the supplier's ASL rows, as Arseniy's own CR-01 encoding does |
| R7 material_certificate | Q_NO_MATERIAL_CERT | same |
| R7 material_strength | Q_NO_MATERIAL_CERT | "required test result not in documents"; ambiguous, closest |
| R7 supplier_record | Q_SUPPLIER_QUALIFICATION_UNKNOWN | in Arseniy's ontology but not in the gold vocabulary -> always counts as fp |
| R7 coating_substances | X_Q_COATING_UNKNOWN | no equivalent -> fp |
| R5 | (none) | Arseniy's plant has no restricted-substance law; never fired |
| R4 / any `info` | dropped | display of supersession history, not a finding |
| — | special_characteristic_violation, deviation_limit_exceeded, Q_SOURCE_RELEASE_UNKNOWN | not supported by engine |

Encoding choices worth knowing: suppliers are location-qualified ids (ASL: "An approval covers the named manufacturing location only"); CSR clauses mapped to the closest Maksim change type (8.5.6.1 -> SourceChange; 8.3.6.1 -> Material/CoatingChange; 8.4.2.1, 8.3.3.3, 7.1.5.3.2 -> ProcessChange); drawing Rev B facts given valid_to 2026-05-31; EML-SQ-2026-1105's restatement "BR-220 ... EN AW-6061-T6, 240 MPa" was **not** encoded (Maksim's own world encodes emails without part facts). No certificates exist in the sources, so R7 certificate fires on every source change. QP-11 in `corpus.jsonl` is a stub holding the policy quotes that `core/rules.py` hard-codes for citations (display only, no facts).

## Per request

| id | category | parse | verdict (got/exp) | fp | fn |
|---|---|---|---|---|---|
| CR-01 | direct_conflict | direct | ok | – | B_OPEN_8D_SAME_ALLOY |
| CR-02 | inference_only | approx (ProcessChange) | ok, exact | – | – |
| CR-03 | stale_rule_trap | direct (ScheduleChange) | ok, exact | – | – |
| CR-04 | clean_control | direct (ScheduleChange) | ok, exact | – | – |
| CR-05 | direct_conflict | direct | ok | Q_NO_MATERIAL_CERT | B_OPEN_8D_SAME_ALLOY |
| CR-06 | missing_data | approx (SourceChange to current source) | ok, exact | – | – |
| CR-07 | inference_only | approx (ProcessChange) | ok, exact | – | – |
| CR-08 | stale_rule_trap | unsupported | no_blockers / blockers | – | special_characteristic_violation |
| CR-09 | direct_conflict | unsupported | no_blockers / blockers | – | deviation_limit_exceeded |
| CR-10 | inference_only | direct | ok | Q_NO_MATERIAL_CERT | – |
| CR-11 | missing_data | direct (SourceChange site TO3) | blockers / needs_info | B_NO_SOURCE_RELEASE, B_CUSTOMER_APPROVAL_REQUIRED, Q_NO_MATERIAL_CERT | Q_SOURCE_RELEASE_UNKNOWN |
| CR-12 | direct_conflict | direct | ok | Q_SUPPLIER_QUALIFICATION_UNKNOWN | – |
| CR-13 | stale_rule_trap | direct (MaterialChange) | ok | B_CUSTOMER_APPROVAL_REQUIRED, Q_NO_MATERIAL_CERT | B_MATERIAL_MISMATCH |
| CR-14 | inference_only | direct (CoatingChange) | ok | X_Q_COATING_UNKNOWN | – |
| CR-15 | clean_control | unsupported | ok, exact (trivially: engine says nothing) | – | – |
| CR-16 | direct_conflict | direct | ok | Q_NO_MATERIAL_CERT | – |
| CR-17 | inference_only | approx (ProcessChange) | ok, exact | – | – |
| CR-18 | stale_rule_trap | direct | ok | – | B_OPEN_8D_SAME_ALLOY |
| CR-19 | missing_data | approx (ScheduleChange) | no_blockers / needs_info | – | Q_SOURCE_RELEASE_UNKNOWN |
| CR-20 | inference_only | approx (ProcessChange) | ok, exact | – | – |

## Misses by reason

**Engine lacks concept (5 fn, 3 fp)**
- B_OPEN_8D_SAME_ALLOY in CR-01, CR-05, CR-18: R3 matches the 8D's material to the part's temper or alloy; 6061-T6 vs 6082-T6 share only the 6xxx series. The ontology has `madeOfSeries`, R3 does not use it, and there is no "same failure feature (fastener holes)" concept.
- special_characteristic_violation (CR-08): no measured value / lot acceptance.
- deviation_limit_exceeded (CR-09): no deviation request or PRC-DEV-007 limits.
- Q_SOURCE_RELEASE_UNKNOWN (CR-11, CR-19): no completeness scope. R1b treats ASL absence as "no approval" for any site (TO3 -> blocker instead of question, and that also triggers R2 via "not already approved"); service-part scope does not exist (CR-19 has nothing to check). CR-11 accounts for 3 fp.
- CR-13 B_MATERIAL_MISMATCH: on MaterialChange the engine compares the new material only to the SC strength; with no typical yield in the documents it asks a question (R7 material_strength) instead of "6061 is not the drawing grade".

**Gold/engine policy difference (genuine disagreement, 6 fp)**
- Q_NO_MATERIAL_CERT on every source change (CR-05, CR-10, CR-16, plus CR-11, CR-13 material_strength): the gold expects it only in CR-01, CR-06, CR-18, not CR-05/10/16, though no certificate from anyone exists in the sources. Arguably gold inconsistency, arguably engine noise.
- CR-13 B_CUSTOMER_APPROVAL_REQUIRED: a material change on a drawing requirement falls under CSR 8.3.6.1 per the documents; gold lists only B_MATERIAL_MISMATCH.

**Mapping ambiguity (2 fp)**
- CR-12 R7 supplier_record -> Q_SUPPLIER_QUALIFICATION_UNKNOWN (not in gold vocabulary).
- CR-14 R7 coating_substances (no gold id).

**Encoding gap**: none detected after fixing an ASL-row regex bug in my encoder (first run silently dropped 5 approvals; reported here because it changed 4 requests).

## Caveats
- 6 parses are approximations (CR-02, 06, 07, 17, 19, 20) and 3 are unsupported (CR-08, 09, 15). 5 of the 8 exact matches rest on approximate parses or on the engine staying silent (CR-15). Direct parses only: 2/11 exact, 10/11 verdict.
- The stale-email trap (CR-13, invariant 5) is passed by the encoder's choice not to extract a part fact from an email, not by the engine.
- Fairness: Arseniy authored both the gold and his own core; rule granularity (e.g. when Q_NO_MATERIAL_CERT is expected) follows his conventions. Maksim's engine was also built on Maksim's own data and gold. Small synthetic set.
