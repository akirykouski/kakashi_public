# Scores: `eval/results/frozen_scale`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B (all documents → model) | 0.86 [0.78–0.92] (83/96) | 1.00 [0.96–1.00] (83/83) | 1.00 [0.91–1.00] (38/38) | 0.72 [0.56–0.84] (26/36) | 0.86 [0.71–0.94] (31/36) | 0.50 [0.22–0.78] (4/8) | – | – | 110769 / 1684 | 17.8 | 0 |
| C (model parse → core) | 0.99 [0.92–1.00] (70/71) | 0.84 [0.75–0.91] (70/83) | 0.95 [0.83–0.99] (36/38) | 0.81 [0.65–0.90] (29/36) | 0.97 [0.86–1.00] (35/36) | 0.00 [0.00–0.32] (0/8) | – | – | 2109 / 251 | 8.09 | 0 |
| C* (hand parse → core) | 1.00 [0.95–1.00] (81/81) | 0.98 [0.92–0.99] (81/83) | 1.00 [0.91–1.00] (38/38) | 0.94 [0.82–0.98] (34/36) | 0.97 [0.86–1.00] (35/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.07 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| B (all documents → model) | 0.88 [0.53–0.98] (7/8) | 0.89 [0.56–0.98] (8/9) | 0.57 [0.25–0.84] (4/7) | 0.75 [0.30–0.95] (3/4) | 0.50 [0.22–0.78] (4/8) |
| C (model parse → core) | 1.00 [0.68–1.00] (8/8) | 0.78 [0.45–0.94] (7/9) | 0.86 [0.49–0.97] (6/7) | 0.00 [0.00–0.49] (0/4) | 1.00 [0.68–1.00] (8/8) |
| C* (hand parse → core) | 1.00 [0.68–1.00] (8/8) | 1.00 [0.70–1.00] (9/9) | 1.00 [0.65–1.00] (7/7) | 0.50 [0.15–0.85] (2/4) | 1.00 [0.68–1.00] (8/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| B (all documents → model) | 0.85 [0.75–0.91] (67/79) | 0.99 [0.92–1.00] (67/68) | 0.88 [0.66–0.97] (15/17) | 1.00 [0.80–1.00] (15/15) |
| C (model parse → core) | 0.98 [0.91–1.00] (61/62) | 0.90 [0.80–0.95] (61/68) | 1.00 [0.70–1.00] (9/9) | 0.60 [0.36–0.80] (9/15) |
| C* (hand parse → core) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.77–1.00] (13/13) | 0.87 [0.62–0.96] (13/15) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| B vs C | 5 / 8, p = 0.5811 | 0 / 4, p = 0.125 |
| B vs Cstar | 2 / 10, p = 0.0386 | 0 / 4, p = 0.125 |
| C vs Cstar | 0 / 5, p = 0.0625 | 0 / 0, p = 1.0 |

Per-request misses and extras:

- **B (all documents → model)**: 10 requests not exact or wrong verdict
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - S03 (stale): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-aur')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')]
  - C05 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
- **C (model parse → core)**: 8 requests not exact or wrong verdict
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-26-009')] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'coating_substances')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_data')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record'), ('U_SOURCE_RELEASE', 'viteria lanzo|hb-620|cust-nor')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
- **C* (hand parse → core)**: 3 requests not exact or wrong verdict
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []

## World A

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|

Per-request misses and extras:

