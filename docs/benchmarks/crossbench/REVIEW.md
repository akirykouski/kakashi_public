# Core M vs Core A: review and merge plan (14 Nov 2026)

Read: both cores' code, ontologies, golds, the three cross-bench reports and per-request results. Nothing was run or changed. Paths: M = `torino_kakashi/`, A = `arseniy_core/`.

## 1. Which core is stronger

**Verdict: neither wins outright. M is the better product base (breadth, write path, extraction, benchmark). A has the better memory semantics (what is in force, when absence may block, proofs). The merged core is M's codebase with four A ideas ported in.**

| Dimension | Stronger | Evidence |
|---|---|---|
| Rule breadth | **M** | Coating → substance → law → market chain (R5, `core/rules.py:266-287`), customer on the approval key (`:125-150`), deviations with status and change type (`:154-172`), capability list, typed change dict. A has no coating, law, customer-on-release or numeric concept (its own `ontology/README.md` "Not done"). |
| Change taxonomy | **M** | M's R2 is keyed on change type (`rules.py:177,202`). A's approval shape requires `cc:proposedSupplier` (`cc-shapes.ttl:131`), so supplier-less changes can never fire: CR-07, CR-14 on A's own gold; S02, M02 on M's. |
| Supersession / authority | **A** | `core.py:106-169`: functional predicates, authority rank, assert vs mention, stale-mention notes, contested pairs, same-date conflicts quarantined, order independence tested over 200 shuffles (`run_scenario.py:138-147`). M has record-level `supersedes` only (`project.py:74-98`); two documents giving one part two materials both enter the graph and `Projection.value` returns whichever comes first (`project.py:125-127`). M passed A's CR-13 e-mail trap only because the encoder left the e-mail fact out (stated in `maksim_on_arseniy/RESULTS.md`). |
| Closed-world handling | **A** | Absence blocks only under a `CompletenessStatement` in force, otherwise it is a question (`cc-shapes.ttl:57-87`). M's R1b is closed-world everywhere: CR-11 gives 3 false findings and a wrong verdict, CR-19 nothing. A's scope is plant-only though (not commodity, not service parts): CR-02, 17, 20, 19. |
| Proof | **A** | Generic backward prover with sub-class, domain and range rules and shallowest-proof search (`core.py:213-296`). M's `explain.py:15-18` takes only the first chain and falls back to a step with no premises and no quote (`:96`). M also hard-codes QP-11 quotes and owner ids in code (`rules.py:104,140,273,363-365`), so the cross-bench needed a stub QP-11. A's policies are graph individuals that switch a shape off when retired, but they carry no quote (`cc-policies.ttl`). |
| Write path, multi-agent | **M**, with holes | A has none (a `status` field only). M: proposals, human acceptance, conflict refusal, tests (`tests/test_core.py:96-131`). Holes: `write_record` checks then inserts without the lock (`factlog.py:92-122`); `propose_fact` + `accept_proposed` skip the conflict check entirely (`:124-136`), so the extractor path can create two current qualifications. |
| Extraction | **M** | Only M has it: quote, predicate, id and grounding checks (`extract.py:161-178`); P 0.97 / R 0.91 on 35 facts, 0 of 15 traps. |
| Benchmark rigour | **M** | Pre-registration with hash, LLM baselines, failed threshold reported. A's gold format is better (`must_not_cite`, `cleared`, 3-way verdict) but its spike was checked against CR-01 only. |
| Speed | tie | Both whole-graph owlrl: M 0.5 s at 510 facts, 3 s at 4.7k; A 0.3 s at 40 facts. M keeps the request outside the graph, so one closure per as-of date can be cached; A re-closes per request. |

