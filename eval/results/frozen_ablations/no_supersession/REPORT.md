# Scores: `eval/results/frozen_ablations/no_supersession`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.93 [0.85–0.97] (79/85) | 0.95 [0.88–0.98] (79/83) | 0.97 [0.86–1.00] (37/38) | 0.75 [0.59–0.86] (27/36) | 0.97 [0.86–1.00] (35/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.02 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.88 [0.53–0.98] (7/8) | 0.67 [0.35–0.88] (6/9) | 0.57 [0.25–0.84] (4/7) | 0.50 [0.15–0.85] (2/4) | 1.00 [0.68–1.00] (8/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 0.92 [0.83–0.96] (66/72) | 0.97 [0.90–0.99] (66/68) | 1.00 [0.77–1.00] (13/13) | 0.87 [0.62–0.96] (13/15) |

Per-request misses and extras:

- **C* (hand parse → core)**: 10 requests not exact or wrong verdict
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I07 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []

## World A

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.63 [0.46–0.77] (22/35) | 0.69 [0.51–0.82] (22/32) | 1.00 [0.78–1.00] (14/14) | 0.35 [0.18–0.57] (7/20) | 0.70 [0.48–0.85] (14/20) | 0.00 [0.00–0.66] (0/2) | 0.38 [0.14–0.69] (3/8) | 0.50 [0.09–0.91] (1/2) | 0 / 0 | 0.01 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.00 [0.00–0.43] (0/5) | 0.67 [0.30–0.90] (4/6) | 0.25 [0.05–0.70] (1/4) | 0.00 [0.00–0.56] (0/3) | 1.00 [0.34–1.00] (2/2) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 0.75 [0.55–0.88] (18/24) | 0.72 [0.52–0.86] (18/25) | 0.36 [0.15–0.65] (4/11) | 0.57 [0.25–0.84] (4/7) |

Per-request misses and extras:

- **C* (hand parse → core)**: 15 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-14 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-16 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]

## World both

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.84 [0.77–0.90] (101/120) | 0.88 [0.81–0.93] (101/115) | 0.98 [0.90–1.00] (51/52) | 0.61 [0.48–0.72] (34/56) | 0.88 [0.76–0.94] (49/56) | 0.00 [0.00–0.28] (0/10) | 0.38 [0.14–0.69] (3/8) | 0.50 [0.09–0.91] (1/2) | 0 / 0 | 0.02 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.54 [0.29–0.77] (7/13) | 0.67 [0.42–0.85] (10/15) | 0.45 [0.21–0.72] (5/11) | 0.29 [0.08–0.64] (2/7) | 1.00 [0.72–1.00] (10/10) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 0.88 [0.79–0.93] (84/96) | 0.90 [0.83–0.95] (84/93) | 0.71 [0.51–0.85] (17/24) | 0.77 [0.57–0.90] (17/22) |

Per-request misses and extras:

- **C* (hand parse → core)**: 25 requests not exact or wrong verdict
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I07 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-14 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'coating_substances')]
  - CR-16 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'br-220')] extra [('U_SUPPLIER_STANDING', 'meccanica c')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
