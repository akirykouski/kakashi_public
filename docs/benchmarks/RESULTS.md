# Results: change-check core vs model baselines

Reported run on the frozen gold (`FROZEN.md`, cecba57), 14 Nov 2026. Core at cecba57. Model for A, A', B and the parser in C: `claude-sonnet-5-5` via the Claude Code subscription CLI (tools, MCP and settings off), temperature = CLI default. Protocol: `docs/methodology.md`; interpretations and deviations: `CHANGES.md`. Full tables and per-request misses: `eval/results/frozen/REPORT.md`; raw answers: `eval/raw/frozen/`.

Two synthetic worlds (M: 36 requests, 83 gold findings; A: 20 requests, 32 findings), scored separately and summed over requests for the decision (facts never pooled). Rates: k/n with 95% Wilson interval. Paired tests: McNemar exact, b/c = first condition right only / second right only. Differences under ~10 points are noise at this n.

## Summary

| Hypothesis | Pre-registered pass rule | Result (both worlds) | World M | World A |
|---|---|---|---|---|
| H1 | Recall on inferred findings, C > A' by at least 20 points | **PASS** | PASS | PASS |
| H2 | Exact match on the stale and missing categories, C > B | **FAIL** | FAIL | FAIL |
| H3 | Exact match at 8x company size: C drops <= 3 points, B drops more than C | **FAIL** (world M only) | FAIL | not run (no scaled world) |
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

### Why H2 failed (reported run, per request)

C got 7 of the 18 stale and missing requests exactly right; B got 12. The 11 misses, by cause:

| Cause | Requests | Where |
|---|---|---|
| The parser dropped names that are in none of our records (a new supplier, coating or material), so the rules never saw them and never asked "not in our records" | M01, M02, M03, M04, CR-11 | `core/parse.py` |
| The core did not ask for a material certificate from a supplier that is not in our records (QP-11 4.4 asks for it on any change of source; added to the gold in re-gold) | M01, M04 | `core/rules.py` |
| The model parse read "order from them again" / "keep ordering" as the current supplier, not a source change | S04, S07 | parser (model) |
| The change schema has no lot release and no measured value | CR-06, CR-08 | `core/contracts.py` |
| Core behaviour: customer approval and extra questions on a plant outside the list (CR-11), on a grade change (CR-13); the parser has no service-part scope (CR-19) | CR-11, CR-13, CR-19 | rules, parser |

With the hand parse (C*) the same core gets 11 of 18: the parser accounts for 4 of the 5 points between C and C*.

### After the fix (post-hoc, not pre-registered)

**Not a test of H2.** These runs use the same 56 frozen requests the failure was found on, so they show what the fixes change, not how the core generalises. H2 stays FAIL. The model's parser answers are replayed from the reported run (`--reuse-parses frozen`), so only the core changes; B is the reported run. Results: `eval/results/posthoc/`.

| Core | What changed | C exact, stale + missing (n = 18) | C exact, all (n = 56) | C precision | C* exact, all |
|---|---|---|---|---|---|
| Reported run (cecba57) | — | 7 | 38 | 0.91 | 44 |
| main a771378 | parser passes names in none of our records to the rules (b144aca, 12:44, written by the core track after the reported run) plus the other core commits since | 9 | 38 | 0.88 | 44 |
| branch `fix/h2-unknown-names` 3733ebe | + certificate question for a supplier not in our records (3 lines in `rules.check`; core tests 321 passed) | **11** | **40** | 0.87 | 46 |
| B, reported run | — | 12 | 38 | 0.85 | — |

What the fixes did: missing-data requests 0 → 4 of 7 (M01–M04 now right). What they did not: stale requests stay 7 of 11, and C is still one request behind B on stale + missing (11 vs 12), so H2 would still fail. Still open: S04/S07 (parse reading of "order again"), CR-06/CR-08 (schema), CR-11/CR-13/CR-19 (core behaviour). Precision drops slightly (0.91 → 0.87) because the passed-on names also raise "not in our records" questions where the gold has none (CR-11).

## H3 — scale: at 8× company size C drops ≤ 3 points and B drops more than C

World M only (world A has no scaled version). World M grown 8.1× by text (corpus 27 kB → 220 kB, 510 → 4,718 facts) with distractors that never touch the 36 requests (`eval/worlds/M_scale/`, hashed in FROZEN.md before the run). Same gold, same prompt.

| Condition | Exact match 1× | Exact match 8× | Drop (points) | Tokens in / request, 1× / 8× |
|---|---|---|---|---|
| B (all documents → model) | 0.67 [0.50–0.80] (24/36) | 0.72 [0.56–0.84] (26/36) | -5.5 | 14,543 / 110,769 |
| C (model parse → core) | 0.78 [0.62–0.88] (28/36) | 0.81 [0.65–0.90] (29/36) | -2.8 | 2,109 / 2,109 |
| C* (hand parse → core) | 0.94 [0.82–0.98] (34/36) | 0.94 [0.82–0.98] (34/36) | +0.0 | 0 / 0 |

