# Change check — economic model

Saved in Control8 on 14 Nov 2026 (model `em_b5119b76_c90`). Every number comes from `v4/model.py`
(standard-library Python; each assumption has a value, a unit, a marker and a source).
Markers: **[verified: source]** · **[declared]** team estimate · **[unverified]** not yet checked.

## Headline (year 1, billed)

| | |
|---|---|
| What we sell | A plant licence: every change request is checked against the plant's own memory before the decision |
| Price | Licence EUR 24,000 per plant per year; paid 8-week pilot EUR 9,500, fully credited to the licence [declared] |
| Year 1 | 3 paid pilots + 1 plant licence = **EUR 43,000** |
| Acquisition | Outbound to supplier-quality directors: 16 meetings a year, 8% to licence → 1 new licence a year; **CAC EUR 15,880**; **payback 7.9 months** |
| Gross margin | **70%** on shared EU hosting (54% on a dedicated instance) |
| Funding | Seed round of about **EUR 230,000** to reach 5–6 licensed plants (ARR about EUR 137,000) by year 3 |

## The problem and its cost

| Fact | Source |
|---|---|
| Failed change management caused 83% of significant supplier quality issues, FY22–FY24 | [verified: Astemo Supplier Change Management Guidebook rev 4.0, Dec 2025] |
| An unapproved change brings New Business Hold, notice to the IATF registrar and possible financial consequences; approval is required at least 180 days ahead | [verified: Adient Global Supplier Standards Manual rev 10.0, 2023] |
| Quality engineers describe supplier and sub-supplier changes reaching them late or not at all | [verified: 10 independent forum threads, team research] |
| A tier-3 supplier changed its moulding process and the tier-2 was not told | [verified: NHTSA recall 18V-806] |
| One escaped unapproved change costs about EUR 29,400 (sorting, expedite, engineering hours, chargeback) | [unverified estimate] |

Catching **0.8** such changes per plant per year pays the licence.

## Market

| Layer | Count | Source |
|---|---|---|
| IATF 16949 sites worldwide | 93,713 | [verified: VDA QMC, Apr 2026] |
| IATF 16949 sites in Italy | 1,589 | [verified: VDA QMC, Apr 2026] |
| Serviceable Italian plants (35%: OEM change burden × budget and data ready) | 556 | [unverified] |

Comparable quality software per year: mid-sized company USD 25,000–100,000 [verified: Monetizely, Aug 2025];
medians Arena USD 55,970 (31 purchases), Greenlight Guru USD 43,989, MasterControl USD 115,673 [verified: Vendr].
Our EUR 24,000 (about USD 27,000) sits at the low end of that band.

## Unit economics per plant per year (shared EU hosting)

| Line | EUR | Marker |
|---|---|---|
| Licence revenue | 24,000 | [declared] |
| Support and ontology upkeep (8 h a month at EUR 70) | 6,720 | [declared] |
| Hosting | 480 | [declared] |
| Model calls (USD 0.0007 per change request, Claude Haiku 5.5) | ~17 | [verified: our measurement] |
| **Cost to serve** | **7,217** | |
| **Gross margin** | **70%** | |

Delivery options: shared EU SaaS (base), dedicated instance (54% margin), on-premise with a local open-weight
model for plants whose data must not leave the site (supported by the product; cost not yet measured).

## Acquisition

| | |
|---|---|
| Channel | Outbound to supplier-quality directors of Italian IATF tier-1/2 plants; founders sell |
| Cost per meeting | EUR 992.50 (outreach, meeting time, share of pilot management) [declared] |
| Funnel | 16 meetings → 3 pilots (18.75%) → 1 licence a year (8%) [unverified] |
| CAC / payback | EUR 15,880 / 7.9 months (Control8) |
| Churn / lifetime value | 20% a year [unverified]; LTV capped at 5 years EUR 56,400; LTV/CAC 4.5× |
| Next channel | Partners: IATF consultancies and ANFIA |

## Three years

| | Low | Base | High |
|---|---|---|---|
| Licensed plants, end of year 3 | 0.9 | 5.7 | 16.9 |
| ARR, end of year 3 | EUR 22,600 | EUR 137,500 | EUR 508,000 |
| Cumulative result, 3 years | EUR −308,000 | EUR −227,800 | EUR +316,000 |
| Funding need | EUR 308,000 | **EUR 228,000** | EUR 48,000 |

Team: three founders on a EUR 2,000 monthly stipend until a seed round, plus EUR 12,000 a year of tools
[declared]. Low sets every range input to its bear value at once (a stress case); High to its bull value.

## What the paid pilot tests

The price and the funnel are team estimates. The pilot replays one plant's last year of change requests through
the product, which measures how many blockers would have been caught and so whether EUR 24,000 a year is worth it.

Full calculation: `v4/model.py`, output in `v4/model_output.md`. Problem sources: `evidence/`.
