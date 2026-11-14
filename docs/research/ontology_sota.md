# Ontology + deductive checking: SOTA review for "Live Context Collision"

Prepared 13 Nov 2026 for KVA "AI brain for industry" (Turin, 14 Nov). This review complements `research/memory_sota.md`, which covers memory systems and is not repeated here.

Markers:
- **[measured]**: we ran it ourselves on 13 Nov.
- **†**: secondary source only, or a claim we could not open at the primary source.
- **unverified**: no source found.

---

## 1. LLM extracts, symbolic reasoner infers

**Pattern.** An LLM fills a fixed schema from text. A deterministic engine then derives and checks.

- **SPIRES / OntoGPT** ([Caufield et al., *Bioinformatics* 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10924283)) is the reference design. It prompts recursively against a user-defined LinkML schema and grounds the extracted terms to ontology IDs. The authors report accuracy "comparable to the mid-range" of supervised relation-extraction systems, with no training data. That is honest evidence that extraction, not reasoning, is the weak link.
- **Text2KGBench** ([ISWC 2023](https://arxiv.org/abs/2308.02357)) scores ontology-conformant extraction on seven metrics, including ontology conformance and hallucination. It is a ready-made metric template for our extractor.
- **LLM-written ontologies.** Ontogenia with o1-preview produced modules that experts rated better than those of novice ontology engineers, but "common mistakes and variability" remain ([Lippolis et al. 2025](https://arxiv.org/abs/2503.05388)). This supports writing the alloy and approval ontology by hand.
- **Quote grounding.** Google's LangExtract maps every extraction to character offsets and sets `char_interval=None` when the text cannot be found ([repo](https://github.com/google/langextract), [blog](https://developers.googleblog.com/en/introducing-langextract-a-gemini-powered-information-extraction-library/)). This is the same idea as our "the quote must be a substring of the page" check, and is useful prior art to cite.

**Evidence that symbolic inference helps:**
- **Logic-LM** (LLM → formal program → solver): +39.2% over standard prompting and +18.4% over chain-of-thought across five logic datasets ([Pan et al., EMNLP Findings 2023](https://arxiv.org/abs/2305.12295)).
- **BABILong:** LLMs "effectively utilize only 10–20% of the context", and performance "declines sharply with increased reasoning complexity". RAG reaches only about 60% on single-fact QA† ([NeurIPS 2024](https://arxiv.org/abs/2406.10149)).
- **OntoURL:** LLMs are good at ontology *understanding* but weak at ontology *reasoning and learning* ([Zhang et al. 2025](https://arxiv.org/abs/2505.11031)).

**Where symbolic inference does not win:**
- **Long context often wins on aggregate QA.** On LaRA (ICML 2025) there is "no silver bullet". At 32k tokens, long context beats RAG by 2.4 points on average, and RAG gains as length grows ([LaRA](https://arxiv.org/abs/2502.09977)). Li et al. find long context "consistently outperforms RAG" when resources allow ([EMNLP 2024](https://arxiv.org/abs/2407.16833)). OIDA's own result is the same: full context 0.83–0.84 EQS vs structured 0.54–0.56 (Section 5).
- **Graph evidence is not uniformly better.** On FactKG multi-hop claims, the graph model GEAR scored 68.8 against 70.1 for a claim-only BERT† ([ACL 2023](https://aclanthology.org/2023.acl-long.895)).
- **Translation failures sink neuro-symbolic pipelines.** If the extractor misses one side of a conflict, the reasoner proves "consistent". OIDA calls this "false consistency".

**Our claim should therefore be narrow.** Symbolic inference beats long context on *closed-world constraint checks with explicit scopes* (approval for part × site × customer, an alloy designation, a superseded revision). The answer there is a proof, and an omission must be flagged, not smoothed over. It does not beat long context on open QA.

## 2. OWL 2 RL / SHACL in Python: what actually works

**owlrl 7.6.2** ([docs](https://owl-rl.readthedocs.io/en/latest/owlrl.html), [PyPI](https://pypi.org/project/owlrl/))
- **Mechanism:** brute-force forward chaining of the OWL 2 RL rules over rdflib.
- **Not implemented:** datatype entailment and the extensional rules. It uses its own lexical-to-Python datatype conversions.
- **New option:** a pyoxigraph store can be passed as the backend.

What we confirmed on 13 Nov **[measured]** (rdflib 7.6.0, Python 3.14, Mac):
- `owl:TransitiveProperty`, `owl:inverseOf` and `owl:propertyChainAxiom` (rule prp-spo2) all fire.
- A violation of `owl:disjointWith` does **not** raise an error. owlrl adds an `ErrorMessage` node to the graph, so the code must look for it.
- Closure inflates the graph. Three input triples became 115, because owlrl adds axiomatic triples.

Closure and validation time **[measured]**:

| Base triples | After closure | owlrl closure | pySHACL SPARQL constraint |
|---|---|---|---|
| 1.3k | 5.0k | 1.1 s | 1.4 s |
| 6.5k | 24.6k | 6.1 s | 8.1 s |
| 26k | 98k | 24.2 s | 33.9 s |

Time grows about linearly with size, at roughly 4k closed triples per second. **Implication:** close the *ontology plus a case subgraph* (≤ 5k triples, about 1 s), not the whole company memory, and pre-close the static TBox.

**pySHACL 0.40.2** ([repo](https://github.com/RDFLib/pySHACL))
- **Covers:** SHACL Core and SHACL-SPARQL; SHACL-AF rules (`sh:SPARQLRule`, `sh:TripleRule`) with `advanced=True`; fixpoint iteration with `iterate_rules`; a `shacl_rules()` call that returns inferred triples; SHACL-JS as an extra.
- **Inference:** the `inference=rdfs|owlrl|both` option runs owlrl before validation. `ont_graph` mixes in the TBox.
- **Missing:** no performance claims, and SHACL 1.2 is not mentioned.
- **Confirmed [measured]:** a `sh:SPARQLRule` that derives `requires PPAPResubmission` from `changesMaterialSource`.
- **SHACL 1.2 Rules** is a W3C draft ([ED](https://w3c.github.io/data-shapes/shacl12-inference-rules/)), so avoid depending on it.

**Key semantic point.** OWL is open-world: a missing approval is *unknown*, not false. Every "missing X" blocker must therefore be a SHACL (closed-world) constraint. Use OWL only for classification and chains, for example 6082-T6 ⊑ Al-Mg-Si alloy, partOf being transitive, and approval scope propagating via a chain.

**Explanations.** Neither owlrl nor pySHACL produces justifications. pySHACL reports focus node, path, value and message, but not *why*. The practical fix is three steps:
1. Make every blocker a SHACL-SPARQL constraint whose `SELECT` returns the premise fact IDs.
2. Look up the stored quote for each premise.
3. Render that as the chain.

Gallina et al. take the same approach: each SHACL rule writes PROV-O triples onto what it derives (Section 4).

**Engines with real proofs or incremental reasoning, if we outgrow rdflib:**
- **RDFox** (commercial): incremental maintenance on commit, plus proofs for materialised facts through an explanation endpoint and console ([docs](https://docs.oxfordsemantic.tech/features-and-requirements.html), [programmatic access](https://docs.oxfordsemantic.tech/5.7/programmatic-access-APIs.html)).
- **Nemo** (Rust, Apache-2.0/MIT, Python and WASM bindings): Datalog with negation and aggregates. Its "tracing… a proof tree that shows the concrete rule applications and input facts", and the authors say it "adds no cost to reasoning" ([KR 2024](https://iccl.inf.tu-dresden.de/w/images/f/fb/KR-2024-CR.pdf), [repo](https://github.com/knowsys/nemo)). It is the best open-source match for "inference chain under every step", but the repo still says releases are "unstable".
- **Oxigraph:** a SPARQL store with no built-in reasoning found. Third-party OWL 2 RL is available through `reasonable`† ([docs.rs](https://docs.rs/crate/reasonable/0.4.4-a1/source/src/common.rs)).
- **Soufflé:** has provenance/explain mode† (not reopened).

## 3. Time, supersession and provenance

**Two clocks.**
- *Valid time*: when the fact holds in the plant, e.g. drawing Rev. C is effective from a date.
- *Transaction time*: when memory learned it. It is immutable and set by the system.

XTDB is a clean reference model (SQL:2011 system-time plus valid-time on every table, with old versions closed rather than overwritten; [docs](https://docs.xtdb.com/about/time-in-xtdb.html)). Our SQLite fact log should copy it: `valid_from`, `valid_to`, `recorded_at`, `superseded_by`, and nothing deleted.

**RDF options.**
- **Named graph per fact or source** (works today in rdflib Dataset/TriG). The nanopublication pattern of *assertion + provenance + pubinfo* graphs is a proven template ([Kuhn et al.](https://arxiv.org/abs/1809.06532)). It models one assertion from one evidence source; a 2025 paper adds a multi-source provenance graph† ([IJDL 2025](https://link.springer.com/article/10.1007/s00799-025-00431-x)).
- **RDF 1.2 triple terms** (RDF-star successor) are a **Candidate Recommendation**, not a Recommendation (7 Apr 2026 snapshot; [W3C](https://www.w3.org/TR/rdf12-concepts/)). Do not make the demo depend on them.

**PROV-O** (W3C Rec, 30 Apr 2013; [spec](https://www.w3.org/TR/prov-o/)) has the exact vocabulary for "superseded, not deleted":
- `prov:wasRevisionOf` for Rev. C → Rev. B;
- `prov:wasInvalidatedBy` and `prov:invalidatedAtTime` for an approval revoked by an ECN;
- `prov:hadPrimarySource` for the drawing or PPAP PSW the quote came from;
- `prov:wasDerivedFrom` for each step of the chain.

**Supersession rule.** Do it by rule, not by LLM. The memory review already showed that LLM supersession is weak. The deterministic version is a SHACL-SPARQL query: same document key (drawing number, PPAP ID, deviation number) with a higher revision or a later effective date → `superseded_by`. A rule is "outdated" when its source carries `prov:invalidatedAtTime` before the meeting date, or when a newer revision of the same key exists. That is a query, not a judgement.

## 4. Manufacturing / automotive ontologies

**IOF Core + Supply Chain (SCRO)**
- **Sources:** [repo](https://github.com/iofoundry/ontology), [SCRO 202603](https://spec.industrialontologies.org/portal/release/202603/supplychain.html). Releases are 202502, 202601 and 202603.
- **Basis:** BFO-based, with MIT licence† and SCRO marked "Provisional" in earlier releases.
- **Useful terms:** supply relationship, supplier evaluation process, "is supplied by at some time", lot, traceable resource unit.
- **Gap:** no supplier *qualification/approval* class in SCRO. Certificates live in the separate Certification ontology.
- **Recommendation:** import a handful of IOF IRIs for alignment credibility, but model `ApprovalScope(part, site, customer, revision)` ourselves. Full IOF + BFO imports would bloat the owlrl closure (Section 2 numbers).

**Catena-X**
- **Format:** semantic models are SAMM aspect models in RDF/Turtle ([CX-0125](https://catenax-ev.github.io/docs/standards/CX-0125-TraceabilityUseCase), [sldt-semantic-models](https://github.com/eclipse-tractusx/sldt-semantic-models)).
- **Quality models:** Quality Task ([CX-0036](https://catenax-ev.github.io/docs/standards/CX-0036-AspectModelQualityTask)), Quality Alerts and Investigations ([CX-0125](https://catenax-ev.github.io/docs/standards/CX-0125-TraceabilityUseCase)), and part analyses (CX-0040).
- **Gaps:** **no 8D model** and **no engineering-change/PCN standard** found. An Engineering committee was launched in Oct 2025, with change requests named as a future vocabulary ([Catena-X news](https://catena-x.net/news/catena-x-introduces-engineering-domain-to-accelerate-efficient-product-development/)).
- **Academic 8D work:** one paper uses OWL+SKOS for 8D (closed access, not read†; [UTS](https://opus.lib.uts.edu.au/handle/10453/179325)).
- **Claim we can make:** "Catena-X-compatible identifiers", not "Catena-X model".

**ISO 15926:** process-plant lifecycle data, heavyweight and not automotive. Mention it only as the ancestor.

**Gallina, Schweizer & Dibowski (Mälardalen + Robert Bosch GmbH)**
- **Paper:** *Regulatory Compliance-aware System Change Management via an Ontology-based Approach*, EuroSPI 2025, Springer, [DOI 10.1007/978-3-032-04288-0_15](https://doi.org/10.1007/978-3-032-04288-0_15), [PDF](https://www.es.mdu.se/pdf_publications/7205.pdf). We read the full text.
- **Model:** an RDF feature-model ontology plus reusable SHACL shapes (mandatory/optional/OR/XOR, cross-feature constraints).
- **Rules:** two **SHACL-SPARQL rules** (`sh:SPARQLRule`, CONSTRUCT) auto-create missing *mandatory* and *required* features. Each created node carries PROV-O (`generatedAtTime`, `wasGeneratedBy`, `wasDerivedFrom`).
- **Chaining:** rules are chained to a fixpoint ("forward chaining").
- **Missing evidence:** `sh:minCount 1` on evidence properties lists the evidence that is still missing.
- **Case:** adding a digital key to a Bosch window lifter pulls in UN R155 (cybersecurity) requirements on top of UN R21/ISO 26262 (safety). The approach detects "key-evidence omission".
- **Limits:** an illustration only. There is **no quantitative evaluation**, no LLM, and no temporal or supersession model. The generated features are "empty placeholders".
- **Relevance to us:** this is the closest published precedent, built at Bosch with the same pySHACL-compatible mechanism. Cite it as "the pattern is industry-validated; we add extraction from documents, quotes, and time".

**Other engineering-change KG work.** No peer-reviewed 2024–26 ECR/ECN/PPAP + KG + LLM paper was found. The closest is ontology-based change-impact analysis from SEAA 2018 ([Novacek et al.](https://arxiv.org/abs/2608.21949)). The rest is vendor material (Siemens, SPREAD, Mendix). That is a positioning gap we can name.

## 5. OIDA (KVA's paper)

**Paper.** Bottino, Ferrero, Dosio (KVA) and Beneventano (MIT), *Retrieval Is Not Enough: AI for Organizations Needs Epistemic Infrastructure*, [arXiv 2604.11759 v2](https://arxiv.org/html/2604.11759). It is a preprint and not peer-reviewed.

**What it does**
- **Graph model:** a typed, signed, time-indexed graph with 9 node types: DECISION, CONSTRAINT, EVIDENCE, NARRATIVE, PLAN, EVALUATION, OBSERVATION, HYPOTHESIS, QUESTION.
- **Edges:** signed and weighted, e.g. SUPPORTS +1.0, SUPERSEDES +0.6, BLOCKS −0.4, CONTRADICTS −0.6. The authors call these coefficients "implementation priors".
- **Supersession:** a superseded node is "demoted, not deleted".
- **Contradiction:** a contradicted node is "down-weighted or paired with its contradiction". It is never deleted.
- **Priority:** a dynamic score K_t combines type prior, urgency, usage, evidence, influence, decay and contradiction penalty. The authors say this is "a model specification, not an empirical result".
- **Open questions:** QUESTION nodes gain urgency while unresolved, and "knowledge gap" sections are surfaced. These appeared in 10/10 structured runs against 5/10 for full context.

**What it does not do (v2)**
- No OWL, SHACL, reasoner or formal axioms.
- No description of *how* contradictions are detected. Extraction is called "load-bearing" and is left to future audits.
- No domain model.
- Scopes are not a distinct mechanism in v2. The product site may differ (unverified).

**Its evaluation**
- **Data:** synthetic corpora, 3 queries × 10 runs, scored with an **LLM judge** on the non-validated EQS metric.
- **Result:** full context wins, 0.833/0.844 vs 0.557/0.540, at about 110k vs about 2k tokens.
- **Equal-budget ablation:** proposed but not run. The authors write that the graph layer is justified only if it helps "at equal or lower token budget". A third-party summary calls this ablation "pre-registered"†; our read of v2 did not find that word, so check v1.

**How we complement it**

| | OIDA says | We say |
|---|---|---|
| Question answered | *which* decision is in force (a decision registry) | *what a proposed change collides with* (a domain model plus deduction) |
| Typed edge comes from | a person or model asserting CONTRADICTS | a constraint over the facts, whose failure *is* the contradiction, with a proof |
| Basis | scored memory | proved blocker; a missing premise becomes a QUESTION with an owner, which is their vocabulary |

Plug-in point: our blockers can be written into OIDA as CONSTRAINT and EVIDENCE nodes with CONTRADICTS/BLOCKS edges. This also answers Martinelli's line: the SHACL constraint fires whatever the LLM believes, and the LLM can only *fail to extract*, which shows up as a gap, not a pass.

## 6. Evaluation without an LLM judge

**Scoring**
- **Blockers:** score blocker sets by exact match against gold IDs (precision, recall, F1 per case) — same idea as MuSiQue/HotpotQA EM/F1.
- **Quotes:** check them mechanically (substring of the source page, right document version).
- **Chains:** check that every chain step's premise exists in the fact log and was valid at the meeting date.
- **Avoid:** existing contradiction benchmarks lean on LLM or human judges; WikiContradict uses a fine-tuned Llama-3-70B judge ([NeurIPS 2024](https://arxiv.org/abs/2406.13805)). Our own gold set is the honest choice.

**Case mix (≥ 30 cases)**
- scope mismatch (approved for BR-180, not BR-220);
- near-miss alloy (6061-T6 vs 6082-T6);
- superseded revision;
- expired derogation (ELV entry, Section 7);
- multi-hop (part → assembly → customer CSR → special characteristic);
- **≥ 30% clean changes**, to measure the false-blocker rate.

**Pre-registration.** Commit `prereg.md` to git *before* the run, so the hash and timestamp are the proof. It holds:
- the case list hash;
- the metrics;
- thresholds, e.g. *fail if blocker recall < 0.9 or false-blocker rate > 0.1 on held-out cases*;
- the exact baselines.

Report a fail as a fail.

**Equal token budget.** This is OIDA's own missing E4. Fix the budget B (e.g. 4k tokens) for the answering LLM in every arm:
1. Full context. This also needs a ≥ 100k unconstrained arm, labelled as such, since LaRA and Li et al. show it is strong.
2. BM25 top-k to B. BM25 beat memory systems in our earlier bench.
3. Ontology: the serialized blocker chain plus quotes, within B.
4. Ontology with no LLM: deterministic output, 0 tokens.

Report F1, false-blocker rate, latency and $ per arm. If arm 2 ties arm 3 on F1, our advantage is the proof and the closed-world "missing" flags, not the accuracy. Say so.

## 7. Regulation in the demo

**Regulation (EU) 2026/1738**, the ELV Regulation. We read the signed text ([PE-CONS 13/1/26 REV 1](https://data.consilium.europa.eu/doc/document/PE-13-2026-REV-1/en/pdf)). EUR-Lex was unreachable from our network; the ELI is [eur-lex.europa.eu/eli/reg/2026/1738/oj](https://eur-lex.europa.eu/eli/reg/2026/1738/oj).
- **Dates:** signed 8 Jul 2026, published in the OJ 24 Jul 2026, **in force 13 Aug 2026** (Art. 59(1)). Generally applicable from **1 Sep 2028** (Art. 59(2)). Art. 5(2)–(9) apply one month after entry into force.
- **Art. 5(4):** vehicle types type-approved from the first day of the month after 72 months (= **1 Sep 2032**), and new parts for them, "shall not contain lead, mercury, cadmium or hexavalent chromium". This is subject to **Annex IV** (Art. 5(5)). Batteries are excluded and covered by Reg. 2023/1542.
- **Annex IV tolerances:** 0.1 wt% in homogeneous material for Pb, Cr(VI) and Hg; 0.01% for Cd.
  - Entry **2(c)(i)**: aluminium alloys for machining with ≤ 0.4% Pb are exempt only for vehicles type-approved before **1 Jan 2028** (and spares).
  - Entry 2(c)(ii) (recycled-Pb Al): before 1 Jan 2027.
  - Entries 13(a)/(b) (Cr(VI) corrosion coatings): spares only.
- **Art. 57(1):** **Directive 2000/53/EC is repealed from 1 Sep 2028**. Its Art. 4(2) and Annex II continue until the last day of the month after 71 months, which we compute as 31 Aug 2032. Annex II entries 5(a), 5(b)(i), 5(b)(ii) and 16 ceased on 13 Aug 2026.
- The Directive's Art. 4(2)(a) ban on Pb/Hg/Cd/Cr(VI) is the existing rule until then. We cite it from knowledge and did not reopen the Directive text.

**REACH Cr(VI)**
- **Current regime:** Cr(VI) substances are on Annex XIV, so authorisation is required. The only Annex XVII restriction is entry 47 (leather ≥ 3 mg/kg, and cement)†.
- **New restriction:** an ECHA Annex XVII proposal that would *replace* authorisation for chromium trioxide, chromic acids, dichromates and others.
  - SEAC agreed a draft opinion in June 2026, with consultation from 17 Jun to 17 Aug 2026 ([team-mastery](https://team-mastery.eu/seac-agrees-draft-opinion-on-chromiumvi-restriction-proposal/)†).
  - The final SEAC opinion is expected at SEAC-73, around end-2026.
  - Commission adoption is expected by end-2028 ([Ekotox](https://ekotox.eu/chromiumvi-compounds-planned-regulation-extended-authorisations-and-timeline/)†).
- **Status:** **not adopted as of 13 Nov 2026** (no source found saying otherwise). ECHA's own page returned 403 to us.

**Demo wording:** "Cr(VI) passivation is restricted by ELV Art. 5 / Annex IV and authorisation-bound under REACH Annex XIV; a REACH restriction is pending". Never say "banned by REACH".

---

## What this means for Saturday

1. **Claim the narrow win.** Say: "deductive blockers on scoped, closed-world constraints, with a proof and quotes". Do not say "beats long context" or "beats RAG". LaRA, Li et al. and OIDA itself show full context wins on general QA.
2. **Put every "missing X" check in SHACL, not OWL.** Use OWL 2 RL only for subclass, transitivity and property chains. Say "OWL classifies, SHACL decides" on stage; Davide will check this distinction.
3. **Build the chain from constraint premises plus PROV-O,** as Gallina et al. do at Bosch. Don't promise "reasoner justifications": owlrl and pySHACL have none. Name Nemo/RDFox as the production path for true proof trees.
4. **Keep the reasoned graph small.** Close a pre-built TBox plus the case subgraph (≤ 5k triples, about 1 s measured). Whole-memory closure is 24 s at 26k triples.
5. **Answer "how memory knows a rule is outdated" with a query:** same document key, higher revision or `prov:invalidatedAtTime` → superseded, plus valid time vs record time in the append-only log. Show one superseded fact greyed out, not deleted.
6. **Answer "humans + agents writing without contradictions":** writes append facts and never edit them; constraints run on write; a conflict becomes an OIDA-style QUESTION with a named owner. The AI never resolves it.
7. **Run the equal-budget, four-arm comparison with a pre-registered fail threshold committed to git.** This is exactly OIDA's unrun E4, which is generous to them and credible to Davide. If BM25 ties on F1, say the value is proof plus closed-world gaps.
8. **Use the real ELV hook:** Annex IV entry 2(c)(i), the leaded machining-aluminium exemption ending for type-approvals from 1 Jan 2028. It is precise, current and fits a machined bracket. Only use it if the scenario has a leaded free-machining alloy; otherwise use Cr(VI) passivation.
9. **Position against OIDA as "domain model + deduction under your decision registry".** Our blockers export as CONSTRAINT/EVIDENCE nodes with CONTRADICTS edges. Avoid "OIDA has no ontology".
10. **Do not claim** "IOF-based" (we align a few IRIs), "Catena-X model" (no 8D or change standard exists), "REACH ban on Cr(VI)" (pending), or accuracy numbers from synthetic data without the caveat.
