# Results: change-check core vs model baselines

**Status: skeleton. No reported number yet.** Filled from `eval/results/frozen/` after the gold is frozen (`FROZEN.md`). Protocol: `docs/methodology.md`; every interpretation and deviation: `CHANGES.md`.

Setup: world M (36 requests) and world A (20 requests), scored per world and summed over requests for the decision (facts never pooled). Model for A, A', B and the parser in C: _model id from `*.meta.json`_. Rates are k/n with 95% Wilson intervals; paired comparisons use McNemar's exact test; differences under ~10 points are treated as noise.

## H1 — inferred blockers: C recall > A' recall + 20 points

| Scope | C | A' | Diff | Result |
|---|---|---|---|---|
| Both worlds (decides) | | | | |
| World M | | | | |
| World A | | | | |

## H2 — replaced rules and missing data: exact match on stale + missing, C > B

| Scope | C | B | McNemar p | Result |
|---|---|---|---|---|
| Both worlds (decides) | | | | |
| World M | | | | |
| World A | | | | |

## H3 — scale: at 8× company size C drops ≤ 3 points and B drops more than C

| Scope | C at 1× / 8× | B at 1× / 8× | Result |
|---|---|---|---|
| World M | | | _not run unless time allows_ |

## H4 — overall: exact match C ≥ B − 5 points

| Scope | C | B | Diff | McNemar p | Result |
|---|---|---|---|---|---|
| Both worlds (decides) | | | | | |
| World M | | | | | |
| World A | | | | | |

## Parser loss: C* − C

| Scope | C* exact | C exact | C* − C |
|---|---|---|---|
| Both worlds | | | |

## Secondary metrics

Per condition and world: precision, recall, verdict accuracy, false alarms on clean requests, `must_not_cite` hits (world A), cleared rules that fire (world A), tokens, seconds. Full tables: `eval/results/frozen/REPORT.md`.

## Threats to validity

From methodology §6:
- Data is synthetic, written by the team.
- The gold and the rules were written by the authors of the cores; the hold-out set (#20) is the only partial answer.
- Small sets: one finding moves a category score by several points (world A has 2 clean and 3 missing requests).
- Only 4 real documents; real-document results are a spot check, single auditor, reported separately.
- In the cross-benchmark, the third-party encoders saw some gold.
- One model family is used for every model condition and for the parser.
- The full-context baseline benefits from small companies; H3 tests this only on synthetic scale-up.

Found while running (logged in `CHANGES.md`):
- The model conditions get one rule catalogue for both worlds (methodology §3). In world M it lists rules that have no data there (measured value, deviation limit), and the model sometimes fires them; with M's 13 Nov world-specific catalogue the same model scored higher on M. The core gets the same rule set, so the comparison is like for like, but B's numbers here are not comparable with the 13 Nov bench.
- Re-gold proposals were written by the non-author of each world and arbitrated by Valentina; items not decided by the freeze are marked "disputed, not re-golded".
- `ChangeRequest` cannot express four world-A requests (lot release, temporary deviation): CR-06, 08, 09, 15. C* and C are scored on them as they come out.

## Safe to say on stage

_Three sentences, written after the reported run, each with n and interval. Never "100%"; never "reasons better than an LLM" unless H1 and H4 both pass; no ranking of the two prepared cores._
