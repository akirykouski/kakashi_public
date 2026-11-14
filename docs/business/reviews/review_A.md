# Review A: economic model v2 (skeptical juror view)

## 1. Arithmetic (recomputed from payload + model.py)
- Annual revenue (Control8 = sum of price x volume): 30,000 x 1 + 20,000 x 4 = **EUR 110,000**. Correct.
- CPL: 15/0.08 + 4h x 70 + (0.25 pilots/meeting x 40h x 70) = 187.5 + 280 + 700 = **1,167.50**. Correct.
- CAC: 1,167.50 / 0.125 = **9,340** (= 100x15 + 8x4x70 + 2x40x70). Correct.
- Gross margin: (30,000 - 3,857) / 30,000 = **87.1%**. Payback on GP: 9,340 / 2,178.6 = **4.3 mo**; on revenue 3.7 mo. LTV 26,143/0.10 = **261k**, 28.0x; fully loaded 261k/18,667 = 14.0x. All correct.
- **MISMATCH 1:** model_output Base year 1 revenue = **EUR 95,000**; payload/note say **EUR 110,000**. Funding need (43k) and "break-even year 2" come from the 95k run. The jury compares headline vs table: pick one (fix model to bill licence upfront, or set note to 95k and explain).
- **MISMATCH 2:** channel says 16 leads x 12.5% = **2 licence customers** in year 1; revenue line bills **1 licence**. Control8 will show 2 customers vs 1 unit. Explain in note ("half of year-1 pilots sign in year 2") or set conversionPct so leads x conv = 1 (6.25%) — better: keep 12.5% and add the lag sentence.
- MISMATCH 3: Base year-1 gross margin is 76% (pilot delivery), headline says 87%. Say "87% steady-state licence margin; 76% blended year 1".

## 2. Control8 compliance
- Integer cents, one currency, volume = units billed in year, horizon in note, markers present: OK.
- Vocabulary (`licence_year`, `project_fee`, `outbound`, `year`) is **unconfirmed** (MODEL.md admits it). Call `get_economic_model` and check before 16:45; an invalid_input at 16:40 is fatal.
- cplCents bundles downstream pilot-management time into "cost per lead": defensible but the label says "lead = meeting held". Add "(incl. pilot mgmt share)" to the label so a juror does not call 1,167 per meeting absurd.
- Payback Control8 shows is probably revenue-based (3.7 mo); pitch says 4.3. State both or the card contradicts the slide.
- Note is ~2,500 chars of dense text; the jury will not read it. Put the 3 verified facts first.

## 3. Assumptions that will be attacked
| Assumption | Jury question | Stronger framing |
|---|---|---|
| Price EUR 30k | "A forum said 35k USD is unjustified; who pays 30k?" | Lead with EUR 24k (your own defended floor) as base; 30k as upside after pilot. |
| 25% meeting to paid pilot, EUR 20k, cold | "Automotive procurement cycle is 6-12 months; 4 paid pilots in year 1?" | Base 2 pilots year 1 (bear case 0.20 already exists); or 4 pilots at EUR 10k. Add sales cycle 6 mo to payback. |
| Churn 10% | "Startup with no reference customer, 10%?" | 20% (= your bear), LTV capped at 5 years; LTV/CAC 14x, still strong. |
| Support 4 h/plant/month | "Ontology upkeep for a whole plant in half a day a month?" | 8 h (your bear) -> EUR 6,720, margin 76%. Still passes. |
| Shared SaaS hosting | "Tier-1s demand TISAX / dedicated or on-prem." | Base = dedicated (EUR 4,200, margin 75% per note); TISAX cost as fixed line. |
| Escaped change EUR 29,400 [unverified] | "Source?" | Say it is a build-up (5,000 pcs x 1.2 sort + 5k expedite + 120 h + 10k debit) and that 1 catch/yr pays the licence; ask the jury's automotive mentor for one real sorting invoice. |
| Team 1.5 FTE x EUR 5k | "Three founders at 90k total?" | 3 FTE x 5k = 180k y1 -> funding need ~EUR 130k, not 43k. Say it. |

## 4. Checklist pitfalls (wshobson / lyndonkl)
- LTV:CAC 28x and 4-month payback are "too good" signals: lyndonkl flags >5x as suspect assumptions.
- LTV undiscounted, churn guessed: both on the checklist.
- No sales-cycle lag in payback; CAC excludes founder time not costed in team line.
- Revenue years 1-2 mostly one-off pilots, presented next to ARR: label clearly.
- Almost every driver is [declared]/[unverified]; rubric: [declared] supports a 4, not a 7. Only verified items: IATF site counts, LLM cost, benchmark.

## 5. Top 5 changes (ranked)
1. **Reconcile year-1 revenue**: either rerun model with licence billed upfront to get 110,000, or change note to "EUR 95,000 recognised / 110,000 billed (licence invoiced upfront)". One number everywhere, same as pitch artifact.
2. **Note line added**: "16 meetings x 12.5% = 2 licence decisions; 1 billed in year 1, 1 in year 2 (pilot lag 3 mo)."
3. **Fund the real team**: team_fte_y1 = 3 -> state "funding need base EUR ~130k (year-1 loss with 3 paid founders)". A 43k ask with 1.5 FTE looks naive.
4. **Use bear values as base for support (8 h) and churn (20%)**: headline becomes GM 76%, payback ~4.9 mo on GP, LTV/CAC ~12x. Still a 7-grade story, far harder to break.
5. **Get one [verified] buyer number before 16:45**: a quote or LOI-level price reaction from one supplier-quality person (mentor call) or a public price page of a comparable change/APQP tool. Mark it `[verified: name/role, date]`. This is what moves 4 -> 7.
