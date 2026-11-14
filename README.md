# Change check: a decision model over company memory

KVA hackathon "AI brain for industry", Turin, 14 November 2026 · track **Decision models** · Valentina, Maksim & Arseniy.

**Live demo: https://change-check.onrender.com** (meeting mode: `/?view=meeting`; free instance, the first request after a pause can take ~50 s to wake up).

In a supplier-quality meeting someone says *"Bormida is two weeks late, let's take the BR-220 blanks from Chisone,
same alloy."* Before the decision is taken, the system answers with the blockers it can prove from the company's
own records, each with the chain of reasoning and a verbatim quote under every step, the open questions and who
owns them, and the row of a declared decision table that says what may be done and who decides. It never approves:
a person decides.

## How it works

- **The model listens and reads; the company's rules decide.** One LLM call turns the remark into a typed change
  request; names are mapped to registry ids by code (a name in none of our records goes to the rules as unknown,
  never guessed). Documents become proposed facts the same way; a fact counts only after code finds its quote
  verbatim in the source and a person accepts it.
- **Memory with time.** An append-only fact log with valid time and record time ("what did we know on 8 Nov?");
  a newer record replaces an older one by date and document rank, the old one stays in history.
- **Reasoning over an ontology.** OWL 2 RL chains from the part to the customer's requirement and to the law of
  the market (part → programme → customer → requirement; part → market → law); rules R1a–R8 read the result.
- **A declared decision model.** `core/decision_table.yaml`: change class × fired rules → allowed actions and the
  role who decides; if no rule covers a change, row R0 sends it to a person. The table is exhaustively checked
  (`python -m core.decision`: 8,704 input sets; the ones no row covers go to a person, overlaps resolved by order).
- **Reproducible decisions.** Each check writes a decision record: request, date, facts in force, rules fired,
  row, and a hash of the rules version. Same request, facts and rules → same answer.
- **Memory maintenance.** Past decisions with their reasons re-checked today, promises past their date,
  deviations about to expire, contradictions shown side by side, "a document changed: what is affected".

Code map: `docs/architecture.md`. Decision model: `docs/decision-model.md`.

## Results (pre-registered, frozen gold)

Protocol `docs/methodology.md` (committed before the run); results `docs/benchmarks/RESULTS.md`. Two synthetic
companies, 56 change requests; model baselines: A' = hybrid retrieval → model, B = all documents → model.

| Hypothesis | Result |
|---|---|
| H1 · blockers that need several documents: our core beats retrieval by ≥ 20 points | **pass**: recall 0.90 vs 0.19 (47/52 vs 10/52) |
| H4 · overall, not worse than a model reading all documents (−5 points) | **pass** on both worlds together: exact 0.68 vs 0.68; world M 0.78 vs 0.67, world A 0.50 vs 0.70 |
| H2 · replaced rules and missing data: better than all documents → model | **fail**: 0.39 vs 0.67. Cause found: the parser dropped unknown names, so the rules never asked "not in our records". Fixed after the freeze (`CHANGES.md`); the frozen result stands |
| H3 · scale | not run under this protocol; exploratory latency in `docs/benchmarks/latency.md` |

Synthetic data, gold written by the team, small n: differences under ~10 points are noise. Earlier research and
benchmarks (memory libraries, the two prepared prototypes, extraction on four real public documents):
`docs/benchmarks/`, `research/prototypes/`.

## Models and tools

Claude Haiku 5.5 through the Vercel AI Gateway (team key, server side) parses remarks and extracts facts; Claude
Sonnet 5.5 via the Claude Code CLI for the model baselines; Claude Code to build. Python: rdflib, owlrl, pySHACL.

## Prepared before the event vs built today

Prepared before 10:30 (organisers confirmed it may be used): the research, the benchmarks, the synthetic companies
and two reference prototypes, now in `research/prototypes/` with their dates. Everything in `core/`, `web/`,
`rules_data/` and `eval/` was written on 14 November; each piece ported from a prototype says so in its commit.

## Run the demo

```sh
cp .env.example .env      # team key, server side only (core/llm.py reads it); never commit .env
pip install -r requirements.txt
python -m web.server      # http://localhost:8000  (--port to change)
```

One process serves the page (`web/static/`, no build step) and the JSON routes; the browser never runs core code
and never sees the key.

| Route | What |
|---|---|
| `POST /api/check` | `{remark, speaker?, as_of?}` (parsed by the model, then deterministic) or `{scenario}` or `{request}`; optional `drop_rows: ["D2"]` re-checks under a decision table edited in memory (`core/decision_table.yaml` is never written). Returns the card, the decision record, replaced records and labels. |
| `GET /api/scenarios` | `data/scenarios.json` and the people registry; the demo buttons are built from it |
| `GET /api/table?drop=D2` | decision table, coverage check, rules_version |
| `GET /api/records` | decision records (append-only `data/decisions.jsonl`), newest first |

On the page: the meeting strip (speaker, remark, as-of date, Check, demo buttons), the parsed change as chips
(unresolved names in amber with candidates), the verdict banner (never "approved"), findings with blockers first
and an expandable proof chain (verbatim quote and document id at every leaf, replaced records struck through in
red with dates and author), "not checked", the matched decision-table row with the coverage line and a link to
the whole table, the decision record, timings, and "Same request, different answer": the coating question under
Aurelia manual rev 3 vs rev 4, time travel between two dates, and a one-row table edit.
