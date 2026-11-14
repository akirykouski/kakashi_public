# Results (36 requests, 81 gold findings)

| Condition | Precision | Recall | Recall, inferred (R2/R3/R5) | Exact match | False alarm on clean | Tokens in / request | Seconds / request | Errors |
|---|---|---|---|---|---|---|---|---|
| C*. Gold parse → core (no model) | 0.99 | 1.00 | 1.00 | 0.97 | 0.12 | 0 | 0.4 | 0 |
| C. Model parses → core | 0.98 | 1.00 | 1.00 | 0.97 | 0.12 | 2483 | 5.8 | 0 |

## Exact match by category

| Condition | direct | inferred | stale | missing | clean |
|---|---|---|---|---|---|
| C*. Gold parse → core (no model) | 1.00 | 1.00 | 1.00 | 1.00 | 0.88 |
| C. Model parses → core | 1.00 | 1.00 | 1.00 | 1.00 | 0.88 |

## Misses per condition

### C*. Gold parse → core (no model)
- C02: missed [] extra [('R2', 'cust-aur')]

### C. Model parses → core
- C02: missed [] extra [('R2', 'cust-aur'), ('R7', 'coating_substances')]

