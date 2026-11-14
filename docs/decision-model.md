# The decision model

Written 14 Nov 2026 after 10:30 (workstream D). Source of truth: `core/decision_table.yaml`. Code that reads
it: `core/decision.py`. Tests: `tests/test_decision.py`.

## Why a declared table, not code

The checks in `core/rules.py` say *what is wrong* with a proposed change; the table says *what may be done
about it and who decides*, and it is data a quality manager can read, review and change without touching
Python. Because the table is declared, it can be checked formally (every input enumerated, gaps and overlaps
listed), and every decision record carries a hash of the table and the rules, so a changed row is visible as a
changed `rules_version`.

## Inputs, output, hit policy

- **Input**: the change class of the request (one of the 17 `CHANGE_TYPES`) and the set of rule ids that
  fired at severity blocker, warning or question. Info findings (R4 "a record was replaced", R2 "notify the
  customer" or "a deviation covers this") are shown on the card but decide nothing.
- **Output**: a `DecisionRow`: row id, allowed actions, the role who decides, and what the row rests on.
- **Hit policy: first.** Rows are read top to bottom; the first row whose condition holds is the answer. The
  last row, **R0**, has no condition: no rule covers this change, a person decides.
- **Verdict**: `not_covered` when the row is R0; otherwise `blockers_found` if any blocker,
  `needs_info` if any open question, else `no_blockers_found`. Never "approved".

Class groups: **checked** = SourceChange, MaterialChange, ProcessChange, CoatingChange,
SubTierSupplierChange (the classes `core/rules.py` examines). **source** = SourceChange,
SubTierSupplierChange. **blocking** = R1a, R1b, R2, R5, R6, R8.

## The table

| Row | Change class | Condition on fired rules | Allowed actions | Decider | Rests on | In plain words |
|---|---|---|---|---|---|---|
| D1 | checked | R5 | stop | plant quality manager | R5, Directive 2000/53/EC Annex II, Regulation (EU) 2026/1738 | The new coating or material contains a substance the law restricts in the part's market. No deviation can lift a legal ban. |
| D2 | source | R1a | stop; expedite current approved source; re-audit supplier | supplier quality engineer | R1a, QP-11 4.3 | The new supplier is conditional: no new parts until the open 8D is closed and a re-audit passes. |
| D3 | SourceChange | R6 | expedite current approved source; re-audit supplier | supplier quality engineer | R6, IATF 16949 8.4.2 | The new supplier is not qualified for the material on the drawing. |
| D4 | MaterialChange | R6 | stop; request customer deviation / PPAP resubmission | customer | R6, IATF 16949 8.3.6.1 | The new material falls below a special characteristic of the part. |
| D5 | SourceChange | R1b and R2 | expedite current approved source; request customer deviation / PPAP resubmission | customer | R1b, R2, IATF 16949 8.5.6.1, AIAG PPAP triggers | No part approval for this supplier, part, plant and customer, and the customer requires approval for this change. |
| D6 | checked | R2 and not R1b | request customer deviation / PPAP resubmission | customer | R2, IATF 16949 8.5.6.1, AIAG PPAP triggers | The customer's current requirement needs approval for this change class and no valid deviation covers it. |
| D7 | SourceChange | R1b and not R2 | run internal part approval; expedite current approved source | plant quality manager | R1b, IATF 16949 8.5.6.1 | No internal part approval for this supplier, part and plant; the customer does not ask for one. |
| D8 | source | R8 | request customer deviation / PPAP resubmission; re-audit supplier | supplier quality engineer | R8, QP-14 | A sub-tier supplier changes material, process, coating or source; notice must travel up the chain. |
| D9 | checked | R3 and none of blocking | re-audit supplier; expedite current approved source | supplier quality engineer | R3, QP-11 | No blocker, but the new supplier has an open 8D or NCR on the part's material. |
| D10 | checked | R7 and none of blocking | obtain material certificate | supplier quality engineer | R7, QP-11 | No blocker, but evidence is missing: ask the named owner. |
| D11 | checked | none of R1a, R1b, R2, R3, R5, R6, R7, R8 | proceed under standard change control | plant quality manager | IATF 16949 8.5.6.1 | The checks for this class ran and none fired. Not an approval. |
| **R0** | any | (none) | a person decides | plant quality manager | – | **No rule covers this change: a person decides.** |

Standards are cited by clause number in our own words; their text is not quoted.

## Coverage check

Method: Calvanese et al., *Semantics and Analysis of DMN Decision Tables* (BPM 2016), applied to a first-hit
table over a finite input. Every subset of the 9 rule ids (R1a, R1b, R2, R3, R4, R5, R6, R7, R8) is
enumerated for each of the 17 change classes. Run it with `python -m core.decision`.

**Table checked: 8704 input sets, 6640 go to a person, 1082 overlap.**

| Result | Input sets | What it means |
|---|---|---|
| Go to a person, class not checked | 6144 | 12 change classes (ScheduleChange, PriceChange, PackagingChange, ToolingChange, ...) are examined by no rule: every input for them falls to R0. Before today these read "no blockers found". |
| Go to a person, rule combination not covered | 496 | A checked class with a combination no row names, e.g. SubTierSupplierChange with R1b or R6 fired, ProcessChange with R1a fired. Most of these cannot happen with today's rules; if one ever does, a person decides rather than the table guessing. |
| Overlaps | 1082 | Input sets matched by more than one non-fallback row; row order decides. |

Overlaps by row pair (the first row wins; the second also matches):

| Pair | Input sets | Why the order is right |
|---|---|---|
| D1 over D6 | 320 | A legal ban (stop) outranks asking the customer for approval. |
| D1 over D2, D8 | 256 each | A legal ban outranks supplier status. |
| D2 over D8 | 128 | A conditional supplier stops before the sub-tier notice matters. |
| D1 over D3, D4 | 128 each | A legal ban outranks material capability. |
| D9 over D10 | 10 | Open 8D and a missing certificate together: re-audit first, the certificate request comes with it. |
| others | ≤ 64 each | Same pattern: stop rows before approval rows before notice rows. |

First-match hits per row: D1 1280, D2 256, D3 64, D4 128, D5 16, D6 208, D7 16, D8 56, D9 20, D10 10,
D11 10, R0 6640. (R4 is info only and never enters the table, so it doubles every count.)

## On the real scenarios (fictional company Valsangone)

| Scenario | Change | Rules fired | Row | Verdict |
|---|---|---|---|---|
| main | SourceChange BR-220 SUP-B → SUP-C | R1a, R1b, R2, R3, R6, R7 | D2 | blockers_found |
| main_after_audit | same, after the re-audit | R1b, R2, R3, R6, R7 | D3 | blockers_found |
| elv | CoatingChange CL-115 → yellow chromate | R2, R5 | D1 | blockers_found |
| silence | ScheduleChange BR-220 | (none) | **R0** | **not_covered** |

`silence` is the case the review flagged: no rule fires because no rule looks at schedule changes. It used to
read "no blockers found"; now it reads "no rule covers this, a person decides".

## Decision record

`record(...)` appends one `DecisionRecord` per decision to `data/decisions.jsonl` (append-only, never
rewritten): request, as_of, `rules_version`, facts in force, rules fired, verdict, row, and later the person
who decided. `rules_version` is sha256 over `ontology/*.ttl`, `ontology/RULES.md`,
`core/decision_table.yaml` and `core/rules.py`; files that are not there yet are skipped and listed
(`python -m core.decision --version`). Tests prove: the same input under the same rules gives the same row
and verdict; editing one row changes the answer for the main scenario (D2 → D3) and the two records carry
different `rules_version` values.

## Standard export (DMN)

The table is also published as a standard **OMG DMN 1.3** model (namespace
`https://www.omg.org/spec/DMN/20191111/MODEL/`), so the same rules open in Camunda Modeler, Drools, Trisotech
or any DMN 1.3 tool: they are not locked in this product. Code: `core/dmn.py`. Tests: `tests/test_dmn.py`.

- **Get it**: `python -m core.dmn --out decision.dmn`, or `GET /api/table.dmn` (download) /
  `GET /api/table?format=dmn` (inline); both take `?drop=D2` for the in-memory edit. In the page: Decision
  table → **DMN** tab (rendered with dmn-js 17.12.3, vendored under `web/static/vendor/`, the bpmn.io
  watermark stays visible per its licence) → **Download .dmn**; the matched row is highlighted. Offline, the
  page shows the committed copy `web/static/dmn/decision.dmn` (regenerate it with the command above after a
  table change; a test checks it holds the current rules).
- **Shape**: one decision "Change decision", hit policy FIRST. Inputs: `change_class` (string) and one
  boolean per rule id, `fired_R1a` … `fired_R8` (labels "R1a fired" …). Outputs: `row_id`, `allowed_actions`
  (FEEL list of strings), `decider`, `rests_on` (FEEL list). One DMN rule per table row in table order (rule
  ids `Rule_D1` … `Rule_R0`); the row meaning is the rule's description (the annotations column). Cells are
  FEEL unary tests of four forms only: `-`, `true`, `false`, `"SourceChange","SubTierSupplierChange"`. A text
  annotation on the decision carries the version note and the `rules_version` hash. An `any` condition (unused
  today) is written as one DMN rule per listed rule id, side by side, which is the same table under FIRST.
- **Proof**: the export validates against the OMG DMN 1.3 XSD (`DMN13.xsd` with DMNDI/DC/DI, `xmllint
  --schema`). `tests/test_dmn.py` reads the XML back with its own FEEL reader (independent of
  `core/decision.py`) and evaluates all **8704 input sets** (2^9 rule sets × 17 change classes): equal to
  `core.decision.match` on every one, also for an edited table with an `any` row. The same 8704 sets were run
  through an independent engine, **pyDMNrules 1.4.5**: 8704 compared, 0 differences.
- **Open it in Camunda Modeler** (desktop, free): File → Open File… → `decision.dmn`. The DRD shows the
  decision and the rules-version note; double-click the decision (or the table icon) for the table. To run
  it in a Camunda 7/8 engine, pass the variables `change_class` and `fired_R1a` … `fired_R8` (booleans); the
  result's `row_id` is the row this product would answer with.
