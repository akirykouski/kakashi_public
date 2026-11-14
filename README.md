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
