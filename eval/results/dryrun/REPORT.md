# Scores: `eval/results/dryrun`

Computed by `eval/tools/score.py` (code, no LLM judge). Rate [95% Wilson interval] (k/n). Worlds are scored separately; the `both` block sums per-world counts over requests (facts are never pooled).

## World M

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.55 [0.41–0.68] (28/51) | 0.35 [0.25–0.45] (28/81) | 0.21 [0.11–0.36] (8/38) | 0.22 [0.12–0.38] (8/36) | 0.53 [0.37–0.68] (19/36) | 0.38 [0.14–0.69] (3/8) | – | – | 4504 / 959 | 8.12 | 0 |
| A' (BM25 + dense top-8 → model) | 0.60 [0.46–0.74] (26/43) | 0.32 [0.23–0.43] (26/81) | 0.18 [0.09–0.33] (7/38) | 0.22 [0.12–0.38] (8/36) | 0.53 [0.37–0.68] (19/36) | 0.25 [0.07–0.59] (2/8) | – | – | 4501 / 913 | 12.68 | 0 |
| B (all documents → model) | 0.84 [0.75–0.90] (77/92) | 0.95 [0.88–0.98] (77/81) | 0.95 [0.83–0.99] (36/38) | 0.58 [0.42–0.73] (21/36) | 0.86 [0.71–0.94] (31/36) | 0.50 [0.22–0.78] (4/8) | – | – | 15308 / 1559 | 16.84 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.12 [0.02–0.47] (1/8) | 0.00 [0.00–0.30] (0/9) | 0.29 [0.08–0.64] (2/7) | 0.00 [0.00–0.49] (0/4) | 0.62 [0.31–0.86] (5/8) |
| A' (BM25 + dense top-8 → model) | 0.00 [0.00–0.32] (0/8) | 0.00 [0.00–0.30] (0/9) | 0.29 [0.08–0.64] (2/7) | 0.00 [0.00–0.49] (0/4) | 0.75 [0.41–0.93] (6/8) |
| B (all documents → model) | 0.62 [0.31–0.86] (5/8) | 0.78 [0.45–0.94] (7/9) | 0.57 [0.25–0.84] (4/7) | 0.25 [0.05–0.70] (1/4) | 0.50 [0.22–0.78] (4/8) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.57 [0.39–0.73] (16/28) | 0.24 [0.15–0.35] (16/68) | 0.22 [0.10–0.42] (5/23) | 0.38 [0.18–0.64] (5/13) |
| A' (BM25 + dense top-8 → model) | 0.62 [0.43–0.79] (15/24) | 0.22 [0.14–0.33] (15/68) | 0.26 [0.12–0.49] (5/19) | 0.38 [0.18–0.64] (5/13) |
| B (all documents → model) | 0.84 [0.74–0.91] (64/76) | 0.94 [0.86–0.98] (64/68) | 0.81 [0.57–0.93] (13/16) | 1.00 [0.77–1.00] (13/13) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| A vs Aprime | 1 / 1, p = 1.0 | 1 / 1, p = 1.0 |
| A vs B | 3 / 16, p = 0.0044 | 2 / 14, p = 0.0042 |
| Aprime vs B | 3 / 16, p = 0.0044 | 3 / 15, p = 0.0075 |

Per-request misses and extras:

- **A (BM25 top-8 → model)**: 28 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra [('U_OPEN_ISSUE', '8d cracking issue on sup-c 6082 material (id not given)'), ('U_SOURCE_RELEASE', 'sup-c|br-220|customer not stated')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|unknown')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no id given)'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d on the 6082 cracks (meccanica chisone, no issue id in documents)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|unknown')]
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
- **A' (BM25 + dense top-8 → model)**: 28 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D02 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-g|sp-700|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-g|sp-700|customer not stated')]
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking issue on sup-c 6082 material (id not stated)')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-b|br-310|unknown')]
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|unknown')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-c|br-310|unknown'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no issue id given)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
- **B (all documents → model)**: 15 requests not exact or wrong verdict
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-pa66gf30')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-dc04')] extra []
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S03 (stale): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-aur')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_MEASURED_VALUE', 'sc-hb620-por')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')]
  - C05 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]

