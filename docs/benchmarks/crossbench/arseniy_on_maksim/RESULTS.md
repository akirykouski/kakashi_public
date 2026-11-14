# Arseniy's reasoning core on Maksim's benchmark (10-request subset)

Run 14 Nov 2026, time box 35 min. Engine: `prep/spikes/reasoning-core/core.py`, byte-identical copy of
`arseniy_core/prep/spikes/reasoning-core/core.py` (sha1 db320bcf916f0c9b3c41d53707e2bf4408b6c597), and
`ontology/cc-*.ttl` copied unchanged. No change to core logic, shapes or axioms.

Files: `encode.py` (world + request facts, quote check by code), `world.facts.jsonl` (118 facts),
`requests.facts.jsonl` (70 facts), `run.py` (thin runner + mapping + scoring), `results.jsonl`.
Reproduce: the runner and encoder are kept outside this repo.

## Subset (first two ids per category)

| Category | Ids |
|---|---|
| direct | D01, D02 |
| inferred | I01, I02 |
| stale | S01, S02 |
| missing | M01, M02 |
| clean | C01, C02 |

33 gold findings (R4 is info-level and not in any key list; none in this subset anyway).

## Headline

| Matching | TP | FP | FN | Precision | Recall | Recall on inferred (R2,R3,R5) |
|---|---|---|---|---|---|---|
| rule + key (primary) | 28 | 1 | 5 | **0.97** | **0.85** | 9/12 = **0.75** |
| rule only | 26 | 0 | 5 | 1.00 | 0.84 | 8/11 = 0.73 |

Keys are comparable for every rule the engine emits (R1a supplier, R1b supplier|part|customer, R2 customer,
R3 report id, R6 drawing material, R7 key), so rule + key is the primary score.
False alarms on clean: **0/2**. Every quote (188 facts) is a literal substring of its registry row,
document or request (checked by `encode.py`, 0 problems). Closure is ~1,170-1,195 triples per request; the whole 10-request run takes about 3.5 s including imports.

## Per category (rule + key)

| Category | Exact match | Gold | Hit | Miss | Extra |
|---|---|---|---|---|---|
| direct | 1/2 | 8 | 7 | 1 (D01 R6) | 0 |
| inferred | 1/2 | 12 | 11 | 1 (I02 R3) | 0 |
| stale | 1/2 | 6 | 5 | 1 (S02 R2) | 0 |
| missing | 0/2 | 7 | 5 | 2 (M02 R2, R7) | 1 (M01 R7 material_certificate) |
| clean | 2/2 | 0 | 0 | 0 | 0 |

Per request: D02, I01, S01, C01, C02 exact. S01 (stale): the engine correctly does NOT raise R1a, because
QS-C-2026 (approved, 2026-11-06) supersedes QS-C-2025 (conditional) in the snapshot; I01 (as of 2026-11-05)
correctly does raise it. That is the bitemporal snapshot working on foreign data.

## Every miss / extra, with reason

| Req | Finding | Type | Reason | Detail |
|---|---|---|---|---|
| D01 | R6 MAT-ALSI9CU3 | miss | engine lacks concept | SUP-E (a coater) has no capability row at all. `B_MATERIAL_MISMATCH` needs an explicit offered material that differs; "supplier has no capability for the drawing material" (closed world over capabilities) is not expressible. |
| I02 | R3 8D-25-031 | miss | genuine different answer (rule semantics) | SERIES-8D also demands the 8D failure feature equal a feature of the part. 8D-25-031 is on fastening holes; FMEA-BR220 gives BR-220 fastening holes, but no document gives BR-225 any feature. Maksim's R3 is alloy-level only. Engine is stricter by design. |
| S02 | R2 CUST-AUR | miss | engine lacks concept | Coating change: no cc change class for coating, and `B_CUSTOMER_APPROVAL_REQUIRED` requires `proposedSupplier`, so R2 can never fire for a change without a new supplier (coating, material, process). |
| M02 | R2 CUST-AUR | miss | engine lacks concept | Same as S02. |
| M02 | R7 coating_substances | miss | engine lacks concept | No coating / substance model, no question shape for an unknown coating. |
| M01 | R7 material_certificate | extra | mapping ambiguity | `Q_NO_MATERIAL_CERT` fires for any `RawMaterialSourceChange` with no cert. I typed every Maksim SourceChange as RawMaterialSourceChange, justified by QP-11 4.4 ("A change of source requires a material certificate ... from the new supplier"). Maksim's gold does not ask for a cert from an unknown supplier (it asks for the supplier record first). Defensible either way. |

By reason: engine lacks concept 4, genuine different answer 1, mapping ambiguity 1, encoding gap 0.

## Mapping Arseniy ids -> Maksim rules (justification)

