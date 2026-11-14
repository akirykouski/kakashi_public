# Economic model

Saved in Control8 on 14 Nov 2026 (model `em_ab34e3e0_e36`, version 1). Control8's own read-back:
annual revenue EUR 43,000 (licence 24,000 recurring + 2 pilots 19,000), blended CAC EUR 15,880 (16 meetings, 1 licence a year),
payback 7.9 months, first-year return 2.71x, coverage complete (no sales team: founders sell).

| Path | What |
|---|---|
| `v4/MODEL.md` | The model: what we know and don't, headline, pricing, unit economics, CAC/LTV/payback, 3-year scenarios, funding need, claims not to make, rubric self-score |
| `v4/model.py` | Stdlib-only model; every assumption with value, unit, marker ([verified]/[declared]/[unverified]) and source |
| `v4/control8_payload.json` | The document saved in Control8 |
| `reviews/` | Two independent reviews (arithmetic and go-to-market) and the consolidated decisions applied in v3 |
| `evidence/` | Problem evidence: practitioner threads, Astemo and Adient supplier documents, comparable software prices |
| `skills/` | The method: the organisers' economic-model and rubric skills, wshobson/agents startup-financial-modeling (MIT), lyndonkl financial-unit-economics (no licence on its repo, so linked, not copied: https://github.com/lyndonkl/claude/tree/main/skills/financial-unit-economics) |

How it was built: v1 (overnight draft) → v2 recalculated with the skills and today's measured costs → two reviews →
consolidation → v3 → v4 with the team's evidence and founder stipend. Price and funnel are team estimates: a paid pilot tests them.
