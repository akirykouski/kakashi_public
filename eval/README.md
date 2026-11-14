# Evaluation

Follows `docs/methodology.md` (pre-registered). Owner of this track: the eval owner; gold decisions: Valentina (#21); hold-out: Valentina (#20).

- `MAPPING.md` — one gold format for both worlds and the rule-vocabulary mapping.
- `worlds/M`, `worlds/A` — the two synthetic worlds, data only, never pooled.
- `gold/` — the golds that are re-golded (`REGOLD.md`) and then frozen (`docs/benchmarks/FROZEN.md`).
- `tools/` — import, scorer, baseline runner.
- `results/`, `raw/` — scored runs and every raw model response.

Dry runs on the unfrozen gold go to `results/dryrun/` and are never reported.
