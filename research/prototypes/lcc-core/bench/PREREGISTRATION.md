# Pre-registration — written before any condition was run (13 Nov 2026, 21:25 CET)

## Question
Does a deductive check over an ontology (our core) find change blockers that a language model misses when it
reads the same company documents, and does it stay quiet when there is nothing to find?

## Set
`bench/requests.jsonl`: 36 change requests in plain English, 81 gold findings, written by hand from the
documents before the engine was run on them. Categories: direct 8, inferred 9, stale 7, missing 4, clean 8.
All data is synthetic and written by us. **The same person wrote the data, the rules and the gold**, so the
"gold parse → engine" condition is an upper bound, not evidence that the rules are right.

## Conditions (one model for all: Claude Sonnet via the subscription CLI)
- **A. Retrieval**: BM25 top-8 chunks from documents dated on or before the request date, then the model
  lists findings.
- **B. Full context**: every document dated on or before the request date in the prompt, then the model lists
  findings.
- **C. Ontology**: the model only parses the request into a structured change (part, supplier, type, coating,
  material, site); the core (owlrl closure + rules) produces the findings.
- **C\*. Gold parse**: the core with the hand-written structured change (no model). Shows parser loss.

All model conditions get the same rule catalogue (R1a…R7 in plain words) and the same output schema.

## Metrics (computed by code, no LLM judge)
A finding matches if rule and key are equal (see `bench/requests.py` for keys). Info-level output is ignored.
- Precision and recall of findings, micro-averaged over all requests.
- Recall on **inferred** findings: rules R2, R3, R5 (each needs at least two sources combined).
- Exact-match rate per category (all findings right, nothing extra).
- False-alarm rate on **clean** requests (any finding = alarm).
- Tokens in / out and latency per request.

## Fail threshold (fixed now)
We say "the system reasons over company memory" in the pitch only if condition C reaches
**recall on inferred findings ≥ condition B + 20 points AND precision ≥ 0.90**.
Otherwise the pitch says "a change-review check with sources", and we show the numbers as they are.

## What would make us distrust a result
- C\* below 1.0 recall: an engine bug or a gold error; each case is logged in `bench/GOLD_CHANGES.md`.
- Any gold change after seeing model outputs is logged with the reason and counted on the slide.
