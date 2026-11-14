# Re-gold arbitration sheet

**Who decides:** Valentina (`eval/README.md`: "gold decisions: Valentina (#21)"). This sheet decides nothing. It sets out each disputed gold item, what each side holds, and the document text both sides argue from.

**Deadline:** any item without a decision by **13:45 Rome** is frozen as it stands now and logged in `docs/benchmarks/CHANGES.md` as "disputed, not re-golded".

**Where the list comes from:** `docs/benchmarks/crossbench/REVIEW.md` §4 ("Re-gold before the merged engine runs …") and §2 rows 1, 2, 3, 5, 6, 7.

## How to read this

- **Two worlds, never pooled.** World A (author Arseniy, requests CR-01..CR-20) and world M (author Maksim, requests D01..C08) reuse ids with different meanings: 8D-25-031 is a different report in each world.
- **Gold edits** use the format in `eval/MAPPING.md`. A finding matches on (`rule_u`, `key`). A blocker makes the verdict `blockers_found`. If there is no blocker, one question makes it `needs_info`.
- **Scoring effect** is counted against the runs that already exist:
  - **M-on-A**: Core M on A's 20 requests (`maksim_on_arseniy/results.jsonl`).
  - **A-on-A**: Core A on A's 20 requests (`arseniy_on_both/results_a.jsonl`).
  - **A-on-M**: Core A on 10 of M's 36 requests (`arseniy_on_maksim/results.jsonl`).
  - **FP** is an engine finding that the gold does not have. **FN** is a gold finding that the engine missed.
- **Who said what.** Third-party encoder agents wrote the three cross-bench reports (`crossbench/README.md`); Maksim and Arseniy did not. `REVIEW.md` is an independent review. Neither author has written down a reason for any disputed item. So each author's position below is read from his gold, his rule notes or his engine, and is marked *inferred*.
- **REVIEW's labels:** "Items 1–3 are errors: fix them, do not engineer around them. Item 6 and the 8D level in item 5 are policy choices the framing owner must make." Each item below carries that label (**Error**, **Policy**, or **Unlabelled**). The label is REVIEW's view only. The decision is still Valentina's.
- **Quotes** are verbatim. Each was checked as a substring of its source; where the source wraps a sentence over two lines, the quote is cut at the line end.

**Abbreviations:**
- **8D**: eight-disciplines report, a supplier's formal file on an open quality problem.
- **PPAP**: Production Part Approval Process, the customer's formal approval of a part from a given source.
- **ASL**: approved supplier list.
- **CSR**: customer-specific requirements.
- **SC**: special characteristic, a drawing requirement the customer marks as critical.
- **IATF 16949**: the automotive quality standard whose clause numbers the CSR uses.

## Summary

| # | Id | World | REVIEW label | Question | Options |
|---|---|---|---|---|---|
| 1 | CR-05 | A | Error (row 1) | Add the "no material certificate" question? | 1 add · 2 keep |
| 2 | CR-10 | A | Error (row 1, "decide CR-10") | Add the "no material certificate" question? | 1 add · 2 keep |
| 3 | CR-12 | A | Error (row 1) | Add the "no material certificate" question? | 1 add · 2 keep |
| 4 | CR-16 | A | Error (row 1) | Add the "no material certificate" question? | 1 add · 2 keep |
| 5 | CR-13 | A | Error (row 2) | Add "customer approval required" (CSR 8.3.6.1)? | 1 add · 2 keep |
| 6 | CR-10 | A | Error (row 3, data fix) | Does a volume shift between two approved sources need customer approval? | 1 keep · 2 add |
| 7 | CR-11 | A | Error (row 3, data fix) | Does a pilot at Plant 3 need customer approval? | 1 keep · 2 add (flips verdict) |
| 8 | CR-02 | A | Policy (row 6) | Add "no record of this supplier" question? | 1 add · 2 keep |
| 9 | CR-12 | A | Policy (row 6) | Add "no record of this supplier" question? | 1 add · 2 keep |
| 10 | CR-17 | A | Policy (row 6) | Add "no record of this supplier" question? | 1 add · 2 keep |
| 11 | CR-20 | A | Policy (row 6) | Add "no record of this supplier" question? | 1 add · 2 keep |
| 12 | CR-19 | A | Unlabelled (row 7 is an engine fix) | Is "unknown, service parts out of scope" the right gold? | 1 keep · 2 split · 3 not_covered |
| 13 | I02 | M | Policy (row 5, 8D level) | Keep the open-8D finding when no document gives the part the 8D's failure feature? | 1 keep · 2 remove |
| 14 | I03 | M | Policy (row 5, 8D level) | Add the open-8D finding on an alloy-series match alone? | 1 keep · 2 add |
| 15 | M01 | M | Unlabelled | Ask an unknown supplier for a material certificate too? | 1 add · 2 keep |
| 16 | M04 | M | Unlabelled | Same question as M01 | 1 add · 2 keep |