## World A

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.66 [0.47–0.80] (19/29) | 0.66 [0.47–0.80] (19/29) | 0.31 [0.13–0.58] (4/13) | 0.40 [0.22–0.61] (8/20) | 0.85 [0.64–0.95] (17/20) | 0.50 [0.09–0.91] (1/2) | 0.38 [0.14–0.69] (3/8) | 0.00 [0.00–0.66] (0/2) | 4259 / 1167 | 23.11 | 0 |
| A' (BM25 + dense top-8 → model) | 0.65 [0.46–0.81] (17/26) | 0.59 [0.41–0.74] (17/29) | 0.23 [0.08–0.50] (3/13) | 0.35 [0.18–0.57] (7/20) | 0.85 [0.64–0.95] (17/20) | 0.00 [0.00–0.66] (0/2) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 5008 / 1295 | 10.07 | 0 |
| B (all documents → model) | 0.76 [0.61–0.87] (29/38) | 1.00 [0.88–1.00] (29/29) | 1.00 [0.77–1.00] (13/13) | 0.65 [0.43–0.82] (13/20) | 0.95 [0.76–0.99] (19/20) | 0.50 [0.09–0.91] (1/2) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 10970 / 1445 | 10.25 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.20 [0.04–0.62] (1/5) | 0.50 [0.19–0.81] (3/6) | 0.25 [0.05–0.70] (1/4) | 0.67 [0.21–0.94] (2/3) | 0.50 [0.09–0.91] (1/2) |
| A' (BM25 + dense top-8 → model) | 0.20 [0.04–0.62] (1/5) | 0.33 [0.10–0.70] (2/6) | 0.25 [0.05–0.70] (1/4) | 0.33 [0.06–0.79] (1/3) | 1.00 [0.34–1.00] (2/2) |
| B (all documents → model) | 0.40 [0.12–0.77] (2/5) | 0.83 [0.44–0.97] (5/6) | 0.75 [0.30–0.95] (3/4) | 0.67 [0.21–0.94] (2/3) | 0.50 [0.09–0.91] (1/2) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.75 [0.53–0.89] (15/20) | 0.62 [0.43–0.79] (15/24) | 0.44 [0.19–0.73] (4/9) | 0.80 [0.38–0.96] (4/5) |
| A' (BM25 + dense top-8 → model) | 0.81 [0.57–0.93] (13/16) | 0.54 [0.35–0.72] (13/24) | 0.40 [0.17–0.69] (4/10) | 0.80 [0.38–0.96] (4/5) |
| B (all documents → model) | 0.86 [0.69–0.94] (24/28) | 1.00 [0.86–1.00] (24/24) | 0.50 [0.24–0.76] (5/10) | 1.00 [0.57–1.00] (5/5) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| A vs Aprime | 2 / 1, p = 1.0 | 1 / 1, p = 1.0 |
| A vs B | 0 / 5, p = 0.0625 | 0 / 2, p = 0.5 |
| Aprime vs B | 1 / 7, p = 0.0703 | 1 / 3, p = 0.625 |

Per-request misses and extras:

- **A (BM25 top-8 → model)**: 12 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **A' (BM25 + dense top-8 → model)**: 13 requests not exact or wrong verdict
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-07 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-11 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MATERIAL', 'br-220'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **B (all documents → model)**: 7 requests not exact or wrong verdict
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]

## World both

