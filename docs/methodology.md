# Methodology: how we evaluate the change-check core

Written 14 Nov 2026, before the merged core is run. The commit time of this file is our pre-registration: hypotheses, thresholds, data and metrics below were fixed before any result on the merged core existed. Any change after the first run is logged in `docs/benchmarks/CHANGES.md` with the reason and the time.

## 1. Question and hypotheses

**Question.** Does a deductive check over an ontology and rules, running on facts that each carry a verbatim source quote, give more reliable change-review decisions than a language model reading the same documents?

| | Hypothesis | Pass if |
|---|---|---|
| H1 | On blockers that need two or more documents combined (inferred blockers), the core has higher recall than retrieval-augmented generation | Recall on inferred findings, C > A' by at least 20 points |
| H2 | On replaced rules and on missing data, the core makes fewer errors than a model reading all documents | Exact match on the `stale` and `missing` categories, C > B |
| H3 | As the company grows, the core's accuracy holds while full context degrades | Exact match at 8× company size: C drops ≤ 3 points, B drops more than C |
| H4 | Overall, the core is not worse than a model reading all documents | Exact match, C ≥ B − 5 points |

H4 replaces the earlier threshold "+20 points over full context", which was pre-registered on 13 Nov and **failed** (+5). We report that failure as it is (`benchmarks/core/PREREGISTRATION.md`, `benchmarks/core/CONCLUSIONS.md`).

## 2. Data

| Set | Size | Author | Role |
|---|---|---|---|
| World M (Valsangone, fictional tier-1 supplier) | 36 requests, 81 gold findings | Maksim | Main set |
| World A (fictional plant, customer renamed from a real OEM) | 20 requests | Arseniy | Second, independent world |
| Hold-out | 10 requests, 5 per world | Valentina | Written after the freeze, seen by neither core author. The only number about generalisation |
| Real documents | 4 public documents (supplier manuals, a change letter, a recall report) | — | Extraction check on real text, reported separately |

Rules:
- The two worlds are run separately. Facts are never pooled: the same ids (e.g. 8D-25-031, BR-220) mean different things in each.
- Disputed gold items (`benchmarks/crossbench/REVIEW.md` §4) are re-golded by the non-author, with Valentina arbitrating; each change is logged with a reason.
- After re-golding, the gold files are frozen and their SHA-256 hashes are written to `docs/benchmarks/FROZEN.md` before the first run.
- All data is synthetic except the 4 real documents. Standards are cited by clause number and paraphrased.

## 3. Conditions

| Id | Condition | What it tests |
|---|---|---|
| A | BM25 top-8 chunks → model | Plain retrieval-augmented generation |
| A' | Hybrid retrieval (BM25 + dense embeddings) top-8 → model | A fair RAG baseline, not a weak one |
| B | All documents dated on or before the request → model | Upper bound for a model reading everything |
| C | Model parses the request → core decides | Our system |
| C* | Hand-written parse → core decides | Upper bound of the core; C* − C is the parser loss |

Same model, same prompt and the same output schema for every model condition (A, A', B and the parser in C). The rule catalogue is given to the model conditions in plain words. Model id and settings are recorded per run.

## 4. Ablations (if time allows)

Run C* with one component switched off at a time:
1. No ontology inference: direct facts only, no property chains, inverse or transitive properties.
2. No supersession: every fact ever recorded stays in force.
3. No question outcome: missing evidence is read as "no blocker".

Each ablation shows which component produces which gain.

## 5. Metrics

Computed by code; no LLM judge.
- Precision and recall of findings, micro-averaged; a finding matches on rule id and key.
- Recall on inferred findings (blockers derived through two or more documents).
- Exact match (all findings right, nothing extra), per category: direct, inferred, stale, missing, clean.
- Three-way verdict accuracy: blockers found / no blockers found / needs information (plus "not covered by rules" once the core has it).
- False-alarm rate on clean requests.
- Citations of superseded or informal sources as authority (`must_not_cite`).
- Tokens in and out, and seconds per request.

Statistics: 95% Wilson intervals on every rate; paired comparison on the same requests with McNemar's test. With about 56 requests, differences under roughly 10 points are treated as noise and reported as such.

## 6. Threats to validity

- Data is synthetic, written by the team.
- The gold and the rules were written by the authors of the cores. The hold-out set is the only partial answer to this.
- Small sets: one finding moves a category score by several points.
- Only 4 real documents; real-document results are a spot check, single auditor.
- In the cross-benchmark, the third-party encoders saw some gold.
- One model family is used for every model condition and for the parser.
- The full-context baseline benefits from small companies; H3 tests this directly but only on synthetic scale-up.

## 7. What we may say on stage

Only numbers produced under this protocol, with their n and interval, and the threats above stated when asked. Never "100%" (own gold), never "reasons better than an LLM" unless H4 and H1 both pass, no ranking of the two prepared cores.
