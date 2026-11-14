# Fact extraction on long documents (exploratory, not pre-registered)

Question: if the hand-written facts are replaced by facts a model extracts from long, realistic documents,
does the core still give the same answers?

## Setup
- `data/longdocs.py`: the 8 documents whose facts feed the rules (CSR-AUR-R3, CSR-AUR-R4, CSR-NOR-R2, LAW-ELV,
  8D-25-031, 8D-26-009, NCR-26-017, DEV-121) grown to 18–26k tokens each (182k total). The original text sits
  verbatim in the middle. Filler sections (scope, definitions, packaging, logistics, warranty, measurement
  tables, test plans, logs) were generated once with Sonnet and cached; paragraphs that state a rule, a status,
  a substance or another record id were dropped. 15 hand-written traps: revision histories quoting the old
  rule, a draft of the next revision, clauses for another division or company, a closed containment action
  inside an open 8D, closed related reports, an expired earlier deviation, "Cr(III), zinc and nickel are not
  restricted". QP-11 and PC-BR220 carry no extractable facts in our model (the rules cite QP-11 directly), so
  they were not included.
- `core/extract.py`: 20k-character chunks with 2k overlap, Sonnet through `claude -p`, JSON facts (s, p, o,
  quote) with a glossary of ids and 11 document predicates. Checks before a fact may enter the log: the quote
  is in the document (whitespace may differ; the stored quote is the document's own text), the predicate is in
  `lcc.ttl` and not an inferred one, every id is known, and a part or supplier object is named in its own
  quote. Failing facts go to a review list. Accepted facts are written as `proposed` and auto-accepted for the
  bench only.
- `bench/extract_eval.py`: gold = the hand facts of those documents in `data/world.py` (35). Then the hand
  facts are swapped for extracted ones (`data_long/facts.jsonl`) and conditions C\* and C are rerun on all 36
  requests. `requests.jsonl` and the gold are unchanged.

## Extraction

| Document | ~tokens | Gold | Found | Wrong extra | Missed | Traps taken | Sent to review |
|---|---|---|---|---|---|---|---|
| 8D-25-031 | 22,834 | 4 | 3 | 1 | 1 | 0 | 1 |
| 8D-26-009 | 23,327 | 4 | 4 | 0 | 0 | 0 | 0 |
| CSR-AUR-R3 | 24,452 | 4 | 4 | 0 | 0 | 0 | 0 |
| CSR-AUR-R4 | 25,598 | 5 | 4 | 0 | 1 | 0 | 0 |
| CSR-NOR-R2 | 24,222 | 4 | 4 | 0 | 0 | 0 | 0 |
| DEV-121 | 21,867 | 5 | 4 | 0 | 1 | 0 | 0 |
| LAW-ELV | 22,687 | 5 | 5 | 0 | 0 | 0 | 0 |
| NCR-26-017 | 17,939 | 4 | 4 | 0 | 0 | 0 | 0 |
| **Total** | 182k | 35 | 32 | 1 | 3 | **0 of 15** | 1 |

Precision 0.97, recall 0.91. Cost: 414k input tokens and 12k output tokens for 8 documents, 23–43 s per
document (4 in parallel, about 4 minutes in all).

Ablation, the same run without the prompt lines that say "ignore revision histories, drafts, other divisions,
reports listed for reference": precision 0.91, recall 0.91, 1 trap taken, 3 facts sent to review. The trap
taken was the old coating rule quoted in the CSR-AUR-R4 revision history. It did not change any answer,
because a requirement for approval wins over one for notification.

## Benchmark on extracted facts (36 requests)

| | Hand facts | Extracted facts | Extracted, no trap lines in prompt |
|---|---|---|---|
| C\*. Gold parse → core, exact match | 1.00 | 0.97 | 0.97 |
| C. Model parses → core, exact match | 0.97 | 0.97 | 0.97 |
| C. Recall on inferred findings | 1.00 | 1.00 | 1.00 |
| C. Precision | 0.98 | 0.98 | 0.98 |

The only request that changed is C02 (lot of HS-410 with 6 µm zinc-nickel, a clean request). With extracted facts
the core raises a false R2 for Aurelia because of the DEV-121 miss below. C already failed C02 for a different
reason (the parser wrote the coating as free text), so C's score did not move.

## Every miss, with the reason
- **DEV-121 permitsChangeType CoatingChange, missed.** The text says "a zinc-nickel layer of at least 6 um
  instead of 8 um". It never says "coating change". The model did not infer it. Effect: the deviation no
  longer covers the coating change, so C02 gets a false customer-approval blocker. This is the one miss with
  an effect on answers.
- **8D-25-031 concernsPart BR-310, sent to review.** The model's quote did not contain "BR-310", so the
  grounding check sent it to a person instead of the log. That is the price of the check.
- **8D-25-031 concernsMaterial MAT-6082-T6, wrong extra.** The filler (generated) says "EN AW-6082 T6
  extrusions", but BR-310 is T5 in our records. The filler contradicts the world here, so this counts against
  the test data, not the model. No effect on answers (BR-220 already reaches the 8D through the alloy).
- **CSR-AUR-R4 requiresNotificationFor SourceChange, missed.** The text says "every planned change"; our hand
  gold maps that to SourceChange only. No rule depends on it.
- Without the grounding check the ablation also accepted "DEV-121 concernsPart BR-220" with a real quote
  about HS-410. The grounding check (a part or supplier must be named in its own quote) now sends such facts
  to review.

## Caveats
- One author wrote the documents, the traps, the extractor prompt and the gold. The guarded prompt names the
  trap categories in general words; the ablation shows how much that helps (1 trap and 2 wrong facts more
  without it).
- One run, no variance measured. Reruns are free because of the cache, but they repeat the same answers.
- Facts from registries (approved supplier list, qualifications, capabilities) were not extracted; they come
  from structured exports in reality too.
- The full-context baseline B was not rerun on the long documents (around 200k tokens per request).
- Facts extracted from long documents are auto-accepted here. In the product a person accepts them.

Files: `data/longdocs.py`, `data_long/docs/*.md`, `data_long/traps.json`, `core/extract.py`,
`bench/extract_eval.py` (`--plain` for the ablation), `bench/results/extraction_long*.json`,
`RESULTS_long.md`, `RESULTS_long_plain.md`.
