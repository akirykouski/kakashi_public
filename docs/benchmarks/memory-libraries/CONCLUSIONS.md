# Benchmark conclusions (13 Nov 2026)

Full tables: `REPORT.md`. Slice: 80 documents, 80 questions (16 per category), 20 meeting transcripts (10 with a collision, 10 without).
Same answer model (Sonnet) and prompt for every system; Haiku extracts facts inside each memory system and judges answers.
1,867 calls on the Claude subscription, 0 errors, $0 API spend.

## Results

| System | All questions | Strict key match | Collision F1 | Ingest 80 docs | Retrieval p95 |
|---|---|---|---|---|---|
| BM25 over raw documents | 75% | 62% | 95% | 0 s | 1 ms |
| LightRAG (mix mode) | 72% | 55% | 95% | 589 s | 4.5 s |
| Mem0 (open source) | 69% | 56% | 86% | 616 s | 0.4 s |
| Graphiti + source documents | 65% | 60% | 71% | (reuses graph) | 0.6 s |
| Graphiti (facts only) | 59% | 46% | 71% | 2,022 s | 0.5 s |

## What this means for tomorrow

1. No off-the-shelf memory library beat plain keyword search over the raw documents with a strong answer model.
   On a corpus this small, the answer model can read everything relevant. The libraries add cost and lose detail.
2. Extracted facts lose the details judges will ask about: who approved, quantity, expiry date, rationale.
   Graphiti scored 19% on "why / who decided" questions. Keep the source text and pass it to the answer model.
3. Graphiti's time model works: it marks replaced facts as SUPERSEDED with a date. But its search finds the right
   document only 75% of the time, against 92% for BM25. Search is the weak part, not the time model.
4. Mem0 open source accepts no dates at all, neither when a fact is written nor when memory is queried,
   but it still scored best on "which rule is valid now" (94%). With 16 items, that is one or two questions of difference.
5. LightRAG takes 3–4.5 s per query. That is too slow for a live meeting card when called on every utterance.

## Recommended design (build during the event)

- Retrieval: BM25 + embeddings over the raw documents (high recall, milliseconds).
- A small temporal fact layer on top, built from our ontology: each fact has a validity interval, what it replaces and its source document.
  Decide what replaces what by rule (PCN/ECN number, revision letter, effective date), not by asking the LLM.
- Inference rules from `ontology/rules.md` (e.g. material change → PPAP resubmission needed → no approval → cannot ship),
  with each inferred link citing the rule and the source facts. This is the "reasons, not only searches" part the judges asked for.
- The answer or warning-card model gets: currently valid facts, replaced facts marked as such, the rule chain, and the source text.

## Caveats

- Each category has 16 items, so one question moves a score by about 6 points. Differences under ~10 points are noise.
- The documents are short (about 58 words on average) and there are only 80 of them. A larger corpus would stress search more and should favour structured memory.
- All extraction ran on Haiku. Larger extraction models would likely improve Graphiti and LightRAG.
- The collision test calls the model once per transcript, with memory looked up for each utterance. A real live system calls it per utterance.