**Result: FAIL.** C does not drop (−2.8, i.e. one more request right, within noise), but neither does B: at about 110,000 tokens of context per request the model reading everything is as accurate as at 14,000. The pre-registered claim that full context degrades as the company grows is not supported at 8×. What does change is cost: C reads the same ~2,100 tokens at any size (the parse only; the core answers in under 0.1 s), B reads 53× more.

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

## Ablations (methodology §4): C* with one component switched off

Run after the reported run on the same frozen gold and hand parses (`eval/tools/run_ablations.py`; switches applied in-process, no core file changed). Both worlds summed over requests; per world in `eval/results/frozen_ablations/*/REPORT.md`. McNemar exact against full C* on exact match: b = full right only, c = ablation right only.

| C* variant | Exact match | Inferred recall | Exact, stale | Exact, missing | Precision | McNemar vs full |
|---|---|---|---|---|---|---|
| Full core | 0.79 [0.66–0.87] (44/56) | 1.00 [0.93–1.00] (52/52) | 0.82 [0.52–0.95] (9/11) | 0.29 [0.08–0.64] (2/7) | 0.93 [0.87–0.96] (107/115) | — |
| No ontology inference (direct facts only) | 0.21 [0.13–0.34] (12/56) | 0.00 [0.00–0.07] (0/52) | 0.18 [0.05–0.48] (2/11) | 0.00 [0.00–0.35] (0/7) | 0.87 [0.68–0.95] (20/23) | 32/0, p = 0.0 |
| No supersession (every fact stays in force) | 0.61 [0.48–0.72] (34/56) | 0.98 [0.90–1.00] (51/52) | 0.45 [0.21–0.72] (5/11) | 0.29 [0.08–0.64] (2/7) | 0.84 [0.77–0.90] (101/120) | 10/0, p = 0.002 |
| No question outcome (missing evidence = no blocker) | 0.61 [0.48–0.72] (34/56) | 1.00 [0.93–1.00] (52/52) | 0.64 [0.35–0.85] (7/11) | 0.00 [0.00–0.35] (0/7) | 0.99 [0.94–1.00] (90/91) | 14/4, p = 0.0309 |

Reading: inference carries the blockers that need several documents (inferred recall 1.00 → 0.00 without it; exact match 44 → 12 of 56). Supersession carries the replaced-rule cases (stale exact 9 → 5 of 11). The question outcome carries the missing-data cases (missing exact 2 → 0 of 7). Each component is needed for a different category; none is decorative.

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
- The full-context baseline benefits from small companies; H3 tests this only on a synthetic 8× scale-up of world M, made of distractors that never touch the requests (easy to ignore), and found no degradation.

Found during this evaluation (all logged in `CHANGES.md`):
- **Re-gold was not arbitrated.** 17 disputed items were decided by the eval track on Maksim's instruction, on document quotes only; for world M the decider was on the author's side. 5 findings were added (certificate question CR-05, CR-12, M01, M04; customer approval CR-13), all else kept.
- **World A's facts for the core** are a hand encoding (crossbench encoder ported by the eval track, which had seen the gold), with world-A policy facts quoted from A's documents.
- **The core's 8D level and ASL completeness for world M** come from QP-15, a procedure written on 14 Nov after the gold; the baselines did not see QP-15.
- **One rule catalogue for both worlds** (same prompt for every model condition): in world M it lists rules with no data there, and the model sometimes fires them. B's numbers are not comparable with the 13 Nov bench, which used a world-specific catalogue.
- **The core changed during the day**; this run is pinned to the commit above.
- **The parser in C runs Sonnet**, the product parser defaults to Haiku through the team gateway.

## Safe to say on stage

1. "On blockers that only show up when two or more documents are combined, our core finds 90% of them (47 of 52, 95% interval 79–96%) where a fair retrieval baseline with BM25 and embeddings finds 19% — measured on 56 change requests across two independently written synthetic companies."
2. "Overall it is on par with a model that reads every document — 68% of requests exactly right in both cases (38 of 56) — and raises a false alarm on 1 of 10 harmless changes instead of 5. Its cost does not grow with the company: at eight times the documents it still reads about 2,000 tokens per request, the model reading everything needs 110,000."
3. "It is not better everywhere: on replaced rules and missing data the model reading everything was ahead, 12 of 18 against our 7. The evaluation showed why — our parser dropped names it did not know — we fixed it, and on the same requests we now get 11 of 18: still one behind, and we say so."

Not safe: "100%", "reasons better than an LLM" (H2 failed; H4 passes only on both worlds together, at a tie), anything about generalisation (no hold-out), "accuracy holds while full context degrades" (H3 failed: full context did not degrade at 8×), a ranking of the two prepared cores.
