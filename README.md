# kakashi_public

Team project for the Control8 hackathon, 14 November 2026 (Valentina, Maksim & Arseniy).

Track: **Decision models**. A remark in a supplier-quality meeting is parsed into a change request and checked against company memory (ontology + rules over quoted facts). The system returns blockers with a proof chain and a quote under every step, or open questions with an owner. It never approves: a person decides.

| Where | What |
|---|---|
| `docs/plan.md` | Decisions and the build plan for the day |
| `docs/research/` | Reviews done before the event: memory systems, ontology + deductive checking |
| `docs/benchmarks/` | Benchmarks done before the event, and the cross-benchmark of the two prepared cores |
| `HACK.md` | The canvas |

Prepared before 10:30 (organisers confirmed it may be used): the research, the benchmarks, a synthetic dataset and a reference core. Product code is written on the day.

## Setup

```sh
cp .env.example .env   # paste the team key from /me («Show the key»)
```

The team key is used server side only. Never commit `.env`.

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
