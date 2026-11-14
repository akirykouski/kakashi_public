# ontology/

PREP material, written 13 November 2026, the night before the event. It is an
ontology draft and a fictional scenario (rules section 7: "an idea, a dataset").
Whether it is brought as is or rewritten on the day is open decision D1.

| File | What it is |
|---|---|
| `cc-core.ttl` | Classes, properties and axioms. OWL 2 RL only. |
| `cc-alloys.ttl` | Aluminium designations used by the scenario. Authored by us from EN 573-3 and EN 515, not imported. |
| `cc-policies.ttl` | The two company rules that gate shapes (`Policy_8D_SERIES`, `Policy_PROBATION`). The frozen data set has no policy document, so they are ontology individuals, not quoted facts. |
| `cc-shapes.ttl` | SHACL-SPARQL shapes. One shape is one blocker type. |
| `scenario/br220.facts.jsonl` | The BR-220 scenario as 35 facts. Every `doc` is a `data/sources/<doc_id>.md` (DWG-BR220-RevC, DWG-BR220-RevB, CP-BR220-R3, BOM-STL-TORINO-27, CSR-STL-2026-02, ASL-TO-2026-04, 8D-25-031, EML-SQ-2026-0814, EML-SQ-2026-1105), every `quote` a literal substring of it. Plant TO1, customer STL. Fictional, matches the frozen `data/` set. |
| `scenario/br220.request-cr01.jsonl` | The 8 facts that turn change request CR-01 (ECN-26-0147) into a graph. Quotes come from the CR-01 `request_text` in `data/eval/change_requests.jsonl`, or from a source document (plant TO1 from CP-BR220-R3, Meccanica C's billet grade from ASL-TO-2026-04 AP-0207). |

Namespace: `cc: <https://example.org/ctxcol#>` (placeholder, not registered).

Test (53 checks, exit 0 on 14 Nov, about 2 s; includes a check that every quote is found in its document):

```
uv run --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 \
    python prep/spikes/reasoning-core/run_scenario.py
```

Cross-check against the frozen gold (CR-01, set comparison of rule ids, exit 0 = equal):

```
uv run --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 \
    python prep/spikes/reasoning-core/crosscheck_gold.py
```

## Blocker type ids

These are the ids the card, the gold set and the decision table refer to.

| Id | Severity | Reached by | Fires when |
|---|---|---|---|
| `B_SUPPLIER_NOT_QUALIFIED` | Blocker | direct fact | proposed supplier's standing in force is "probation" (EML-SQ-2026-0814; revoked for Meccanica C by EML-SQ-2026-1105 on 2026-11-05) |
| `B_NO_SOURCE_RELEASE` | Blocker | closed world, scoped | no release for supplier x part x plant, and a source list in force declares itself complete for that plant |
| `B_MATERIAL_MISMATCH` | Blocker | closed world over our own taxonomy | offered designation neither equals nor refines the drawing designation |
| `B_CUSTOMER_APPROVAL_REQUIRED` | Blocker | inferred | part is subject (programme, customer, clause) to a customer approval requirement covering this class of change, and no approval or deviation in force covers the proposed supplier |
| `B_OPEN_8D_SAME_ALLOY` | Blocker | inferred | proposed supplier has an open 8D on the same alloy series (alloy group, rule SERIES-8D below) and the same failure feature as the part |
| `Q_SUPPLIER_QUALIFICATION_UNKNOWN` | Question | absence | no standing in force for the proposed supplier |
| `Q_SOURCE_RELEASE_UNKNOWN` | Question | absence | no release found and no source list is declared complete for the plant |
| `Q_NO_MATERIAL_CERT` | Question | absence | raw material source change and no material certificate from the proposed supplier for the part |

A Blocker is proved from facts in force. A Question means required evidence is
absent and nothing licenses reading the absence as a "no". The system has no
third output: it never says "approved".

## Closed vocabulary for the extractor

The extractor may emit only these. Anything else is dropped.

Classes: `Supplier`, `Customer`, `Plant`, `Part`, `Programme`, `MaterialDesignation`,
`Alloy`, `AlloySeries`, `CustomerApprovalRequirement`, `CompanyPolicy`, `SourceRelease`,
`CustomerPartApproval`, `Deviation`, `Report8D`, `MaterialOffer`, `MaterialCertificate`,
`SpecialCharacteristic`, `CompletenessStatement`, and the change classes
`RawMaterialSourceChange`, `SubSupplierChange`, `ProcessChange`, `LocationChange`.

| Property | From | To | Functional |
|---|---|---|---|
| `partOfProgramme` | Part | Programme | |
| `forCustomer` | Programme | Customer | |
| `imposes` | Customer | Requirement | |
| `appliesToChangeClass` | Requirement | a change class | |
| `clause` | Requirement | text | |
| `requiresMaterial` | Part | MaterialDesignation | yes |
| `releaseSupplier`, `releasePart`, `releasePlant` | SourceRelease | Supplier, Part, Plant | |
| `releaseStatus` | SourceRelease | "released" or "blocked" | yes |
| `supplierStanding` | Supplier | "probation" or "good_standing" | yes |
| `approvalForPart`, `approvalCoversSupplier` | CustomerPartApproval | Part, Supplier | |
| `approvalStatus` | CustomerPartApproval | "approved" or other | yes |
| `deviationForPart`, `deviationCoversSupplier` | Deviation | Part, Supplier | |
| `reportAgainst` | Report8D | Supplier | |
| `concernsMaterial` | Report8D | MaterialSpec | |
| `reportStatus` | Report8D | "open" or "closed" | yes |
| `offeredBy`, `offerForPart` | MaterialOffer | Supplier, Part | |
| `offeredMaterial` | MaterialOffer | MaterialDesignation | yes |
| `certSupplier`, `certForPart` | MaterialCertificate | Supplier, Part | |
| `hasFeature` | Part | Feature (e.g. `FastenerHole`) | |
| `failureFeature` | Report8D | Feature | |
| `characteristicOf` | SpecialCharacteristic | Part | |
| `constrainsMaterial`, `controlPlanLine` | SpecialCharacteristic | boolean, text | |
| `completeForClass`, `completeForPlant` | CompletenessStatement | a class, Plant | |
| `forPart`, `atPlant`, `currentSupplier`, `proposedSupplier` | change request | Part, Plant, Supplier, Supplier | |

Never extracted, only derived by axioms: `subjectTo`, `requiresAlloy`, `alloyRequiredBy`,
`hasReport`, `concernsAlloy`, `ofSeries`, `concernsSeries`, `requiresSeries`, `seriesRequiredBy`, `hasQualityHistoryOn` (alloy level), `hasSeriesQualityHistoryOn` (series level), and every superclass membership.

"Functional" means one value in force at a time for a given subject. The memory
uses it to decide what supersedes what. See `docs/plan/01-solution.md` section 3.

## Three distinctions the scenario depends on

1. A release is per supplier, part and plant. A supplier-level audit grade never grants one.
2. 6061 and 6082 are different alloys. "Same alloy family" is not "meets the drawing". The material check compares designations; the 8D rule compares series (next section).
3. A newer document that only restates an old value does not bring it back.

## Named rule SERIES-8D (series-level match)

The data documents state the alloy group, not the alloy, where the 8D and the part meet:
8D-25-031 D2 says "EN AW-6061-T6 (alloy group 6xxx)", DWG-BR220-RevC note 1 says
"EN AW-6082-T6 billet (alloy group 6xxx, Al-Mg-Si)". `data/eval/RULES.md` words the rule as
"an open 8D on a failure mode plausible for the part (alloy group 6xxx, fastener holes). No document links
the 8D to the part." So `B_OPEN_8D_SAME_ALLOY` (the id is frozen in the gold) matches on series plus feature:

1. `cc:ofSeries` = `ofAlloy` then `refines` (cc-alloys.ttl): every designation and alloy lifts to its series.
2. `concernsSeries` = `concernsMaterial` then `ofSeries`; `requiresSeries` = `requiresMaterial` then `ofSeries`.
3. `hasSeriesQualityHistoryOn` = `hasReport` then `concernsSeries` then `seriesRequiredBy` (cc-core.ttl).
4. The shape also needs the 8D `failureFeature` to equal a `hasFeature` of the part (FastenerHole from DWG note 3 and 8D D2), the report `open`, and `Policy_8D_SERIES` in force.

The alloy-level link `hasQualityHistoryOn` stays declared and does NOT fire here (6061 vs 6082), which a test asserts.
Removing `Policy_8D_SERIES` from cc-policies.ttl, an 8D on a 5xxx alloy, a missing feature, or a closed 8D each switch the blocker off.

## Not done

- Approval is per part x plant x customer in the data. `SourceRelease` still carries supplier, part and plant only; the customer is not modelled (every BR-220 fact is customer STL).
- The offer behind `B_MATERIAL_MISMATCH` takes Meccanica C's billet grade (EN AW-6061-T6) from its approval AP-0207 for BR-180, because no document states what C would supply for BR-220.
- `Policy_8D_SERIES` and `Policy_PROBATION` are not extracted from a policy document (the frozen set has none).
- No alignment triples to IOF Core yet. The class names were chosen to map (Supplier,
  MaterialProduct, RequirementSpecification) but the IOF IRIs were not verified, so none are asserted.
- `owl:hasKey` on SourceRelease is declared and not tested.
- Deviation quantity caps are not modelled. Validity dates are, through the fact log.
- The T651-meets-T6 assumption needs a metallurgist's yes.