| Condition | Precision | Recall | Inferred recall | Exact match | Verdict | False alarm, clean | must_not_cite hits | Cleared fired | Tokens in / out | s / req | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.59 [0.48–0.69] (47/80) | 0.43 [0.34–0.52] (47/110) | 0.24 [0.14–0.37] (12/51) | 0.29 [0.18–0.41] (16/56) | 0.64 [0.51–0.76] (36/56) | 0.40 [0.17–0.69] (4/10) | 0.38 [0.14–0.69] (3/8) | 0.00 [0.00–0.66] (0/2) | 4417 / 1033 | 13.47 | 0 |
| A' (BM25 + dense top-8 → model) | 0.62 [0.51–0.73] (43/69) | 0.39 [0.30–0.48] (43/110) | 0.20 [0.11–0.32] (10/51) | 0.27 [0.17–0.40] (15/56) | 0.64 [0.51–0.76] (36/56) | 0.20 [0.06–0.51] (2/10) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 4682 / 1049 | 11.75 | 0 |
| B (all documents → model) | 0.82 [0.74–0.87] (106/130) | 0.96 [0.91–0.99] (106/110) | 0.96 [0.87–0.99] (49/51) | 0.61 [0.48–0.72] (34/56) | 0.89 [0.79–0.95] (50/56) | 0.50 [0.24–0.76] (5/10) | 0.25 [0.07–0.59] (2/8) | 0.00 [0.00–0.66] (0/2) | 13759 / 1518 | 14.48 | 0 |

Exact match by category:

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.15 [0.04–0.42] (2/13) | 0.20 [0.07–0.45] (3/15) | 0.27 [0.10–0.57] (3/11) | 0.29 [0.08–0.64] (2/7) | 0.60 [0.31–0.83] (6/10) |
| A' (BM25 + dense top-8 → model) | 0.08 [0.01–0.33] (1/13) | 0.13 [0.04–0.38] (2/15) | 0.27 [0.10–0.57] (3/11) | 0.14 [0.03–0.51] (1/7) | 0.80 [0.49–0.94] (8/10) |
| B (all documents → model) | 0.54 [0.29–0.77] (7/13) | 0.80 [0.55–0.93] (12/15) | 0.64 [0.35–0.85] (7/11) | 0.43 [0.16–0.75] (3/7) | 0.50 [0.24–0.76] (5/10) |

Findings by kind (precision / recall):

| Condition | blocker P | blocker R | question P | question R |
|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.65 [0.50–0.77] (31/48) | 0.34 [0.25–0.44] (31/92) | 0.28 [0.16–0.45] (9/32) | 0.50 [0.29–0.71] (9/18) |
| A' (BM25 + dense top-8 → model) | 0.70 [0.55–0.82] (28/40) | 0.30 [0.22–0.40] (28/92) | 0.31 [0.17–0.49] (9/29) | 0.50 [0.29–0.71] (9/18) |
| B (all documents → model) | 0.85 [0.76–0.90] (88/104) | 0.96 [0.89–0.98] (88/92) | 0.69 [0.50–0.83] (18/26) | 1.00 [0.82–1.00] (18/18) |

Paired comparisons (McNemar exact; b = first right only, c = second right only):

| Pair | Exact match b / c, p | Verdict b / c, p |
|---|---|---|
| A vs Aprime | 3 / 2, p = 1.0 | 2 / 2, p = 1.0 |
| A vs B | 3 / 21, p = 0.0003 | 2 / 16, p = 0.0013 |
| Aprime vs B | 4 / 23, p = 0.0003 | 4 / 18, p = 0.0043 |

Per-request misses and extras:

