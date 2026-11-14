# Frozen gold

SHA-256 of every gold and input file, committed **before** any reported run. A reported result is valid only if its files hash to the values below (`shasum -a 256 <file>`). Frozen at **2026-11-14 12:30 CET**, after the re-gold (`eval/REGOLD.md`, `CHANGES.md`).

| File | SHA-256 | Requests / rows |
|---|---|---|
| `eval/gold/M.jsonl` | 5b80202952ecd5f1aa13e22e77e9212fcca78cfd0b621351fa027e2e33c437ec | 36 |
| `eval/gold/A.jsonl` | f0c1ef74ebaed79ce25d804dffc0f475d02c168680cb01454d184d2a6a631caf | 20 |
| `eval/parses/M_hand.jsonl` (C* input) | f0e40615066008221032e35df6a38803f6f42ec8a0230404e8fb6906d104180f | 36 |
| `eval/parses/A_hand.jsonl` (C* input) | a2aba3dc137170f9bde501a0bfed5ca54dab7e140a0f4dabd114db867d59b64a | 20 |
| `eval/worlds/M/core/facts.jsonl` (core input, world M) | ded2c61f8a98d697487cfd28fe5d389503d67781cec62fedede8e7ed05052bb9 | 510 facts |
| `eval/worlds/A/core/facts.jsonl` (core input, world A) | df2f313dbb3041c95f32b3d0c095e7be2ce758e4f63c88f7fc521ca5d7e903da | 179 facts |
| `eval/tools/run_baselines.py` (prompt, catalogue, schema) | 3a8f80e1c5b4b3ea3137c017c8ae3bd576859ab77161db165277590b1f79b38f | — |
| `eval/gold/holdout.jsonl` (Valentina, #20) | — | 10 (5 per world), not yet written |

Hold-out: written by Valentina after this freeze, seen by neither core author. Stored outside this repo until scored; its hash is added here when it is handed over, and it is published only after the reported run.
