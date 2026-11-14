# Scores: `eval/results/posthoc/1_main_a771378`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C (model parse → core) | 0.99 [0.93–1.00] (73/74) | 0.88 [0.79–0.93] (73/83) | 0.89 [0.76–0.96] (34/38) | 0.83 [0.68–0.92] (30/36) | 0.94 [0.82–0.98] (34/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.02 | 0 |
| C* (hand parse → core) | 1.00 [0.95–1.00] (81/81) | 0.98 [0.92–0.99] (81/83) | 1.00 [0.91–1.00] (38/38) | 0.94 [0.82–0.98] (34/36) | 0.97 [0.86–1.00] (35/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.02 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C (model parse → core) | 1.00 [0.68–1.00] (8/8) | 0.78 [0.45–0.94] (7/9) | 0.71 [0.36–0.92] (5/7) | 0.50 [0.15–0.85] (2/4) | 1.00 [0.68–1.00] (8/8) |
| C* (hand parse → core) | 1.00 [0.68–1.00] (8/8) | 1.00 [0.70–1.00] (9/9) | 1.00 [0.65–1.00] (7/7) | 0.50 [0.15–0.85] (2/4) | 1.00 [0.68–1.00] (8/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C (model parse → core) | 0.98 [0.91–1.00] (60/61) | 0.88 [0.78–0.94] (60/68) | 1.00 [0.77–1.00] (13/13) | 0.87 [0.62–0.96] (13/15) |
| C* (hand parse → core) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.77–1.00] (13/13) | 0.87 [0.62–0.96] (13/15) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| C vs Cstar | 0 / 4, p = 0.125 | 0 / 1, p = 1.0 |

Per-request misses and extras:

- **C (model parse → core)**: 7 requests not exact or wrong verdict
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - S04 (stale): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-26-009'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor'), ('U_SUPPLIER_STANDING', 'sup-d')] extra []
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-26-009')] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
- **C* (hand parse → core)**: 3 requests not exact or wrong verdict
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []

## World A

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C (model parse → core) | 0.67 [0.50–0.80] (24/36) | 0.75 [0.58–0.87] (24/32) | 0.93 [0.69–0.99] (13/14) | 0.40 [0.22–0.61] (8/20) | 0.55 [0.34–0.74] (11/20) | 0.50 [0.09–0.91] (1/2) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.01 | 0 |
| C* (hand parse → core) | 0.76 [0.60–0.88] (26/34) | 0.81 [0.65–0.91] (26/32) | 1.00 [0.78–1.00] (14/14) | 0.50 [0.30–0.70] (10/20) | 0.70 [0.48–0.85] (14/20) | 0.00 [0.00–0.66] (0/2) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.01 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C (model parse → core) | 0.40 [0.12–0.77] (2/5) | 0.50 [0.19–0.81] (3/6) | 0.50 [0.15–0.85] (2/4) | 0.00 [0.00–0.56] (0/3) | 0.50 [0.09–0.91] (1/2) |
| C* (hand parse → core) | 0.40 [0.12–0.77] (2/5) | 0.67 [0.30–0.90] (4/6) | 0.50 [0.15–0.85] (2/4) | 0.00 [0.00–0.56] (0/3) | 1.00 [0.34–1.00] (2/2) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C (model parse → core) | 0.80 [0.61–0.91] (20/25) | 0.80 [0.61–0.91] (20/25) | 0.36 [0.15–0.65] (4/11) | 0.57 [0.25–0.84] (4/7) |
| C* (hand parse → core) | 0.96 [0.79–0.99] (22/23) | 0.88 [0.70–0.96] (22/25) | 0.36 [0.15–0.65] (4/11) | 0.57 [0.25–0.84] (4/7) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| C vs Cstar | 0 / 2, p = 0.5 | 1 / 4, p = 0.375 |

Per-request misses and extras:

- **C (model parse → core)**: 14 requests not exact or wrong verdict
  - CR-02 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'supplier_record'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-06 (missing): verdict not_covered (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-09 (direct): verdict not_covered (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'supplier_record')]
  - CR-12 (direct): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-14 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-16 (direct): verdict not_covered (gold blockers_found); missed [('U_SOURCE_RELEASE', 'br-310')] extra []
  - CR-19 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_data')]
- **C* (hand parse → core)**: 12 requests not exact or wrong verdict
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-14 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-16 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]

## World both

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C (model parse → core) | 0.88 [0.81–0.93] (97/110) | 0.84 [0.77–0.90] (97/115) | 0.90 [0.79–0.96] (47/52) | 0.68 [0.55–0.79] (38/56) | 0.80 [0.68–0.89] (45/56) | 0.10 [0.02–0.40] (1/10) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.02 | 0 |
| C* (hand parse → core) | 0.93 [0.87–0.96] (107/115) | 0.93 [0.87–0.96] (107/115) | 1.00 [0.93–1.00] (52/52) | 0.79 [0.66–0.87] (44/56) | 0.88 [0.76–0.94] (49/56) | 0.00 [0.00–0.28] (0/10) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.02 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C (model parse → core) | 0.77 [0.50–0.92] (10/13) | 0.67 [0.42–0.85] (10/15) | 0.64 [0.35–0.85] (7/11) | 0.29 [0.08–0.64] (2/7) | 0.90 [0.60–0.98] (9/10) |
| C* (hand parse → core) | 0.77 [0.50–0.92] (10/13) | 0.87 [0.62–0.96] (13/15) | 0.82 [0.52–0.95] (9/11) | 0.29 [0.08–0.64] (2/7) | 1.00 [0.72–1.00] (10/10) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C (model parse → core) | 0.93 [0.86–0.97] (80/86) | 0.86 [0.78–0.92] (80/93) | 0.71 [0.51–0.85] (17/24) | 0.77 [0.57–0.90] (17/22) |
| C* (hand parse → core) | 0.99 [0.94–1.00] (90/91) | 0.97 [0.91–0.99] (90/93) | 0.71 [0.51–0.85] (17/24) | 0.77 [0.57–0.90] (17/22) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| C vs Cstar | 0 / 6, p = 0.0312 | 1 / 5, p = 0.2188 |

Per-request misses and extras:

- **C (model parse → core)**: 21 requests not exact or wrong verdict
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - S04 (stale): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-26-009'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor'), ('U_SUPPLIER_STANDING', 'sup-d')] extra []
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-26-009')] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-02 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'supplier_record'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-06 (missing): verdict not_covered (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-09 (direct): verdict not_covered (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'supplier_record')]
  - CR-12 (direct): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-14 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-16 (direct): verdict not_covered (gold blockers_found); missed [('U_SOURCE_RELEASE', 'br-310')] extra []
  - CR-19 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_data')]
- **C* (hand parse → core)**: 15 requests not exact or wrong verdict
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-14 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-16 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