- **A (BM25 top-8 → model)**: 40 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-220|cust-aur')] extra [('U_OPEN_ISSUE', '8d cracking issue on sup-c 6082 material (id not given)'), ('U_SOURCE_RELEASE', 'sup-c|br-220|customer not stated')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|unknown')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no id given)'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d on the 6082 cracks (meccanica chisone, no issue id in documents)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-aur'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|unknown')]
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **A' (BM25 + dense top-8 → model)**: 41 requests not exact or wrong verdict
  - D01 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-alsi9cu3'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D02 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-pa66gf30'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-g|sp-700|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-g|sp-700|customer not stated')]
  - D03 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_SOURCE_RELEASE', 'sup-b|br-180|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-b|br-180|unknown')]
  - D04 (direct): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - D07 (direct): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-dc04'), ('U_MISSING_EVIDENCE', 'material_certificate')] extra []
  - D08 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I01 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking issue on sup-c 6082 material (id not stated)')]
  - I02 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur'), ('U_SUPPLIER_STANDING', 'sup-c')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - I03 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_SUPPLIER_STANDING', 'sup-c')]
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I05 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - I06 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_MATERIAL', 'mat-6082-t5'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'sup-b|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-b|br-310|unknown')]
  - I07 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-42crmo4'), ('U_SOURCE_RELEASE', 'sup-c|pn-050|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|pn-050|unknown')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'sup-c|br-310|cust-nor')] extra [('U_SOURCE_RELEASE', 'sup-c|br-310|unknown'), ('U_SUPPLIER_STANDING', 'sup-c')]
  - I09 (inferred): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S01 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_OPEN_ISSUE', '8d cracking on chisone 6082 material (no issue id given)')]
  - S02 (stale): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S05 (stale): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_MATERIAL', 'mat-6082-t6'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031'), ('U_SOURCE_RELEASE', 'sup-c|br-225|cust-aur')] extra [('U_SOURCE_RELEASE', 'sup-c|br-225|unknown')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur'), ('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_SOURCE_RELEASE', 'viteria lanzo|cl-115|cust-nor')] extra []
  - M02 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra []
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-aur')] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict needs_info (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - CR-01 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_OPEN_ISSUE', '8d-25-031')] extra [('U_SUPPLIER_STANDING', 'meccanica c s.p.a.')]
  - CR-02 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-07 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
  - CR-08 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-11 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra [('U_SOURCE_RELEASE', 'br-220')]
  - CR-18 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MATERIAL', 'br-220'), ('U_MISSING_EVIDENCE', 'material_certificate'), ('U_OPEN_ISSUE', '8d-25-031')] extra []
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-20 (inferred): verdict no_blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'stl')] extra []
- **B (all documents → model)**: 22 requests not exact or wrong verdict
  - D02 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-pa66gf30')] extra []
  - D06 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - D07 (direct): verdict blockers_found (gold blockers_found); missed [('U_MATERIAL', 'mat-dc04')] extra []
  - I04 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - I08 (inferred): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra []
  - S03 (stale): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-aur')]
  - S04 (stale): verdict blockers_found (gold blockers_found); missed [('U_CUSTOMER_APPROVAL', 'cust-nor')] extra [('U_MEASURED_VALUE', 'sc-hb620-por')]
  - S07 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_MEASURED_VALUE', 'sc-hb620-por'), ('U_SOURCE_RELEASE', 'sup-d|hb-620|cust-nor')]
  - M01 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - M03 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MATERIAL', 'en aw-7075'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - M04 (missing): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - C03 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', '8d-25-031')]
  - C04 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor'), ('U_OPEN_ISSUE', '8d-25-031')]
  - C05 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'cust-nor')]
  - C06 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_OPEN_ISSUE', 'ncr-26-017')]
  - CR-05 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-09 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-12 (direct): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-13 (stale): verdict blockers_found (gold blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl'), ('U_MISSING_EVIDENCE', 'material_certificate')]
  - CR-15 (clean): verdict blockers_found (gold no_blockers_found); missed [] extra [('U_CUSTOMER_APPROVAL', 'stl')]
  - CR-17 (inferred): verdict blockers_found (gold blockers_found); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate'), ('U_SOURCE_RELEASE', 'br-220')]
  - CR-19 (missing): verdict needs_info (gold needs_info); missed [] extra [('U_MISSING_EVIDENCE', 'material_certificate')]
