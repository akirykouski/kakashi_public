# Demo script: presenter mode (3 minutes)

The live slot is 5:00: about 3:00 of demo, then questions. The page drives itself: one key per beat, a caption
bar at the bottom says the line to speak. Every screen is the real page answering from the real routes; nothing
is a screenshot.

## Start

```sh
python -m web.snapshot          # after the last merge: re-record the offline replay
REMARKS_PER_IP_PER_10_MIN=1000 python -m web.server --port 8000
```

Open http://localhost:8000/?demo=1 at 1440×900 (or click **▶ Demo** in the top bar). Offline replay:
http://localhost:8000/?offline=1&demo=1. If the server is unreachable or a route errors, the page switches to
offline replay by itself and the demo continues.

The public deployment caps meeting lines and remarks at 30 per IP per 10 minutes. Each forward run sends about
6 of them, and going back over the meeting replays them. Rehearse on the local server with the higher cap. When
the cap is hit, the page falls back to offline replay on its own.

Keys: **→** or **Space** = next, **←** = back, **Esc** = exit. Each beat re-applies its whole state (meeting
replayed to the right line, document review reset and redone), so going back is always safe. Step 0 resets the
document review to the original company memory and resets the meeting.

## Steps

| # | Beats (→) | The page does | Say (caption) | Time |
|---|---|---|---|---|
| 0 | 1 | Title card over the live page. Resets the documents and the meeting | "A supplier-quality meeting. The decision is about to be taken." | 0:00 |
| 1 | 1 | Meeting view: lines 1–4 play (about 2 s). Line 4 (Giulia Ferri, "Bormida is two weeks late… take the BR-220 blanks from Chisone, same alloy") turns red and its card appears | "One sentence in a meeting — the model only turns it into a typed change request." | 0:10 |
| 2 | 2 | Full card of the same request (scenario `main`, 5 Nov). Beat 1 opens R6's proof: same alloy, wrong temper, T5 vs T6, 230 < 250 MPa. Beat 2 opens R2's chain part → programme → customer → CSR-AUR-R4, quotes and the customer's consequence (chargeback) | "Every step is a fact with a verbatim quote; the chain is inferred over the ontology." | 0:25 |
| 3 | 1 | Decision panel: row D2, allowed actions, who decides | "A declared decision table decides what may be done and who decides. It never approves." | 0:45 |
| 4 | 1 | Past decisions: DEC-031, rejected 2 Oct; each reason re-checked today: still holds | "The company already decided this once — and why still holds." | 0:55 |
| 5 | 2 | Beat 1: meeting lines 5–8. "We re-audited Chisone last week" re-checks the card as of 14 Nov: R1a no longer fires, blockers 4 → 3. Beat 2: full card after the re-audit: R4 "QS-C-2026 supersedes QS-C-2025 (was: conditional). This does not approve any part", QS-C-2025 struck through with its author and dates | "New facts replace old ones by date and authority; history stays." | 1:05 |
| 6 | 4 | Documents: the Aurelia deviation email DEV-AUR-26-044 with highlighted quotes → reject the wrong proposal ("Chisone needs written customer approval for source changes") → accept the other four → re-check: R2 is now "Covered by valid deviation DEV-AUR-26-044 (until 2026-12-31)" | "Documents become facts only after a person accepts them." | 1:25 |
| 7 | 1 | Rule-change compare: the coating question as of 15 Jun (CSR-AUR-R3: notify) vs 14 Nov (R4: approval), both decision records side by side | "Same question, different rules in force, different answer — and the record says which." | 1:55 |
| 8 | 1 | Meeting lines 9–12. Line 12 ("move the BR-220 final inspection to the new CMM") gets a grey card: row R0, a person decides | "No rule covers it: a person decides, not the model." | 2:10 |
| 9 | 3 | "Table checked: 8704 input sets" → whole decision table, row D2 highlighted → DMN tab, **Download .dmn** highlighted | "The rules are a standard DMN table — open them in any DMN engine." | 2:25 |
| 10 | 2 | "What would clear this" opened under the first blocker → **Explain this decision**, auditor view (rules_version, row, fact ids) | "Each decision is reproducible and explainable." | 2:40 |
| 11 | 1 | Closing card: 0.90 recall of inferred blockers vs 0.19 for retrieval (pre-registered, synthetic data); change-check.onrender.com · github.com/akirykouski/kakashi_public | "Inferred blockers: 0.90 recall vs 0.19 for retrieval. The model reads; the company's rules decide." | 2:55 |

23 beats in all. Without the model: the meeting lines, the remarks and the document extraction come from recorded
fixtures and the snapshot, so the demo makes no model calls.

## Code

`web/static/demo.js` and `web/static/demo.css`. They call the same functions as the buttons: `runCheck`,
`runRuleChange` and `showTable` (app.js), `Meeting.ready/reset/step/position` (meeting.js), and
`Docs.reset/loadDemo/review/reviewMany/recheck` (documents.js). To change a caption or a step, edit `STEPS` in
demo.js.