**Where the cross-bench numbers mislead**
- M on A's 20: 16/20 verdict, 8/20 exact. Five of the 8 exact rest on approximate parses or silence; direct parses only: 2/11 exact. CR-06 is "exact" by accident (source change to the current source; the cert question fires because no certificate exists anywhere).
- A on A's 20: 13/20 verdict, 6/20 exact, on its author's own gold. Three extras flip with the encoder's class choice (CR-10, CR-11).
- A on M: P 0.97 / R 0.85 on 10 requests, 33 findings; one finding = 3 points. The 26 untested requests include every R5 case, where A would score zero. 0/2 clean alarms is cheap: A cannot see those change types.
- M on M: 1.00 is the author's own gold; an upper bound.
- Contamination: both third-party encoders saw gold (disclosed in their reports).
- The two worlds reuse ids with different content: 8D-25-031 is on 6082 in M and 6061 in A; BR-180, BR-220, BR-310 differ. Never pool facts.
- Do not rank the cores from these numbers. Use them as a list of gaps.

## 2. Fastest gains (ranked)

| # | Change | Effect | Min |
|---|---|---|---|
| 1 | **Gold fix (A):** `Q_NO_MATERIAL_CERT` is expected in CR-01/18 but not CR-05, 12, 16 (same change class, no certificate anywhere). Add it there; decide CR-10. | −3 FP for M (CR-05, 10, 16), −3 FP for A (CR-05, 10, 12) | 10 |
| 2 | **Gold fix (A):** CR-13 add `B_CUSTOMER_APPROVAL_REQUIRED` (8.3.6.1, drawing requirement). Both engines fire it. | −1 FP each | 2 |
| 3 | **Data fix (A):** fact f10 maps clause 8.5.6.1 to `ProductOrProcessChange`; its text covers source, sub-supplier and sub-supplier location only. Map to `SupplyChainChange` + `LocationChange`. | Removes the class-dependent extras on CR-10, CR-11 | 5 |
| 4 | **A rule:** make `proposedSupplier` optional in the approval shape; apply the approval/deviation exemption only when a supplier is bound. | CR-07, CR-14; S02, M02 (R2) | 10 |
| 5 | **M rule:** R3 at series level plus feature, gated by a policy fact (`rules.py:237` uses only `madeOf`/`madeOfAlloy`; `madeOfSeries` already exists in `lcc.ttl:129`). | CR-01, 05, 18 (+3 TP). Without the feature gate M's own I03 gains an R3 its gold lacks: add the gate or re-gold. | 20 |
| 6 | **Vocabulary:** `Q_SUPPLIER_QUALIFICATION_UNKNOWN` is absent from A's gold. Fire only when the supplier has no record at all (M's `supplier_record`), and gold it on CR-02, 17, 20. | −6 FP for A, −1 for M (CR-12) | 15 |
| 7 | **Scope:** type the completeness statement by commodity (material source) and exclude service parts; give M's R1b the blocker/question split. | A: CR-02, 17, 20 (−3 FP), CR-19. M: CR-11 (−3 FP, +1 TP, verdict), CR-19 | 30 |
| 8 | **M rule:** on MaterialChange, new material ≠ drawing designation in force is a blocker (currently only compared with the yield minimum, `rules.py:328-351`). | CR-13 | 10 |
| 9 | **New rules:** measured value vs special characteristic; deviation caps (PRC-DEV-007). | CR-08, CR-09; makes CR-15 a real pass | 40 |
| 10 | **A:** take M's coating/law chain and closed capability list. | D01 R6, M02 R7, all R5 requests | port, not patch |

Items 1–3 are errors: fix them, do not engineer around them. Item 6 and the 8D level in item 5 are policy choices the framing owner must make.

## 3. The merged core

**Base: M's repository.** Port from A: the snapshot resolver, completeness scoping, the series-plus-feature 8D policy, the generic Explainer, the gold format. Keep rules in Python over the closure (one function per rule): numeric checks, owners and keys are faster to write and debug today than SHACL-SPARQL; keep SHACL for memory integrity only.

**Fact row** (M's SQLite log plus A's fields): `id, s, p, o, source, quote, valid_from, valid_to, recorded_at, review(proposed|accepted|rejected), kind(assert|mention), rank(1 customer/law, 2 controlled record, 3 informal), supersedes`.

