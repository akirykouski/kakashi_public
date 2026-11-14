# Results: change-check core vs model baselines

Reported run on the frozen gold (`FROZEN.md`, cecba57), 14 Nov 2026. Core at cecba57. Model for A, A', B and the parser in C: `claude-sonnet-5-5` via the Claude Code subscription CLI (tools, MCP and settings off), temperature = CLI default. Protocol: `docs/methodology.md`; interpretations and deviations: `CHANGES.md`. Full tables and per-request misses: `eval/results/frozen/REPORT.md`; raw answers: `eval/raw/frozen/`.

Two synthetic worlds (M: 36 requests, 83 gold findings; A: 20 requests, 32 findings), scored separately and summed over requests for the decision (facts never pooled). Rates: k/n with 95% Wilson interval. Paired tests: McNemar exact, b/c = first condition right only / second right only. Differences under ~10 points are noise at this n.

## Summary

| Hypothesis | Pre-registered pass rule | Result (both worlds) | World M | World A |
|---|---|---|---|---|
| H1 | Recall on inferred findings, C > A' by at least 20 points | **PASS** | PASS | PASS |
| H2 | Exact match on the stale and missing categories, C > B | **FAIL** | FAIL | FAIL |
| H3 | Exact match at 8x company size: C drops <= 3 points, B drops more than C | **not decided** | not decided | not decided |
| H4 | Exact match, C >= B - 5 points | **PASS** | PASS | FAIL |

## H1 — inferred blockers: C recall > A' recall + 20 points

| Scope | C | A' | Diff | McNemar A' vs C (exact match) | Result |
|---|---|---|---|---|---|
| Both worlds (decides) | 0.90 [0.79–0.96] (47/52) | 0.19 [0.11–0.32] (10/52) | +0.71 | 6/27, p = 0.0003 | PASS |
| World M | 0.89 [0.76–0.96] (34/38) | 0.18 [0.09–0.33] (7/38) | +0.71 | 0/20, p = 0.0 | PASS |
| World A | 0.93 [0.69–0.99] (13/14) | 0.21 [0.08–0.48] (3/14) | +0.71 | 6/7, p = 1.0 | PASS |

## H2 — replaced rules and missing data: exact match on stale + missing, C > B

| Scope | C | B | Result |
|---|---|---|---|
| Both worlds (decides) | 0.39 [0.20–0.61] (7/18) | 0.67 [0.44–0.84] (12/18) | FAIL |
| World M | 0.45 [0.21–0.72] (5/11) | 0.64 [0.35–0.85] (7/11) | FAIL |
| World A | 0.29 [0.08–0.64] (2/7) | 0.71 [0.36–0.92] (5/7) | FAIL |

By category (both worlds): stale C 0.64 [0.35–0.85] (7/11) vs B 0.64 [0.35–0.85] (7/11); missing C 0.00 [0.00–0.35] (0/7) vs B 0.71 [0.36–0.92] (5/7).

Why C fails on missing data: the core's parser keeps only names it can resolve against the registries and moves the rest to `unresolved` (by design: "never guessed"). An unknown supplier, coating or material therefore never reaches the rules, and the question the rules would ask ("not in our records") is never raised: M01, M02, M03, M04 lose every finding. With the hand parse (C*), which keeps the name, the same requests are right except for the certificate question added in re-gold. This is a product gap found by the evaluation; it is not fixed and re-run here, because tuning on the frozen set is not allowed.

## H3 — scale: at 8× company size C drops ≤ 3 points and B drops more than C

Not run today. The pre-event bench on world M at 4.7k facts is in `docs/benchmarks/core/RESULTS_scale.md` (earlier core, not this protocol).

## H4 — overall: exact match C ≥ B − 5 points

| Scope | C | B | Diff | McNemar B vs C | Result |
|---|---|---|---|---|---|
| Both worlds (decides) | 0.68 [0.55–0.79] (38/56) | 0.68 [0.55–0.79] (38/56) | +0.00 | 10/10, p = 1.0 | PASS |
| World M | 0.78 [0.62–0.88] (28/36) | 0.67 [0.50–0.80] (24/36) | +0.11 | 5/9, p = 0.424 | PASS |
| World A | 0.50 [0.30–0.70] (10/20) | 0.70 [0.48–0.85] (14/20) | -0.20 | 5/1, p = 0.2188 | FAIL |

H4 passes on the two worlds together at a difference of exactly 0, and fails on world A alone (−20 points; 5 of A's 20 requests are lot releases, deviations or service parts that the core's change schema cannot express or its parser does not mark: CR-06, 08, 09, 15, 19).

## Parser loss: C* − C

