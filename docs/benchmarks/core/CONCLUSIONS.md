# What the benchmark says (13 Nov 2026, run once, no gold changes after seeing outputs)

36 change requests, 81 gold findings, Claude Sonnet via the subscription CLI for every model condition.
Raw numbers: `RESULTS.md`. Thresholds were fixed before the run: `../PREREGISTRATION.md` (sha256 in
`../PREREGISTRATION.sha256`).

## Headline
- **Pre-registered threshold: NOT PASSED.** Ontology condition C reaches 1.00 recall on inferred findings,
  but full context (B) already reaches 0.95. We needed +20 points. So, as agreed in advance, the pitch says
  **"a change-review check with sources"**, not "it reasons better than an LLM".
- Retrieval (A, BM25 top-8 chunks) is the weak baseline: recall 0.44, inferred recall 0.18. Eight chunks
  rarely contain the program → customer → requirement chain together.
- Full context is strong on this corpus because the whole company is about 12k tokens. This matches the
  literature (OIDA's own paper, LaRA): on small corpora full context wins general QA.

## Where the ontology still wins on this set (and what we can say)
| | C. model parses → core | B. all documents → model |
|---|---|---|
| Exact match, all findings right and nothing extra | 0.97 | 0.86 |
| Exact match on **stale** requests (superseded rule or record decides) | 1.00 | 0.71 |
| Exact match on **missing-data** requests (must ask, not guess) | 1.00 | 0.50 |
| Input tokens per request | ~2.5k | ~12.2k (grows with the company) |
| Every step has a quote checked by code | yes | no (model lists source ids) |

Full-context errors were the cases the ontology is built for: it used the old Aurelia manual (rev 3) on a
date when it was still valid but cited it as needing approval (S03, extra R2), missed that the Pinerolo site
is not covered by the Beinasco approval (I03), and missed an open 8D on an as-of date (S07).

## Honest limits
- The same person wrote the data, the rules and the gold. C\* = 1.00 is an upper bound, not proof the rules
  are right.
- 36 requests: one request moves exact match by about 3 points.
- Synthetic, small, clean data. A real archive is larger (full context stops fitting) and messier
  (extraction errors, which this benchmark does not test: facts were written by hand).
- The ontology condition lost one clean request (C02) to the parser: it wrote the coating as free text
  ("6 um zinc-nickel") and dropped the supplier, so the deviation did not match. Entity linking for
  coatings and suppliers is a Saturday task.
- Two full-context "extra" findings (M01, M04: no certificate from an unknown supplier) are defensible; gold
  counts the unknown supplier as one question. We did not change gold.

## What to say on stage
"On our synthetic supplier, a model reading everything finds most blockers too. What the ontology adds is
that it is exact on replaced rules and missing evidence, it asks instead of guessing, it uses 5× fewer
tokens, and every step of the chain points to a quote that code has checked."
