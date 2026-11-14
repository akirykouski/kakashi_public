# Review B: go-to-market and market (14 Nov, 15:45)

Verdict: the arithmetic is clean. The weak point is the buyer: price, pilot and funnel assume a well-funded tier-1 site, but most of the 1,589 Italian IATF sites are SMEs feeding a shrinking Stellantis Italy volume.

## 1. Unit and packaging
- Per-plant pricing fits a tier-1 group (IATF certificate and audits are per site); it is wrong for a single-site tier-2 with 50-200 staff, where the "supplier-quality director" is one quality manager and EUR 30k is close to a junior quality engineer's salary. Group buyers will ask for a group price; SMEs will not sign at 30k.
- A EUR 20k pilot with no references is the hardest sale in the model.
- Better packaging: paid pilot **EUR 9,500, 8 weeks, credited 100% against the first-year licence**. Licence in two tiers: **Site EUR 18k** (one OEM customer, up to 40 changes a month) and **Site Plus EUR 30k**. For groups: the second and later plants at **-30%**.

## 2. Market sizing
- 1,589 Italian IATF sites [verified, VDA QMC] is fine. The 70% x 50% shares are guesses applied twice.
- **Double counting / population mix:** Piedmont 257 = ANFIA 734 x 35%. ANFIA's count covers design, engineering and service firms that hold no IATF certificate, so it is not a subset of 1,589. Saying "Piedmont 257 of 556 Italian SAM" (46%) mixes two populations. Use Piedmont IATF sites from the same database, or relabel 257 as a non-IATF upper bound.
- Juror questions: Stellantis Italy output fell sharply (~0.5M vehicles 2024 [unverified]), so quality budgets are being cut; and why not do this inside the PLM/QMS change workflow?
- Anchors (all [unverified] today): CAQ suites (Babtec, CAQ AG, iqs) and Plex/ETQ/Teamcenter/ENOVIA change modules sell per user or inside large licences. CoLab proves engineers pay for review tooling, not per-site. Taktile/Camunda/InRule/Rainbird back the category, not this price. The only price signal in the files (Elsmar: "USD 35k/yr unjustified") counts against the price.

## 3. Acquisition
- 8% from cold contact to meeting with quality directors is 3-5x typical cold outbound (1-3% [unverified benchmark]).
- Warm channels, ranked: (1) **IATF consultancies and trainers** (certification bodies cannot recommend tools: impartiality rules); (2) **ANFIA and the CEIPiemonte "From Concept to Car" supplier programme** [unverified name/current status]; (3) a tier-1 asking its own sub-suppliers to use the check (one sale opens 10 plants).
- Sales cycle: a pilot takes 3-6 months to decide, plus 3 months to run, plus procurement. A licence signed in year 1 means a pilot signed by about month 4. Four paid pilots in year 1 from 3 part-time founders with no reference customer is optimistic. **The High case shows a profit in year 1 (+EUR 179k, 10.8 pilots)**: not credible.
- Consistency flags: Control8 shows EUR 110k (licence billed up front) while the model shows EUR 95k; the "new customers/yr" read-back gives 2, but the model books 1. The rubric requires the pitch to show the same price and volume as Control8, so pick one figure and put it on the slide.

## 4. The number the case rests on
The licence price willingness to pay (EUR 30k, and the 20k pilot) [declared]. Conversion cannot be verified today; price can. **Fastest route before 16:30:** in a mentor call or an ANFIA/KVA industry contact, ask one quality manager at a supplier: "Would you pay EUR X for an 8-week replay of last year's change requests, credited to a EUR Y licence?" Record name, role, time and the number they give, then mark it [verified: name, role, 14 Nov]. Also: 20 LinkedIn messages to Piedmont quality managers now; reply count at 16:30 = first CPL datapoint.

## 5. Top 5 changes (ranked)
1. **Pilot price:** `price_pilot` 20,000 -> **9,500, credited against the licence**. Text: "Paid 8-week replay, EUR 9,500, fully credited to year-1 licence."
2. **Licence base:** `price_licence` 30,000 -> **24,000** (it is already the "defended floor"), High 30,000 (not 36k, which exceeds the USD 35k a forum rejected). Add a group discount of -30% from the second plant.
3. **Year-1 volume:** pilots 4 -> **3**, licences billed in year 1 **1** (one figure in both Control8 and the deck). Control8 revenue = 24,000 + 3 x 9,500 = **EUR 52,500**. Small but defensible.
4. **Second channel in Control8:** `partner_consultancy` (IATF consultants + ANFIA), CPL **EUR 400** [declared], conversion **20%**, 10 leads per year, with a 15% revenue share costed in. Outbound conversion 12.5% -> **8%**.
5. **Market text:** replace "Piedmont beachhead 257" with "Piedmont: 734 ANFIA supply-chain firms (not all IATF); beachhead = first 30 IATF tier-2s reachable through partners". Cap the High case at year-1 pilots <= 5 and delete the year-1 profit.