**In force** = A's `snapshot()` for functional predicates + M's transitive record-level `supersedes`. One addition: a lower-rank fact may not supersede a higher-rank one (A's `core.py:127` allows it today).

**Change request**: `{classes[], part, site, scope(series|service), to_supplier?, supplier_role(material_source|subcontractor|lab|location), from_supplier?, new_material?, new_coating?, measured{characteristic,value}?, deviation{pieces,weeks}?}`.

**Taxonomy** (OWL subclasses; a clause names the classes it covers): SourceChange {MaterialSource, SubSupplier, SupplierLocation}; ReceivingSiteChange; DrawingRequirementChange {Material, Coating/Finish}; ProcessChange {ControlPlan, TestLab, SubcontractedProcess}; LotRelease; DeviationRequest; Operational {Schedule, Packaging, Volume}. Customer approval fires when a requirement in force covers a class of the change. The certificate check keys on "material from a source with no certificate for that material" (MaterialSource or LotRelease). Neither depends on a new supplier being present.

**Minimal rule set**: supplier standing; source release (blocker inside a completeness scope of plant × customer × commodity × series/service, question outside); customer approval; open 8D (alloy match, or series + feature under policy); restricted substance; material vs drawing and capability; measured value vs special characteristic; deviation caps; missing evidence → question with an owner read from the data. Every rule names the requirement it rests on and cites it as a fact with a quote.

**Write path**: extractor and agents → `proposed` → person accepts → conflict check at acceptance, inside one transaction → SHACL integrity. Agents never write accepted facts.

**Modules**: `factlog.py` (M + kind/rank) · `snapshot.py` (A's resolver) · `project.py` (closure, cached per as-of) · `rules.py` (M, re-keyed) · `explain.py` (A's prover) · `extract.py` (M) · `check.py` (3-way verdict) · `bench/` (M's runner, A's gold fields).

**Build order**
1. Freeze the eval, re-gold, pre-register (30 min, both).
2. Change schema and taxonomy; R2 and cert re-keyed; load A's world with the existing `maksim_on_arseniy/crossbench/encode_world.py` (40).
3. Snapshot resolver into the projection; port A's order-independence and stale-mention tests (45).
4. Completeness scoping for source release (30).
5. 8D series + feature policy (20).
6. Material vs drawing on MaterialChange (10).

**— cut line: above this is the demo —**

7. Generic Explainer swap (25).
8. Measured value and deviation caps (40).
9. Policies as quoted facts, owners from data (30).
10. Write-path lock and acceptance-time conflict check (20). Until then, do not claim multi-agent safety.

## 4. Honest evaluation

- **One set, two worlds**: 36 + 20 = 56 requests, run per world, never pooled as facts. One vocabulary (rule + key), blockers and questions scored separately, plus 3-way verdict, `must_not_cite` hits, `cleared` rules that fire, false alarms on clean.
- **Re-gold before the merged engine runs**, by the non-author, third teammate arbitrating, each change logged with a reason: CR-05/10/12/16 (cert), CR-13 (approval), CR-10/11 (class), CR-02/12/17/20 (supplier question), CR-19 (scope), I03 and I02 (8D level), M01/M04 (cert from an unknown supplier).
- **Hold-out**: 10 new requests by the third teammate (5 per world), written after the freeze, seen by neither author. This is the only number that speaks to generalisation.
- **Pre-register**: metric definitions, gold-parse and model-parse conditions, the full-context LLM baseline on both worlds, the hash of the gold, and the sentence the pitch uses if the threshold fails.
- **Safe to say**: "Each engine ran unchanged on the other author's requests: 16 of 20 verdicts right one way, precision 0.97 and recall 0.85 on a 10-request sample the other way; no superseded source was cited in any of the 30 runs." "A model reading all documents finds 95% of inferred blockers on our small company; the core is exact where a rule was replaced (7 of 7 vs 5 of 7) and where evidence is missing (4 of 4 vs 2 of 4)." "Extraction: 32 of 35 facts found, 0 of 15 traps taken."
- **Not safe**: "100%" (own gold), "reasons better than an LLM" (pre-registered threshold failed), a ranking of the two cores, multi-agent safety, anything about scale beyond 4.7k facts, hold-out numbers before they exist.