| Scope | C* exact | C exact | C* − C | McNemar C vs C* |
|---|---|---|---|---|
| Both worlds | 0.79 [0.66–0.87] (44/56) | 0.68 [0.55–0.79] (38/56) | +0.11 | 1/7, p = 0.0703 |
| World M | 0.94 [0.82–0.98] (34/36) | 0.78 [0.62–0.88] (28/36) | +0.17 | 0/6, p = 0.0312 |
| World A | 0.50 [0.30–0.70] (10/20) | 0.50 [0.30–0.70] (10/20) | +0.00 | 1/1, p = 1.0 |

## Secondary metrics (both worlds)

| Condition | Precision | Recall | Verdict accuracy | False alarm on clean | must_not_cite hits (A) | Tokens in / request | s / request |
|---|---|---|---|---|---|---|---|
| A (BM25 top-8 → model) | 0.65 [0.54–0.75] (50/77) | 0.43 [0.35–0.53] (50/115) | 0.66 [0.53–0.77] (37/56) | 0.30 [0.11–0.60] (3/10) | 0.38 [0.14–0.69] (3/8) | 4882 | 9.49 |
| A' (BM25 + dense top-8 → model) | 0.65 [0.53–0.75] (46/71) | 0.40 [0.32–0.49] (46/115) | 0.66 [0.53–0.77] (37/56) | 0.20 [0.06–0.51] (2/10) | 0.25 [0.07–0.59] (2/8) | 5147 | 9.09 |
| B (all documents → model) | 0.85 [0.78–0.91] (112/131) | 0.97 [0.93–0.99] (112/115) | 0.89 [0.79–0.95] (50/56) | 0.50 [0.24–0.76] (5/10) | 0.25 [0.07–0.59] (2/8) | 13116 | 10.85 |
| C (model parse → core) | 0.91 [0.83–0.95] (89/98) | 0.77 [0.69–0.84] (89/115) | 0.80 [0.68–0.89] (45/56) | 0.10 [0.02–0.40] (1/10) | 0.00 [0.00–0.32] (0/8) | 2117 | 5.26 |
| C* (hand parse → core) | 0.93 [0.87–0.96] (107/115) | 0.93 [0.87–0.96] (107/115) | 0.88 [0.76–0.94] (49/56) | 0.00 [0.00–0.28] (0/10) | 0.00 [0.00–0.32] (0/8) | 0 | 0.02 |

C's tokens are the parser call only; the core itself reads no tokens and answers in ~20 ms.

## Threats to validity

From methodology §6:
- Data is synthetic, written by the team.
- The gold and the rules were written by the authors of the cores; **there is no hold-out**: nobody who had seen neither gold nor core could write one in time (#20). There is no number about generalisation.
- Small sets: one finding moves a category score by several points (world A has 2 clean and 3 missing requests).
- Only 4 real documents; real-document results are a spot check, reported separately.
- In the cross-benchmark, the third-party encoders saw some gold.
- One model family for every model condition and for the parser.
- The full-context baseline benefits from small companies; H3 was not run.

Found during this evaluation (all logged in `CHANGES.md`):
- **Re-gold was not arbitrated.** 17 disputed items were decided by the eval track on Maksim's instruction, on document quotes only; for world M the decider was on the author's side. 5 findings were added (certificate question CR-05, CR-12, M01, M04; customer approval CR-13), all else kept.
- **World A's facts for the core** are a hand encoding (crossbench encoder ported by the eval track, which had seen the gold), with world-A policy facts quoted from A's documents.
- **The core's 8D level and ASL completeness for world M** come from QP-15, a procedure written on 14 Nov after the gold; the baselines did not see QP-15.
- **One rule catalogue for both worlds** (same prompt for every model condition): in world M it lists rules with no data there, and the model sometimes fires them. B's numbers are not comparable with the 13 Nov bench, which used a world-specific catalogue.
- **The core changed during the day**; this run is pinned to the commit above.
- **The parser in C runs Sonnet**, the product parser defaults to Haiku through the team gateway.

## Safe to say on stage

1. "On blockers that only show up when two or more documents are combined, our core finds 90% of them (47 of 52, 95% interval 79–96%) where a fair retrieval baseline with BM25 and embeddings finds 19% — measured on 56 change requests across two independently written synthetic companies."
2. "Overall it is on par with a model that reads every document — 68% of requests exactly right in both cases (38 of 56) — while reading about 2,000 tokens per request instead of 13,000 and raising a false alarm on 1 of 10 harmless changes instead of 5."
3. "It is not better everywhere: when a supplier or material is missing from our records, the model reading everything gets 5 of 7 right and we get none, because our parser drops names it doesn't know — that is the next fix."

Not safe: "100%", "reasons better than an LLM" (H2 failed; H4 passes only on both worlds together, at a tie), anything about generalisation (no hold-out), anything about scale (H3 not run), a ranking of the two prepared cores.