Two choices decide several rows at once: the certificate policy (rows 1–4, 15–16) and the 8D level (rows 13–14, and indirectly A's CR-01/05/18). Each is set out once in its section below.

---

## 1. Certificate question on source changes: CR-05, CR-10, CR-12, CR-16

**REVIEW label:** Error (row 1). REVIEW says: "`Q_NO_MATERIAL_CERT` is expected in CR-01/18 but not CR-05, 12, 16 (same change class, no certificate anywhere). Add it there; decide CR-10."

**Question:** should these four requests carry the open question "no material certificate (EN 10204 type 3.1) on file", as the gold does for CR-01, CR-06 and CR-18?

**Arseniy (author of A), inferred:**
- His gold asks the question on CR-01 and CR-18 (Meccanica C as a new BR-220 source) and on CR-06 (lot release).
- It does not ask it on CR-05, 10, 12 or 16, nor on CR-03 or CR-04.
- His engine fires the question only on a "raw material source change" (`arseniy_core/ontology/README.md`).
- He gives no reason for leaving it out of the four.
- One possible reason, in the data: the native change types differ. CR-01, 05 and 18 are `material_source_change`, CR-10 is `source_volume_shift`, CR-12 is `source_location_change` and CR-16 is `source_plant_change` (`eval/worlds/A/change_requests.jsonl`). So only CR-05 has the same native type as CR-01 and CR-18.

**Other side:**
- REVIEW, as quoted above.
- Core M run (`maksim_on_arseniy/RESULTS.md`): "Arguably gold inconsistency, arguably engine noise."
- Core A run (`arseniy_on_both/RESULTS.md`): "**Genuine disagreement / gold inconsistency**: same change class as CR-01 and CR-18, where the gold *does* expect this question."

**Evidence (common):**
> [A · DWG-BR220-RevC] 5. Material certificate EN 10204 type 3.1 required with each lot.

> [A · CP-BR220-R3] | 20 | Material certificate review | Grade and temper on certificate | EN AW-6082-T6, EN 10204 type 3.1 | Each lot, before release to production | Hold lot, notify Supplier Quality Engineer |

> [A · ASL-TO-2026-04] Material certificates are not stored in this record.

> [author A · eval/worlds/A/RULES.md] Required material certificate or test result is not in the documents. Missing data, not a violation.

Two facts from the documents:
- No A document contains a certificate from any supplier.
- A certificate requirement is stated only for BR-220 (drawing Rev C note 5, control-plan line 20). No A document states one for BR-180 (CR-10) or BR-310 (CR-16).

**Edit used below (C):** `{rule: "Q_NO_MATERIAL_CERT", rule_u: "U_MISSING_EVIDENCE", key: "material_certificate", kind: "question", inferred: false}`. All four requests are already `blockers_found`, so no verdict changes.

### 1.1 CR-05 (world A)
- **Request:** "Meccanica C quoted BR-220 billet in EN AW-6061-T6 and says the strength is equivalent to 6082. Can I add them as alternate source for BR-220?"
- **Current gold** (`blockers_found`):
  - U_SOURCE_RELEASE / BR-220 / blocker
  - U_MATERIAL / BR-220 / blocker
  - U_CUSTOMER_APPROVAL / STL / blocker (inferred)
  - U_OPEN_ISSUE / 8D-25-031 / blocker (inferred)
- **Specific to this request:** same supplier, part and native change type as CR-01 and CR-18. Both of those carry the question.
- **Option 1:** add C. M-on-A loses 1 FP; A-on-A loses 1 FP.
- **Option 2:** keep as is. Both engines keep 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 1 (add the certificate question).** Same part, same new source and same native change type as CR-01 and CR-18, which carry it. Drawing Rev C note 5 requires a 3.1 certificate with each BR-220 lot, and no A document holds one from Meccanica C.

Decision (Valentina):  — time:

### 1.2 CR-10 (world A), certificate part
- **Request:** "Meccanica C is approved for BR-180 and has capacity. Move 40% of BR-180 volume at Plant 1 for STL from Alluminio B to C."
- **Current gold** (`blockers_found`): U_OPEN_ISSUE / 8D-25-031 / blocker (inferred).
- **Specific to this request:**
  - Meccanica C already holds the approval for this exact part, plant and customer.
  - No A document states a certificate requirement for BR-180.
  - REVIEW leaves CR-10 open ("decide CR-10").

  > [A · ASL-TO-2026-04] APPROVAL AP-0207: part BR-180; plant TO1; customer STL; supplier Meccanica C S.p.A. (Chieri); billet grade EN AW-6061-T6; status APPROVED 2024-09-02 (PPAP-2024-077)

- **Option 1:** add C. M-on-A loses 1 FP; A-on-A loses 1 FP.
- **Option 2:** keep as is. Both engines keep 1 FP.
- CR-10 has a second disputed item in §3.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 2 (keep).** No A document states a certificate requirement for BR-180; the question is for a *required* certificate that is missing (A's RULES.md), so nothing is required here.

Decision (Valentina):  — time:

### 1.3 CR-12 (world A), certificate part
- **Request:** "Alluminio B wants to ship the BR-220 billet from its Rovereto plant to catch up. Same alloy 6082-T6. OK for Plant 1?"
- **Current gold** (`blockers_found`):
  - U_SOURCE_RELEASE / BR-220 / blocker
  - U_CUSTOMER_APPROVAL / STL / blocker (inferred)
- **Specific to this request:** it is the same supplier at a new location. The BR-220 certificate requirement (note 5 above) applies.

  > [A · ASL-TO-2026-04] An approval covers the named manufacturing location only.

- **Option 1:** add C. A-on-A loses 1 FP; M-on-A gains 1 FN (Core M asked for the supplier record here instead).
- **Option 2:** keep as is. A-on-A keeps 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 1 (add).** BR-220's certificate requirement (Rev C note 5, control plan line 20) applies, and the Rovereto plant is a location the approval does not cover ("An approval covers the named manufacturing location only."), so no certified lot from it exists — the same situation as a new source in CR-01.

Decision (Valentina):  — time:

### 1.4 CR-16 (world A), certificate part
- **Request:** "Run BR-310 for Cantieri Lombardi at Plant 1 using Meccanica C billet, the Plant 2 line is down."
- **Current gold** (`blockers_found`): U_SOURCE_RELEASE / BR-310 / blocker.
- **Specific to this request:**
  - Meccanica C is already the approved BR-310 source, at Plant 2.
  - No A document states a certificate requirement for BR-310.

  > [A · ASL-TO-2026-04] APPROVAL AP-0344: part BR-310; plant TO2; customer CLM; supplier Meccanica C S.p.A. (Chieri); billet grade EN AW-5083-H111; status APPROVED 2025-06-11 (PPAP-2025-052)

- **Option 1:** add C. M-on-A loses 1 FP; A-on-A gains 1 FN (Core A did not fire it here).
- **Option 2:** keep as is. M-on-A keeps 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 2 (keep).** No A document states a certificate requirement for BR-310.

Decision (Valentina):  — time:

---

## 2. CR-13: customer approval for a material change (world A)

**REVIEW label:** Error (row 2). REVIEW says: "CR-13 add `B_CUSTOMER_APPROVAL_REQUIRED` (8.3.6.1, drawing requirement). Both engines fire it."

- **Request:** "Elena's 5 Nov mail says BR-220 is EN AW-6061-T6, min 240 MPa. Alluminio B can ship 6061-T6 bar this week instead of 6082. Accept?"
- **Current gold** (`blockers_found`): U_MATERIAL / BR-220 / blocker. The gold also lists the 5 Nov e-mail and drawing Rev B under `must_not_cite`, so citing either as authority is scored as an error.
- **Question:** does accepting 6061-T6 instead of the drawing's 6082-T6 also need written customer approval under CSR clause 8.3.6.1?

**Arseniy (author of A), inferred:** the gold lists only the material mismatch. Its claim reads: "An informal email restating the old 6061 value does not change the drawing." He gives no reason for leaving out customer approval.

**Other side:**
- REVIEW, as quoted above.
- Core M run: "a material change on a drawing requirement falls under CSR 8.3.6.1 per the documents; gold lists only B_MATERIAL_MISMATCH."
- Core A run: "The engine is arguably right here."

**Evidence:**
> [A · CSR-STL-2026-02] 8.3.6.1 Any change to a requirement stated on a customer drawing, including material and finish, needs written approval from Stellantis before the change is implemented.

> [A · CSR-STL-2026-02] These requirements apply to every part delivered to Stellantis for a program listed in Annex A.

> [A · BOM-STL-TORINO-27] BOM-LINE 120: part BR-220 (drawing Rev C); program STL-Torino-27; customer STL; material EN AW-6082-T6; features: 4 fastener holes

> [A · DWG-BR220-RevC] 1. Material: EN AW-6082-T6 billet (alloy group 6xxx, Al-Mg-Si).

**Options:**
- **Option 1:** add `{rule: "B_CUSTOMER_APPROVAL_REQUIRED", rule_u: "U_CUSTOMER_APPROVAL", key: "STL", kind: "blocker", inferred: true}`. The verdict stays `blockers_found`. M-on-A loses 1 FP; A-on-A loses 1 FP.
- **Option 2:** keep as is. Both engines keep 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 1 (add customer approval).** CSR 8.3.6.1 names material explicitly: "Any change to a requirement stated on a customer drawing, including material and finish, needs written approval from Stellantis"; BR-220 is on STL-Torino-27 (BOM line 120).

Decision (Valentina):  — time:

---

## 3. Customer approval and change class: CR-10, CR-11 (world A)

**REVIEW label:** Error (row 3). REVIEW treats this as a **data** fix, not a gold fix: "fact f10 maps clause 8.5.6.1 to `ProductOrProcessChange`; its text covers source, sub-supplier and sub-supplier location only. Map to `SupplyChainChange` + `LocationChange`." The effect it gives is "Removes the class-dependent extras on CR-10, CR-11".

Fact f10 lives in Arseniy's engine data (`arseniy_core/ontology/scenario/br220.facts.jsonl`), not in `eval/`. Fixing it is outside this sheet. **The gold question is only whether the current gold, with no customer approval on either request, stands.**

Core A run: "**Encoding ambiguity**: I typed the 40% volume shift between approved sources as `RawMaterialSourceChange`. Typed as a plain `ChangeRequest`, the engine returns exactly gold". For CR-11, typed as a plain change request, Core A still adds the supplier question ("verdict right, still not exact").

**Evidence (common):**
> [A · CSR-STL-2026-02] 8.5.6.1 A change of material source, of a sub-supplier, or of the manufacturing location of a sub-supplier needs a documented risk analysis and written approval from Stellantis before any shipment of affected parts.

The CSR excerpt has six clauses: 8.3.6.1, 8.3.3.3, 7.1.5.3.2, 8.5.6.1, 8.4.2.1 and 8.7.1.1. None of them names a change of our own receiving plant or a change in volume split.

**Edit used below (P):** `{rule: "B_CUSTOMER_APPROVAL_REQUIRED", rule_u: "U_CUSTOMER_APPROVAL", key: "STL", kind: "blocker", inferred: true}`.

### 3.1 CR-10, customer-approval part
- **Request:** see 1.2.
- **Current gold** (`blockers_found`): U_OPEN_ISSUE / 8D-25-031 only.
- **Question:** does moving 40% of BR-180 volume to a source already approved for that exact part, plant and customer need written customer approval under 8.5.6.1?
- **Arseniy, inferred:** no. The gold carries no approval.
- **Maksim, inferred from his rule notes:** no. His customer-approval rule fires only if "the new source is not already approved" (`torino_kakashi/ontology/RULES.md`, R2). Core M did not fire it.

**Evidence:**
> [A · ASL-TO-2026-04] APPROVAL AP-0207: part BR-180; plant TO1; customer STL; supplier Meccanica C S.p.A. (Chieri); billet grade EN AW-6061-T6; status APPROVED 2024-09-02 (PPAP-2024-077)

> [A · ASL-TO-2026-04] APPROVAL AP-0208: part BR-180; plant TO1; customer STL; supplier Alluminio B S.r.l. (Settimo Torinese); billet grade EN AW-6061-T6; status APPROVED 2024-10-14 (PPAP-2024-091)

**Options:**
- **Option 1:** keep as is. A-on-A keeps 1 FP until f10 or the request typing is fixed. Core M is unaffected.
- **Option 2:** add P. The verdict does not change. A-on-A loses 1 FP; M-on-A gains 1 FN.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 1 (keep).** CSR 8.5.6.1 names a change of material source; Meccanica C is already the approved source for this exact part, plant and customer (AP-0207), and no CSR clause names a change of volume split.

Decision (Valentina):  — time:

### 3.2 CR-11
- **Request:** "Plant 3 starts BR-180 pilot builds for STL next month. Billet from Alluminio B Settimo, OK?"
- **Current gold** (`needs_info`): U_SOURCE_RELEASE / BR-180 / question.
- **Question:** does a BR-180 pilot build at Plant 3, which is outside the approved-supplier list's scope, need written customer approval?
- **Arseniy (author), from his rule notes:** "Absence of an approval is a blocker only where a controlled record declares itself complete for that scope. Otherwise it is a question with an owner (CR-11, CR-19)." (`eval/worlds/A/RULES.md`). He gives no position on customer approval.
- **Other side:** both engines fire customer approval here.
  - REVIEW calls Core M's result "3 false findings and a wrong verdict".
  - The Core M run explains its own extra: "TO3 -> blocker instead of question, and that also triggers R2 via "not already approved"".
  - Core A fires it through the f10 class mapping.

**Evidence:**
> [A · ASL-TO-2026-04] Torino Plant 3 (TO3) is not in scope of this record.

> [A · BOM-STL-TORINO-27] BOM-LINE 110: part BR-180 (drawing Rev F); program STL-Torino-27; customer STL; material EN AW-6061-T6; features: 4 fastener holes

> [A · CSR-STL-2026-02] These requirements apply to every part delivered to Stellantis for a program listed in Annex A.

**Options:**
- **Option 1:** keep as is. Both engines keep 1 FP and a wrong verdict.
- **Option 2:** add P. The verdict becomes `blockers_found`. Both engines lose 1 FP, and both verdicts become right, because both engines already answer `blockers_found`.
  - Watch out: this option moves the gold onto what the engines already output.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 1 (keep).** No CSR clause names a change of our own receiving plant; the ASL says TO3 is out of its scope, so the gold's question is what the documents support. Option 2 would also move the gold onto what both engines already output.

Decision (Valentina):  — time:

---

## 4. "No record of this supplier" question: CR-02, CR-12, CR-17, CR-20 (world A)

**REVIEW label:** Policy (row 6). REVIEW says: "`Q_SUPPLIER_QUALIFICATION_UNKNOWN` is absent from A's gold. Fire only when the supplier has no record at all (M's `supplier_record`), and gold it on CR-02, 17, 20." So REVIEW proposes the question for CR-02, CR-17 and CR-20, **not** for CR-12.

**Question:** when the proposed supplier, subcontractor or lab appears in no document, should the gold carry an open question asking for its qualification record?

**Arseniy (author of A), inferred:**
- His engine has this question, defined as "no standing in force for the proposed supplier" (`arseniy_core/ontology/README.md`).
- His gold and his `RULES.md` never use it.
- In world A a supplier's standing is on record only for Meccanica C (the two e-mails), so his engine fires the question for every other supplier.

**Maksim (author of M), inferred:**
- His gold asks it only when the supplier is missing from the supplier master (M01 and M04: `supplier_record`).
- His rule note: "evidence is missing (unknown supplier, coating, material, or no 3.1 certificate) → a question with a named owner, not a violation" (`torino_kakashi/ontology/RULES.md`, R7).

**Core A run:** "It is defensible as a question, but the gold never expects it."

**Evidence:** this is an absence, so no document can be quoted for it. A text search of all 10 A sources finds no "Rivestimenti", "Termica", "Sigma" or "Rovereto". The only standing records are `EML-SQ-2026-0814` and `EML-SQ-2026-1105`, and both are about Meccanica C.

**Vocabulary:** `eval/MAPPING.md` has no row for this rule. The Core M run mapped M's `R7 supplier_record` onto it. Adding it to the gold therefore also needs one MAPPING row: `Q_SUPPLIER_QUALIFICATION_UNKNOWN` → `U_MISSING_EVIDENCE`, key `supplier_record`.

**Edit used below (S):** `{rule: "Q_SUPPLIER_QUALIFICATION_UNKNOWN", rule_u: "U_MISSING_EVIDENCE", key: "supplier_record", kind: "question", inferred: false}`. All four requests are already `blockers_found`, so no verdict changes.

### 4.1 CR-02
- **Request:** "Anodica Veneta has no capacity. I want to move BR-220 anodising to Rivestimenti Nord S.r.l. for the next 3 lots."
- **Current gold** (`blockers_found`): U_CUSTOMER_APPROVAL / STL / blocker (inferred).
- **Specific to this request:** the new party is an anodising subcontractor, not a material source. The only subcontractor on record is the current one:

  > [A · CP-BR220-R3] | 50 | Surface treatment (subcontracted to Anodica Veneta S.r.l.) |

- **Option 1:** add S. A-on-A loses 1 FP; M-on-A gains 1 FN (Core M read this as a process change with no supplier).
- **Option 2:** keep as is. A-on-A keeps 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 2 (keep)** — policy call. No A document states a qualification-record requirement for subcontractors, and A has no supplier master to be absent from; the clause that does apply (CSR 8.4.2.1, surface treatment) is already in the gold as customer approval. Adding it would bring a rule into A that A's vocabulary does not have.

Decision (Valentina):  — time:

### 4.2 CR-12, supplier-record part
- **Request:** see 1.3.
- **Current gold:** see 1.3.
- **Specific to this request:**
  - The supplier is on record; only its Rovereto location is not.
  - REVIEW proposes **not** adding the question here.
  - Core M fired the question only because its encoder gave each supplier location its own id.

  > [A · ASL-TO-2026-04] APPROVAL AP-0311: part BR-220; plant TO1; customer STL; supplier Alluminio B S.r.l. (Settimo Torinese)

- **Option 1:** add S. A-on-A loses 1 FP; M-on-A loses 1 FP.
- **Option 2:** keep as is (REVIEW's proposal). Both engines keep 1 FP; REVIEW expects the engines to stop firing it.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 2 (keep)**, as REVIEW proposes. The supplier is on record; only the location is new, and that is already the source-release blocker.

Decision (Valentina):  — time:

### 4.3 CR-17
- **Request:** "Alluminio B wants to move homogenisation of our BR-220 billet to a toll processor, Termica Nord S.r.l. Same 6082-T6 spec. Accept?"
- **Current gold** (`blockers_found`): U_CUSTOMER_APPROVAL / STL / blocker (inferred).
- **Specific to this request:** Termica Nord would be a sub-supplier of Alluminio B. It appears in no document.
- **Option 1:** add S. A-on-A loses 1 FP; M-on-A gains 1 FN.
- **Option 2:** keep as is. A-on-A keeps 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 2 (keep)** — policy call. Same reason as CR-02: no A document requires a record for a sub-supplier; CSR 8.5.6.1 (change of sub-supplier) is already in the gold as customer approval.

Decision (Valentina):  — time:

### 4.4 CR-20
- **Request:** "The Plant 1 tensile machine is down. Send BR-220 tensile tests for the line 30 check to Laboratorio Sigma in Milan."
- **Current gold** (`blockers_found`): U_CUSTOMER_APPROVAL / STL / blocker (inferred).
- **Specific to this request:** the new party is a test laboratory, not a material supplier.

  > [A · CP-BR220-R3] Note: Tensile tests are performed in the Plant 1 internal materials laboratory.

- **Option 1:** add S. A-on-A loses 1 FP; M-on-A gains 1 FN.
- **Option 2:** keep as is. A-on-A keeps 1 FP.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 2 (keep)** — policy call. Same reason as CR-02; the clause that applies to an external laboratory (CSR 7.1.5.3.2, notification and acceptance of the lab scope) is already in the gold as customer approval.

Decision (Valentina):  — time:

---

## 5. CR-19: service parts (world A)

**REVIEW label:** Unlabelled. REVIEW row 7 is an engine change: "type the completeness statement by commodity (material source) and exclude service parts". It does not propose a gold change.

- **Request:** "Can we ship 300 BR-220 as service parts for STL-Torino-27 using the Alluminio B billet we have in stock?"
- **Current gold** (`needs_info`): U_SOURCE_RELEASE / BR-220 / question. The gold claim reads: "Approval and customer requirements for service parts cannot be determined."
- **Question:** is a single "cannot determine: service parts are outside the approved-supplier list, and the service-part requirements document is not provided" question the right gold?
- **Arseniy (author):** yes. His `RULES.md` uses CR-19 as the example for `Q_SOURCE_RELEASE_UNKNOWN`, and his invariant 4 names it (quoted in 3.2).
- **Other side:** nobody disputes this gold in writing. Both engines return nothing here, and both runs put that down to the engine:
  - Core M run: "service-part scope does not exist (CR-19 has nothing to check)".
  - Core A run: "completeness is scoped by plant only, so "service parts not in scope" cannot be expressed."

**Evidence:**
> [A · ASL-TO-2026-04] Service and aftermarket parts are not in scope of this record.

> [A · CSR-STL-2026-02] Service parts are governed by a separate document, STL-CSR-SP-01, which is not part of this excerpt.

> [A · ASL-TO-2026-04] BR-220 at TO1 for STL has one approved material source: Alluminio B S.r.l. (Settimo Torinese).

**Options:**
- **Option 1:** keep as is. Both engines keep 1 FN and a wrong verdict.
- **Option 2** (nobody has proposed this; listed because the gold claim already covers two things): split into two findings. Keep the current one and add `{rule_u: "U_CUSTOMER_APPROVAL", key: "STL", kind: "question"}` for the missing service-part requirements. The verdict stays `needs_info`. Both engines gain 1 FN.
- **Option 3** (also not proposed): set the verdict to `not_covered`, as `eval/MAPPING.md` allows ("no rule covers the request"). Both engines still get the verdict wrong.

Proposal (Maksim, non-author of world A; based on the documents only): **Option 1 (keep).** "Service and aftermarket parts are not in scope of this record" and "Service parts are governed by a separate document, STL-CSR-SP-01, which is not part of this excerpt": one open question is what the documents support.

Decision (Valentina):  — time:

---

## 6. Open-8D level: I02, I03 (world M)

**REVIEW label:** Policy (row 5, "the 8D level"). REVIEW says: "R3 at series level plus feature, gated by a policy fact … Without the feature gate M's own I03 gains an R3 its gold lacks: add the gate or re-gold."

**Policy question:** when a supplier has an open 8D on one aluminium alloy, when does it count against a part the 8D does not name? Three readings:
- **(a)** same alloy only;
- **(b)** same alloy series (6xxx) only;
- **(c)** same series **and** a document gives the part the 8D's failure feature (fastening holes).

**Maksim (author of M):** reading (a). His rule note: "new supplier has an *open* 8D/NCR on the part's material or alloy" (`torino_kakashi/ontology/RULES.md`, R3). His engine matches on alloy only.

**Arseniy (author of A):** reading (c). His note: "So `B_OPEN_8D_SAME_ALLOY` (the id is frozen in the gold) matches on series plus feature" (`arseniy_core/ontology/README.md`). His gold rule text:
> [author A · eval/worlds/A/RULES.md] Supplier has an open 8D on a failure mode plausible for the part (alloy group 6xxx, fastener holes). No document links the 8D to the part.

**Effects beyond the two rows below:**
- A's gold for CR-01, CR-05 and CR-18 includes the open 8D. That finding holds only under (b) or (c): the 8D is on 6061-T6 and BR-220 is 6082-T6. Under (a) all three would be wrong.
- Under (c), M's S05 loses its open-8D finding too, since it is the same BR-225 case as I02.
- Under (b), I03 is the only M request that changes. Of the SUP-C source changes on 6xxx parts, I01, I02, I08, S01 and S05 already carry the finding.

**Evidence (common, world M):**
> [M · 8D-25-031] 8D report 8D-25-031. Supplier: Meccanica Chisone (SUP-C). Opened 2025-03-20. Status: open.

> [M · 8D-25-031] D2 Problem: cracks around fastening holes on brackets machined from EN AW-6082 material delivered by

> [M · REG-MATERIALS] ALY-6082,EN AW-6082 (AlSi1MgMn),Alloy,,Series6xxx,

> [M · REG-MATERIALS] ALY-6061,EN AW-6061 (AlMg1SiCu),Alloy,,Series6xxx,

> [M · FMEA-BR220] PFMEA BR-220, line 12. Failure mode: crack at the fastening holes under fatigue load.

Only two M documents mention "fastening": 8D-25-031 and FMEA-BR220. No document gives BR-225 or BR-180 any feature.

### 6.1 I02
- **Request** (as of 2026-10-01): "Can Meccanica Chisone take over the BR-225 blanks?"
- **Current gold** (`blockers_found`):
  - U_SUPPLIER_STANDING / SUP-C / blocker
  - U_SOURCE_RELEASE / SUP-C|BR-225|CUST-AUR / blocker
  - U_MATERIAL / MAT-6082-T6 / blocker
  - U_CUSTOMER_APPROVAL / CUST-AUR / blocker (inferred)
  - U_OPEN_ISSUE / 8D-25-031 / blocker (inferred)
  - U_MISSING_EVIDENCE / material_certificate / question
- **Question:** keep the open-8D finding although no document says BR-225 has fastening holes?
- **Maksim:** keep it. The 8D is on EN AW-6082 and BR-225 is drawn in 6082-T6, so the alloy matches.
- **Core A run (describing Arseniy's engine):** "SERIES-8D also demands the 8D failure feature equal a feature of the part. … no document gives BR-225 any feature. Maksim's R3 is alloy-level only. Engine is stricter by design."

**Evidence:**
> [M · REG-MATERIALS] MAT-6082-T6,EN AW-6082-T6,AlloyTemper,ALY-6082,,260

> [M · MTG-2026-10-02] And Chisone is conditional, the cracking 8D on their 6082 material is still open.

The parts register gives BR-225 the material `MAT-6082-T6` (row `BR-225,"Rear subframe bracket, milled",PRG-X,B,MAT-6082-T6,COAT-ANOD,SC-BR225-YS`).

**Options:**
- **Option 1:** keep as is (reading a or b). A-on-M keeps 1 FN.
- **Option 2:** remove `{rule: "R3", rule_u: "U_OPEN_ISSUE", key: "8D-25-031"}` (reading c). The verdict stays `blockers_found`. A-on-M loses 1 FN, and I02 becomes an exact match for Core A. Core M gains 1 FP. For consistency, apply the same removal to S05, where Core M gains another FP.

Decision (Valentina):  — time:

### 6.2 I03
- **Request** (as of 2026-11-14): "Chisone will deliver BR-180 to Pinerolo from now on instead of Beinasco."
- **Current gold** (`blockers_found`):
  - U_SOURCE_RELEASE / SUP-C|BR-180|CUST-AUR / blocker
  - U_CUSTOMER_APPROVAL / CUST-AUR / blocker (inferred)
- **Question:** add the open-8D finding because BR-180 (6061-T6) and the 8D's 6082 are both in the 6xxx series?
- **Maksim:** no, under reading (a).
- **Arseniy:** also no, under reading (c), because no document gives BR-180 a fastening-hole feature. Only reading (b) adds the finding.
- I03 was not in the 10-request sample that Core A ran on, so no run covers it.

**Evidence:**
> [M · REG-MATERIALS] MAT-6061-T6,EN AW-6061-T6,AlloyTemper,ALY-6061,,240

> [M · REG-ASL] APR-002,SUP-C,BR-180,PLT-BEI,CUST-AUR,approved,2023-05-20,,PER-BIANCHI,

The parts register gives BR-180 the material `MAT-6061-T6`. Chisone already supplies BR-180 at Beinasco; only the receiving site changes.

**Options:**
- **Option 1:** keep as is (reading a or c).
- **Option 2:** add `{rule: "R3", rule_u: "U_OPEN_ISSUE", key: "8D-25-031", kind: "blocker", inferred: true}` (reading b). The verdict stays `blockers_found`. Core M today gains 1 FN; a merged engine that matches on series without the feature check would score it as a hit.

Decision (Valentina):  — time:

---

## 7. Certificate from an unknown supplier: M01, M04 (world M)

**REVIEW label:** Unlabelled. The item is listed only in §4 as "M01/M04 (cert from an unknown supplier)".

**Question:** when the proposed supplier is not in the supplier master at all, should the gold also ask for its material certificate, or only for the supplier record?

**Maksim (author of M), inferred from his gold and engine:** only the supplier record. For a supplier missing from the master, his engine asks for the supplier record, checks part approval, and skips the certificate check (`torino_kakashi/core/rules.py`, `check`). The Core A run on M describes it the same way: "Maksim's gold does not ask for a cert from an unknown supplier (it asks for the supplier record first)."

**Arseniy (author of A), inferred from his engine:** also ask for the certificate. His engine asks for one on every raw-material source change that has none on file, and it did so on M01. The Core A run calls the item "Defensible either way."

**Evidence:**
> [M · QP-11] 4.4 A change of source requires a material certificate (EN 10204 type 3.1) from the new supplier for

> [M · QP-11] the drawing material. Missing certificates are an open question for the supplier quality engineer.

"Viteria" appears in no M document, meeting or register. The supplier master lists SUP-B to SUP-H, and the certificates register has no row for it.

**Edit used below (U):** `{rule: "R7", rule_u: "U_MISSING_EVIDENCE", key: "material_certificate", kind: "question", inferred: false}`. It is a different key from the existing `supplier_record`, so it counts as a separate finding. Both verdicts stay `blockers_found`.

### 7.1 M01
- **Request:** "Viteria Lanzo quoted 20% less for the CL-115 clips, let's switch."
- **Current gold** (`blockers_found`):
  - U_MISSING_EVIDENCE / supplier_record / question
  - U_SOURCE_RELEASE / Viteria Lanzo|CL-115|CUST-AUR / blocker
  - U_SOURCE_RELEASE / Viteria Lanzo|CL-115|CUST-NOR / blocker
  - U_CUSTOMER_APPROVAL / CUST-AUR / blocker (inferred)
  - U_CUSTOMER_APPROVAL / CUST-NOR / blocker (inferred)
- **Option 1:** add U. A-on-M loses 1 FP; Core M gains 1 FN.
- **Option 2:** keep as is. A-on-M keeps 1 FP.

Decision (Valentina):  — time:

### 7.2 M04
- **Request:** "Viteria Lanzo can also cast HB-620, let's ask them for the next batch."
- **Current gold** (`blockers_found`):
  - U_MISSING_EVIDENCE / supplier_record / question
  - U_SOURCE_RELEASE / Viteria Lanzo|HB-620|CUST-NOR / blocker
  - U_CUSTOMER_APPROVAL / CUST-NOR / blocker (inferred)
- **Specific to this request:** this is the same pattern as M01, so the ruling should match M01's. M04 was not in Core A's 10-request sample.
- **Option 1:** add U. Core M gains 1 FN.
- **Option 2:** keep as is.

Decision (Valentina):  — time:

---

## 8. Schedule and packaging changes: "no blockers" or "not covered"? C01, C03, C06, C08 (world M)

**Added 14 Nov 11:30** after the merged core (d75144b) was first wired to the eval (adapter check, not a reported run).

- **Requests:** C01 "We postpone the BR-220 delivery to Aurelia by one week." · C03 "Chisone will pack BR-310 forty per layer from next week." · C06 "Double the CL-115 order for December." · C08 "Move the BK-330 delivery slot from Monday to Wednesday."
- **Current gold:** no findings, verdict `no_blockers_found` (derived; M's gold has no verdict field, `eval/MAPPING.md` decision 1).
- **Question:** when no rule covers a change class (schedule, packaging, volume), is the right answer "rules ran, nothing blocks" (`no_blockers_found`) or "no rule covers this, a person decides" (`not_covered`, decision row R0, issue #3)?
- **Maksim (author of M), 13 Nov:** `no_blockers_found`. His rule catalogue: "Changes of delivery date, quantity or packaging alone need no finding unless a rule above applies."
- **Merged core (14 Nov):** `not_covered` for all four: the decision table lists ScheduleChange and PackagingChange among classes no rule covers.
- Findings are not affected (both say: no finding). Only the verdict differs.
- **Option 1:** keep `no_blockers_found`. The core gets 4 wrong verdicts on M.
- **Option 2:** set the verdict of these four to `not_covered`. Model baselines, which cannot answer `not_covered`, get 4 wrong verdicts. Watch out: this moves the gold onto the core's output.
- **Option 3:** score both answers as right on clean schedule/packaging requests (a scoring rule, logged in CHANGES.md).

Decision (Valentina):  — time:
