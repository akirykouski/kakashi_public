# Evaluation

Follows `docs/methodology.md` (pre-registered). Owner of this track: Maksim. Re-gold decided by the eval track on Maksim's instruction (#21, closed); hold-out (#20) skipped unless written by someone who has seen neither gold nor core.

- `STATUS.md` — what is done, running and next (start here).
- `MAPPING.md` — one gold format for both worlds and the rule-vocabulary mapping.
- `worlds/M`, `worlds/A` — the two synthetic worlds, data only, never pooled.
- `gold/` — the golds that are re-golded (`REGOLD.md`) and then frozen (`docs/benchmarks/FROZEN.md`).
- `tools/` — import, scorer, baseline runner.
- `results/`, `raw/` — scored runs and every raw model response.

Dry runs on the unfrozen gold go to `results/dryrun/` and are never reported.
