# Arseniy's reasoning core on his own 20-request gold (part a)

Date: 14 Nov 2026. Part (b) (Maksim's 36) is handled by a separate agent in `../arseniy_on_maksim/`, so it is not in this file.

## Setup
- Engine: `arseniy_core_copy/prep/spikes/reasoning-core/core.py`, ontology and shapes **unchanged**. The adapter `engine.py` runs snapshot → owlrl closure → SHACL check → Explainer, as `run_scenario.py` does.
- World: Arseniy's 35 facts (`br220.facts.jsonl`) plus 39 new facts in `a/world_extra.jsonl`, all taken from `data/sources`: ASL approvals AP-0208/0212/0351/0402; BOM lines for BR-180, CV-015 and BR-310 (programme CLM-Lombardia-26 → CLM, 5083-H111); four more STL CSR clauses (8.3.6.1, 8.3.3.3, 7.1.5.3.2, 8.4.2.1).
- Requests: CR-01 uses Arseniy's own `br220.request-cr01.jsonl` (valid 2026-11-10). CR-02..CR-20 are hand-parsed from `request_text` into `a/requests/CR-NN.jsonl` (valid 2026-11-14), with no LLM.
- Quotes: all 129 new facts were checked by code. Each quote is a whitespace-normalised literal substring of its source document or request text: 0 problems.
- Parse convention: `proposedSupplier` names the party that would take on new business or scope (a new supplier, plant, site or material). An incumbent that keeps its current business is `currentSupplier`. CR-18 takes Meccanica C's grade from AP-0207, the same convention as Arseniy's CR-01 fact c08.
- Verdict: `blockers_found` if any Blocker fires, else `needs_info` if any Question fires, else `no_blockers_found`.
- Run: `bench/.venv/bin/python a/build_facts_a.py && bench/.venv/bin/python a/run_a.py`

## Headline
| Metric | Value |
|---|---|
| Verdict match | 13/20 |
| Rule-id precision | 0.61 (23 TP, 15 FP) |
| Rule-id recall | 0.79 (6 FN); 0.85 without the 2 NEW gold ids the engine has no shape for |
| Exact rule-set match | 6/20 (CR-01, 03, 04, 15, 16, 18) |
| must_not_cite hits | 0 (stale Rev B and the 0814 probation are never cited; the EML-1105 restatement is flagged as a stale mention) |
| Wrongly-firing `cleared` rules | 0 (B_SUPPLIER_NOT_QUALIFIED stays off in CR-03 and CR-18) |

## By category
| Category | n | Verdict match | Exact | TP | FP | FN |
|---|---|---|---|---|---|---|
| direct_conflict | 5 | 4 | 2 | 12 | 3 | 1 |
| inference_only | 6 | 4 | 0 | 4 | 8 | 2 |
| stale_rule_trap | 4 | 3 | 2 | 6 | 2 | 1 |
| missing_data | 3 | 0 | 0 | 1 | 2 | 2 |
| clean_control | 2 | 2 | 2 | 0 | 0 | 0 |

## Every miss (FN), with reason
| Req | Missed | Reason |
|---|---|---|
| CR-06 | Q_NO_MATERIAL_CERT | **Engine lacks concept**: the cert question targets only `RawMaterialSourceChange`. There is no lot or heat release, and no "certificate for heat H-4471". |
| CR-07 | B_CUSTOMER_APPROVAL_REQUIRED | **Engine lacks concept**: the shape requires `proposedSupplier`. A supplier-less change (sampling frequency) cannot fire, even though 8.3.3.3 is encoded. |
| CR-14 | B_CUSTOMER_APPROVAL_REQUIRED | **Engine lacks concept**: same cause (the finish change is done in-house, so there is no supplier). |
| CR-08 | special_characteristic_violation | **Not supported by engine** (NEW id, no measurement model). |
| CR-09 | deviation_limit_exceeded | **Not supported by engine** (NEW id, PRC-DEV-007 caps not modelled). |
| CR-19 | Q_SOURCE_RELEASE_UNKNOWN | **Engine lacks concept**: completeness is scoped by plant only, so "service parts not in scope" cannot be expressed. The TO1 approval AP-0311 makes the absence check pass. |

## Every extra (FP), with reason
| Req | Extra | Reason |
|---|---|---|
| CR-02, CR-17, CR-20 | B_NO_SOURCE_RELEASE | **Engine lacks concept**: the release and completeness scope is not typed by commodity. A coater (Rivestimenti Nord), a toll heat-treater (Termica Nord) or a test lab (Laboratorio Sigma) is checked against the *material-source* ASL. |
| CR-02, 11, 12, 13, 17, 20 | Q_SUPPLIER_QUALIFICATION_UNKNOWN | **Engine id absent from the gold vocabulary**: it fires for any proposed supplier with no standing on record (only Meccanica C has one). It is not listed in data/eval/RULES.md. It is defensible as a question, but the gold never expects it. |
| CR-05, CR-10, CR-12 | Q_NO_MATERIAL_CERT | **Genuine disagreement / gold inconsistency**: same change class as CR-01 and CR-18, where the gold *does* expect this question. |
| CR-10 | B_CUSTOMER_APPROVAL_REQUIRED (and the cert Q above) | **Encoding ambiguity**: I typed the 40% volume shift between approved sources as `RawMaterialSourceChange`. Typed as a plain `ChangeRequest`, the engine returns exactly gold (`B_OPEN_8D_SAME_ALLOY` only; re-run checked). |
| CR-11 | B_CUSTOMER_APPROVAL_REQUIRED | **Encoding ambiguity**: I typed the Plant 3 pilot as `LocationChange`. As a plain `ChangeRequest` it gives Q_SOURCE_RELEASE_UNKNOWN + Q_SUPPLIER_QUALIFICATION_UNKNOWN: verdict right, still not exact. |
| CR-13 | B_CUSTOMER_APPROVAL_REQUIRED | **Genuine disagreement**: Arseniy's own fact f10 maps 8.5.6.1 to all `ProductOrProcessChange`, and 8.3.6.1 covers material changes. The gold lists only the mismatch. The engine is arguably right here. |

## Reading
- Verified strengths: the hard inferred cases (8D series rule in CR-01, 05, 10 and 18; the customer-approval chain) and supersession/stale handling. There were 0 must_not_cite hits and 0 wrongly cleared rules, and CR-03, CR-13 and CR-18 are right on the stale traps.
- Engine gaps, in priority order: (1) the customer-approval shape needs a proposed supplier; (2) source-release completeness is not typed by commodity; (3) Q_SUPPLIER_QUALIFICATION_UNKNOWN fires on every supplier without a standing; (4) there is no lot, measurement, deviation-cap or service-part scope. Each is recorded as a finding; no ontology or shape was changed.
- Fairness caveats:
  - Arseniy wrote this gold, the data and the engine. Maksim's benchmark has the same issue for his own engine.
  - The request parses (class, proposed vs current supplier) are mine, and 3 extras flip with the class choice.
  - Disclosure: before encoding, I accidentally saw the first ~3 KB of `data/eval/canonical.json`, which mirrors the gold items for CR-01..CR-05. CR-01 used Arseniy's file, and the CR-02..05 parses follow the same rule as all the others.

## Files
`engine.py` (adapter), `a/build_facts_a.py`, `a/world_extra.jsonl`, `a/requests/CR-*.jsonl`, `a/run_a.py`, `results_a.jsonl` (per request: produced items, tp/missed/extra, cited leaves, snapshot notes).
