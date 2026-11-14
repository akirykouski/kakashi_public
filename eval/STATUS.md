# Evaluation track: status

Owner: Maksim (eval track). Updated 12:39 Rome. Protocol: `docs/methodology.md`. Every interpretation and deviation: `docs/benchmarks/CHANGES.md`.

**One line:** gold is frozen, the reported run of all five conditions is running now; results and the three sentences for the pitch land in `docs/benchmarks/RESULTS.md` by 15:00. Nothing is needed from the rest of the team.

## Done

| Step | What | Where |
|---|---|---|
| 1 | Both synthetic worlds imported as data, never pooled (world M: 36 requests; world A: 20) | `eval/worlds/`, `eval/worlds/SOURCE.txt` |
| 2 | One gold format for both worlds; mapping of the two rule vocabularies (R1a–R7 vs B_*/Q_*) | `eval/gold/`, `eval/MAPPING.md` |
| 3 | Re-gold of 17 disputed items: decided by the eval track on Maksim's instruction, on document quotes only. 5 findings added (certificate question CR-05, CR-12, M01, M04; customer approval CR-13), all else kept, no verdict changed. Logged as a deviation (no arbitration by Valentina) | `eval/REGOLD.md`, `CHANGES.md` |
| 4 | Scorer: code only, no LLM judge; Wilson 95% intervals; McNemar exact on paired requests | `eval/tools/score.py`, `eval/tools/hypotheses.py` |
| 5 | Freeze: SHA-256 of gold, hand parses, world encodings and baseline prompt, committed before the run | `docs/benchmarks/FROZEN.md` |
| 6 | Baselines A (BM25 top-8), A' (BM25 + dense top-8), B (all documents) → Claude Sonnet via the subscription CLI; raw answers saved | `eval/tools/run_baselines.py`, `eval/raw/` |
| 7 | C* (hand parse → core) and C (core's own parser → core), thin adapter, no change to `core/` | `eval/tools/run_core.py`, `eval/parses/`, `eval/tools/encode_A.py` |

A dry run on the unfrozen gold checked the pipeline; its numbers are never reported (`eval/results/dryrun/`).

## Running now

Reported run on the frozen gold, all five conditions, both worlds → `eval/results/frozen/`.

## Next

1. Score, decide H1–H4, write `docs/benchmarks/RESULTS.md` with the threats to validity and three sentences safe to say on stage (by 15:00).
2. H3 (8× company size) on world M if time allows; otherwise reported as "not run".
3. Ablations (methodology §4) only if everything above is done by 14:45.

## Decisions taken (so nobody has to ask)

- **Hold-out (#20) is skipped.** It must be written by someone who has seen neither gold nor core; nobody on the team qualifies in time. RESULTS.md says there is no generalisation number. If Valentina writes one and runs the scripts herself, it is added.
- **World M for the eval is the frozen snapshot**, not today's `data/`: Valentina's #19 additions and the sub-tier records are demo data and do not enter the eval (they would invalidate the gold).
- **World A enters the core** through a ported crossbench encoding with world-A policy facts; the core's `rules_data/` (world M) is not loaded for A.
- **Same model for every model condition**, including the parser in C (Sonnet via CLI; the team gateway key is not used for the eval).

## What the core owner should know (no action required for the eval)

- `ChangeRequest` cannot express lot release or temporary deviation (A: CR-06, 08, 09, 15): honest misses for C*/C.
- `rules.covered()` (row R0) projects the default `data/` world; the adapter works around it for the eval.
- `LocationChange` does not check source release (A: CR-12).
- Schedule/packaging changes get "not covered" from the core; the gold says "no blockers" (6 requests, verdict only).

## Rules we keep on stage

Only numbers from `eval/results/frozen/`, each with n and interval. Never "100%". Never "reasons better than an LLM" unless H1 and H4 both pass. No ranking of the two prepared cores.
