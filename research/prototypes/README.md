# Research prototypes

Two research prototypes the team wrote while working out the design. They are kept here for transparency
and as reference. They are **not** the product: the product core in `core/` at the repository root is new
code written during the event, and it ports ideas and pieces from here.

| Folder | Author | What it is |
|---|---|---|
| `lcc-core/` | Maksim (with Arseniy's fixes 1 to 8) | Bitemporal fact log, OWL 2 RL ontology + SHACL shapes, rules R1a to R8 with proof chains, fact extraction from long documents with quote and grounding checks, a fictional tier-1 supplier ("mini-company") and a benchmark |
| `reasoning-spike/` | Arseniy | Throwaway reasoning-core spike on the BR-220 scenario: facts in force, OWL RL closure, SHACL check, proof trees, a frozen synthetic dataset with 20 change requests and gold answers |

## Dates (Rome time, 14 November 2026)

Two commits, so the history shows what existed when:

1. **"Research prototypes as of 10:23"**: the tree as of private commit `4d5554b` (10:23), before build
   time started at 10:30. The reasoning spike is unchanged after this commit.
2. **"Arseniy's fixes 1-8 (10:37-10:53), merged"**: eight fix branches Arseniy wrote between 10:37 and
   10:53, merged into `lcc-core/` by Maksim's agent. The fix-6 branch also carried a 09:54 note from the
   private repo (`insights_to_merge.md`, an internal decision memo); it is not copied here.

Per-fix write-ups with measurements: `lcc-core/bench/results/FIX_1.md` to `FIX_8.md`.

| Fix | One line |
|---|---|
| 1 | Catch-all: requirements the ontology cannot express are kept as "not checked" and listed on the card, never reasoned on |
| 2 | Larger change-type vocabulary (up to 17 types, notice and lead-time predicates), measured at three sizes |
| 3 | Two-span quotes: `context_quote` (governing sentence) + `quote` (list item), both verbatim, context within 1500 chars before the quote |
| 4 | The R2 blocker shows the customer's own consequence of an unapproved change (new business hold, registrar notification, chargeback), quoted |
| 5 | Grounding accepts person-confirmed aliases; onboarding helper `core/aliases.py` |
| 6 | Table-aware PDF conversion (`data_real/tables.py`): one line per table row with column headers |
| 7 | Extraction prompt: a blanket rule emits one fact per covered change type |
| 8 | Tier awareness: `suppliesTo` chain, rule R8 for changes at sub-tier suppliers, `subtier` scenario, requests T01 to T03 |

## How to run

Python 3.12 with `rdflib owlrl pyshacl pyyaml rank-bm25 pytest` (and `pdfplumber` for `data_real/tables.py`).
No API keys are needed for anything below.

```sh
cd research/prototypes/lcc-core
python -m pytest -q tests                       # unit tests
python data/validate_world.py                   # every quote is in its source, every id resolves
python core/integrity.py                        # SHACL integrity of the fact log
for s in main main_after_audit elv silence subtier; do python core/check.py --scenario $s; done

cd ../reasoning-spike
python -m pytest -q data/test_validate.py       # mutation tests of the dataset validator
python data/validate.py                         # tamper lock + integrity of the frozen dataset
python prep/spikes/reasoning-core/run_scenario.py
python prep/spikes/reasoning-core/crosscheck_gold.py
```

## Verification of the merged state (14 Nov 2026, macOS arm64, Python 3.12)

| Check | Result |
|---|---|
| `lcc-core`: `pytest tests` | 35 passed (15 before the fixes) |
| `lcc-core`: `data/validate_world.py` | 531 facts, 50 sources, 0 errors |
| `lcc-core`: `core/integrity.py` (SHACL) | conforms=True |
| `lcc-core`: `core/check.py --scenario main` | exit 0; blockers R1a, R1b, R6, R2 (with 3 quoted consequences), warning R3, question R7 |
| `--scenario main_after_audit` | exit 0; R1a gone, R1b, R6, R2 stay; R4 info on the superseded qualification |
| `--scenario elv` | exit 0; R2 x2 and R5 (Cr(VI) restricted) blockers |
| `--scenario silence` | exit 0; no blocker ("This is not an approval") |
| `--scenario subtier` | exit 0; R8 blocker, chain SUP-I -> SUP-B -> plant |
| `reasoning-spike`: `data/test_validate.py` | 80 passed |
| `reasoning-spike`: `data/validate.py` | all checks passed |
| `reasoning-spike`: `run_scenario.py` | 56 checks passed |
| `reasoning-spike`: `crosscheck_gold.py` | 5 ids equal the gold set for CR-01 |

### Merge notes

- `bench/llm.py`: every fix branch carried its own version of the same CLI fix (the CLI now prints a JSON
  array of events). One version is kept: it parses from the first `[` or `{` and takes the last `result` event.
- `core/extract.py`: `check_fact` takes both `aliases` (fix 5) and `scope` (fix 3); the glossary keeps the
  larger change-type vocabulary (fix 2) and adds the consequence types (fix 4); the two-ended grounding of
  `suppliesTo` (fix 8) also accepts aliases.
- Fix 8 had loosened the supplier-name grounding rule (name before the first comma). That contradicts fix 5's
  tests (the name rule must not change; aliases are the way to accept "DEMO"). The loosening is dropped and fix
  8's `suppliesTo` test grounds through aliases instead, the same resolution Arseniy chose in the private repo.
- `data/facts.jsonl` regenerated with `data/build.py`. `data_long/facts.jsonl` is not regenerated with an
  LLM: it is the new `data/facts.jsonl` base plus the 35 facts already extracted from the long documents,
  unchanged; `data_long/corpus.jsonl` and `registries.json` are rebuilt the same way `bench/extract_eval.py`
  builds them. `data_long_plain/` is as merged, not rebuilt.

## What is not here

- No real third-party documents. `lcc-core/data_real/` holds only `SOURCES.md` (URLs and terms), the
  registries written by the team, and the conversion scripts. The FIX and EXTRACTION_real write-ups quote
  single short sentences from those public documents for the audit, as `SOURCES.md` allows.
- Internal planning, compliance and pitch material of the private repository.
- All companies, people and part numbers in the synthetic data are fictional, except where `data/README.md`
  of the spike says otherwise.
