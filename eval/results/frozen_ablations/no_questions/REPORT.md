# Scores: `eval/results/frozen_ablations/no_questions`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 1.00 [0.95–1.00] (68/68) | 0.82 [0.72–0.89] (68/83) | 1.00 [0.91–1.00] (38/38) | 0.64 [0.48–0.78] (23/36) | 0.97 [0.86–1.00] (35/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.02 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.62 [0.31–0.86] (5/8) | 0.56 [0.27–0.81] (5/9) | 0.71 [0.36–0.92] (5/7) | 0.00 [0.00–0.49] (0/4) | 1.00 [0.68–1.00] (8/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.95–1.00] (68/68) | – | 0.00 [0.00–0.20] (0/15) |

Per-request misses and extras:

- **C* (hand parse → core)**: 14 requests not exact or wrong verdict
  - D01 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I02 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I06 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I07 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record')] extra []
  - M02 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'coating_substances')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_data')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []

## World A

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.96 [0.79–0.99] (22/23) | 0.69 [0.51–0.82] (22/32) | 1.00 [0.78–1.00] (14/14) | 0.55 [0.34–0.74] (11/20) | 0.65 [0.43–0.82] (13/20) | 0.00 [0.00–0.66] (0/2) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.01 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.20 [0.04–0.62] (1/5) | 1.00 [0.61–1.00] (6/6) | 0.50 [0.15–0.85] (2/4) | 0.00 [0.00–0.56] (0/3) | 1.00 [0.34–1.00] (2/2) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 0.96 [0.79–0.99] (22/23) | 0.88 [0.70–0.96] (22/25) | – | 0.00 [0.00–0.35] (0/7) |

Per-request misses and extras:

- **C* (hand parse → core)**: 11 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-180')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-19 (missing): verdict no_blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra []

## World both

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C* (hand parse → core) | 0.99 [0.94–1.00] (90/91) | 0.78 [0.70–0.85] (90/115) | 1.00 [0.93–1.00] (52/52) | 0.61 [0.48–0.72] (34/56) | 0.86 [0.74–0.93] (48/56) | 0.00 [0.00–0.28] (0/10) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.02 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C* (hand parse → core) | 0.46 [0.23–0.71] (6/13) | 0.73 [0.48–0.89] (11/15) | 0.64 [0.35–0.85] (7/11) | 0.00 [0.00–0.35] (0/7) | 1.00 [0.72–1.00] (10/10) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| C* (hand parse → core) | 0.99 [0.94–1.00] (90/91) | 0.97 [0.91–0.99] (90/93) | – | 0.00 [0.00–0.15] (0/22) |

Per-request misses and extras:

- **C* (hand parse → core)**: 25 requests not exact or wrong verdict
  - D01 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I02 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I06 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I07 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record')] extra []
  - M02 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'coating_substances')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_data')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-06 (missing): verdict no_blockers_found (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []; ERROR no change type the core accepts
  - CR-08 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra []; ERROR no change type the core accepts
  - CR-09 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []; ERROR no change type the core accepts
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-180')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-19 (missing): verdict no_blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra []
