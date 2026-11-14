# Scores: `eval/results/frozen`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.61 [0.47–0.73] (31/51) | 0.37 [0.28–0.48] (31/83) | 0.24 [0.13–0.39] (9/38) | 0.25 [0.14–0.41] (9/36) | 0.58 [0.42–0.73] (21/36) | 0.25 [0.07–0.59] (2/8) | – | – | 4532 / 1008 | 9.25 | 0 |
| A' (BM25 + dense top-8 → model) | 0.59 [0.44–0.72] (27/46) | 0.33 [0.23–0.43] (27/83) | 0.18 [0.09–0.33] (7/38) | 0.22 [0.12–0.38] (8/36) | 0.56 [0.40–0.70] (20/36) | 0.25 [0.07–0.59] (2/8) | – | – | 4364 / 904 | 8.12 | 0 |
| B (all documents → model) | 0.87 [0.79–0.92] (80/92) | 0.96 [0.90–0.99] (80/83) | 0.97 [0.86–1.00] (37/38) | 0.67 [0.50–0.80] (24/36) | 0.86 [0.71–0.94] (31/36) | 0.50 [0.22–0.78] (4/8) | – | – | 14543 / 1566 | 10.98 | 0 |
| C (model parse → core) | 0.99 [0.92–1.00] (66/67) | 0.80 [0.70–0.87] (66/83) | 0.89 [0.76–0.96] (34/38) | 0.78 [0.62–0.88] (28/36) | 0.94 [0.82–0.98] (34/36) | 0.00 [0.00–0.32] (0/8) | – | – | 2109 / 262 | 5.74 | 0 |
| C* (hand parse → core) | 1.00 [0.95–1.00] (81/81) | 0.98 [0.92–0.99] (81/83) | 1.00 [0.91–1.00] (38/38) | 0.94 [0.82–0.98] (34/36) | 0.97 [0.86–1.00] (35/36) | 0.00 [0.00–0.32] (0/8) | – | – | 0 / 0 | 0.02 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.12 [0.02–0.47] (1/8) | 0.00 [0.00–0.30] (0/9) | 0.29 [0.08–0.64] (2/7) | 0.00 [0.00–0.49] (0/4) | 0.75 [0.41–0.93] (6/8) |
| A' (BM25 + dense top-8 → model) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.30] (0/9) | 0.29 [0.08–0.64] (2/7) | 0.00 [0.00–0.49] (0/4) | 0.75 [0.41–0.93] (6/8) |
| B (all documents → model) | 0.75 [0.41–0.93] (6/8) | 0.78 [0.45–0.94] (7/9) | 0.57 [0.25–0.84] (4/7) | 0.75 [0.30–0.95] (3/4) | 0.50 [0.22–0.78] (4/8) |
| C (model parse → core) | 1.00 [0.68–1.00] (8/8) | 0.78 [0.45–0.94] (7/9) | 0.71 [0.36–0.92] (5/7) | 0.00 [0.00–0.49] (0/4) | 1.00 [0.68–1.00] (8/8) |
| C* (hand parse → core) | 1.00 [0.68–1.00] (8/8) | 1.00 [0.70–1.00] (9/9) | 1.00 [0.65–1.00] (7/7) | 0.50 [0.15–0.85] (2/4) | 1.00 [0.68–1.00] (8/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.61 [0.42–0.76] (17/28) | 0.25 [0.16–0.36] (17/68) | 0.30 [0.16–0.51] (7/23) | 0.47 [0.25–0.70] (7/15) |
| A' (BM25 + dense top-8 → model) | 0.62 [0.43–0.78] (16/26) | 0.24 [0.15–0.35] (16/68) | 0.30 [0.15–0.52] (6/20) | 0.40 [0.20–0.64] (6/15) |
| B (all documents → model) | 0.86 [0.76–0.92] (65/76) | 0.96 [0.88–0.98] (65/68) | 0.94 [0.72–0.99] (15/16) | 1.00 [0.80–1.00] (15/15) |
| C (model parse → core) | 0.98 [0.91–1.00] (57/58) | 0.84 [0.73–0.91] (57/68) | 1.00 [0.70–1.00] (9/9) | 0.60 [0.36–0.80] (9/15) |
| C* (hand parse → core) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.95–1.00] (68/68) | 1.00 [0.77–1.00] (13/13) | 0.87 [0.62–0.96] (13/15) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| A vs Aprime | 1 / 0, p = 1.0 | 2 / 1, p = 1.0 |
| A vs B | 4 / 19, p = 0.0026 | 3 / 13, p = 0.0213 |
| A vs C | 0 / 19, p = 0.0 | 1 / 14, p = 0.001 |
| A vs Cstar | 0 / 25, p = 0.0 | 0 / 14, p = 0.0001 |
| Aprime vs B | 3 / 19, p = 0.0009 | 3 / 14, p = 0.0127 |
| Aprime vs C | 0 / 20, p = 0.0 | 1 / 15, p = 0.0005 |
| Aprime vs Cstar | 0 / 26, p = 0.0 | 0 / 15, p = 0.0001 |
| B vs C | 5 / 9, p = 0.424 | 1 / 4, p = 0.375 |
| B vs Cstar | 2 / 12, p = 0.0129 | 0 / 4, p = 0.125 |
| C vs Cstar | 0 / 6, p = 0.0312 | 0 / 1, p = 1.0 |

Per-request misses and extras:

- **A (BM25 top-8 → model)**: 27 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra [('U_OPEN_ISSUE', 'cracking 8d on sup-c 6082 material (issue id not given in documents)'), ('U_SOURCE_RELEASE', 'sup-c|br-220|customer not stated')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|unknown')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no issue id in documents)'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d on chisone 6082 cracks (no issue id given)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra [('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|unknown')]
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
- **A' (BM25 + dense top-8 → model)**: 28 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3')] extra []
  - D02 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-g|sp-700|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-g|sp-700|unknown')]
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d on cracking, chisone 6082 material (id not in documents)')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-b|br-310|unknown')]
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|customer not identified')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-c|br-310|unknown'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no issue id in documents)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
- **B (all documents → model)**: 12 requests not exact or wrong verdict
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-pa66gf30')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I06 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-6082-t5')] extra []
  - S03 (stale): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-aur')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')]
  - C05 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
- **C (model parse → core)**: 9 requests not exact or wrong verdict
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - S04 (stale): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-26-009'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor'), ('U_SUPPLIER_STANDING', 'sup-d')] extra []
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
| A (BM25 top-8 → model) | 0.73 [0.54–0.86] (19/26) | 0.59 [0.42–0.74] (19/32) | 0.21 [0.08–0.48] (3/14) | 0.45 [0.26–0.66] (9/20) | 0.80 [0.58–0.92] (16/20) | 0.50 [0.09–0.91] (1/2) | 0.38 [0.14–0.69] (3/8) | 0.00 [0.00–0.66] (0/2) | 5511 / 1307 | 9.93 | 0 |
| A' (BM25 + dense top-8 → model) | 0.76 [0.57–0.89] (19/25) | 0.59 [0.42–0.74] (19/32) | 0.21 [0.08–0.48] (3/14) | 0.45 [0.26–0.66] (9/20) | 0.85 [0.64–0.95] (17/20) | 0.00 [0.00–0.66] (0/2) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 6556 / 1400 | 10.83 | 0 |
| B (all documents → model) | 0.82 [0.67–0.91] (32/39) | 1.00 [0.89–1.00] (32/32) | 1.00 [0.78–1.00] (14/14) | 0.70 [0.48–0.85] (14/20) | 0.95 [0.76–0.99] (19/20) | 0.50 [0.09–0.91] (1/2) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 10548 / 1516 | 10.6 | 0 |
| C (model parse → core) | 0.74 [0.57–0.86] (23/31) | 0.72 [0.55–0.84] (23/32) | 0.93 [0.69–0.99] (13/14) | 0.50 [0.30–0.70] (10/20) | 0.55 [0.34–0.74] (11/20) | 0.50 [0.09–0.91] (1/2) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 2132 / 426 | 4.41 | 0 |
| C* (hand parse → core) | 0.76 [0.60–0.88] (26/34) | 0.81 [0.65–0.91] (26/32) | 1.00 [0.78–1.00] (14/14) | 0.50 [0.30–0.70] (10/20) | 0.70 [0.48–0.85] (14/20) | 0.00 [0.00–0.66] (0/2) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.01 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.20 [0.04–0.62] (1/5) | 0.50 [0.19–0.81] (3/6) | 0.50 [0.15–0.85] (2/4) | 0.67 [0.21–0.94] (2/3) | 0.50 [0.09–0.91] (1/2) |
| A' (BM25 + dense top-8 → model) | 0.20 [0.04–0.62] (1/5) | 0.33 [0.10–0.70] (2/6) | 0.50 [0.15–0.85] (2/4) | 0.67 [0.21–0.94] (2/3) | 1.00 [0.34–1.00] (2/2) |
| B (all documents → model) | 0.60 [0.23–0.88] (3/5) | 0.83 [0.44–0.97] (5/6) | 0.75 [0.30–0.95] (3/4) | 0.67 [0.21–0.94] (2/3) | 0.50 [0.09–0.91] (1/2) |
| C (model parse → core) | 0.40 [0.12–0.77] (2/5) | 0.83 [0.44–0.97] (5/6) | 0.50 [0.15–0.85] (2/4) | 0.00 [0.00–0.56] (0/3) | 0.50 [0.09–0.91] (1/2) |
| C* (hand parse → core) | 0.40 [0.12–0.77] (2/5) | 0.67 [0.30–0.90] (4/6) | 0.50 [0.15–0.85] (2/4) | 0.00 [0.00–0.56] (0/3) | 1.00 [0.34–1.00] (2/2) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.82 [0.59–0.94] (14/17) | 0.56 [0.37–0.73] (14/25) | 0.56 [0.27–0.81] (5/9) | 0.71 [0.36–0.92] (5/7) |
| A' (BM25 + dense top-8 → model) | 0.81 [0.57–0.93] (13/16) | 0.52 [0.34–0.70] (13/25) | 0.67 [0.35–0.88] (6/9) | 0.86 [0.49–0.97] (6/7) |
| B (all documents → model) | 0.86 [0.69–0.94] (25/29) | 1.00 [0.87–1.00] (25/25) | 0.70 [0.40–0.89] (7/10) | 1.00 [0.65–1.00] (7/7) |
| C (model parse → core) | 0.83 [0.64–0.93] (20/24) | 0.80 [0.61–0.91] (20/25) | 0.43 [0.16–0.75] (3/7) | 0.43 [0.16–0.75] (3/7) |
| C* (hand parse → core) | 0.96 [0.79–0.99] (22/23) | 0.88 [0.70–0.96] (22/25) | 0.36 [0.15–0.65] (4/11) | 0.57 [0.25–0.84] (4/7) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| A vs Aprime | 1 / 1, p = 1.0 | 1 / 2, p = 1.0 |
| A vs B | 1 / 6, p = 0.125 | 0 / 3, p = 0.25 |
| A vs C | 5 / 6, p = 1.0 | 8 / 3, p = 0.2266 |
| A vs Cstar | 6 / 7, p = 1.0 | 6 / 4, p = 0.7539 |
| Aprime vs B | 2 / 7, p = 0.1797 | 1 / 3, p = 0.625 |
| Aprime vs C | 6 / 7, p = 1.0 | 9 / 3, p = 0.146 |
| Aprime vs Cstar | 6 / 7, p = 1.0 | 6 / 3, p = 0.5078 |
| B vs C | 5 / 1, p = 0.2188 | 8 / 0, p = 0.0078 |
| B vs Cstar | 6 / 2, p = 0.2891 | 6 / 1, p = 0.125 |
| C vs Cstar | 1 / 1, p = 1.0 | 1 / 4, p = 0.375 |

Per-request misses and extras:

- **A (BM25 top-8 → model)**: 11 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **A' (BM25 + dense top-8 → model)**: 11 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-07 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MATERIAL', 'br-220'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **B (all documents → model)**: 6 requests not exact or wrong verdict
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-16 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
- **C (model parse → core)**: 12 requests not exact or wrong verdict
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-06 (missing): verdict not_covered (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-09 (direct): verdict not_covered (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-180')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-16 (direct): verdict not_covered (gold blockers_found); missed [('U_SOURCE_RELEASE', 'br-310')] extra []
  - CR-19 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
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
| A (BM25 top-8 → model) | 0.65 [0.54–0.75] (50/77) | 0.43 [0.35–0.53] (50/115) | 0.23 [0.14–0.36] (12/52) | 0.32 [0.21–0.45] (18/56) | 0.66 [0.53–0.77] (37/56) | 0.30 [0.11–0.60] (3/10) | 0.38 [0.14–0.69] (3/8) | 0.00 [0.00–0.66] (0/2) | 4882 / 1115 | 9.49 | 0 |
| A' (BM25 + dense top-8 → model) | 0.65 [0.53–0.75] (46/71) | 0.40 [0.32–0.49] (46/115) | 0.19 [0.11–0.32] (10/52) | 0.30 [0.20–0.43] (17/56) | 0.66 [0.53–0.77] (37/56) | 0.20 [0.06–0.51] (2/10) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 5147 / 1081 | 9.09 | 0 |
| B (all documents → model) | 0.85 [0.78–0.91] (112/131) | 0.97 [0.93–0.99] (112/115) | 0.98 [0.90–1.00] (51/52) | 0.68 [0.55–0.79] (38/56) | 0.89 [0.79–0.95] (50/56) | 0.50 [0.24–0.76] (5/10) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 13116 / 1548 | 10.85 | 0 |
| C (model parse → core) | 0.91 [0.83–0.95] (89/98) | 0.77 [0.69–0.84] (89/115) | 0.90 [0.79–0.96] (47/52) | 0.68 [0.55–0.79] (38/56) | 0.80 [0.68–0.89] (45/56) | 0.10 [0.02–0.40] (1/10) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 2117 / 320 | 5.26 | 0 |
| C* (hand parse → core) | 0.93 [0.87–0.96] (107/115) | 0.93 [0.87–0.96] (107/115) | 1.00 [0.93–1.00] (52/52) | 0.79 [0.66–0.87] (44/56) | 0.88 [0.76–0.94] (49/56) | 0.00 [0.00–0.28] (0/10) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.66] (0/2) | 0 / 0 | 0.02 | 4 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.15 [0.04–0.42] (2/13) | 0.20 [0.07–0.45] (3/15) | 0.36 [0.15–0.65] (4/11) | 0.29 [0.08–0.64] (2/7) | 0.70 [0.40–0.89] (7/10) |
| A' (BM25 + dense top-8 → model) | 0.08 [0.01–0.33] (1/13) | 0.13 [0.04–0.38] (2/15) | 0.36 [0.15–0.65] (4/11) | 0.29 [0.08–0.64] (2/7) | 0.80 [0.49–0.94] (8/10) |
| B (all documents → model) | 0.69 [0.42–0.87] (9/13) | 0.80 [0.55–0.93] (12/15) | 0.64 [0.35–0.85] (7/11) | 0.71 [0.36–0.92] (5/7) | 0.50 [0.24–0.76] (5/10) |
| C (model parse → core) | 0.77 [0.50–0.92] (10/13) | 0.80 [0.55–0.93] (12/15) | 0.64 [0.35–0.85] (7/11) | 0.00 [0.00–0.35] (0/7) | 0.90 [0.60–0.98] (9/10) |
| C* (hand parse → core) | 0.77 [0.50–0.92] (10/13) | 0.87 [0.62–0.96] (13/15) | 0.82 [0.52–0.95] (9/11) | 0.29 [0.08–0.64] (2/7) | 1.00 [0.72–1.00] (10/10) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.69 [0.54–0.80] (31/45) | 0.33 [0.25–0.43] (31/93) | 0.38 [0.23–0.55] (12/32) | 0.55 [0.35–0.73] (12/22) |
| A' (BM25 + dense top-8 → model) | 0.69 [0.54–0.81] (29/42) | 0.31 [0.23–0.41] (29/93) | 0.41 [0.26–0.59] (12/29) | 0.55 [0.35–0.73] (12/22) |
| B (all documents → model) | 0.86 [0.78–0.91] (90/105) | 0.97 [0.91–0.99] (90/93) | 0.85 [0.66–0.94] (22/26) | 1.00 [0.85–1.00] (22/22) |
| C (model parse → core) | 0.94 [0.87–0.97] (77/82) | 0.83 [0.74–0.89] (77/93) | 0.75 [0.51–0.90] (12/16) | 0.55 [0.35–0.73] (12/22) |
| C* (hand parse → core) | 0.99 [0.94–1.00] (90/91) | 0.97 [0.91–0.99] (90/93) | 0.71 [0.51–0.85] (17/24) | 0.77 [0.57–0.90] (17/22) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| A vs Aprime | 2 / 1, p = 1.0 | 3 / 3, p = 1.0 |
| A vs B | 5 / 25, p = 0.0003 | 3 / 16, p = 0.0044 |
| A vs C | 5 / 25, p = 0.0003 | 9 / 17, p = 0.1686 |
| A vs Cstar | 6 / 32, p = 0.0 | 6 / 18, p = 0.0227 |
| Aprime vs B | 5 / 26, p = 0.0002 | 4 / 17, p = 0.0072 |
| Aprime vs C | 6 / 27, p = 0.0003 | 10 / 18, p = 0.1849 |
| Aprime vs Cstar | 6 / 33, p = 0.0 | 6 / 18, p = 0.0227 |
| B vs C | 10 / 10, p = 1.0 | 9 / 4, p = 0.2668 |
| B vs Cstar | 8 / 14, p = 0.2863 | 6 / 5, p = 1.0 |
| C vs Cstar | 1 / 7, p = 0.0703 | 1 / 5, p = 0.2188 |

Per-request misses and extras:

- **A (BM25 top-8 → model)**: 38 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra [('U_OPEN_ISSUE', 'cracking 8d on sup-c 6082 material (issue id not given in documents)'), ('U_SOURCE_RELEASE', 'sup-c|br-220|customer not stated')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|unknown')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no issue id in documents)'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d on chisone 6082 cracks (no issue id given)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra [('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|unknown')]
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **A' (BM25 + dense top-8 → model)**: 39 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3')] extra []
  - D02 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-g|sp-700|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-g|sp-700|unknown')]
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d on cracking, chisone 6082 material (id not in documents)')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-b|br-310|unknown')]
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|customer not identified')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-c|br-310|unknown'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no issue id in documents)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-07 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MATERIAL', 'br-220'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **B (all documents → model)**: 18 requests not exact or wrong verdict
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-pa66gf30')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I06 (inferred): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-6082-t5')] extra []
  - S03 (stale): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-aur')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')]
  - C05 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-16 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
