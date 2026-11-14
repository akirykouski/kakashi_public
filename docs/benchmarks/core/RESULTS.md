# Results (36 requests, 81 gold findings)

| Condition | Precision | Recall | Recall, inferred (R2/R3/R5) | Exact match | False alarm on clean | Tokens in / request | Seconds / request | Errors |
|---|---|---|---|---|---|---|---|---|
| C*. Gold parse → core (no model) | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 0 | 0.5 | 0 |
| C. Model parses → core | 0.98 | 1.00 | 1.00 | 0.97 | 0.12 | 2483 | 5.3 | 0 |
| A. BM25 top-8 chunks → model | 0.75 | 0.44 | 0.18 | 0.28 | 0.12 | 3832 | 9.2 | 0 |
| B. All documents → model | 0.96 | 0.98 | 0.95 | 0.86 | 0.00 | 12212 | 8.5 | 0 |

## Exact match by category

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C*. Gold parse → core (no model) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| C. Model parses → core | 1.00 | 1.00 | 1.00 | 1.00 | 0.88 |
| A. BM25 top-8 chunks → model | 0.12 | 0.00 | 0.29 | 0.00 | 0.88 |
| B. All documents → model | 1.00 | 0.89 | 0.71 | 0.50 | 1.00 |

## Pre-registered threshold

C inferred recall 1.00 vs B 0.95 (needs +0.20); C precision 0.98 (needs ≥ 0.90): **NOT PASSED**.

## Misses per condition

### C*. Gold parse → core (no model)

### C. Model parses → core
- C02: missed [] extra [('R2', 'cust-aur'), ('R7', 'coating_substances')]

### A. BM25 top-8 chunks → model
- D01: missed [('R2', 'cust-nor')] extra []
- D02: missed [('R2', 'cust-aur')] extra []
- D03: missed [('R1b', 'sup-b|br-180|cust-aur'), ('R2', 'cust-aur')] extra [('R1b', 'sup-b|br-180|customer not identified in documents'), ('R7', 'material_certificate')]
- D04: missed [('R2', 'cust-aur')] extra []
- D05: missed [('R2', 'cust-aur')] extra []
- D06: missed [('R5', 'crvi')] extra []
- D07: missed [('R6', 'mat-dc04')] extra []
- I01: missed [('R1b', 'sup-c|br-220|cust-aur'), ('R2', 'cust-aur'), ('R3', '8d-25-031')] extra [('R3', 'cracking 8d on sup-c 6082 material (8d id not stated in the documents)')]
- I02: missed [('R1a', 'sup-c'), ('R1b', 'sup-c|br-225|cust-aur'), ('R2', 'cust-aur'), ('R3', '8d-25-031'), ('R6', 'mat-6082-t6')] extra []
- I03: missed [('R2', 'cust-aur')] extra [('R1a', 'sup-c'), ('R7', 'material_certificate')]
- I04: missed [('R2', 'cust-aur'), ('R2', 'cust-nor')] extra []
- I05: missed [('R2', 'cust-aur')] extra []
- I06: missed [('R2', 'cust-nor'), ('R6', 'mat-6082-t5')] extra []
- I07: missed [('R1b', 'sup-c|pn-050|cust-aur'), ('R2', 'cust-aur'), ('R6', 'mat-42crmo4'), ('R7', 'material_certificate')] extra []
- I08: missed [('R2', 'cust-nor'), ('R3', '8d-25-031')] extra [('R1a', 'sup-c'), ('R3', 'open 8d cracking on sup-c 6082 material (issue id not stated in documents)')]
- I09: missed [('R2', 'cust-nor')] extra [('R7', 'material_certificate')]
- S01: missed [('R2', 'cust-aur'), ('R3', '8d-25-031')] extra [('R3', '8d on 6082 cracks at meccanica chisone (no issue id given in documents)')]
- S02: missed [('R2', 'cust-aur')] extra []
- S04: missed [('R2', 'cust-nor')] extra []
- S05: missed [('R1b', 'sup-c|br-225|cust-aur'), ('R2', 'cust-aur'), ('R3', '8d-25-031'), ('R6', 'mat-6082-t6')] extra []
- S07: missed [('R3', '8d-26-009')] extra []
- M01: missed [('R1b', 'viteria lanzo|cl-115|cust-aur'), ('R1b', 'viteria lanzo|cl-115|cust-nor'), ('R2', 'cust-aur'), ('R2', 'cust-nor')] extra [('R7', 'material_certificate')]
- M02: missed [('R2', 'cust-aur')] extra []
- M03: missed [('R2', 'cust-aur')] extra []
- M04: missed [('R2', 'cust-nor')] extra [('R7', 'material_certificate')]
- C05: missed [] extra [('R7', 'material_certificate')]

### B. All documents → model
- I03: missed [('R2', 'cust-aur')] extra []
- S03: missed [] extra [('R2', 'cust-aur')]
- S07: missed [('R3', '8d-26-009')] extra []
- M01: missed [] extra [('R7', 'material_certificate')]
- M04: missed [] extra [('R7', 'material_certificate')]

