# Hand parses for C* (hand parse → core)

- `M_hand.jsonl`: Maksim's 13 Nov gold parses (`change` in `worlds/M/requests_native.jsonl`); all six types exist in `core/contracts.py` CHANGE_TYPES unchanged.
- `A_hand.jsonl`: written 14 Nov by the eval track from the request text only, without looking at gold findings or engine output. Supplier names as said; the adapter resolves names to world-A ids.
- `schema_gap`: what the request says that `ChangeRequest` (core/contracts.py, dbc2571) cannot carry. Four A requests have no fitting change type at all (`type` absent): CR-06 and CR-08 (lot release / acceptance), CR-09 and CR-15 (temporary deviation). They are run and scored as they come out; no gold is changed for them.

These files are inputs of C*; they are hashed with the gold in `docs/benchmarks/FROZEN.md`.