- **C (model parse → core)**: 21 requests not exact or wrong verdict
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_SOURCE_RELEASE', 'sup-c|br-180|cust-aur')] extra []
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra []
  - S04 (stale): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-26-009'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor'), ('U_SUPPLIER_STANDING', 'sup-d')] extra []
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [('U_OPEN_ISSUE', '8d-26-009')] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'coating_substances')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_data')] extra []
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'supplier_record'), ('U_SOURCE_RELEASE', 'viteria lanzo|hb-620|cust-nor')] extra []
  - C03 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-03 (stale): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-04 (clean): verdict not_covered (gold no_blockers_found); missed [] extra []
  - CR-06 (missing): verdict not_covered (gold needs_info); missed [('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [('U_MEASURED_VALUE', 'sc-01')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-09 (direct): verdict not_covered (gold blockers_found); missed [('U_DEVIATION_LIMIT', 'prc-dev-007')] extra []
  - CR-10 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-11 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-180')] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict not_covered (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_MISSING_EVIDENCE', 'material_strength')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-16 (direct): verdict not_covered (gold blockers_found); missed [('U_SOURCE_RELEASE', 'br-310')] extra []
  - CR-19 (missing): verdict blockers_found (gold needs_info); missed [('U_SOURCE_RELEASE', 'br-220')] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
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
