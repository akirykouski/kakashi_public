#!/usr/bin/env python3
"""v4 (14 Nov 2026, 16:00): founders on EUR 2k/month stipend [declared]; price sits inside verified market band (Vendr, Monetizely); problem evidence (Astemo 83%, Adient consequences, sorting $30-50/h). Base v3 unchanged otherwise.
v3 (14 Nov 2026, 15:50): CONSOLIDATED.md applied (reviews A+B): licence 24k, pilot 9.5k credited, 3 pilots + 1 licence
billed in year 1 (EUR 43,000), conversion 8%, bear support/churn as base, LTV capped 5 years, 3 paid founders,
billed-basis revenue, High year-1 pilots capped at 5, Piedmont out of SAM, on-prem/local-model option (cost null).
v2 (14 Nov 2026, 15:40): measured Haiku LLM cost, two delivery options, markers, KVA checks.
Business model for the 16:30 financial validation (KVA hackathon, 14 Nov 2026).

Stdlib only. Run:  python3 docs/business/model.py
Writes docs/business/model_output.md and prints the same markdown to stdout.

CONVENTIONS
- Every input lives in ASSUMPTIONS as {value, unit, source, confidence}.
  Range inputs also carry "bear" and "bull": the value that is WORSE / BETTER for the business
  (so a cost has bear > value, a price has bear < value; for the escaped-change cost inputs, bear is the
  CHEAPER event, because a cheaper event is the weaker case for us). Scenarios map: Low = bear, Base = value, High = bull.
- source is a file path / URL, or "assumption: <reasoning>".
- confidence: V = verified in a primary source we read, P = portal or secondary material (can change),
  E = our estimate (brief 01 estimate or ours), U = unverified guess. Nothing marked V is a forecast.
- Money in EUR unless the unit says USD. No number here is a promise; the weak points are printed first.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRIEF = "docs/prep/01-brief-kva-hackathon.html"
ANALYSIS = "docs/plan/00-analysis.md"
NHTSA = "prep/research-archive/nhtsa-change-recalls/"
PRICING_URL = "https://platform.claude.com/docs/en/about-claude/pricing (fetched 2026-11-13)"
SKILL = "prep/research-archive/kva-8hack-skill/plugins/8hack/skills/hack-economic-model/SKILL.md"


def A(value, unit, source, conf, bear=None, bull=None):
    d = {"value": value, "unit": unit, "source": source, "confidence": conf}
    if bear is not None:
        d["bear"] = bear
        d["bull"] = bull
    return d


ASSUMPTIONS = {
    # ---------------- MARKET (counts) ----------------
    "sites_world_iatf": A(93713, "sites", BRIEF + " #numbers (VDA QMC, 23 Apr 2026)", "V"),
    "sites_italy_iatf": A(1589, "sites", BRIEF + " #numbers (VDA QMC, 23 Apr 2026)", "V"),
    "sites_piedmont_anfia": A(734, "firms", BRIEF + " #numbers (Osservatorio ANFIA, Oct 2026). ANFIA supply-chain firms incl. design/engineering/service firms with NO IATF certificate: NOT a subset of the 1,589 IATF sites. v3: NOT in SAM; shown only as a non-IATF upper bound for the Piedmont beachhead", "V"),
    "firms_italy_components": A(2110, "firms", BRIEF + " #numbers (Osservatorio ANFIA, Oct 2026)", "V"),
    "share_oem_change_burden": A(0.70, "share of sites", "assumption: share of IATF sites that ship to an OEM or tier-1 under customer-specific change approval (PPAP, Stellantis 8.5.6.1 style). IATF 16949 s.8.5.6.1 itself requires change control, so we guess most; no count found", "U", bear=0.50, bull=0.85),
    "share_budget_and_data_ready": A(0.50, "share of sites", "assumption: share with a quality team large enough to run the tool, documents in digital form and a software budget line of EUR 24-36k. No count found", "U", bear=0.30, bull=0.65),
    "som_cap_italy_3y": A(0.05, "share of SAM", "assumption: no single-product vendor passes 5% of a serviceable plant base in 3 years from a standing start; used only as a sanity cap on the funnel", "U"),

    # ---------------- PRICING ----------------
    "price_pilot": A(9500, "EUR per pilot", "assumption: v3 (review B, CONSOLIDATED): paid 8-week replay EUR 9,500, 100% credited against the year-1 licence; lowest barrier without a reference customer. Team estimate, no buyer quote [declared]", "E", bear=9500, bull=9500),
    "price_licence": A(24000, "EUR per plant per year", BRIEF + " #market (licence EUR 24-36k labelled estimate). v3: base = 24k defended floor, 30k upside only (High), 36k dropped. v4: the price itself is [declared] (no buyer has said it); it sits inside / below the market band of comparable QMS software [verified: Vendr - Arena median $55,970/yr (31 purchases), Greenlight Guru median $43,989, MasterControl median $115,673; Monetizely Aug 2025 - mid-sized enterprise QMS $25-100k/yr]", "E", bear=24000, bull=30000),
    "price_warning_usd": A(35000, "USD per year", BRIEF + " #market: COUNTERPOINT (v4: no longer the only price evidence): a practitioner forum (Elsmar Cove) called a USD 35k/year price unjustified. Our EUR 24k base is below it; EUR 30k upside is about at it", "V"),
    "qms_price_arena_usd": A(55970, "USD per year (median, 31 purchases)", "docs/research/online-confirmation.md (team research 14 Nov; econ/evidence/problem_evidence_2026-11-14.md): Vendr, Arena median contract", "V"),
    "qms_price_greenlight_usd": A(43989, "USD per year (median)", "docs/research/online-confirmation.md (team research 14 Nov): Vendr, Greenlight Guru median contract", "V"),
    "qms_price_mastercontrol_usd": A(115673, "USD per year (median)", "docs/research/online-confirmation.md (team research 14 Nov): Vendr, MasterControl median contract", "V"),
    "qms_band_low_usd": A(25000, "USD per year", "docs/research/online-confirmation.md (team research 14 Nov): Monetizely Aug 2025, mid-sized enterprise QMS low end", "V"),
    "qms_band_high_usd": A(100000, "USD per year", "docs/research/online-confirmation.md (team research 14 Nov): Monetizely Aug 2025, mid-sized enterprise QMS high end", "V"),
    "pilot_months": A(2, "months", "assumption: v3: 8-week paid replay of last year's change requests (onboarding inside the 8 weeks)", "U"),
    "pilot_credit_share": A(1.0, "share of pilot fee", "assumption: v3: pilot fee fully credited against the first-year licence of the same plant [declared]", "E"),
    "pilots_y1_cap": A(5, "pilots", "assumption: v3 (review B): no more than 5 paid pilots in year 1 for 3 founders without a reference customer; caps High", "E"),
    "licences_billed_y1": A(1, "licences", "assumption: v3: 1 licence billed in year 1 (16 meetings x 8% = 1.28 decisions; the rest signs in year 2) [declared]", "E"),
    "ltv_cap_years": A(5, "years", "assumption: v3 (review A): LTV counts at most 5 years of gross profit, undiscounted", "E"),
    "eur_per_usd": A(0.88, "EUR per USD", "assumption: round FX rate for conversions only; not looked up for 14 Nov 2026", "U"),

    # ---------------- UNIT COST: LLM (v2: MEASURED, replaces Sonnet token guesses) ----------------
    "llm_usd_per_request": A(0.0007, "USD per change request / meeting", "docs/measure: our measurement, 14 Nov: meeting mode, Claude Haiku 5.5 via Vercel AI Gateway, 10 of 14 lines filtered by code, 6 model calls = USD 0.0007; reasoning uses no tokens", "V", bear=0.007, bull=0.0005),
    "llm_usd_per_doc": A(0.05, "USD per document extracted", "docs/measure: our measurement, 14 Nov: Adient manual ~32k in + 9k out tokens = 'a few cents'; 0.05 is our upper reading", "V", bear=0.15, bull=0.02),
    "haiku_price_note": A(0, "n/a", "assumption: Haiku 5.5 list price per MTok NOT looked up today (timebox); cost above is measured spend, not price x tokens", "U"),
    "build_day_llm_usd": A(0.03, "USD", "docs/measure: our measurement, 14 Nov: whole build day incl. demo recordings", "V"),
    "llm_price_in": A(2.0, "USD per MTok input", PRICING_URL + ": Claude Sonnet 5.5 base input", "V"),
    "llm_price_out": A(10.0, "USD per MTok output", PRICING_URL + ": Claude Sonnet 5.5 base output", "V"),
    "requests_per_plant_month": A(60, "change requests per plant per month", "assumption: UNMEASURED. Range 20-150 for a plant with ~15 active programs; prep found no plant-level count (" + ANALYSIS + " section 6, 'Plant volumes'). The pilot measures it. Held at base in all scenarios; see sensitivity 7b", "U"),
    "tokens_in_per_request": A(25000, "input tokens per request", "assumption: request text, candidate documents for the part, graph neighbourhood, schema prompt", "U", bear=80000, bull=10000),
    "tokens_out_per_request": A(4000, "output tokens per request", "assumption: structured parse plus proposed conflicts with quotes", "U", bear=10000, bull=2000),
    "llm_call_multiplier": A(2.0, "x", "assumption: retries and the quote-verification pass re-send context; the reasoning itself (OWL RL + SHACL) uses no tokens (" + ANALYSIS + " 3.7)", "U", bear=3.0, bull=1.5),
    "docs_per_plant": A(1500, "documents", "assumption: drawings, control plans, 8Ds, audit reports, customer requirement extracts, approvals for one plant", "U", bear=5000, bull=500),
    "tokens_per_doc": A(8000, "input tokens", "assumption: average document incl. tables", "U"),
    "ingest_output_ratio": A(0.15, "output/input", "assumption: extracted facts with quotes", "U"),
    "ingest_refresh_yearly": A(0.25, "share of docs re-ingested per year", "assumption: revisions and new documents", "U"),

    # ---------------- UNIT COST: INFRA, SUPPORT, ONBOARDING ----------------
    "infra_per_plant_month": A(40, "EUR per plant per month", "assumption: BASE = shared EU SaaS: one python:3.12-slim container answers in 0.05-1.2 s (measured 14 Nov, 569-47k facts), so one small instance serves many plants; EUR 40 covers instance share, DB, backups, monitoring [declared]. bear = dedicated per-plant instance", "U", bear=350, bull=15),
    "infra_dedicated_month": A(350, "EUR per plant per month", "assumption: OPTION B dedicated per-plant EU instance or customer tenant (v1 base): runs inside the customer tenant or a dedicated EU instance (practitioner demand: nothing leaves the plant perimeter, " + BRIEF + " #market); DB, compute, monitoring, backups", "U", bear=800, bull=150),
    "support_hours_per_plant_month": A(8, "hours", "assumption: v3: v2 bear (8 h) taken as base (review A); ontology upkeep, rule edits, user questions [declared]", "U", bear=12, bull=4),
    "rate_eur_per_hour": A(70, "EUR per hour", "assumption: loaded cost of an engineer in Italy", "U"),
    "onboarding_days": A(10, "person-days per first plant", "assumption: TARGET with self-serve onboarding (drop a folder of plant documents, the system drafts facts with quotes, a quality engineer confirms them in a queue). Without it " + BRIEF + " #market estimates 20-40 person-days. The 10 is not measured; the hackathon build times onboarding of our 10-document corpus and the pilot measures it on a real plant", "U", bear=20, bull=6),
    "rate_eur_per_day": A(500, "EUR per person-day", "assumption: loaded cost, about 7 x rate_eur_per_hour", "U", bear=650, bull=450),

    # ---------------- GO TO MARKET ----------------
    "contacts_y1": A(200, "outreach contacts", "assumption: part-time founder outreach starting after the hackathon; one seller-equivalent does about 400 a year", "U", bear=100, bull=300),
    "contacts_y2": A(400, "outreach contacts", "assumption: one seller", "U", bear=200, bull=600),
    "contacts_y3": A(800, "outreach contacts", "assumption: two sellers", "U", bear=300, bull=1000),
    "contacts_per_seller_year": A(400, "contacts per seller-year", "assumption", "U"),
    "conv_contact_to_meeting": A(0.08, "share", "assumption: cold outreach to supplier quality directors; warm intros from ANFIA or the Turin cluster would beat it", "U", bear=0.05, bull=0.12),
    "conv_meeting_to_pilot": A(0.1875, "share", "assumption: v3: 3 pilots of 16 meetings in year 1 (CONSOLIDATED)", "U", bear=0.15, bull=0.225),
    "conv_pilot_to_licence": A(0.08 / 0.1875, "share", "assumption: v3: set so meeting->licence = 8% (review B; 18.75% x 42.7%); the number the pilot produces", "U", bear=0.34, bull=0.51),
    "pilot_to_licence_lag": A(0.5, "share signing in the year the pilot starts", "assumption: 3 month pilot plus 3 month procurement; the rest signs next year", "U"),
    "cost_per_contact": A(15, "EUR", "assumption: data, tooling, 10 minutes of founder time", "U"),
    "meeting_hours": A(4, "hours per meeting held", "assumption: prep, meeting, follow-up", "U"),
    "pilot_mgmt_hours": A(40, "hours per pilot", "assumption: scoping, weekly reviews, contract", "U"),
    "seller_cost_year": A(72000, "EUR per seller-year", "assumption: EUR 6k per month loaded", "U"),
    "events_year": A(10000, "EUR per year", "assumption: plant-quality events, ANFIA and Turin cluster", "U"),
    "churn_year": A(0.20, "share of plants lost per year", "assumption: v3: v2 bear (20%) taken as base (review A); no reference customer yet", "U", bear=0.30, bull=0.10),
    "team_fte": A(3, "FTE", ANALYSIS + " C22 (team of three)", "P"),
    "team_fte_y1": A(3, "paid FTE in year 1", "assumption: v3 (review A): 3 founders paid from year 1; v4: at EUR 2k/month stipend [declared]", "U"),
    "team_fte_y2": A(3, "paid FTE in year 2", "assumption: v3: 3 founders paid [declared]", "U"),
    "founder_contacts_year": A(300, "contacts per year", "assumption: founder-led sales; sellers are hired only for contacts above this", "U"),
    "team_cost_month": A(2000, "EUR per FTE per month", "assumption: v4: team decision 14 Nov - founders on a minimum stipend until a seed round (v3: EUR 5,000 loaded) [declared]", "E"),
    "tools_year": A(12000, "EUR per year", "assumption: SaaS, security audit, legal", "U"),

    # ---------------- VALUE SIDE: cost of one escaped unapproved change (supplier side) ----------------
    "sort_pieces": A(5000, "pieces", "assumption: pieces in stock, in transit or at the customer needing 100% sorting after an unapproved material or source change is found", "U", bear=1000, bull=20000),
    "sort_cost_per_piece": A(1.2, "EUR per piece", "assumption: 100% inspection, third-party sorting of small parts. v4 sanity check: base sorting EUR 6,000 = about 136-227 sorter-hours at USD 30-50/h charge-back (one practitioner account, team research 14 Nov) - plausible for a multi-day sort, still [unverified]", "U", bear=0.6, bull=2.0),
    "sort_chargeback_usd_hour_low": A(30, "USD per sorter-hour", "docs/research/practitioner-voice.md (team research 14 Nov): sorting charged back at USD 30-50/h in ONE practitioner account (Elsmar Cove); one account only", "P"),
    "sort_chargeback_usd_hour_high": A(50, "USD per sorter-hour", "docs/research/practitioner-voice.md: same single practitioner account", "P"),
    "astemo_failed_change_share": A(0.83, "share of significant supplier quality issues", "docs/research/online-confirmation.md (team research 14 Nov): Astemo Supplier Change Management Guidebook rev 4.0 (Dec 2025): 83% of significant supplier quality issues FY22-FY24 caused by failed change management (one OEM-tier customer's own data; framing only, not converted to a per-plant frequency)", "V"),
    "adient_notice_days": A(180, "days", "docs/research/online-confirmation.md (team research 14 Nov): Adient Global Supplier Standards Manual rev 10.0 (2023): written approval >=180 days before any product/process change, else New Business Hold, notice to the IATF registrar, possible financial consequences (framing only)", "V"),
    "expedite_eur": A(5000, "EUR per event", "assumption: premium freight and overtime to keep the customer line fed", "U", bear=2000, bull=15000),
    "eng_hours_per_event": A(120, "hours", "assumption: 8D, containment, customer meetings, re-approval submission", "U", bear=60, bull=250),
    "chargeback_eur": A(10000, "EUR per event", "assumption: customer debit note or penalty. Supplier-side downtime cost is NOT sourced; the USD 2.3M/h Siemens figure is OEM loss and is never used here", "U", bear=0, bull=60000),
    "review_minutes_saved": A(15, "minutes per request", "assumption: engineer no longer hunts the documents by hand for each change request. NOT used in break-even", "U"),
    "ires_rate": A(0.24, "rate", "assumption: standard Italian corporate income tax rate (IRES); confirm with a tax adviser", "U"),
    "ai_deduction_multiple": A(1.8, "x of cost deductible", BRIEF + " #numbers (180% up to EUR 2.5M, 2026-2028, Law 199/2025). Whether a plant licence qualifies is NOT checked", "P"),

    # ---------------- VERIFIED HARM FIGURES (framing only, never converted to a frequency) ----------------
    "gm_ignition_loss_usd": A(900_000_000, "USD", BRIEF + " #numbers (GM reporting, NHTSA recall DB). Supplier changed the part, part number unchanged", "V"),
    "gm_ignition_vehicles": A(2_190_934, "vehicles", BRIEF + " #numbers", "V"),
    "ford_25v270000_vehicles": A(160729, "vehicles", BRIEF + " #numbers (Ford 2025 recall 25V270000, unauthorized tooling change at a sub-supplier)", "V"),
    "nhtsa_change_share": A(0.059, "share of recalls", NHTSA + " (975 sampled, 206 read; CI 3.5-8.3% per archived rerun, see prep/research-archive/README.md Reproduce; lower bound; one reviewer; US only)", "V"),
    "nhtsa_supplier_share": A(0.405, "share of recalls", NHTSA + " (same sample, supplier-originated)", "V"),
    "siemens_downtime_usd_hour": A(2_300_000, "USD per hour", BRIEF + " #numbers (Siemens 2024, survey of 181, large OEM plants). OEM loss, NOT supplier cost: excluded from every calculation", "V"),
}

SCEN = {"Low": "bear", "Base": "value", "High": "bull"}


def g(key, scen="Base"):
    """Value of an assumption for a scenario (Low = bear, High = bull, falls back to value)."""
    a = ASSUMPTIONS[key]
    k = SCEN[scen]
    return a["value"] if k == "value" else a.get(k, a["value"])


def validate():
    for key, a in ASSUMPTIONS.items():
        for f in ("value", "unit", "source", "confidence"):
            assert f in a and a[f] not in (None, ""), (key, f)
        assert a["confidence"] in ("V", "P", "E", "U"), key
        src = a["source"]
        assert src.startswith(("assumption", "docs/", "prep/", "http")), (key, src)
        if a["confidence"] == "U":
            assert src.startswith("assumption"), key
        if "bear" in a:
            assert "bull" in a, key


# ------------------------------------------------------------------ calculations
def market():
    s = {}
    ps = g("price_licence")
    share = g("share_oem_change_burden") * g("share_budget_and_data_ready")
    s["share"] = share
    s["world_tam_eur"] = g("sites_world_iatf") * ps
    s["italy_tam_eur"] = g("sites_italy_iatf") * ps
    s["italy_sam_plants"] = g("sites_italy_iatf") * share
    s["italy_sam_eur"] = s["italy_sam_plants"] * ps
    s["piedmont_upper_bound_firms"] = g("sites_piedmont_anfia")  # non-IATF upper bound, NOT in SAM
    s["som_cap_plants"] = s["italy_sam_plants"] * g("som_cap_italy_3y")
    return s


def llm_cost_usd(tin, tout, mult, pin=None, pout=None):
    pin = g("llm_price_in") if pin is None else pin
    pout = g("llm_price_out") if pout is None else pout
    return (tin * pin + tout * pout) / 1e6 * mult


def unit_economics(scen="Base"):
    u = {}
    req = g("requests_per_plant_month")
    mult = g("llm_call_multiplier", scen)
    u["llm_per_request_eur"] = g("llm_usd_per_request", scen) * g("eur_per_usd")
    u["llm_run_year"] = u["llm_per_request_eur"] * req * 12
    ing_in = g("docs_per_plant", scen) * g("tokens_per_doc")
    u["llm_ingest_once"] = g("docs_per_plant", scen) * g("llm_usd_per_doc", scen) * g("eur_per_usd")
    u["llm_ingest_year"] = u["llm_ingest_once"] * g("ingest_refresh_yearly")
    u["llm_year"] = u["llm_run_year"] + u["llm_ingest_year"]
    u["infra_year"] = g("infra_per_plant_month", scen) * 12
    u["support_year"] = g("support_hours_per_plant_month", scen) * 12 * g("rate_eur_per_hour")
    u["cogs_year"] = u["llm_year"] + u["infra_year"] + u["support_year"]
    u["price"] = g("price_licence", scen)
    u["gp_year"] = u["price"] - u["cogs_year"]
    u["gm"] = u["gp_year"] / u["price"]
    onboarding = g("onboarding_days", scen) * g("rate_eur_per_day", scen)
    u["pilot_delivery_cost"] = (onboarding + g("pilot_months") * g("infra_per_plant_month", scen)
                                + u["llm_ingest_once"] + u["llm_per_request_eur"] * req * g("pilot_months"))
    u["pilot_price"] = g("price_pilot", scen)
    u["pilot_margin"] = u["pilot_price"] - u["pilot_delivery_cost"]
    m, p, c = g("conv_contact_to_meeting", scen), g("conv_meeting_to_pilot", scen), g("conv_pilot_to_licence", scen)
    pilots_per_lic = 1 / c
    meetings_per_lic = pilots_per_lic / p
    contacts_per_lic = meetings_per_lic / m
    rate = g("rate_eur_per_hour")
    subsidy = max(0.0, -u["pilot_margin"]) * pilots_per_lic
    u["contacts_per_licence"] = contacts_per_lic
    u["meetings_per_licence"] = meetings_per_lic
    u["pilots_per_licence"] = pilots_per_lic
    u["cac_variable"] = (contacts_per_lic * g("cost_per_contact") + meetings_per_lic * g("meeting_hours") * rate
                         + pilots_per_lic * g("pilot_mgmt_hours") * rate + subsidy)
    u["payback_months_variable"] = u["cac_variable"] / (u["gp_year"] / 12) if u["gp_year"] > 0 else float("inf")
    churn = g("churn_year", scen)
    u["life_years"] = sum((1 - churn) ** k for k in range(int(g("ltv_cap_years"))))
    u["ltv_gp"] = u["gp_year"] * u["life_years"]  # undiscounted, capped at ltv_cap_years
    u["payback_months_revenue"] = u["cac_variable"] / (u["price"] / 12)
    u["ltv_cac"] = u["ltv_gp"] / u["cac_variable"]
    return u


def three_year(scen="Base"):
    u = unit_economics(scen)
    m, p, c = g("conv_contact_to_meeting", scen), g("conv_meeting_to_pilot", scen), g("conv_pilot_to_licence", scen)
    lag = g("pilot_to_licence_lag")
    churn = g("churn_year", scen)
    contacts = [g("contacts_y1", scen), g("contacts_y2", scen), g("contacts_y3", scen)]
    rows, plants, prev_pilots, cum = [], 0.0, 0.0, 0.0
    cap_plants = market()["som_cap_plants"]
    carry = 0.0
    for t in range(3):
        pilots = contacts[t] * m * p
        if t == 0:
            pilots = min(pilots, g("pilots_y1_cap"))
            new = min(g("licences_billed_y1"), pilots * c)
            carry = pilots * c - new  # decisions from year-1 pilots that sign in year 2
        else:
            new = lag * pilots * c + (1 - lag) * prev_pilots * c if t > 1 else lag * pilots * c + carry
        start = plants
        end = start * (1 - churn) + new
        capped = end > cap_plants
        if capped:
            new -= end - cap_plants
            end = cap_plants
        avg = (start + end) / 2
        billed = start * (1 - churn) + new  # licences invoiced annually upfront in the year
        credit = new * u["pilot_price"] * g("pilot_credit_share")
        lic_rev = billed * u["price"] - credit
        pil_rev = pilots * u["pilot_price"]
        rev = lic_rev + pil_rev
        cogs = billed * u["cogs_year"] + pilots * u["pilot_delivery_cost"]
        sellers = max(0.0, contacts[t] - g("founder_contacts_year")) / g("contacts_per_seller_year")
        sm = sellers * g("seller_cost_year") + contacts[t] * g("cost_per_contact") + g("events_year")
        fte = [g("team_fte_y1"), g("team_fte_y2"), g("team_fte")][t]
        fixed = fte * g("team_cost_month") * 12 + g("tools_year")
        ebit = rev - cogs - sm - fixed
        cum += ebit
        rows.append({
            "year": t + 1, "contacts": contacts[t], "pilots": pilots, "new_plants": new, "plants_end": end,
            "plants_avg": avg, "billed": billed, "credit": credit, "arr_end": end * u["price"], "rev": rev, "lic_rev": lic_rev, "pilot_rev": pil_rev,
            "cogs": cogs, "gm": (rev - cogs) / rev if rev else 0.0, "sm": sm, "fixed": fixed, "ebit": ebit,
            "cum": cum, "capped": capped, "cac_loaded": sm / new if new else float("inf"),
        })
        plants, prev_pilots = end, pilots
    return rows


def break_even_plants(scen="Base"):
    u = unit_economics(scen)
    fixed = g("team_fte") * g("team_cost_month") * 12 + g("tools_year")
    return fixed / u["gp_year"]


def event_cost(scen="Base"):
    return (g("sort_pieces", scen) * g("sort_cost_per_piece", scen) + g("expedite_eur", scen)
            + g("eng_hours_per_event", scen) * g("rate_eur_per_hour") + g("chargeback_eur", scen))


def value_side(scen="Base"):
    """Break-even uses the BASE licence price for all three event-cost cases; price is varied in the grid."""
    per_event = event_cost(scen)
    lic = g("price_licence")
    return {"per_event": per_event, "licence": lic, "break_even_issues": lic / per_event}


def value_grid():
    prices = [24000, 30000]
    events = [8000, 15000, 30000, 60000, 150000]
    return prices, events, [[p / ev for ev in events] for p in prices]


def tokens_grid():
    reqs = [20, 60, 150, 400]
    tins = [10000, 25000, 80000, 200000]
    grid = [[llm_cost_usd(ti, ti * 0.16, g("llm_call_multiplier")) * g("eur_per_usd") * r * 12 for ti in tins] for r in reqs]
    return reqs, tins, grid


def model_grid():
    models = [("Haiku 5.5 (prompts up to 100k)", 0.10, 0.50), ("Sonnet 5.5 (base case)", 2.0, 10.0),
              ("Opus 5.5", 4.0, 20.0), ("Fable 5.2", 8.0, 40.0)]
    out = []
    for name, pi, po in models:
        c = llm_cost_usd(g("tokens_in_per_request"), g("tokens_out_per_request"), g("llm_call_multiplier"), pi, po) * g("eur_per_usd")
        out.append((name, pi, po, c, c * g("requests_per_plant_month") * 12))
    return out


def price_adoption_grid():
    mk = market()
    prices = [20000, 24000, 30000, 36000, 40000]
    shares = [0.005, 0.01, 0.02, 0.05]
    return prices, shares, [[mk["italy_sam_plants"] * s * p for s in shares] for p in prices]


# ------------------------------------------------------------------ rendering
def e(x, d=0):
    if x == float("inf"):
        return "n/a"
    return f"EUR {x:,.{d}f}"


def pct(x, d=0):
    return f"{x*100:.{d}f}%"


def render():
    L = []
    w = L.append
    mk = market()
    ue = {s: unit_economics(s) for s in SCEN}
    ty = {s: three_year(s) for s in SCEN}
    ub = ue["Base"]
    vb = {s: value_side(s) for s in SCEN}
    base_end = ty["Base"][2]["plants_end"]

    def fl_pb(scen, i):
        # fully loaded CAC of year i+1 divided by monthly gross profit of one plant
        gp = ue[scen]["gp_year"]
        return ty[scen][i]["cac_loaded"] / (gp / 12) if gp > 0 else float("inf")
    high_end = ty["High"][2]["plants_end"]

    w("# Business model output")
    w("")
    w("Generated by `docs/business/model.py` (stdlib only). Every input is in the ASSUMPTIONS dict at the top of that file with unit, source and confidence. Confidence: V verified, P portal or secondary, E estimate (brief 01 or ours), U unverified guess.")
    w("")
    w("## WHAT WE DO NOT KNOW (said first)")
    w("")
    w("1. **Plant volumes are unmeasured.** Change requests per plant per month (assumed 20 / 60 / 150) and how many of them hide a blocker are in no source we found. The pilot replays last year's requests to measure both.")
    w("2. **Cost of one escaped change is our estimate**, built from sorting, expedite, engineering hours and chargeback inputs (all `U`). The verified harm figures (GM, Ford, NHTSA) are OEM or recall level and are not converted to a per-plant frequency.")
    w("3. **The funnel rates are guesses** (8% contact to meeting, 18.75% to pilot, 42.7% to licence = 8% meeting to licence). No buyer interview exists. The price is [declared]: no buyer has said it. It sits inside/below the verified band of comparable QMS software (Vendr medians USD 44k-116k; Monetizely USD 25-100k); counterpoint: one forum called USD 35k unjustified; v4 tops out at EUR 30k.")
    w("4. **Piedmont 734 is an ANFIA supply-chain firm count, not IATF.** It is not a subset of the 1,589 Italian IATF sites, so v3 keeps it out of SAM (upper bound only). The serviceable shares (70% x 50%) are guesses.")
    w("5. **Tax incentive eligibility is not checked.** Whether a plant licence qualifies for the 180% deduction is for the buyer's adviser.")
    w("")

    w("## HEADLINE")
    w("")
    w("| Metric | Low | Base | High |")
    w("|---|---|---|---|")
    w(f"| Licence price per plant per year | {e(ue['Low']['price'])} | {e(ue['Base']['price'])} | {e(ue['High']['price'])} |")
    w(f"| Pilot price | {e(ue['Low']['pilot_price'])} | {e(ue['Base']['pilot_price'])} | {e(ue['High']['pilot_price'])} |")
    w(f"| Gross margin per licensed plant | {pct(ue['Low']['gm'])} | {pct(ue['Base']['gm'])} | {pct(ue['High']['gm'])} |")
    w(f"| Variable CAC per licence customer | {e(ue['Low']['cac_variable'])} | {e(ue['Base']['cac_variable'])} | {e(ue['High']['cac_variable'])} |")
    w(f"| CAC payback on gross profit (variable CAC) | {ue['Low']['payback_months_variable']:.1f} mo | {ue['Base']['payback_months_variable']:.1f} mo | {ue['High']['payback_months_variable']:.1f} mo |")
    w(f"| CAC payback on licence revenue (variable CAC) | {ue['Low']['payback_months_revenue']:.1f} mo | {ue['Base']['payback_months_revenue']:.1f} mo | {ue['High']['payback_months_revenue']:.1f} mo |")
    w(f"| LTV (gross profit, 5-year cap, undiscounted) / variable CAC | {ue['Low']['ltv_cac']:.1f}x | {ue['Base']['ltv_cac']:.1f}x | {ue['High']['ltv_cac']:.1f}x |")
    w(f"| Year-1 pilots / licences billed | {ty['Low'][0]['pilots']:.1f} / {ty['Low'][0]['new_plants']:.2f} | {ty['Base'][0]['pilots']:.1f} / {ty['Base'][0]['new_plants']:.2f} | {ty['High'][0]['pilots']:.1f} / {ty['High'][0]['new_plants']:.2f} |")
    w(f"| Year-1 revenue billed (pilots + licence net of pilot credit) | {e(ty['Low'][0]['rev'])} | {e(ty['Base'][0]['rev'])} | {e(ty['High'][0]['rev'])} |")
    w(f"| Year-1 operating result | {e(ty['Low'][0]['ebit'])} | {e(ty['Base'][0]['ebit'])} | {e(ty['High'][0]['ebit'])} |")
    w(f"| CAC payback on gross profit, fully loaded, year 3 (seller salary included) | {fl_pb('Low', 2):.1f} mo | {fl_pb('Base', 2):.1f} mo | {fl_pb('High', 2):.1f} mo |")
    w(f"| Plants under licence, end of year 3 | {ty['Low'][2]['plants_end']:.1f} | {base_end:.1f} | {high_end:.1f} |")
    w(f"| ARR at end of year 3 | {e(ty['Low'][2]['arr_end'])} | {e(ty['Base'][2]['arr_end'])} | {e(ty['High'][2]['arr_end'])} |")
    w(f"| Revenue in year 3 (licences + pilots) | {e(ty['Low'][2]['rev'])} | {e(ty['Base'][2]['rev'])} | {e(ty['High'][2]['rev'])} |")
    w(f"| Cumulative operating result, 3 years | {e(ty['Low'][2]['cum'])} | {e(ty['Base'][2]['cum'])} | {e(ty['High'][2]['cum'])} |")
    fnd = {sc: -min(0, min(r['cum'] for r in ty[sc])) for sc in SCEN}
    w(f"| Funding need (largest cumulative loss, 3 years) | {e(fnd['Low'])} | {e(fnd['Base'])} | {e(fnd['High'])} |")
    w(f"| Break-even caught issues per year per plant (base licence) | {vb['Low']['break_even_issues']:.1f} | {vb['Base']['break_even_issues']:.1f} | {vb['High']['break_even_issues']:.1f} |")
    w("")
    w("Low = every range input at its bear value, High = every range input at its bull value. All bears at once is a stress case, not a forecast. Revenue is BILLED basis (annual licence invoiced upfront, pilot fee credited against it); year-1 pilots capped at 5; year-1 licences billed capped at 1 (`licences_billed_y1`).")
    w("")

    w("## 1. MARKET (bottom-up, Italy first)")
    w("")
    w("| Layer | Count | Value at base price | Source key |")
    w("|---|---|---|---|")
    w(f"| World IATF 16949 sites (ceiling, not a target) | {g('sites_world_iatf'):,} | {e(mk['world_tam_eur'])} per year | `sites_world_iatf` |")
    w(f"| Italy IATF sites | {g('sites_italy_iatf'):,} | {e(mk['italy_tam_eur'])} per year | `sites_italy_iatf` |")
    w(f"| Serviceable share (OEM change burden {pct(g('share_oem_change_burden'))} x budget and data ready {pct(g('share_budget_and_data_ready'))}) | {pct(mk['share'])} | n/a | `share_oem_change_burden`, `share_budget_and_data_ready` |")
    w(f"| Italy serviceable plants (SAM) | {mk['italy_sam_plants']:,.0f} | {e(mk['italy_sam_eur'])} per year | derived |")
    w(f"| Piedmont: ANFIA supply-chain firms, NOT IATF sites (upper bound only, NOT in SAM) | {mk['piedmont_upper_bound_firms']:,} | not valued | `sites_piedmont_anfia` |")
    w(f"| 3-year sanity cap ({pct(g('som_cap_italy_3y'))} of Italy SAM) | {mk['som_cap_plants']:,.0f} plants | {e(mk['som_cap_plants']*g('price_licence'))} ARR | `som_cap_italy_3y` |")
    w("")
    w(f"Check: Base ends year 3 with {base_end:.1f} plants = {pct(base_end/mk['italy_sam_plants'],1)} of Italy SAM; High {high_end:.1f} plants = {pct(high_end/mk['italy_sam_plants'],1)}. High is {'inside' if high_end <= mk['som_cap_plants'] else 'OUTSIDE'} the {pct(g('som_cap_italy_3y'))} cap of {mk['som_cap_plants']:.0f} plants.")
    w("")

    w("## 2. PRICING")
    w("")
    w("| Item | Low | Base | High | Source key |")
    w("|---|---|---|---|---|")
    w(f"| Pilot (8 weeks, credited to licence, replay of last year's change requests) | {e(g('price_pilot','Low'))} | {e(g('price_pilot'))} | {e(g('price_pilot','High'))} | `price_pilot` |")
    w(f"| Licence per plant per year | {e(g('price_licence','Low'))} | {e(g('price_licence'))} | {e(g('price_licence','High'))} | `price_licence` |")
    w("")
    w(f"COUNTERPOINT (`price_warning_usd`, v4: no longer the only price evidence): a practitioner forum called a USD {g('price_warning_usd'):,} per year price unjustified. EUR 36k is about USD {round(36000/g('eur_per_usd'),-3):,.0f} at our round FX, so v3 dropped it. Base = EUR 24k (defended floor); EUR 30k is upside after a pilot shows caught issues. Pilot (EUR 9,500, credited) and licence are team estimates, not quotes from any buyer.")
    w(f"MARKET BAND (v4) [verified: Vendr medians per year - Arena USD {g('qms_price_arena_usd'):,} (31 purchases), Greenlight Guru USD {g('qms_price_greenlight_usd'):,}, MasterControl USD {g('qms_price_mastercontrol_usd'):,}; Monetizely Aug 2025 - mid-sized enterprise QMS USD {g('qms_band_low_usd'):,}-{g('qms_band_high_usd'):,}]. EUR 24k is about USD {round(24000/g('eur_per_usd'),-3):,.0f} at our round FX: inside the Monetizely band, at its low end, and below every Vendr median. The band shows plants already pay this order of money for quality software; it does NOT show anyone would pay OUR price, which stays [declared] until a buyer says it.")
    w("")
    w("Pricing logic at base cost to serve and base funnel (derived, no new inputs): the floor is set by margin and payback, the ceiling by the value of one avoided escaped change.")
    w("")
    w("| Licence per plant per year | Gross margin | Variable CAC payback | Fully loaded CAC payback, year 3 | Caught issues per year to pay it (base event cost) |")
    w("|---|---|---|---|---|")
    ev = event_cost("Base")
    for price in (20000, 24000, 30000, 36000):
        gp = price - ub["cogs_year"]
        w(f"| {e(price)} | {pct(gp/price)} | {ub['cac_variable']/(gp/12):.1f} mo | {ty['Base'][2]['cac_loaded']/(gp/12):.1f} mo | {price/ev:.1f} |")
    w("")
    def band(price):
        gp = price - ub["cogs_year"]
        return gp / price, ub["cac_variable"] / (gp / 12), ty["Base"][2]["cac_loaded"] / (gp / 12), price / ev
    lo, hi, fl = band(24000), band(30000), band(20000)
    w(f"Reading: at EUR 20k the margin is {pct(fl[0])} and fully loaded payback {fl[2]:.0f} months; EUR 36k is above the USD 35k a forum rejected. In the EUR 24k to 30k band: gross margin {pct(lo[0])} to {pct(hi[0])}, variable payback {hi[1]:.0f} to {lo[1]:.0f} months, fully loaded year-3 payback {hi[2]:.0f} to {lo[2]:.0f} months, and {lo[3]:.1f} to {hi[3]:.1f} avoided escaped changes a year (base estimate {e(ev)}, unverified) pay the licence. The pilot replay decides where in the band a plant sits.")
    w("")
    net = g("price_licence") * (1 - g("ai_deduction_multiple") * g("ires_rate"))
    w(f"Buyer-side tax incentive (`ai_deduction_multiple`, `ires_rate`): Italy offers a 180% deduction on AI software up to EUR 2.5M, 2026-2028 (Law 199/2025, per brief 01 #numbers). If a plant licence qualified, a {e(g('price_licence'))} licence would cost the buyer about {e(net)} after IRES at {pct(g('ires_rate'))}. Eligibility is unverified: a supporting argument, not part of any number above.")
    w("")

    w("## 3. UNIT ECONOMICS PER PLANT (steady state, per year)")
    w("")
    w("| Line | Low | Base | High | Source keys |")
    w("|---|---|---|---|---|")

    def row(label, key, keys, d=0):
        w(f"| {label} | {e(ue['Low'][key], d)} | {e(ue['Base'][key], d)} | {e(ue['High'][key], d)} | {keys} |")
    row("LLM cost per change request (measured)", "llm_per_request_eur", "`llm_usd_per_request`", 5)
    row(f"LLM run cost per plant ({g('requests_per_plant_month'):.0f} requests per month)", "llm_run_year", "`requests_per_plant_month`")
    row("LLM ingestion refresh per plant", "llm_ingest_year", "`docs_per_plant`, `llm_usd_per_doc`, `ingest_refresh_yearly`", 1)
    row("Infrastructure (Low = dedicated instance, Base = shared SaaS)", "infra_year", "`infra_per_plant_month`")
    row("Support and ontology upkeep", "support_year", "`support_hours_per_plant_month`, `rate_eur_per_hour`")
    row("Cost of revenue per plant", "cogs_year", "sum")
    row("Revenue per plant", "price", "`price_licence`")
    row("Gross profit per plant", "gp_year", "derived")
    w(f"| Gross margin | {pct(ue['Low']['gm'])} | {pct(ue['Base']['gm'])} | {pct(ue['High']['gm'])} | derived |")
    w("")
    w(f"LLM cost: MEASURED today on Claude Haiku 5.5 via Vercel AI Gateway (USD {g('llm_usd_per_request')} per meeting/request, about USD {g('llm_usd_per_doc')} per document extracted). Haiku list price not looked up [unverified]; the cost is measured spend. The OWL RL + SHACL reasoning uses no tokens, so tokens are {pct(ub['llm_year']/ub['cogs_year'],1)} of base cost of revenue. People and hosting set the margin, not the model.")
    w("")
    w("Pilot and onboarding:")
    w("")
    w("| Line | Low | Base | High | Source keys |")
    w("|---|---|---|---|---|")
    row("Pilot delivery cost (onboarding days + hosting + tokens)", "pilot_delivery_cost", "`onboarding_days`, `rate_eur_per_day`, `pilot_months`")
    row("Pilot price", "pilot_price", "`price_pilot`")
    row("Pilot margin", "pilot_margin", "derived")
    w("")
    w("A pilot is priced to pay for its own onboarding. Where it loses money, the loss is counted in CAC. The pilot fee is credited against the first-year licence, so in the 3-year table the credit is netted from licence revenue.")
    w("")

    w("## 4. CAC AND PAYBACK (pilot-led sales)")
    w("")
    w("Funnel per licence customer: contact, meeting, paid pilot, licence.")
    w("")
    w("| Line | Low | Base | High | Source keys |")
    w("|---|---|---|---|---|")
    w(f"| Contacts per licence | {ue['Low']['contacts_per_licence']:.0f} | {ue['Base']['contacts_per_licence']:.0f} | {ue['High']['contacts_per_licence']:.0f} | `conv_contact_to_meeting`, `conv_meeting_to_pilot`, `conv_pilot_to_licence` |")
    w(f"| Meetings per licence | {ue['Low']['meetings_per_licence']:.1f} | {ue['Base']['meetings_per_licence']:.1f} | {ue['High']['meetings_per_licence']:.1f} | same |")
    w(f"| Pilots per licence | {ue['Low']['pilots_per_licence']:.1f} | {ue['Base']['pilots_per_licence']:.1f} | {ue['High']['pilots_per_licence']:.1f} | same |")
    row("Variable CAC (time and outreach cost, plus any pilot loss)", "cac_variable", "`cost_per_contact`, `meeting_hours`, `pilot_mgmt_hours`")
    w(f"| Payback on gross profit | {ue['Low']['payback_months_variable']:.1f} mo | {ue['Base']['payback_months_variable']:.1f} mo | {ue['High']['payback_months_variable']:.1f} mo | derived |")
    w(f"| Gross-profit lifetime / variable CAC (undiscounted) | {ue['Low']['ltv_cac']:.1f}x | {ue['Base']['ltv_cac']:.1f}x | {ue['High']['ltv_cac']:.1f}x | `churn_year` |")
    w("")
    w("Fully loaded CAC (seller salary, outreach and events divided by new licences in the year) is far higher early because year 1 signs few plants:")
    w("")
    w("| Year | Low | Base | High | Base payback on gross profit |")
    w("|---|---|---|---|---|")
    for i in range(3):
        w(f"| Year {i+1} | {e(ty['Low'][i]['cac_loaded'])} | {e(ty['Base'][i]['cac_loaded'])} | {e(ty['High'][i]['cac_loaded'])} | {fl_pb('Base', i):.1f} mo |")
    w("")
    w(f"Two paybacks, both defended: {ub['payback_months_variable']:.1f} months on variable CAC (the cost of winning one more plant once sellers exist) and {fl_pb('Base', 2):.1f} months fully loaded in year 3 (seller salary included). Pilot fees are not credited against CAC; in base each pilot leaves {e(ub['pilot_margin'])}, which would lower both.")
    w("")

    w("## 5. THREE-YEAR SCENARIOS")
    w("")
    for s in SCEN:
        w(f"### {s}")
        w("")
        w("| Year | Contacts | Pilots | New plants | Plants at year end | ARR at year end | Revenue | Gross margin | S&M | Team and tools | Operating result | Cumulative |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in ty[s]:
            w(f"| {r['year']} | {r['contacts']:.0f} | {r['pilots']:.1f} | {r['new_plants']:.1f} | {r['plants_end']:.1f} | {e(r['arr_end'])} | {e(r['rev'])} | {pct(r['gm'])} | {e(r['sm'])} | {e(r['fixed'])} | {e(r['ebit'])} | {e(r['cum'])} |")
        w("")
    fund = {s: -min(0, min(r['cum'] for r in ty[s])) for s in SCEN}
    w(f"Funding need over 3 years (largest cumulative loss): Low {e(fund['Low'])}, Base {e(fund['Base'])}, High {e(fund['High'])}. Plants needed for plant gross profit alone to cover team and tools: Low {break_even_plants('Low'):.1f}, Base {break_even_plants('Base'):.1f}, High {break_even_plants('High'):.1f}. Revenue in years 1 and 2 is mostly one-off pilot fees; ARR is the recurring line.")
    w("")

    w("## 6. VALUE SIDE: what one caught change is worth to a supplier plant")
    w("")
    w("Verified harm figures (framing only; none is a per-plant frequency):")
    w("")
    w("| Fact | Number | Source key |")
    w("|---|---|---|")
    w(f"| GM ignition switch, part changed, part number unchanged | USD {g('gm_ignition_loss_usd')/1e6:,.0f}M over {g('gm_ignition_vehicles'):,} vehicles, about USD {g('gm_ignition_loss_usd')/g('gm_ignition_vehicles'):,.0f} per vehicle (derived) | `gm_ignition_loss_usd`, `gm_ignition_vehicles` |")
    w(f"| Ford recall 25V270000, unauthorized tooling change at a sub-supplier | {g('ford_25v270000_vehicles'):,} vehicles | `ford_25v270000_vehicles` |")
    w(f"| US recalls caused by an unapproved or unverified change | {pct(g('nhtsa_change_share'),1)} (CI 3.5-8.3%), lower bound, one reviewer | `nhtsa_change_share` |")
    w(f"| US recalls that start at a supplier | {pct(g('nhtsa_supplier_share'),1)} | `nhtsa_supplier_share` |")
    w(f"| Downtime of a large OEM plant (Siemens 2024) | USD {g('siemens_downtime_usd_hour')/1e6:.1f}M per hour: OEM loss, reaches a supplier only as penalties. NOT USED in any calculation | `siemens_downtime_usd_hour` |")
    w("")
    w("Supplier-side cost of ONE escaped unapproved change (our estimate; every component is an assumption):")
    w("")
    w("| Component | Low | Base | High | Source keys |")
    w("|---|---|---|---|---|")

    def comp(label, fn, keys):
        w(f"| {label} | {e(fn('Low'))} | {e(fn('Base'))} | {e(fn('High'))} | {keys} |")
    comp("100% sorting", lambda s: g('sort_pieces', s) * g('sort_cost_per_piece', s), "`sort_pieces`, `sort_cost_per_piece`")
    comp("Expedite and premium freight", lambda s: g('expedite_eur', s), "`expedite_eur`")
    comp("Engineering and quality hours (8D, re-approval)", lambda s: g('eng_hours_per_event', s) * g('rate_eur_per_hour'), "`eng_hours_per_event`")
    comp("Customer chargeback", lambda s: g('chargeback_eur', s), "`chargeback_eur`")
    w(f"| **Total per event** | {e(vb['Low']['per_event'])} | {e(vb['Base']['per_event'])} | {e(vb['High']['per_event'])} | sum |")
    w(f"| **Break-even: caught issues per year to pay a EUR {g('price_licence'):,.0f} licence** | {vb['Low']['break_even_issues']:.1f} | {vb['Base']['break_even_issues']:.1f} | {vb['High']['break_even_issues']:.1f} | licence price / cost per event |")
    w("")
    w("A caught issue means a real blocker a human would otherwise have missed and that would have cost money. The pilot counts these on last year's requests. Break-even in caught issues per year, licence price x cost per escaped event:")
    w("")
    prices, events, bg = value_grid()
    w("| Licence per year \\ cost per event | " + " | ".join(e(x) for x in events) + " |")
    w("|---|" + "---|" * len(events))
    for p, r in zip(prices, bg):
        w(f"| {e(p)} | " + " | ".join(f"{x:.1f}" for x in r) + " |")
    w("")
    sav = g("review_minutes_saved") / 60 * g("requests_per_plant_month") * 12 * g("rate_eur_per_hour")
    w(f"Secondary value, NOT in break-even (`review_minutes_saved`): {g('review_minutes_saved')} minutes saved per request x {g('requests_per_plant_month'):.0f} requests per month = {e(sav)} per plant per year at base. The product never says approved, so we do not sell it as speed.")
    w("")

    w("## 7. SENSITIVITY")
    w("")
    w("### 7a. ARR at end of year 3: price x adoption (share of Italy SAM)")
    w("")
    pr, sh, gr = price_adoption_grid()
    w(f"Italy SAM = {mk['italy_sam_plants']:,.0f} plants. Adoption = share of those plants under licence at end of year 3. Base scenario lands at {pct(base_end/mk['italy_sam_plants'],1)}.")
    w("")
    w("| Licence per plant per year \\ adoption | " + " | ".join(pct(x, 1) + f" ({mk['italy_sam_plants']*x:.0f} plants)" for x in sh) + " |")
    w("|---|" + "---|" * len(sh))
    for p, r in zip(pr, gr):
        w(f"| {e(p)} | " + " | ".join(e(x) for x in r) + " |")
    w("")
    w("## 8. FIELDS FOR THE ECONOMIC MODEL (Control8 `update_economic_model`)")
    w("")
    w("Schema as described in " + SKILL + ": revenue lines with price (integer cents), volume (units billed in the period), period, recurring flag; channels with cost per lead, conversion share, leads per period; sellers (count, monthly cost); cost to serve goes in the note. The vocabulary (allowed units, periods, channel names) is returned by `get_economic_model` at runtime and is NOT in any file we have; check it before saving.")
    w("")
    b = ty["Base"]
    w("| Field | Value (Base) | Source key |")
    w("|---|---|---|")
    w(f"| Line 1: pilot, price | {e(g('price_pilot'))} = {int(g('price_pilot')*100)} cents, recurring: no | `price_pilot` |")
    w(f"| Line 1: volume (pilots started per year) | year 1: {b[0]['pilots']:.0f}; year 2: {b[1]['pilots']:.0f}; year 3: {b[2]['pilots']:.0f} | derived |")
    w(f"| Line 2: licence per plant, price | {e(g('price_licence'))} = {int(g('price_licence')*100)} cents, recurring: yes, period: year | `price_licence` |")
    w(f"| Line 2: volume (plants billed in the year, average) | year 1: {b[0]['plants_avg']:.1f}; year 2: {b[1]['plants_avg']:.1f}; year 3: {b[2]['plants_avg']:.1f}; run-rate at end of year 3: {b[2]['plants_end']:.1f} | derived |")
    lead_cost = g("cost_per_contact") / g("conv_contact_to_meeting") + g("meeting_hours") * g("rate_eur_per_hour")
    lead_cost_all = ub["cac_variable"] / ub["meetings_per_licence"]
    w(f"| Channel: direct outreach to supplier quality directors, cost per lead (lead = meeting held), all variable acquisition cost incl. pilot management time | {e(lead_cost_all)} = {round(lead_cost_all*100)} cents (outreach and meeting only: {e(lead_cost)}) | `cost_per_contact`, `conv_contact_to_meeting`, `meeting_hours`, `pilot_mgmt_hours` |")
    w(f"| Channel: conversion, lead to licence customer | {pct(g('conv_meeting_to_pilot')*g('conv_pilot_to_licence'),1)} | `conv_meeting_to_pilot`, `conv_pilot_to_licence` |")
    w(f"| Channel: leads per year (meetings held) | year 1: {b[0]['contacts']*g('conv_contact_to_meeting'):.0f}; year 2: {b[1]['contacts']*g('conv_contact_to_meeting'):.0f}; year 3: {b[2]['contacts']*g('conv_contact_to_meeting'):.0f} | `contacts_y1`, `contacts_y2`, `contacts_y3` |")
    sl = lambda t: max(0.0, b[t]['contacts'] - g('founder_contacts_year')) / g('contacts_per_seller_year')
    w(f"| Sellers (founders cover the first {g('founder_contacts_year'):.0f} contacts a year) | year 1: {sl(0):.2f}; year 2: {sl(1):.2f}; year 3: {sl(2):.2f} at {e(g('seller_cost_year')/12)} per month | `seller_cost_year`, `founder_contacts_year` |")
    w(f"| Cost to serve one plant per year | {e(ub['cogs_year'])}; gross margin {pct(ub['gm'])} | section 3 |")
    w("")
    w(f"With the all-in cost per lead, Control8's lead cost / conversion = {e(lead_cost_all / (g('conv_meeting_to_pilot')*g('conv_pilot_to_licence')))}, equal to our variable CAC. Seller salaries are entered separately as sellers, so Control8's blended CAC may move toward our fully loaded figure (section 4); its exact formula is not in our files. Leads x conversion gives {b[2]['contacts']*g('conv_contact_to_meeting')*g('conv_meeting_to_pilot')*g('conv_pilot_to_licence'):.0f} licences a year at year-3 pace; the model books {b[2]['new_plants']:.0f} in year 3 because half of each year's pilots sign the following year.")
    w("")
    return "\n".join(L) + "\n"


MARK = {"V": "verified", "P": "declared", "E": "declared", "U": "unverified"}


def extras():
    L = []
    w = L.append
    ub = unit_economics("Base")
    w("## 9. v2 ADDITIONS")
    w("")
    w("### 9a. Delivery options (same base everything else)")
    w("")
    w("| Option | Infra per plant per year | Cost of revenue | Gross margin | Variable CAC payback |")
    w("|---|---|---|---|---|")
    for name, m in (("A shared EU SaaS (BASE)", g("infra_per_plant_month")), ("B dedicated per-plant instance", g("infra_dedicated_month"))):
        cogs = ub["cogs_year"] - ub["infra_year"] + m * 12
        gp = ub["price"] - cogs
        w(f"| {name} | {e(m*12)} | {e(cogs)} | {pct(gp/ub['price'])} | {ub['cac_variable']/(gp/12):.1f} mo |")
    w("")
    w("| C on-prem, LOCAL open-weight model (OpenAI-compatible endpoint via LLM_BASE_URL / LLM_MODEL) | null | null | null | null |")
    w("")
    w("C is supported by the product today (LLM_BASE_URL / LLM_MODEL point the pipeline at any OpenAI-compatible endpoint; quotes are verified by code, not by the model) but its cost is NOT measured [unverified]: customer hardware, GPU or CPU inference, and our install/support time are unknown, and benchmark recall on a local model is NOT measured. Left null on purpose.")
    w("")
    w("Base = A: the measured container (1.2 s at 47k facts, one python:3.12-slim image) needs no per-plant hardware, and pilots replay documents the plant chooses to share. B is offered as a priced option (a surcharge of about EUR 3,700/yr would hold margin) for plants that require nothing to leave their perimeter.")
    w("")
    w("### 9b. Break-even caught changes per plant per year")
    w("")
    w("| Escaped-change cost | Licence 24k (base) | 30k (upside) |")
    w("|---|---|---|")
    for ev in (event_cost("Low"), event_cost("Base"), event_cost("High")):
        w(f"| {e(ev)} | " + " | ".join(f"{p/ev:.2f}" for p in (24000, 30000)) + " |")
    w("")
    w(f"Base escaped-change cost {e(event_cost('Base'))} [unverified]: {g('price_licence')/event_cost('Base'):.2f} caught changes per plant per year pay the licence.")
    w("")
    w("### 9c. Funnel sensitivity (base otherwise; contact->meeting x meeting->pilot x pilot->licence)")
    w("")
    w("| Funnel | Lead->licence | Variable CAC | Payback on GP | LTV/CAC (5-yr cap) |")
    w("|---|---|---|---|---|")
    rate = g("rate_eur_per_hour")
    for lab, m, p, c in (("bear 5/15/34%", .05, .15, .34), ("base 8/18.75/42.7%", .08, .1875, .08 / .1875), ("bull 12/22.5/51%", .12, .225, .51), ("v2 base 8/25/50% (for reference)", .08, .25, .50)):
        pil = 1 / c; mee = pil / p; con = mee / m
        cac = con * g("cost_per_contact") + mee * g("meeting_hours") * rate + pil * g("pilot_mgmt_hours") * rate
        w(f"| {lab} | {pct(p*c,1)} | {e(cac)} | {cac/(ub['gp_year']/12):.1f} mo | {ub['ltv_gp']/cac:.1f}x |")
    w("")
    w("### 9d. Assumption markers (KVA vocabulary)")
    w("")
    w("| Key | Value | Unit | Marker | Source |")
    w("|---|---|---|---|---|")
    for k, a in ASSUMPTIONS.items():
        w(f"| `{k}` | {a['value']} | {a['unit']} | [{MARK[a['confidence']]}] | {a['source'][:140]} |")
    w("")
    return "\n".join(L) + "\n"


def main():
    validate()
    out = render() + extras()
    assert chr(0x2014) not in out, "em dash in output"
    with open(os.path.join(HERE, "model_output.md"), "w", encoding="utf-8") as f:
        f.write(out)
    sys.stdout.write(out)


if __name__ == "__main__":
    main()
