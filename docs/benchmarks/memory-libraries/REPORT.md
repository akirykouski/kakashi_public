# Memory benchmark, KVA slice

Answer model: sonnet (same prompt for every system). Judge: haiku. Extraction model inside each memory system: haiku. Embeddings: multilingual-e5-small (local).

## Answer accuracy by category

| Category | bm25 | graphiti | mem0 | lightrag | graphiti_sources |
|---|---|---|---|---|---|
| supersession | 81% (n=16) | 75% (n=16) | 94% (n=16) | 75% (n=16) | 81% (n=16) |
| provenance | 56% (n=16) | 19% (n=16) | 50% (n=16) | 69% (n=16) | 31% (n=16) |
| multi_hop_inference | 69% (n=16) | 69% (n=16) | 69% (n=16) | 75% (n=16) | 62% (n=16) |
| multi_agent_conflict | 100% (n=16) | 100% (n=16) | 75% (n=16) | 100% (n=16) | 94% (n=16) |
| ontology_evolution | 69% (n=16) | 31% (n=16) | 56% (n=16) | 44% (n=16) | 56% (n=16) |
| ALL questions | 75% (n=80) | 59% (n=80) | 69% (n=80) | 72% (n=80) | 65% (n=80) |
| ALL, strict key match (dataset scorer) | 62% | 46% | 56% | 55% | 60% |

## Sources and retrieval

| Metric | bm25 | graphiti | mem0 | lightrag | graphiti_sources |
|---|---|---|---|---|---|
| Gold doc in retrieved context (recall) | 92% | 75% | 80% | 82% | 75% |
| Citation precision | 75% | 56% | 67% | 63% | 62% |
| Citation recall | 82% | 65% | 73% | 74% | 69% |

## Live collision (transcripts)

| Metric | bm25 | graphiti | mem0 | lightrag | graphiti_sources |
|---|---|---|---|---|---|
| Precision | 100% | 86% | 82% | 91% | 86% |
| Recall | 90% | 60% | 90% | 100% | 60% |
| F1 | 95% | 71% | 86% | 95% | 71% |
| Type correct (of true positives) | 78% | 50% | 56% | 70% | 50% |
| Evidence doc hit (of true positives) | 100% | 100% | 100% | 90% | 100% |
| Mean fire-index error | 0.00 | 0.17 | 0.00 | 0.00 | 0.17 |

## Cost and latency

| Metric | bm25 | graphiti | mem0 | lightrag | graphiti_sources |
|---|---|---|---|---|---|
| Ingest time, whole slice (s) | 0 | 2022 | 616 | 589 | 0 |
| Retrieval p50 (ms) | 0 | 139 | 100 | 2891 | 151 |
| Retrieval p95 (ms) | 1 | 472 | 433 | 4494 | 595 |
