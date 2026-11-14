# Scores: `eval/results/frozen_ablations/no_inference`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.94 [0.74–0.99] (17/18) | 0.20 [0.13–0.30] (17/83) | 0.00 [0.00–0.09] (0/38) | 0.25 [0.14–0.41] (9/36) | 0.47 [0.32–0.63] (17/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.02 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.30] (0/9) | 0.14 [0.03–0.51] (1/7) | 0.00 [0.00–0.49] (0/4) | 1.00 [0.68–1.00] (8/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 1.00 [0.76–1.00] (12/12) | 0.18 [0.10–0.28] (12/68) | 0.83 [0.44–0.97] (5/6) | 0.33 [0.15–0.58] (5/15) |

Per-request misses and extras:

- **C* (hand parse → core)**: 29 requests not exact or wrong verdict
  - D01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-e|hb-620|cust-nor')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-g|sp-700|cust-aur')] extra []
  - D03 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra []
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_RESTRICTED_SUBSTANCE', 'crvi')] extra []
  - D06 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_RESTRICTED_SUBSTANCE', 'crvi')] extra []
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|hs-410|cust-aur')] extra []
  - D08 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6061-t6')] extra [('U_MISSING_EVIDENCE', 'material_data')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra []
  - I02 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra []
  - I03 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I04 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_RESTRICTED_SUBSTANCE', 'crvi')] extra []
  - I05 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-310|cust-nor')] extra []
  - I07 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra []
  - I08 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - I09 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-h|hb-620|cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra []
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-26-009'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra []
  - S06 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S07 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-26-009')] extra []
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|hb-620|cust-nor')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - C04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []

## World A

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.60 [0.23–0.88] (3/5) | 0.09 [0.03–0.24] (3/32) | 0.00 [0.00–0.22] (0/14) | 0.15 [0.05–0.36] (3/20) | 0.20 [0.08–0.42] (4/20) | 0.00 [0.00–0.66] (0/2) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.01 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.00 [0.00–0.43] (0/5) | 0.00 [0.00–0.39] (0/6) | 0.25 [0.05–0.70] (1/4) | 0.00 [0.00–0.56] (0/3) | 1.00 [0.34–1.00] (2/2) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 1.00 [0.44–1.00] (3/3) | 0.12 [0.04–0.30] (3/25) | 0.00 [0.00–0.66] (0/2) | 0.00 [0.00–0.35] (0/7) |

Per-request misses and extras:

- **C* (hand parse → core)**: 19 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-02 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-07 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-10 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-11 (missing): verdict no_blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-180')] extra []
  - CR-12 (direct): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MATERIAL', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_data')]
  - CR-14 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-16 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'br-310')] extra []
  - CR-17 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-19 (missing): verdict no_blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-20 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []

## World both

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.87 [0.68–0.95] (20/23) | 0.17 [0.12–0.25] (20/115) | 0.00 [0.00–0.07] (0/52) | 0.21 [0.13–0.34] (12/56) | 0.38 [0.26–0.51] (21/56) | 0.00 [0.00–0.28] (0/10) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.01 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.00 [0.00–0.23] (0/13) | 0.00 [0.00–0.20] (0/15) | 0.18 [0.05–0.48] (2/11) | 0.00 [0.00–0.35] (0/7) | 1.00 [0.72–1.00] (10/10) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 1.00 [0.80–1.00] (15/15) | 0.16 [0.10–0.25] (15/93) | 0.62 [0.31–0.86] (5/8) | 0.23 [0.10–0.43] (5/22) |

Per-request misses and extras:

- **C* (hand parse → core)**: 48 requests not exact or wrong verdict
  - D01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-e|hb-620|cust-nor')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-g|sp-700|cust-aur')] extra []
  - D03 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra []
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_RESTRICTED_SUBSTANCE', 'crvi')] extra []
  - D06 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_RESTRICTED_SUBSTANCE', 'crvi')] extra []
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|hs-410|cust-aur')] extra []
  - D08 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6061-t6')] extra [('U_MISSING_EVIDENCE', 'material_data')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra []
  - I02 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra []
  - I03 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I04 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_RESTRICTED_SUBSTANCE', 'crvi')] extra []
  - I05 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-310|cust-nor')] extra []
  - I07 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra []
  - I08 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - I09 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-h|hb-620|cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra []
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-26-009'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra []
  - S06 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S07 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-26-009')] extra []
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|hb-620|cust-nor')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - C04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-02 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-07 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-10 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-11 (missing): verdict no_blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-180')] extra []
  - CR-12 (direct): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MATERIAL', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_data')]
  - CR-14 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-16 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'br-310')] extra []
  - CR-17 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-19 (missing): verdict no_blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-20 (inferred): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