| Arseniy id | Maksim | Why |
|---|---|---|
| `B_SUPPLIER_NOT_QUALIFIED` | R1a | Standing "probation" fed from qualification "conditional"; QP-11 4.3 "A supplier with status conditional may not receive new parts" is the same rule as `Policy_PROBATION`. Key = supplier. |
| `B_NO_SOURCE_RELEASE` | R1b | Release supplier x part x plant from the ASL; QP-11 4.2 encoded as a `CompletenessStatement` for both sites (closed list). Customer is not in the engine's release; the runner adds the customer(s) of the part's programme(s) to build Maksim's key. |
| `Q_SOURCE_RELEASE_UNKNOWN` | R1b | Same condition without a closed list. Never fired here (QP-11 closes the list). |
| `B_MATERIAL_MISMATCH` | R6 | Offered material neither equals nor refines the drawing material. Key = drawing material (`?req`). |
| `B_CUSTOMER_APPROVAL_REQUIRED` | R2 | Customer requirement covering the change class, no approval/deviation for the new supplier. Key = customer that imposes `?req`. |
| `B_OPEN_8D_SAME_ALLOY` | R3 | Open 8D on the part's material family. Engine matches on series + feature (stricter). Key = report id. |
| `Q_SUPPLIER_QUALIFICATION_UNKNOWN` | R7 supplier_record | No standing on record for the supplier. |
| `Q_NO_MATERIAL_CERT` | R7 material_certificate | No 3.1 certificate from the new supplier. |

## Encoding decisions (disclosed)

- Registry rows -> facts with the CSV line as quote; documents -> facts with a phrase from the body.
- `supplier_qualification.csv` -> `supplierStanding` with `supersedes` carried over; `asl.csv` -> `SourceRelease`
  (approved -> "released", revoked -> "blocked").
- Capabilities -> one `MaterialOffer` per capability row with `offerForPart` = the request's part (the row names no
  part). Same move Arseniy made for CR-01 (AP-0207's billet grade used as the offer for BR-220). Caveat: with
  several capabilities the shape fires if ANY offer mismatches, so a supplier that has the right material plus
  another would get a false R6. Did not occur in this subset (SUP-C: 6061-T6 + 6082-T5 vs 6082-T6; SUP-G: steels vs PA66).
- Certificates are per supplier x material in Maksim's data, per supplier x part in the engine. None of the
  proposed suppliers holds a cert for the drawing material, so no cert fact was needed; in general this is a gap.
- CSR clauses: "change of source" -> `cc:SupplyChainChange`, "change of manufacturing process" -> `cc:ProcessChange`.
  "change of material" and "change of coating" have no cc class and were not encoded.
- 8D: Maksim's ALY-6082 -> Arseniy's `cc:EN_AW_6082`, MAT-6082-T6 -> `cc:EN_AW_6082_T6` (his alloy taxonomy).
  8D-25-031 `failureFeature FastenerHole` from "cracks around fastening holes"; BR-220 `hasFeature FastenerHole`
  from FMEA-BR220. NCR-26-017 typed as `Report8D` (engine has no NCR class).
- DEV-127 (a rejected deviation request) left out: the engine's `Deviation` has no status and would silently
  suppress R2. DEV-121 encoded with its validity window.
- Request plant = site(s) of the part's approved ASL rows (no site in the change JSON).
- Clean requests: C01 is a ScheduleChange and C02 a coating change; both are typed only `cc:ChangeRequest`
  with no new supplier, so the engine stays quiet partly because it cannot see these change types at all.
  The 0/2 false alarms is real but cheap.
- Contamination: `bench/requests.jsonl` carries gold next to the utterance, and I saw D01-I02 gold while
  reading the request format. World facts were derived from registries/documents per entity in scope, not per finding.

## Maksim's rules: support in Arseniy's engine

| Rule | Support | Note |
|---|---|---|
| R1a supplier-level qualification | native | `B_SUPPLIER_NOT_QUALIFIED` + supersession in snapshot; stale case S01 right. |
| R1b part x site x customer approval | partial | supplier x part x plant only; customer dimension missing (README "Not done" says so). |
| R2 customer approval via chain | partial | chain part -> programme -> customer -> requirement is native; fires only for changes with a new supplier and only for change classes the ontology has (no coating, no material change). |
| R3 open 8D on material | partial | native chain, but at series level plus a mandatory failure-feature match; no NCR class. |
| R4 superseded record (info) | native (as snapshot notes) | `superseded` / `stale_mention` notes; not scored. |
| R5 restricted substance via market | not supported | no coating, substance, law or market concepts. |
| R6 material / temper capability | partial | mismatch of an offered designation works (taxonomy with tempers); no "no capability at all", no special-characteristic numeric check (min yield). |
| R7 missing evidence as question | partial | supplier record and material certificate: native questions; coating substances and material data: no shape. Questions have no named owner. |

Ontology extensions the engine would need (findings, not implemented): coating + substance + `restricts` law +
`soldIn` market chain (R5, R7 coating); `CoatingChange` / `MaterialChange` classes and an R2 shape not keyed on
`proposedSupplier`; supplier capability as a closed list; certificates per supplier x material; customer on
`SourceRelease`; deviation status and change type; NCR class; numeric special characteristics.

## Fairness caveat

Each author wrote his own gold, data and rules. This run measures Arseniy's engine against Maksim's gold
and Maksim's vocabulary, encoded by a third party in ~35 minutes; the subset has 3/10 coating changes, a
concept the engine was never meant to cover. 10 requests, 33 findings: one finding moves recall by 3 points.
