# Ontology and rules in plain words

The ontology (`lcc.ttl`) describes one process: a change of source, material, process or coating for a part
at a tier-1 automotive supplier. OWL 2 RL axioms *classify and connect*; closed-world checks in
`core/rules.py` (SPARQL over the reasoned graph) and `shapes.ttl` (SHACL) *decide*. OWL alone cannot say
"there is no approval", because OWL assumes that what is not written may still be true elsewhere.

## Inferred links (OWL property chains, inverse and transitive properties)

| Inferred link | How it is derived | Why it matters |
|---|---|---|
| part **subjectTo** customer requirement | part usedIn program → program forCustomer customer → customer imposes requirement | the CSR that applies to a part is never written on the part |
| part **subjectToLaw** law | part usedIn program → program soldIn market → market hasLaw law (inverse of appliesInMarket) | the ELV ban reaches a clip through the vehicle's market |
| part **deliveredTo** customer | usedIn → forCustomer | approval is per customer |
| part **madeOfAlloy** alloy | part madeOf alloy-in-temper → temperOf alloy | an 8D that names only "EN AW-6082" reaches a part drawn in EN AW-6082-T6 |
| supplier **hasIssue** issue | inverse of issue concernsSupplier | "what does this supplier have open" |
| supplier **feedsInto** supplier | transitive closure of `suppliesTo` (sub-supplier delivers to supplier, ...) | a tier-3 supplier reaches the tier-1 supplier of a part through every tier in between; each hop has its own quote |
| record **supersedes** record | transitive | rev D replaces rev C replaces rev B |

## Checks on a proposed change

| Rule | Fires when | Severity |
|---|---|---|
| R1a | new supplier's company-level qualification is *conditional* | blocker |
| R1b | no current approval for this supplier × part × our site × customer | blocker |
| R2 | the customer's current requirement needs approval (PPAP) for this change type, no valid deviation covers it, and the new source is not already approved | blocker |
| R3 | new supplier has an *open* 8D/NCR on the part's material or alloy | warning |
| R4 | a record the answer depends on replaced an older one: show the old one in red, keep it in history | info |
| R5 | new coating contains a substance the law of the part's market restricts | blocker |
| R6 | new supplier not qualified for the drawing material; or a new material is below the special characteristic | blocker |
| R8 | change of material, process, coating or source at a *sub-tier* supplier (`at_supplier`) that feeds an approved supplier of the part: notice must travel up the chain to the plant (QP-14); the customer must approve if a current customer requirement of the part says `requiresCustomerApprovalForSubTier` for this change type, is notified if it says `requiresNotificationForSubTier`, else the finding names the gap | blocker if customer approval is required, else warning |
| R7 | evidence is missing (unknown supplier, coating, material, no 3.1 certificate, or no known chain from a sub-tier supplier to a supplier of the part) → a question with a named owner, not a violation | question |

The system never says "approved". It says "blockers found, with sources" or "no blocker found in memory".

## Memory rules

- **Two times.** valid time (when it is true in the world) and record time (when we learned it). A question
  can be asked "as of" any date, and "as known at" any moment.
- **Replace, never delete.** A newer record names what it supersedes. The older one leaves the current graph
  and stays in history.
- **Humans and agents.** Agents write *proposed* facts; they count only after a person accepts them. A write
  that contradicts a current record (second qualification for the same supplier, second approval for the
  same key) is refused unless it explicitly supersedes the current one.
- **Every fact has a quote** that is literally in its source (`data/validate_world.py` checks this).
