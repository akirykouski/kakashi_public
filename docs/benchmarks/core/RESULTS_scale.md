# Results (36 requests, 81 gold findings)

| Condition | Precision | Recall | Recall, inferred (R2/R3/R5) | Exact match | False alarm on clean | Tokens in / request | Seconds / request | Errors |
|---|---|---|---|---|---|---|---|---|
| C*. Gold parse → core (no model) | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 0 | 3.1 | 0 |
| C. Model parses → core | 0.98 | 1.00 | 1.00 | 0.97 | 0.12 | 7968 | 12.9 | 0 |
| A. BM25 top-8 chunks → model | 0.82 | 0.44 | 0.16 | 0.25 | 0.12 | 9323 | 9.1 | 0 |
| B. All documents → model | 0.94 | 0.94 | 0.92 | 0.78 | 0.00 | 90196 | 10.4 | 0 |

## Exact match by category

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C*. Gold parse → core (no model) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| C. Model parses → core | 1.00 | 1.00 | 1.00 | 1.00 | 0.88 |
| A. BM25 top-8 chunks → model | 0.00 | 0.00 | 0.29 | 0.00 | 0.88 |
| B. All documents → model | 0.88 | 0.67 | 0.71 | 0.50 | 1.00 |

## Pre-registered threshold

C inferred recall 1.00 vs B 0.92 (needs +0.20); C precision 0.98 (needs ≥ 0.90): **NOT PASSED**.

## Misses per condition

### C*. Gold parse → core (no model)

### C. Model parses → core
- C02: missed [] extra [('R2', 'cust-aur'), ('R7', 'coating_substances')]

### A. BM25 top-8 chunks → model
- D01: missed [('R2', 'cust-nor'), ('R6', 'mat-alsi9cu3')] extra []
- D02: missed [('R2', 'cust-aur'), ('R6', 'mat-pa66gf30')] extra []
- D03: missed [('R1b', 'sup-b|br-180|cust-aur'), ('R2', 'cust-aur')] extra [('R1b', 'sup-b|br-180|customer not stated')]
- D04: missed [('R2', 'cust-aur')] extra []
- D05: missed [('R2', 'cust-aur'), ('R5', 'crvi')] extra []
- D06: missed [('R5', 'crvi')] extra []
- D07: missed [('R2', 'cust-aur')] extra []
- D08: missed [('R2', 'cust-aur')] extra []
- I01: missed [('R2', 'cust-aur'), ('R3', '8d-25-031')] extra [('R3', 'open cracking 8d on chisone 6082 material (8d id not given in the documents)')]
- I02: missed [('R1a', 'sup-c'), ('R1b', 'sup-c|br-225|cust-aur'), ('R2', 'cust-aur'), ('R3', '8d-25-031'), ('R6', 'mat-6082-t6')] extra []
- I03: missed [('R2', 'cust-aur')] extra [('R1a', 'sup-c')]
- I04: missed [('R2', 'cust-aur'), ('R2', 'cust-nor')] extra []
- I05: missed [('R2', 'cust-aur')] extra []
- I06: missed [('R2', 'cust-nor'), ('R6', 'mat-6082-t5')] extra []
- I07: missed [('R1b', 'sup-c|pn-050|cust-aur'), ('R2', 'cust-aur'), ('R6', 'mat-42crmo4')] extra []
- I08: missed [('R2', 'cust-nor')] extra []
- I09: missed [('R2', 'cust-nor')] extra [('R7', 'material_certificate')]
- S01: missed [('R2', 'cust-aur'), ('R3', '8d-25-031')] extra [('R3', 'open 8d on cracking in sup-c 6082 material (no issue id given in the documents)')]
- S02: missed [('R2', 'cust-aur')] extra []
- S04: missed [('R2', 'cust-nor')] extra []
- S05: missed [('R1b', 'sup-c|br-225|cust-aur'), ('R2', 'cust-aur'), ('R6', 'mat-6082-t6')] extra [('R1b', 'sup-c|br-225|customer not stated in documents')]
- S07: missed [('R3', '8d-26-009')] extra []
- M01: missed [('R1b', 'viteria lanzo|cl-115|cust-aur'), ('R1b', 'viteria lanzo|cl-115|cust-nor'), ('R2', 'cust-aur'), ('R2', 'cust-nor')] extra []
- M02: missed [('R2', 'cust-aur')] extra []
- M03: missed [('R2', 'cust-aur')] extra []
- M04: missed [('R2', 'cust-nor')] extra [('R7', 'material_certificate')]
- C05: missed [] extra [('R7', 'material_certificate')]

### B. All documents → model
- D02: missed [('R1b', 'sup-g|sp-700|cust-aur')] extra [('R1b', 'minuterie germanasca s.r.l.|sp-700|cust-aur')]
- I06: missed [('R1b', 'sup-b|br-310|cust-nor')] extra [('R1b', 'alluminio bormida|br-310|cust-nor')]
- I08: missed [('R2', 'cust-nor')] extra []
- I09: missed [('R2', 'cust-nor')] extra []
- S03: missed [] extra [('R2', 'cust-aur')]
- S07: missed [('R3', '8d-26-009')] extra []
- M01: missed [] extra [('R7', 'material_certificate')]
- M04: missed [] extra [('R7', 'material_certificate')]

