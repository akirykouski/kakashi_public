# Agent memory, ontologies and contradiction detection: SOTA review for "Live Context Collision"

Prepared 13 Nov 2026 for the KVA "AI brain for industry" hackathon (Turin, 14 Nov).
GitHub stats were pulled with `gh api` on 13 Nov 2026. Items marked † are cited from the paper's abstract or README as I know it and were **not re-opened in this session**. Items marked **unverified** have no primary source I could confirm.

---

## 1. Bottom line

Build on **Graphiti** ([repo](https://github.com/getzep/graphiti), Apache-2.0, 32.8k stars, pushed 11 Nov 2026) as the memory store. It is the only mature open-source library that has all of these together: bi-temporal edges (`t_valid/t_invalid` plus `t'_created/t'_expired`), invalidation instead of deletion, provenance from each fact back to its source "episode", and Pydantic entity and edge types that work as a light ontology ([Zep paper](https://arxiv.org/html/2501.13956v1)).

Do **not** let an LLM decide supersession or merge concurrent writes. The 2026 evidence agrees on this:
- an LLM classifies create/update/supersede correctly only **20.1%** of the time ([FEB-30](https://arxiv.org/html/2610.22209v1));
- Zep scores **7%** and Mem0 **18%** on MemoryAgentBench FactConsolidation single-hop ([MemoryAgentBench v4, Table 3](https://arxiv.org/html/2507.05257v4));
- a deterministic version-aware resolver reaches **78.0%** (gpt-4o-mini) and **94.8%** (gpt-4o) on the same task ([Reddy & Challaram 2026](https://arxiv.org/pdf/2606.01435));
- write-time symbolic conflict checks reach **0.97** on ConflictBank, against **0.61** for aggregation baselines ([LatticeMind](https://arxiv.org/abs/2608.08236)).

Automotive documents give us the keys for this for free: PCN and ECN numbers, drawing revision letters, PPAP submission levels, deviation numbers and effective dates. Use them as **deterministic supersession keys**, plus a small rule layer (Python rules or pySHACL/owlrl, see Section 2b) to infer the missing link. For the live step, use a **two-tier collision detector**:
1. a fast claim extractor and a hybrid retrieval over *current* edges only;
2. a small NLI or fact-check model ([MiniCheck](https://arxiv.org/html/2404.10774v2)), or a fast LLM, as a gate, with the full LLM verifier run only on flagged candidates.

This matches the latency evidence: uniform RAG takes 8–15 s on fact checks in live meetings ([MeetBench-XL](https://arxiv.org/html/2602.03285v1)). Keep the expensive Graphiti ingestion (several LLM calls per episode) **out of the hot path**: pre-ingest company memory before the demo, and write meeting statements asynchronously.

---

## 2. Systems comparison

Abbreviations: KG = knowledge graph, temporal = timestamps but no invalidation, n/a = not supported or not documented.

| System | Core mechanism | Supersession / temporal validity | Provenance | Multi-agent writes and contradictions | Ontology / inference | Latency (as reported) | Licence, maturity | Link |
|---|---|---|---|---|---|---|---|---|
| **Zep / Graphiti** | Temporal KG: episode subgraph → entity/fact edges → communities. Hybrid search: cosine + BM25 + BFS | **Yes, bi-temporal.** An LLM compares a new edge with related edges. Only *temporally overlapping* contradictions invalidate. Old edge `t_invalid` = new `t_valid`. History kept | Every edge links back to its source episode(s) | `group_id` partitions. `SEMAPHORE_LIMIT`=10. No locking or merge semantics documented. Reference MCP server has **no auth** ("any caller can … delete data in any group_id") | Custom entity and edge types via Pydantic ("prescribed" ontology). No reasoner | LongMemEval_S end-to-end 2.58 s (gpt-4o), 1.6k context tokens. Search 0.513 / 0.778 s p50/p95 in Mem0's run. "sub-200 ms p95" is a Zep Cloud vendor claim. Ingestion latency not published (**unverified**) | Apache-2.0, 32.8k stars, Python. Neo4j / FalkorDB / Neptune | [paper](https://arxiv.org/html/2501.13956v1), [repo](https://github.com/getzep/graphiti) |
| **Mem0 / Mem0g** | LLM extracts facts. Per fact, top-s similar memories → LLM picks ADD/UPDATE/DELETE/NOOP. Mem0g adds an entity-relation graph | 2025: DELETE on contradiction. Mem0g marks edges invalid. **2026 algorithm is ADD-only** (no UPDATE/DELETE, so memories accumulate) | Weak: metadata only | No documented concurrency semantics | Graph variant only, no schema or rules | Search p50/p95 0.148/0.200 s, total 0.708/1.440 s (Mem0); Mem0g 0.476/0.657 s. 2026 algorithm p50 0.88–1.09 s (vendor) | Apache-2.0, 68.9k stars, Python and TS | [paper](https://arxiv.org/html/2504.19413v1), [2026 blog](https://mem0.ai/blog/ai-memory-benchmarks-in-2026), [repo](https://github.com/mem0ai/mem0) |
| **Letta (MemGPT)** | LLM-as-OS: core memory blocks in context, plus archival and recall memory edited by the agent through tools† | Agent rewrites blocks; no validity model† | n/a | Shared memory blocks across agents† | n/a | n/a | Apache-2.0, 25.4k stars | [MemGPT†](https://arxiv.org/abs/2310.08560), [repo](https://github.com/letta-ai/letta), [filesystem benchmark](https://www.letta.com/blog/benchmarking-ai-agent-memory) |
| **Hindsight** | 4 networks (world facts, experiences, entity summaries, evolving beliefs). Retain / recall / reflect. Recall = vector + BM25 + graph over entities and causal links | Beliefs are "updated traceably"; mechanism not detailed in abstract | Reflection layer described as traceable | n/a | n/a | n/a | MIT, 60.8k stars | [paper](https://arxiv.org/abs/2512.12818), [repo](https://github.com/vectorize-io/hindsight) |
| **Cognee** | ECL pipeline (`cognify`) → KG + vectors. `memify` post-processing | `temporal_cognify` adds time-stamped events. A third-party review says it has **no invalidation** | Chunk → node links† | n/a | **Accepts OWL/RDF (RDFLib).** Grounds entities to classes; validates against domain/range/hierarchy. Docs disagree on API | n/a | Apache-2.0, 33.3k stars | [ontology docs](https://docs.cognee.ai/core-concepts/further-concepts/ontologies), [review](https://zby.github.io/commonplace/notes/related-systems/cognee), [repo](https://github.com/topoteretes/cognee) |
| **HippoRAG 2** | OpenIE triples + passage nodes, Personalized PageRank ("non-parametric continual learning") | None | Passage nodes | n/a | Schema-less triples. Multi-hop by PPR, not rules | n/a | MIT, 4.1k stars | [paper](https://arxiv.org/pdf/2502.14802), [repo](https://github.com/OSU-NLP-Group/HippoRAG) |
| **GraphRAG (Microsoft)** | LLM-extracted KG → Leiden communities → community summaries† | None (batch re-index)† | Text-unit links† | n/a | Prompt-defined entity types† | Expensive indexing† | MIT, 36.6k stars | [paper†](https://arxiv.org/abs/2404.16130), [repo](https://github.com/microsoft/graphrag) |
| **LightRAG** | KG + vector dual-level retrieval, incremental inserts† | None† | Chunk links† | n/a | n/a | n/a | MIT, 40.7k stars | [paper†](https://arxiv.org/abs/2410.05779), [repo](https://github.com/HKUDS/LightRAG) |
| **A-Mem** | Zettelkasten notes with LLM links; new notes trigger "memory evolution" of old notes† | Note rewriting only† | n/a | n/a | n/a | Search 0.668/1.485 s p50/p95 (in Mem0 paper) | MIT, 1.2k stars, last push Dec 2025 | [paper†](https://arxiv.org/abs/2502.12110), [repo](https://github.com/agiresearch/A-mem) |
| **MemoryOS / MemOS / MIRIX / EverMemOS** | OS-style tiered memory (short / mid / long). MIRIX: 6 typed memories + multi-agent manager. EverMemOS: self-organising "MemCells"† | EverMemOS reports its largest gain on knowledge-update (+15.5 pp over MemOS, self-reported) | n/a | MIRIX routes writes through memory-manager agents† | n/a | n/a | All Apache-2.0. MemOS 12.4k, EverOS 13.9k, MIRIX 3.5k, MemoryOS 1.6k stars | [EverMemOS](https://arxiv.org/pdf/2601.02163), [MIRIX†](https://arxiv.org/abs/2507.07957), [MemOS†](https://arxiv.org/abs/2507.03724), [MemoryOS†](https://arxiv.org/abs/2506.06326) |
| **LatticeMind** (research, Aug 2026) | Structured memory with item **status**; cheap symbolic conflict checks at **write time**; LLM reconciler only for unresolved semantic conflicts | Status tracking | n/a | **Built for multi-agent.** Conflicts resolved at write, not by vote/debate/judge. Serialization of simultaneous writes not described | n/a | n/a | No code link found | [arXiv 2608.08236](https://arxiv.org/abs/2608.08236) |
| **StateFuse** (research, Jul 2026) | OpSet/CRDT merge + agent-facing semantics: immutable history, **explicit conflict objects**, correction handles | Immutable history | History is the log | **CRDT merge.** Contradictions stay visible instead of being collapsed. Ties on accuracy (282-question MemoryAgentBench conflict slice); gains are abstention and auditability | n/a | n/a | Repo listed in paper | [arXiv 2607.05844](https://arxiv.org/abs/2607.05844) |
| **Veracium / hybrid v2** (research, Jul 2026) | Layered typed provenance graph compiled to a curated map | Knowledge-update 121/123 | Typed provenance graph | n/a | n/a | n/a | Released by author | [Ground Truth First](https://arxiv.org/html/2607.21962v1) |

**Takeaways for us**
- Rendering superseded edges to the answerer hurts. Prose-inline history scored 79/81 and bi-temporal versioned edges 72/81 on knowledge-update-past questions, because stale values leaked ([Ground Truth First](https://arxiv.org/html/2607.21962v1)). So: filter to `t_invalid IS NULL` by default, and show history only on the card as "superseded by …".
- Supersession is usually local: derived records are not re-examined ([Always-On Agents survey](https://arxiv.org/html/2606.30306v1)). Cascading invalidation is the hard case in STALE ([STALE](https://arxiv.org/abs/2605.06527)) and RECON ([RECON](https://arxiv.org/abs/2607.16716)).

### 2b. Ontology construction, evolution and reasoning

| Topic | What exists | Relevance | Link |
|---|---|---|---|
| Ontology learning from text | OLLM: fine-tuned LLM builds the taxonomic backbone, scored with semantic graph metrics (NeurIPS 2024). OntoGPT/SPIRES: schema-guided recursive zero-shot extraction (BSD-3, 1.1k stars). NeOn-GPT: methodology-driven pipeline | SPIRES pattern = our "schema-guided extraction into Pydantic types" | [OLLM](https://arxiv.org/pdf/2410.23584), [OntoGPT](https://github.com/monarch-initiative/ontogpt), [NeOn-GPT](https://eprints.soton.ac.uk/511839/1/neon_gpt_2_final.pdf) |
| Benchmarking infrastructure | OntoLearner (Jul 2026): 180 ontologies, 22 domains, LLM pipelines | Could supply a reference ontology quickly | [arXiv 2607.01977](https://arxiv.org/pdf/2607.01977) |
| Ontology evolution / versioning | OM4OV: versioning as a task separate from matching, plus Agent-OV. Evo-DKD: dual decoder (edit + justification). TRACE-OU-Bench: 620 human-reviewed update candidates from SEC 10-Qs, 2016–2026 | Evo-DKD's "edit + justification" = our "why the ontology changed" record | [OM4OV](https://arxiv.org/pdf/2409.20302v9), [Evo-DKD](https://arxiv.org/abs/2507.21438), [TRACE-OU](https://ceur-ws.org/Vol-4316/pd-short-8.pdf) |
| Ontology alignment | OAEI 2025: Agent-OM in top 3 on Anatomy F-measure. LogMap + LLM oracle 2nd on bio-ml | Map customer vocabulary (e.g. OEM-specific CSR terms) to ours | [OAEI 2025 Anatomy](https://oaei.ontologymatching.org/2025/results/anatomy/index.html), [LogMap-LLM](https://arxiv.org/abs/2508.08500) |
| SHACL / OWL gates on LLM graphs | SHACL as a deterministic post-generation gate (missing links, invalid types). LLM repair of SHACL violations benchmarked. SHACL + OWL/DL + competency-question feedback loop for LLM-drafted ontologies. MFG-AgentGraph: RDF + SPARQL + SHACL critic for manufacturing | Use SHACL-style constraints as **compliance rules** ("PCN ⇒ customer approval before ship") | [NeurIPS 2026 validation](https://neurips.cc/virtual/2026/158007), [KG repair](https://arxiv.org/abs/2507.22419v1), [xpSHACL](https://www.emergentmind.com/papers/2507.08432), [LLMs4KGOE](https://ceur-ws.org/Vol-4246/llms4kgoe-6.pdf) |
| Rules / Datalog over KGs | SymAgent: LLM induces rules from the KG and detects missing triples. VADAOrchestra: Datalog± engine does all inference, LLM orchestrates. PyReason annotated Datalog for Graph-RAG | "Infer missing link from two relations" = one Datalog rule. Run it deterministically, not in the LLM | [SymAgent](https://arxiv.org/pdf/2502.03283), [VADAOrchestra](https://www.alphaxiv.org/abs/2606.22485.md), [KDMiLe 2025](https://sol.sbc.org.br/index.php/kdmile/article/download/44971/44734/) |
| Industrial ontologies | IOF Core (BFO 2020 based), 90 classes in release 202603. Maintenance and Production Planning modules | Upper-level anchor for Part, Process, Equipment, Organization | [IOF 202603](https://spec.industrialontologies.org/portal/release/202603/core.html), [OAGi release note](https://oagi.org/blogs/oagi-news-and-articles/oagi-announces-second-2025-release-of-iof-ontologies) |
| FMEA / automotive | FMEA ontology + KG-enhanced RAG (BMW/Fraunhofer, 2024–25). Ontology-guided LLM extraction of FMEA sheets → GNN, automotive pressure-sensor lines, F1@20 0.523 vs RAG 0.267 | Closest prior art to our domain | [Bahr et al.](https://arxiv.org/abs/2406.18114v2), [Okazaki et al.](https://arxiv.org/abs/2510.15428v1) |
| PPAP / APQP / 8D / PCN ontology | **None found** in this search (**unverified that none exists**) | Open gap: our hand-built mini-ontology is a credible novelty claim | — |

---

## 3. Benchmarks

| Benchmark | Measures | Metrics / size | Best published numbers (source; **SR** = self-reported by vendor or author of the system) |
|---|---|---|---|
| **LongMemEval** (ICLR 2025) | 5 abilities: information extraction, multi-session, temporal reasoning, **knowledge update**, abstention | 500 questions; _S (~115k tokens) and _M | Zep 71.2% (gpt-4o), with knowledge-update 83.3% and temporal 62.4% ([Zep paper](https://arxiv.org/html/2501.13956v1), SR). Hindsight 91.4% ([paper](https://arxiv.org/abs/2512.12818), SR). Mem0 2026 94.4% ([blog](https://mem0.ai/blog/ai-memory-benchmarks-in-2026), SR). Synap 95.6%, Mastra 94.87% (gpt-5-mini; 84.23% with gpt-4o) ([summary](https://www.maximem.ai/blog/synap-number-one-longmemeval), SR). EverMemOS 82–83% (SR). Judge and answer models differ, so **not comparable**. [paper](https://arxiv.org/abs/2410.10813), [repo](https://github.com/xiaowu0162/LongMemEval) |
| **LoCoMo** | Very long conversations: single-hop, multi-hop, temporal, open-domain QA; event summarisation | ~300 turns, ~9k tokens, up to 35 sessions per conversation; LLM-judge J | Paper run: Mem0g 68.44, Mem0 66.88, Zep 65.99, full-context 72.90 ([Mem0 paper](https://arxiv.org/html/2504.19413v1), SR). Letta filesystem agent 74.0 (gpt-4o-mini) ([Letta](https://www.letta.com/blog/benchmarking-ai-agent-memory), SR). Zep disputed Mem0's Zep run (75.14 or 84; sources disagree, **unverified**). 2026 claims: Mem0 92.5, Zep 94.7, EverMemOS 92.3 (all SR) ([Mem0 blog](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)). [paper](https://arxiv.org/abs/2402.17753) |
| **MemoryAgentBench** (v4, Jun 2026) | Accurate retrieval, test-time learning, long-range understanding, **selective forgetting / conflict resolution** (FactConsolidation SH/MH) | Contexts 6K/32K/64K/262K; accuracy | FC-SH / FC-MH: GPT-5-mini long-context 78.0/28.0; GPT-4o 60/5; HippoRAG-v2 54/5; BM25 48/3; Cognee 28/3; MemGPT 28/3; Mem0 18/2; GraphRAG 14/2; **Zep 7/3** ([Table 3](https://arxiv.org/html/2507.05257v4), independent). Deterministic resolver: 94.8 SH, 51.5 MH with gpt-4o ([Reddy & Challaram](https://arxiv.org/pdf/2606.01435), SR) |
| **STALE** (May 2026) | Implicit invalidation: state resolution, premise resistance, implicit policy adaptation | 400 scenarios, 1,200 queries, up to 150K tokens | Best model Gemini-3.1-pro 55.2% overall ([arXiv 2605.06527](https://arxiv.org/abs/2605.06527), independent of vendors). No code link found |
| **FEB-30** (Oct 2026) | **Intrinsic** store inspection: create/update/supersede classification, temporal correctness, **multi-author attribution** | 30 trajectories, 147 documents; UDR, FUR, fact accuracy, classification accuracy | One unnamed extract-embed-classify system: classification 20.1%, UDR 73.6%, FUR 22.2%, multi-author attribution 41.5% intrinsic ([arXiv 2610.22209](https://arxiv.org/html/2610.22209v1)). Closest existing benchmark to our provenance question |
| **MemConflict** (May 2026) | Dynamic, static and conditional conflicts (temporal validity, factual correctness, applicability); white-box retrieval and ranking | 6 systems; size not in abstract | Numbers not read (**unverified**) ([arXiv 2605.20926](https://arxiv.org/abs/2605.20926)) |
| **RECON** (Jul 2026) | Provenance-graph reasoning: which conclusions lose support when evidence is invalidated | 24 case files, 50–100k tokens | Best non-oracle 22.4% ([arXiv 2607.16716](https://arxiv.org/abs/2607.16716)) |
| **BEAM** (ICLR 2026) | 10 abilities incl. updating, **contradiction resolution**, temporal ordering, multi-hop | ~100 conversations up to 10M tokens, 2,000 questions | Mem0 64.1% (1M), 48.6% (10M) (SR) ([Mem0 blog](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)). Paper link not verified |
| **Ground Truth First** (Jul 2026) | Longitudinal (9-week) memory; knowledge update; write-stage quality | ~380 questions, 15 types | Hybrid v2 93.2% at week 9; knowledge-update 121/123 ([arXiv 2607.21962](https://arxiv.org/html/2607.21962v1), author's own system) |
| **ConflictBank** (NeurIPS 2024) | Misinformation, temporal and semantic knowledge conflicts | 7M claim-evidence pairs, 553k QA | LatticeMind 0.97 vs 0.61 baseline ([LatticeMind](https://arxiv.org/abs/2608.08236), SR). [ConflictBank](https://arxiv.org/abs/2408.12076v1) |
| **LLM-AggreFact** | Claim vs grounding-document fact checking (our collision step) | 10 datasets; balanced accuracy | MiniCheck-FT5 (770M) ≈ GPT-4 at ~400× lower cost ([MiniCheck](https://arxiv.org/html/2404.10774v2)). Bespoke-MiniCheck-7B 77.4% vs HHEM-2.1 71.8% ([vendor](https://bespokelabs.ai/bespoke-minicheck), SR, undated) |
| **MeetBench-XL** (Feb 2026) | Real-time meeting agents over ASR + enterprise KB | Latency + quality | Uniform RAG 8–15 s; 34% abandonment above 3 s (n=127); dual-policy router −30% latency ([arXiv 2602.03285](https://arxiv.org/html/2602.03285v1)) |

**Contradiction-detection literature for the collision step**
- Taxonomy of context-memory, inter-context and intra-memory conflicts: [Xu et al. survey](https://arxiv.org/abs/2403.08319) (link to the arXiv ID found via a mirror).
- Small NLI or fact-check models are the cheap gate: [MiniCheck](https://arxiv.org/html/2404.10774v2).
- Prior hackathon art with the same concept: ContextGuard, which compared extracted decisions with a memory graph and showed a cited card ([lablab](https://lablab.ai/submissions/wtu5jicnstcrbx4a4wmto7xr)). Judges may have seen this; we need the domain and the rule-inference edge.

---

## 4. What to copy to be "SOTA" on the four challenge questions

1. **Supersession ("when is a rule superseded?")**
   - Bi-temporal edges in the Graphiti style (`valid_from`, `valid_to`, `recorded_at`, `expired_at`), with invalidation, not deletion ([Zep](https://arxiv.org/html/2501.13956v1)).
   - **Deterministic supersession keys first**: same `(subject, predicate, scope)` plus a higher doc revision, PCN number or effective date, then `max(version)` wins ([Reddy & Challaram](https://arxiv.org/pdf/2606.01435)). Use the LLM only for "is this the same slot?" matching.
   - **Cascade invalidation**: when a fact is invalidated, re-check facts derived from it through `derived_from` edges. STALE, RECON and the survey all name this as the gap ([STALE](https://arxiv.org/abs/2605.06527), [RECON](https://arxiv.org/abs/2607.16716)).
   - Answer and retrieve over current edges only; show history on the card ([Ground Truth First](https://arxiv.org/html/2607.21962v1)).
2. **Many agents writing ("without contradicting each other")**
   - Append-only event log per writer (agent id, source, timestamp), with a single serialized resolver.
   - **Write-time conflict check**: symbolic first, LLM reconciler only for leftovers ([LatticeMind](https://arxiv.org/abs/2608.08236)).
   - Unresolved conflicts become explicit **Conflict nodes** linking both claims, instead of a silent overwrite ([StateFuse](https://arxiv.org/abs/2607.05844)).
   - Authority ranking for automatic resolution: compliance rule > customer-approved PPAP > engineering change > meeting statement.
3. **Decision rationale ("why was this decided")**
   - A `Decision` node with `decided_by`, `decided_at`, `source_episode` (transcript span or document page), `rationale`, `alternatives_rejected` and `supersedes`.
   - Graphiti episodes give source-span provenance. FEB-30 shows multi-author attribution is the weakest dimension (41.5%) ([FEB-30](https://arxiv.org/html/2610.22209v1)), so store the author as structured data, never inferred.
4. **Ontology (build, evolve, reason)**
   - **Build**: a mini PPAP/APQP/PCN/8D ontology as Pydantic types (Part, Supplier, Customer, PPAP Submission, PCN/ECN, Deviation, Control Plan, Capacity, Commitment, Decision, Rule), anchored to IOF Core classes ([IOF](https://spec.industrialontologies.org/portal/release/202603/core.html)). Fill it with schema-guided extraction, SPIRES style ([OntoGPT](https://github.com/monarch-initiative/ontogpt)).
   - **Evolve**: ontology changes are themselves versioned edits with a justification record ([Evo-DKD](https://arxiv.org/abs/2507.21438), [OM4OV](https://arxiv.org/pdf/2409.20302v9)). The demo moment: "the process changed, the old relation was replaced by the new one".
   - **Reason, not search**: 3–5 Datalog-style rules run deterministically, for example `affects(PCN, Part) ∧ supplied_to(Part, Customer) ⇒ requires_approval(PCN, Customer)`, and `depends_on` transitivity for dependencies. Add SHACL-style constraints as compliance checks ([SymAgent](https://arxiv.org/pdf/2502.03283), [VADAOrchestra](https://www.alphaxiv.org/abs/2606.22485.md), [SHACL gate](https://neurips.cc/virtual/2026/158007)). Every inferred edge carries `inferred_by: rule_id` and links to the premises.
5. **Live collision pipeline (latency)**
   - Streaming ASR partials, then a claim extractor (fast LLM, structured output) on final segments only.
   - Retrieval keyed by entity and slot over current edges plus inferred edges (no LLM).
   - A cheap NLI or MiniCheck gate, then the LLM verifier on the top-k candidates only.
   - The card cites the source episode and the rule.
   - Two-tier routing follows [MeetBench-XL](https://arxiv.org/html/2602.03285v1). Target from that paper: under 3 s from end of utterance to card.

---

## 5. How to benchmark our system

**Cheap existing subsets.** No paid API was run for this review. These cost estimates are for the team.
- **LongMemEval_S**: only the `knowledge-update` and `temporal-reasoning` question types ([repo](https://github.com/xiaowu0162/LongMemEval)). The per-type question counts were not checked (**unverified**). Compare with Zep's per-category 83.3 / 62.4 (gpt-4o).
- **MemoryAgentBench FactConsolidation-SH** at the **6K and 32K** context sizes, not 262K ([HF dataset](https://huggingface.co/datasets/ai-hyz/MemoryAgentBench)). Reference points: Zep 7, Mem0 18, HippoRAG-v2 54, deterministic resolver 78 (4o-mini). This is the most direct "supersession" number and the strongest slide.
- **STALE**: a small sample of state-resolution and premise-resistance queries, if the data is released (no link found).
- **LLM-AggreFact** subset for the NLI gate model choice ([MiniCheck](https://arxiv.org/html/2404.10774v2)).

**Custom domain benchmark (synthetic automotive supplier, about 50–100 items)**

| Metric | Definition |
|---|---|
| Supersession accuracy | Given a query at time t, the current value is returned, and no superseded value is shown as current. Also report a false-update rate, as in FEB-30 UDR/FUR |
| Cascade accuracy | Derived facts correctly invalidated after an upstream change |
| Provenance accuracy | The card's cited source episode, author and date match the gold record exactly. Report separately for multi-author cases |
| Multi-hop inference accuracy | Precision and recall of rule-inferred edges against gold. Plus rule-only vs LLM-only ablation |
| Collision precision / recall / F1 | On scripted meeting utterances. Include "near-miss" negatives (consistent restatements, a newer valid decision) to measure false alarms |
| Concurrent-write consistency | Run N agents writing conflicting facts in random order. The final state must be the same across orderings (determinism) and every conflict must be surfaced |
| Latency | p50 / p95 from end of utterance to card, split by stage (ASR, extract, retrieve, gate, verify) |

Report the deterministic resolver against an LLM-only resolver against vanilla Graphiti invalidation on the same items. This mirrors the published 7% → 78% gap.

---

## 6. Open questions and things I could not verify

- Graphiti **ingestion** latency per episode, and its behaviour under concurrent `add_episode` calls on the same `group_id`: not published (**unverified**). Measure it before the demo.
- Graphiti latest release number: the README did not state it. Third-party sources say v0.29.x (**unverified**).
- LongMemEval and LoCoMo 2026 leaderboard numbers (Mem0 94.4/92.5, Zep 94.7, Synap 95.6, Hindsight 91.4) are **all self-reported**, with different judge and answer models. The Zep vs Mem0 LoCoMo dispute (75.14 vs 84 vs 65.99) is unresolved.
- MemConflict numbers, BEAM paper link and STALE code/data availability: not found.
- The LatticeMind concurrency model (ordering and locking) is not described in the abstract.
- No PPAP/APQP/PCN/8D ontology found. The absence is not proven.
- Rows marked † (Letta, GraphRAG, LightRAG, A-Mem, MemOS, MIRIX, MemoryOS mechanism details and arXiv IDs) were not re-opened today.
- The Hindsight star count (60.8k) is unusually high for its age. It is reported as returned by the GitHub API.
- The Felarity "live contradiction alerts with DeBERTa NLI" claim is marketing only ([page](https://felarity-com.pages.dev/product/)).
