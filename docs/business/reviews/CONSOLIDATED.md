# v3 decision list (reviews A + B consolidated)

## 1. Agreed: apply as-is
- One year-1 figure in Control8, note and pitch (v2 shows 110k vs 95k).
- Channel read-back must equal licences billed (v2: 2 vs 1).
- Licence base EUR 24k; 30k is upside only; drop 36k.
- Four EUR 20k pilots in year 1 with no reference: not credible.
- Price is the number to verify today; almost everything else is [declared].
- Confirm vocabulary with `get_economic_model` before saving.

## 2. Conflicts: decision
- **Pilot 20k/10k (A) vs 9.5k credited (B):** 9,500 credited. Lowest barrier without a reference.
- **Year-1 revenue 110k / 95k / 52.5k:** **EUR 43,000 billed.** B's 52.5k ignores its own credit: 3 x 9,500 + (24,000 - 9,500) = 43,000.
- **Pilots 4 (v2), 2 (A), 3 (B):** 3 = 16 meetings x 18.75%.
- **Churn/support base vs bear:** bear as base (20%, 8 h). B silent; survives attack.
- **Hosting dedicated (A) vs shared:** shared stays base; dedicated and on-prem/local model shown as options. No measured on-prem cost.
- **Founders' pay:** 3 FTE x EUR 5k (A). 1.5 FTE looks naive.
- **Partner channel (B):** not in Control8. No partner exists; CPL 400 / 20% would be invented. Name it in the pitch as next step.
- **Outbound conversion 12.5% vs 8%:** 8%. 16 x 8% = 1.28, about 1 licence billed; fixes the read-back.
- **Site/Site Plus tiers, group -30%:** one price now; group discount as note text only.

## 3. v3 parameters
| Name | v2 | v3 | Marker | Reason |
|---|---|---|---|---|
| price_licence | 30,000 | 24,000 (high 30,000) | [declared] | defended floor, A+B |
| price_pilot | 20,000 | 9,500, credited to licence | [declared] | B |
| pilots_y1 | 4 | 3 | [declared] | B |
| licences_billed_y1 | 1 | 1 | [declared] | both |
| revenue_y1_billed | 110,000 | 43,000 | computed | credit netted |
| meeting_to_pilot | 25% | 18.75% | [unverified] | 3 of 16 |
| lead_to_licence | 12.5% | 8% | [unverified] | B |
| CPL | 1,167.50 | 992.50 (187.50 + 280 + 0.1875 x 2,800) | [declared] | follows pilots |
| CAC | 9,340 | 12,406 | computed | 992.50 / 8% |
| support h/month | 4 | 8 | [declared] | A |
| cost to serve, shared | 3,857 | 7,217 | [declared]; LLM part [verified] | 6,720 + 480 + 17 |
| gross margin | 87% | 70% (dedicated 54%) | computed | at 24k |
| on-prem, local model | none | cost null | [unverified] | new fact, not measured |
| churn | 10% | 20%, LTV capped 5 years | [unverified] | A |
| LTV / CAC | 28x | about 4.5x (56.4k / 12.4k) | computed | |
| payback | 4.3 mo | 8.9 mo gross profit; 6.2 revenue; plus 6-month sales cycle | computed | |
| team_fte_y1 | 1.5 | 3 | [declared] | A |
| funding need | 43k | rerun model.py; expect about 150k+ | computed | never quote 43k |

model.py output overrides the hand-computed rows.

## 4. Control8 payload
- `plant_licence`: priceCents 2400000, volume 1.
- `paid_pilot`: priceCents 950000, **volume 2**, label "Paid 8-week replay, EUR 9,500, fully credited to year-1 licence (third pilot is inside the licence line)".
- Headline: 24,000 + 19,000 = **EUR 43,000** = pitch.
- Channel: cplCents 99250, conversionPct 8, leadsPerPeriod 16; label adds "(incl. pilot management share)".
- Note, in this order:
  1. Verified: 1,589 IATF sites; LLM cost; benchmark.
  2. Horizon: year 1, billed: 3 pilots (one credited) + 1 licence = EUR 43,000.
  3. 16 x 8% = 1.28 licence decisions, 1 billed in year 1.
  4. Margin 70% shared, 54% dedicated; on-prem with local open-weight model (OpenAI-compatible endpoint, quotes verified by code): cost [unverified].
  5. Payback both bases; funding need with 3 founders.
  6. Delete: 87%, 28x, 43k, "Piedmont 257".

## 5. Do not claim; verify
Do not claim: "validated"; 87% / 28x / 4.3 months / EUR 43k funding; a year-1 profit; Piedmont 257 of 556; any local-model cost, or that benchmark recall holds on a local model; TISAX readiness; the partner channel as existing.

**Verify before 16:30: licence price.** Ask one supplier quality manager (mentor call): "Would you pay EUR 9,500 for an 8-week replay, credited to a EUR 24,000 licence?" Record name, role, time, answer; mark `[verified: name, role, 14 Nov]`.
