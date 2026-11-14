# Build plan, 14 Nov 2026

Draft, 10:20. Times are Rome time. Owners for Arseniy and Valentina are proposals until they confirm.

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Track | **Decision models** (locks at 12:15) |
| 2 | Input | **A remark in a meeting** → parsed into a change request → checked. A typed form is the fallback |
| 3 | Which fictional company | **Open.** Proposal: Valsangone (core M's world). It has fictional customers (no Stellantis), 27 documents plus long documents with traps, and 54 meeting snippets that fit decision 2. Keep A's 20 requests as a second, separate eval world; never pool the facts |
| 4 | Core | Core M as the base, with the A ideas listed in `docs/benchmarks/crossbench/REVIEW.md` §3 ported in |
| 5 | Repo | `kakashi_public` (public) holds the code from 10:30, plus research, benchmarks and decisions. `torino_kakashi` stays private |

Register `kakashi_public` with `set_team_repo` before 16:45.

## Gaps from Valentina's review (track fit)

1. The decision model is not a model: checks are Python functions; the table "blockers → allowed actions → who decides" exists only on paper.
2. No decision record: which rule version, which facts were in force, which rule fired.
3. No explicit "no rule covers this → to a person" outcome (row R0). Today "no blockers found" mixes "rules checked, none fired" with "rules do not cover this".
4. The meeting story was dropped: input is a change request while the pitch is about meetings (closed by decision 2).
5. Stellantis in A's data is a risk with a Turin jury (closed if decision 3 = Valsangone).

| Track requires | Where we are |
|---|---|
| One real decision, rules from a regulation or procedure | ✓ (interviews close "the team made up the rules") |
| An agent fills the model's inputs from unstructured text | ✗ parser missing |
| The decision names the rule that produced it | ✓ rule id + chain with quotes |
| Same input same answer; a changed rule changes the answer; the record shows the rule version | ½ |
| Uncovered cases go to a person | ½ |
| The decision model is declared explicitly | ½ |

## Schedule

| Time | Maksim (core) | Arseniy | Valentina |
|---|---|---|---|
| 10:30–10:45 | Core into `kakashi_public` in one commit "prepared inputs (before 10:30)", disclosed in the README; one shared environment | Server and page skeleton | Track on the portal; interviews |
| 10:45–11:30 | Change-class taxonomy; customer approval and certificate keyed on class, not on a new supplier; R0 outcome "no rule covers this" | Card: blockers, chain with quotes, replaced facts in red | Interviews; 10 hold-out requests |
| 11:30–12:15 | Decision table as data → allowed actions and decider; decision record (rules hash, facts in force, rules fired, answer, decider) | Show the table row and the decision record | Abstract, video script |
| 12:15–12:30 | Technical lines for the abstract and the video | Video | Upload video and abstract |
| 12:30–13:30 | Vote, lunch | | |
| 13:30–14:15 | A's snapshot resolver (document rank, no lower-rank supersede); close the write-path gap | First `pitch` artifact by 14:00 | Re-gold disputed items; policy calls (8D level, "supplier qualification unknown") |
| 14:15–15:00 | Parser: meeting remark → change request (Haiku via the team key), names → ids | Demo "the rule changed → a different answer" | Economic model |
| **— cut line: above this is the demo —** | | | |
| 15:00–15:45 | Completeness scoped by list; 8D at alloy-series level (if Valentina says yes) | Fallbacks, recorded run | Pitch |
| 15:45–16:00 | Run on the frozen set: requests parsed by hand and by the model | | |
| 16:00 | **Feature freeze**: only the demo path from here | | |
| 16:30 | Financial validation | | |
| 16:45 | Pitch delivery deadline (`pitch` artifact, repo link, models and AI tools used) | | |

## Fixed rules for the day

- No product code written before 10:30. Organisers confirmed the pre-event core and dataset may be used; say so in the README and on stage.
- Numbers on stage only from `docs/benchmarks/crossbench/REVIEW.md` §4 "Safe to say". Never "100%", never "reasons better than an LLM", no ranking of the two cores.
- Standards by clause number and in our own words (IATF 16949 8.5.6.1 and 8.3.6.1, AIAG PPAP triggers); the standard text is paid and we do not quote it. ELV: Directive 2000/53/EC, replaced by Regulation (EU) 2026/1738, which applies from 1 Sep 2028.
- The team key (`AI_GATEWAY_API_KEY`) is for the product only, in `.env`, never committed.
