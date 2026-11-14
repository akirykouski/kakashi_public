# Blocker rule slugs

The `rule` field in `gold.jsonl` uses the blocker type ids listed in `ontology/README.md` (checked 13 Nov 2026, peer-owned, read only here). Two gold rules have no ontology id yet and keep a provisional snake_case slug (marked NEW below). `cleared` entries carry the id of the blocker that does not fire.

| rule | kind | meaning | example (request id) |
|---|---|---|---|
| `B_NO_SOURCE_RELEASE` | blocker | No approval for this exact part x plant x customer x supplier location, in a list that declares itself complete for that scope (ASL-TO-2026-04). | CR-01: Meccanica C has no approval for BR-220 at TO1 for STL |
| `B_MATERIAL_MISMATCH` | blocker | Offered or requested grade differs from the grade on the current drawing revision. 6061 and 6082 are different alloys. | CR-01: C supplies 6061-T6, drawing Rev C requires 6082-T6 |
| `B_CUSTOMER_APPROVAL_REQUIRED` | inferred | A change falls under an OEM requirement clause reached through part -> program (BOM) -> clause. | CR-01: source change -> STL-Torino-27 -> clause 8.5.6.1 (IATF 16949 8.5.6.1) |
| `B_OPEN_8D_SAME_ALLOY` | inferred | Supplier has an open 8D on a failure mode plausible for the part (alloy group 6xxx, fastener holes). No document links the 8D to the part. | CR-01: 8D-25-031 |
| `B_SUPPLIER_NOT_QUALIFIED` | cleared | Supplier-level probation. Appears only in `cleared` after the 2026-11-05 email supersedes the 2026-08-14 email. | CR-03, CR-18 |
| `Q_NO_MATERIAL_CERT` | question | Required material certificate or test result is not in the documents. Missing data, not a violation. | CR-06: heat H-4471 |
| `Q_SOURCE_RELEASE_UNKNOWN` | question | No controlled record covers the scope, so absence of an approval is unknown, not a blocker. | CR-11: Plant 3; CR-19: service parts |
| `special_characteristic_violation` (NEW) | blocker | A measured value fails a special characteristic of the current drawing and control plan. | CR-08: 245 MPa vs >= 250 MPa (SC-01) |
| `deviation_limit_exceeded` (NEW) | blocker | Temporary deviation request exceeds PRC-DEV-007 limits (2000 pieces, 6 weeks). | CR-09: 3,500 pieces over 10 weeks |

## Domain invariants encoded in the gold

1. Approval is per part x plant x customer (and supplier manufacturing location), never per supplier.
2. EN AW-6061-T6 and EN AW-6082-T6 are different alloys.
3. A supplier audit does not grant a part approval (CR-18: probation clears, part approval stays missing).
4. Absence of an approval is a blocker only where a controlled record declares itself complete for that scope. Otherwise it is a question with an owner (CR-11, CR-19).
5. A newer document cannot supersede a controlled record by restating an old value. EML-SQ-2026-1105 restates the Rev B alloy and yield in passing. It is informal and does not override drawing Rev C (CR-13).
6. A superseded fact is never cited as authority: Rev B values, the 2026-08-14 probation (`must_not_cite`).
