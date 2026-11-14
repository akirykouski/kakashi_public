# Changes to the evaluation protocol and gold

Every deviation from `docs/methodology.md`, every interpretation fixed before a run, and every gold decision. Times are Rome time (CET). Who: Maksim = eval owner for this track; Valentina = arbiter of gold (#21).

## Interpretations fixed before any run (no hypothesis, threshold or metric changed)

| Time | What | Why | Who |
|---|---|---|---|
| 2026-11-14 11:00 CET | One gold format for both worlds (`eval/MAPPING.md`); a finding matches on unified rule id + key. Native rule ids kept beside the unified id. | Methodology §5 needs one vocabulary; the two worlds use R1a–R7 and B_*/Q_* for the same checks. | Maksim |
| 2026-11-14 11:00 CET | World M verdicts derived from finding kinds (any blocker → blockers_found; else question → needs_info; else no_blockers_found). The same rule reproduces all 20 authored A verdicts. Model and core verdicts are derived by the same rule. | M's gold has no verdict field; one rule for gold and predictions keeps verdict accuracy comparable. | Maksim |
| 2026-11-14 11:00 CET | World A keys added by the eval owner, one entity per rule (MAPPING.md, decision 3). A has at most one finding per rule per request, so gold content is unchanged. | Methodology §5 matches on rule + key; A's gold had no key. | Maksim |
| 2026-11-14 11:00 CET | Inferred findings: M = rules R2, R3, R5 (M's pre-registration); A = kind `inferred`. | Each author's own definition of "two or more documents combined". | Maksim |
| 2026-11-14 11:00 CET | `must_not_cite` and `cleared` are scored on world A only; M has none authored. A cited quote matches a forbidden one if same doc id and ≥ 60% of the shorter quote's tokens overlap. | No new gold is invented for M outside re-gold. | Maksim |
| 2026-11-14 11:00 CET | Hypotheses are decided on the two worlds together: per-world scores summed over requests (n = 56; facts never pooled). Per-world numbers are reported beside them. | Methodology gives one threshold per hypothesis and one set of 56 requests; per-world n (20, 36) is too small for a decision on its own. | Maksim |
| 2026-11-14 11:00 CET | A' = reciprocal rank fusion (k = 60) of BM25 and dense embeddings (`intfloat/multilingual-e5-small`, chosen because world A mixes English and Italian), top-8 chunks of ~350 characters, same chunks as A. | Methodology names "BM25 + dense" without a model. | Maksim |
| 2026-11-14 11:00 CET | World A requests have no date; as_of = 2026-11-14 (all A documents are dated earlier, so B reads all 10). | B needs a request date. | Maksim |
| 2026-11-14 11:00 CET | Model conditions: one system prompt, one rule catalogue (unified ids, plain words) and one output schema for both worlds; only the documents and the key format lines differ per world. Model `sonnet` alias via the subscription CLI (resolved id recorded in each `*.meta.json`), temperature = CLI default (not settable). | Methodology §3: same model, prompt and schema. | Maksim |
| 2026-11-14 11:00 CET | Dry runs on the unfrozen gold go to `eval/results/dryrun/` and `eval/raw/dryrun/`; reported runs never reuse their raw responses. | Dry-run numbers are never reported. | Maksim |
| 2026-11-14 11:25 CET | C* and C read world M through `eval/worlds/M/core/facts.jsonl`: the core's own encoding (`data/facts.jsonl` at d75144b, new fields kind/rank/epistemic) filtered to the 510 facts of the frozen snapshot. The 21 facts added to `data/` after the snapshot (sub-tier lists SUBLIST-B/C, CSR-AUR-S1, consequences) are left out. Policy facts in `rules_data/` are engine configuration and are loaded. | Core and model baselines must read the same world the gold was written for. | Maksim |
| 2026-11-14 11:25 CET | A core answer with no findings and decision row R0 is scored as verdict `not_covered`, not as a finding. | Methodology §5 lists "not covered by rules" as a verdict once the core has it. | Maksim |

## Gold decisions (re-gold, #21)

| Time | Item | Decision | Why | Who |
|---|---|---|---|---|
