# KVA's own research, and how we build on it

The organisers do research. At the opening call they stressed it, and their track pages ship
reading lists. Their main paper is about exactly our problem, and it ends with a list of things it
did not test. This note maps that list to what we already have and proposes five cheap additions
in their vocabulary. Read on 14 November 2026. Times are estimates, owners are for the team to set.

## 1. What they published

| What | Where | Why it matters to us |
|---|---|---|
| **"Retrieval Is Not Enough: Why Organizational AI Needs Epistemic Infrastructure"**, Bottino, Ferrero, Dosio, Beneventano (arXiv 2604.11759, v1 April 2026, v2 May 2026). Bottino is KVA's founder, Ferrero KVA's head of product; Beneventano is at MIT. It describes their product **OIDA** | [arXiv](https://arxiv.org/abs/2604.11759) | Same thesis as ours: an organisation's knowledge is scattered, and a model reading documents cannot tell what is binding, what was superseded, what contradicts what, and what is unknown |
| **OIDA evaluation corpora**: six BEIR-style corpora (synthetic organisations, investigative cases, office threads), queries built around evolving decisions, contradictions, open questions and topical traps; CC BY 4.0 | [kakashi-ventures/oida-evaluation-corpora](https://github.com/kakashi-ventures/oida-evaluation-corpora) | Their test bed. Corpus B, **FireGlass** (IoT product development: architecture decisions, constraints, technical debt, negative knowledge), is released but **not analysed in the paper** |
| **MAGELLAN**: multi-agent cross-disciplinary discovery built on Claude Code, with cross-model validation of every result | [kakashi-ventures/magellan-cli](https://github.com/kakashi-ventures/magellan-cli) | They value results that an independent second check confirms |

A KVA team member also writes that more papers on an "epistemic system" are coming. This is their
main line of work.

## 2. OIDA in one page (from the paper)

**Knowledge objects have an epistemic type**, each with a prior weight and a temporal behaviour:

| Type | Prior | Temporal behaviour |
|---|---|---|
| DECISION | 1.00 | stable until superseded |
| CONSTRAINT | 0.90 | stable until changed |
| EVIDENCE | 0.80 | slow decay |
| NARRATIVE | 0.70 | stable |
| PLAN | 0.65 | time-bounded decay |
| EVALUATION | 0.55 | moderate decay |
| OBSERVATION | 0.40 | decays unless reinforced |
| HYPOTHESIS | 0.30 | decays if untested |
| QUESTION | 0.30 | urgency grows while unresolved |

**Signed edges**: SUPPORTS +1.0, BASED_ON +0.8, IMPLEMENTS +0.7, SUPERSEDES +0.6, REFINES +0.5,
DERIVES_FROM +0.5, ENABLES +0.4, PRECEDES +0.3, BLOCKS −0.4, CONTRADICTS −0.6. A superseded or
contradicted node is demoted or paired with its contradiction, never deleted.

**QUESTION** is a first-class object: an open information need. The paper says the systems it
surveyed have no such primitive. Urgency of a question:

```
h = clamp( age_days / 30 * 0.3  +  blocking_edges * 0.2  +  stakes * 0.5 , 0, 1 )
```

**Epistemic Quality Score (EQS)**, an LLM-judged diagnostic rubric:
`EQS = 0.20 type fidelity + 0.25 groundedness + 0.20 context coverage + 0.20 contradiction handling + 0.15 decision utility`.

**Their own results** (small pilot, honest): on small corpora that fit in the context window, full
context beats their structured retrieval on EQS (about 0.83 vs 0.55), at roughly 40 times the tokens.
Structured retrieval surfaced a "knowledge gap" section in 10 of 10 runs, full context in 5 of 10.

## 3. What they say is still open, and what we already have

The paper's own next steps and gaps, next to our answer. Numbers only from
`docs/benchmarks/crossbench/REVIEW.md` §4 "Safe to say".

| Open in the OIDA paper | What we have |
|---|---|
| The out-of-window regime, where the system must select what to read | The core reasons over the request's subgraph, not over all documents. Scale numbers exist on Maksim's branch but are **not** on the safe-to-say list: do not use them on stage without Maksim |
| Contradiction-edge precision and extraction audits ("missing one side of a contradiction can produce false consistency"); report node-type accuracy and edge precision | Every fact carries a quote that code verifies against the source. Safe to say: "Extraction: 32 of 35 facts found, 0 of 15 traps taken" |
| A static typed-graph baseline as the decisive comparison | Our core is a typed graph with formal axioms (OWL 2 RL) and constraint checks (SHACL), not heuristic weights |
| Ingestion at scale, ontology design and governance, storage (not described in the paper) | Ontology with closed vocabulary for the extractor, bitemporal append-only fact log, agent-proposed facts that count only after a person accepts them, supersession that demotes and never deletes |

Pitch sentence (one, respectful): *"Your paper leaves out-of-window selection, extraction audits and
the ontology open. We show an answer on one industrial decision."*

Framing: we **complement** OIDA. OIDA tells an agent which decision is in force; we add the plant
model and the rules that show what a change collides with, with a proof.

## 4. Five additions in their vocabulary, cheapest first

### 4.1 OIDA epistemic type on every record (about 30 min)

Annotate our classes with an OIDA type and show it as a badge on the card. Mapping proposal (ours,
to review):

| Our class (`lcc.ttl`) | OIDA type |
|---|---|
| `Law`, `CustomerRequirement`, `InternalProcedure`, `Standard`, `SpecialCharacteristic` | CONSTRAINT |
| `Decision` (meeting), `PartApproval`, `SupplierQualification`, `PPAPRecord`, `Deviation` (time-bounded) | DECISION |
| `EightD`, `NCR`, `MaterialCertificate`, `SupplierCapability` | EVIDENCE |
| `ChangeRequest` (a proposed change parsed from a meeting remark) | PLAN |
| Open question (R7 / `Q_*`) | QUESTION |

Implementation: one annotation property (for example `lcc:epistemicType`) on each class, or a
small mapping dict in the card renderer. No change to the reasoning.

### 4.2 Question urgency with their formula, and BLOCKS edges (30–45 min)

Each open question gets a `blocks` link to the change it holds up, and an urgency computed with the
formula above. `stakes` is our choice, for example 1.0 when a special characteristic or a law is
involved, 0.5 for customer approval, 0.3 otherwise. Sort questions by urgency on the card:
"3.1 certificate from supplier C: blocks the BR-220 source change, urgency 0.62, owner: supplier
quality engineer".

### 4.3 Contradictions shown side by side, not only refused (about 1 h)

Today the fact log refuses a write that contradicts a current record unless it supersedes it. Add a
third path: store the new record as *contested*, add a CONTRADICTS edge (−0.6) to the current one,
keep the current one in force, and open a QUESTION owned by the person who can decide. The card shows
both versions with their sources. In OIDA a person or a model creates contradiction edges by hand;
here a rule finds them (two current values of a functional property).

### 4.4 Formal coverage check of the decision table (about 40 lines)

From the Decision models reading list: Calvanese et al., *Semantics and Analysis of DMN Decision
Tables* (BPM 2016), detects overlapping rules and uncovered inputs. Our table's input is a set of
blocker and question ids, so the input space is small (2^k sets, k about 8, so about 256).
Enumerate every set, find the first matching row, and report:

- sets that fall through to the fallback row R0 ("no rule covers this, a person decides"): the
  uncovered cases, listed explicitly;
- sets that match more than one non-fallback row: overlaps, resolved by row order, listed so the
  order is a visible choice.

Print the result on the card as "table checked: N input sets, M go to a person". This turns "no rule
applies" into a proved outcome and speaks to Fit with the track (25%).

### 4.5 "A document changed: what is affected" (about 1 h)

When a document is superseded (for example `CSR-AUR-R3` by `CSR-AUR-R4`), list every rule row,
fact and recorded decision whose source quote points at the old revision, and mark them "review:
source superseded". This is their core interest (ingesting many documents and keeping them usable)
and the closest challenge question of the ontology track ("show what happens to the ontology when one
document changes"). The supersession chain already exists; this is a report over it.

### Stretch, or "next step" on a slide

- Score our benchmark answers with EQS, next to the full-context baseline.
- Run our quote-verified extraction on their **FireGlass** corpus, which their paper did not analyse.

## 5. What not to say

From the team brief, still right:

- "We bypass long context": their paper reports full context winning on small corpora, and says so
  openly.
- "OIDA has no ontology": they sell an organisational ontology.
- "The AI resolves conflicts": in OIDA and in our system a named person decides.
- Any number outside `docs/benchmarks/crossbench/REVIEW.md` §4 "Safe to say".
