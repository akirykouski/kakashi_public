# Retrieval only (full corpus, 377 docs, 284 queries)

Gold source documents vs the ranking, after dropping documents dated after the question's as-of date.

## Overall

| Method | Recall@5 | Recall@10 | MRR | nDCG@10 | Index build (s) | Per query (ms) |
|---|---|---|---|---|---|---|
| BM25 | 0.58 | 0.72 | 0.49 | 0.50 | 0 | 2 |
| e5-small (multilingual) | 0.56 | 0.66 | 0.45 | 0.47 | 4 | 3 |
| bge-m3 | 0.61 | 0.71 | 0.50 | 0.52 | 33 | 31 |
| qwen3-embedding-0.6b | 0.59 | 0.67 | 0.47 | 0.49 | 110 | 99 |
| Hybrid: BM25 + bge-m3 (RRF) | 0.63 | 0.78 | 0.52 | 0.55 | 33 | 33 |
| BM25 → CE bge-reranker-v2-m3 | 0.67 | 0.81 | 0.56 | 0.60 | 0 | 8432 |
| bge-m3 → CE bge-reranker-v2-m3 | 0.67 | 0.80 | 0.55 | 0.59 | 33 | 6796 |
| Hybrid → CE bge-reranker-v2-m3 | 0.66 | 0.82 | 0.55 | 0.60 | 33 | 6355 |
| BM25 → CE mMiniLM-L12 (light) | 0.62 | 0.74 | 0.49 | 0.53 | 0 | 492 |
| bge-m3 → CE mMiniLM-L12 (light) | 0.60 | 0.71 | 0.48 | 0.51 | 33 | 550 |
| Hybrid → CE mMiniLM-L12 (light) | 0.63 | 0.74 | 0.49 | 0.53 | 33 | 545 |

## Recall@10 by category

| Category | BM25 | e5-small (multilingual) | bge-m3 | qwen3-embedding-0.6b | Hybrid: BM25 + bge-m3 (RRF) | BM25 → CE bge-reranker-v2-m3 | bge-m3 → CE bge-reranker-v2-m3 | Hybrid → CE bge-reranker-v2-m3 | BM25 → CE mMiniLM-L12 (light) | bge-m3 → CE mMiniLM-L12 (light) | Hybrid → CE mMiniLM-L12 (light) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| supersession (n=50) | 0.84 | 0.86 | 0.88 | 0.86 | 0.92 | 0.96 | 0.96 | 0.94 | 0.92 | 0.92 | 0.90 |
| provenance (n=42) | 0.85 | 0.80 | 0.80 | 0.62 | 0.89 | 0.96 | 0.94 | 0.95 | 0.93 | 0.90 | 0.90 |
| multi_hop_inference (n=48) | 0.76 | 0.62 | 0.70 | 0.61 | 0.69 | 0.75 | 0.76 | 0.74 | 0.83 | 0.77 | 0.79 |
| multi_agent_conflict (n=49) | 0.63 | 0.80 | 0.73 | 0.88 | 0.76 | 0.82 | 0.82 | 0.90 | 0.82 | 0.76 | 0.86 |
| ontology_evolution (n=41) | 0.78 | 0.55 | 0.60 | 0.54 | 0.72 | 0.76 | 0.68 | 0.75 | 0.69 | 0.65 | 0.68 |
| live_collision (n=54) | 0.49 | 0.37 | 0.56 | 0.50 | 0.69 | 0.64 | 0.64 | 0.65 | 0.33 | 0.34 | 0.37 |
| ALL (n=284) | 0.72 | 0.66 | 0.71 | 0.67 | 0.78 | 0.81 | 0.80 | 0.82 | 0.74 | 0.71 | 0.74 |
