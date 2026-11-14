# Exploratory: the same benchmark on a company 8× larger (NOT pre-registered)

`data/scale.py --units 90` adds 90 distractor suppliers, 180 parts, 90 programs, 90 8D reports, 180 part
cards and 90 short meetings that never touch the benchmark's entities. 406 sources, 4,718 facts, ~8× the text.
Gold is unchanged (C\* still 1.00). Raw numbers: `RESULTS_scale.md`.

| | Small company (46 sources) | 8× company (406 sources) |
|---|---|---|
| B. All documents → model: recall on inferred findings | 0.95 | 0.92 |
| B. exact match (all right, nothing extra) | 0.86 | 0.78 |
| B. exact match on inferred requests | 0.89 | 0.67 |
| B. input tokens per request | ~12k | ~90k |
| C. Model parses → core: exact match | 0.97 | 0.97 |
| C. input tokens per request | ~2.5k | ~8k (glossary of names grows) |
| Core reasoning + check per request | ~0.5 s | ~3 s |

Reading:
- Full context degrades slowly, not sharply, at 8×. It drops mostly on the inferred requests (site-scoped
  approvals and the deviation/approval exceptions to R2). Two of its eight misses are formatting (it wrote the
  supplier's name instead of its id), so the real drop is smaller than the exact-match number suggests.
- The core's answers do not change with size; its cost moves from tokens to reasoning time (3 s per request
  on 4.7k facts, whole-graph closure). Next step is reasoning only over the subgraph of the request's
  entities, as the SOTA review recommends.
- A real supplier's archive is far beyond 90k tokens (thousands of PPAP files, 8Ds, emails), where full
  context does not fit at all. We did not test that size; say so if asked.
