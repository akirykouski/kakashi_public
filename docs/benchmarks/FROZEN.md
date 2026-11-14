# Frozen gold

SHA-256 of every gold file, written and committed **before** any reported run. A reported result is valid only if the gold it was scored on hashes to the value below (`shasum -a 256 eval/gold/*.jsonl`).

Not frozen yet: re-gold in progress (`eval/REGOLD.md`, #21). Freeze time: 13:45 Rome at the latest.

| File | SHA-256 | Requests | Frozen at |
|---|---|---|---|
| `eval/gold/M.jsonl` | — | 36 | — |
| `eval/gold/A.jsonl` | — | 20 | — |
| `eval/gold/holdout.jsonl` (Valentina, #20) | — | 10 (5 per world) | — |

Hold-out: written by Valentina after the freeze and seen by neither core author. Stored outside this repo until scored, so neither core author can read it; its hash is added here when it is handed over, and it is published only after the reported run.
