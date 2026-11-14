# Docs

| Path | What it is |
|---|---|
| `plan.md` | Team decisions (track, input, core) and the plan for 14 Nov |
| `methodology.md` | Evaluation protocol: hypotheses, data, conditions, metrics, threats to validity (pre-registered by commit time) |
| `research/memory_sota.md` | Review of agent memory systems (Graphiti/Zep, Mem0, LightRAG, …) and contradiction detection, 13 Nov |
| `research/ontology_sota.md` | Review of LLM + ontology reasoning, OWL/SHACL in Python, bitemporal memory, manufacturing ontologies, KVA's OIDA paper, evaluation without an LLM judge, 13 Nov |
| `benchmarks/memory-libraries/` | 13 Nov: BM25 over raw documents vs Graphiti, Mem0, LightRAG on a synthetic supplier archive; retrieval-only comparison on 377 documents |
| `benchmarks/core/` | 13–14 Nov: the reference core vs retrieval vs full context on 36 change requests, pre-registered; scale run; fact extraction from long documents |
| `benchmarks/crossbench/` | 14 Nov morning: each of the two prepared cores run on the other author's requests, plus an independent review and a merge plan |

All data in these benchmarks is synthetic: companies, people, parts and documents are invented. Standards are referenced by clause number and paraphrased. Paths inside the reports (`bench/`, `core/`, `data/`) refer to the prepared code, which is not in this repo yet.
