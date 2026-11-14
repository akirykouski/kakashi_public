"""Rules: check a proposed change against company memory (workstream R, product core).

Deductive checks over the OWL 2 RL closure built by project.py; no language model. Every finding cites its
evidence as proof steps (explain.py) whose leaves are facts with a source and a verbatim quote.

Ported from research/prototypes (Maksim's core/rules.py on night-shift/2026-11-13-kva-plan, R1a-R7) with
Arseniy's fixes fix/1 (not_checked), fix/2 (17 change types, notice + lead time), fix/4 (consequence on R2),
fix/8 (R8 sub-tier), and ideas from Arseniy's spike (completeness-scoped closed world, 8D at series + feature).

Nothing policy-specific is hard-coded here: policy quotes, question owners, the 8D policy level, the change
classes that need a material certificate and the completeness scopes of the approved supplier list are facts
(rules_data/facts.jsonl, built by rules_data/build.py). Load them with `extend_log(log)` before projecting.

A change is a ChangeRequest dict (core/contracts.py):
  type, part, to_supplier, from_supplier, site, new_material, new_coating, scope (series|service), as_of
  at_supplier   sub-tier supplier that makes the change (R8; prototype key, kept)

Rules
  R1a supplier standing            R1b source release (blocker inside a declared-complete scope, else question)
  R2  customer approval / notice / notification, keyed on change class; consequence from the customer's text
  R3  open 8D: exact alloy or part, or alloy series (+ failure feature) under the policy in force
  R4  replaced records (info)      R5 restricted substance via coating and law
  R6  material vs drawing, capability, special characteristic
  R7  missing evidence -> question with an owner read from data
  R8  change at a sub-tier supplier
"""
import json
import os
from dataclasses import asdict

from rdflib import Literal

try:
    from .contracts import Finding
    from .explain import explain, valid_step
    from .project import ROOT, local_name
except ImportError:  # core/ on sys.path
    from contracts import Finding
    from explain import explain, valid_step
    from project import ROOT, local_name

RULES_DATA = os.path.join(ROOT, "rules_data")
SEVERITY_ORDER = {"blocker": 0, "warning": 1, "question": 2, "info": 3}
DEFAULT_8D_LEVEL = "series+feature"   # used only when no policy fact in force sets the level
_corpus = {}


# ---- data ------------------------------------------------------------------------------------------------

def extend_log(log):
    """Load the rules' policy facts (owners, quotes, levels, completeness) into a fact log. Idempotent."""
    if getattr(log, "_rules_data_loaded", False):
        return log
    log.load_jsonl(os.path.join(RULES_DATA, "facts.jsonl"))
    log._rules_data_loaded = True
    return log


def corpus():
    if not _corpus:
        for path in (os.path.join(ROOT, "data", "corpus.jsonl"), os.path.join(RULES_DATA, "corpus.jsonl")):
            if os.path.exists(path):
                with open(path) as file:
                    for line in file:
                        item = json.loads(line)
                        _corpus[item["id"]] = item
    return _corpus


# ---- finding construction ----------------------------------------------------------------------------------

def entity_ids(entities):
    found = []
    for value in entities.values():
        for item in (value if isinstance(value, (list, tuple)) else [value]):
            if item and isinstance(item, str) and item not in found:
                found.append(item)
    return found


def finding(rule, severity, title, evidence, entities, owner=None, note=None, consequence=None):
    """A Finding dict exactly per core/contracts.py. Steps without a proof are dropped, never padded."""
    steps = [step for step in evidence if valid_step(step)]
    return asdict(Finding(rule=rule, severity=severity, title=title, evidence=steps, entities=entity_ids(entities),
                          owner=owner, note=note, consequence=consequence))


def policy(projection, policy_id):
    """Proof step citing a policy statement (fact `policy statedIn source` with its quote), or None."""
    source = projection.value(policy_id, "statedIn")
    return explain(projection, policy_id, "statedIn", source) if source else None


def question(projection, kind, title, evidence, entities):
    """R7 question. Owner and the policy sentence naming the owner come from data (`Q-<kind> questionOwner`)."""
    key = f"Q-{kind}"
    owner = projection.value(key, "questionOwner")
    steps = list(evidence)
    if owner:
        steps.append(explain(projection, key, "questionOwner", owner))
    return finding("R7", "question", title, steps, dict(entities, question=key), owner=owner)


def consequence_of(projection, requirement):
    """First consequence the customer's own document names for an unapproved change (fix/4); None if none."""
    for consequence in sorted(projection.objects(requirement, "hasConsequence")):
        step = explain(projection, requirement, "hasConsequence", consequence)
        if step and not step["inferred"]:
            return {"type": consequence, "source": step["source"], "quote": step["quote"].replace("\n", " ")}
    return None


# ---- graph helpers ---------------------------------------------------------------------------------------

def records_of(projection, class_name, predicate, value):
    rows = projection.query(
        f"SELECT ?record WHERE {{ ?record a lcc:{class_name} ; lcc:{predicate} ?value }}", value=value)
    return sorted(local_name(row[0]) for row in rows)


def approvals(projection, supplier=None, part=None):
    result = []
    for record in projection.instances("PartApproval"):
        item = {"id": record, "supplier": projection.value(record, "approvedSupplier"),
                "part": projection.value(record, "approvedPart"), "site": projection.value(record, "approvedSite"),
                "customer": projection.value(record, "approvedForCustomer"),
                "status": projection.value(record, "status")}
        if supplier and item["supplier"] != supplier:
            continue
        if part and item["part"] != part:
            continue
        result.append(item)
    return result


def history_note(projection, record_ids):
    notes = []
    for record in record_ids:
        for older in projection.objects(record, "supersedes"):
            older_facts = projection.history_by_subject.get(older, [])
            status = next((json.loads(fact["o"]) for fact in older_facts if fact["p"] == "status"), None)
            notes.append(f"{record} supersedes {older}" + (f" (was: {status})" if status else ""))
    return notes


def literal_value(projection, subject, predicate):
    value = projection.value(subject, predicate)
    return str(value) if value is not None else None


def series_of_material(projection, material):
    """Alloy series of a material: its own inSeries, or its alloy's (temperOf)."""
    found = set(projection.objects(material, "inSeries"))
    for alloy in projection.objects(material, "temperOf"):
        found |= set(projection.objects(alloy, "inSeries"))
    return found


def change_scope(change):
    return change.get("scope") or "series"


# ---- R1a supplier standing -------------------------------------------------------------------------------

def rule_supplier_qualification(projection, change):
    supplier = change["to_supplier"]
    findings = []
    for record in records_of(projection, "SupplierQualification", "qualifiedSupplier", supplier):
        status = projection.value(record, "status")
        evidence = [explain(projection, record, "qualifiedSupplier", supplier),
                    explain(projection, record, "status", Literal(status))]
        notes = history_note(projection, [record])
        if status in ("conditional", "disqualified"):
            evidence.append(policy(projection, "POL-QP11-4.3"))
            findings.append(finding("R1a", "blocker",
                                    f"{projection.label(supplier)} is {status} as a supplier: no new parts",
                                    evidence, {"supplier": supplier, "record": record}, note="; ".join(notes) or None))
        elif notes:
            evidence.append(policy(projection, "POL-QP11-4.1"))
            findings.append(finding("R4", "info",
                                    f"Supplier qualification of {projection.label(supplier)} was replaced: "
                                    f"{'; '.join(notes)}. This does not approve any part.",
                                    evidence, {"supplier": supplier, "record": record}))
    return findings


# ---- R1b source release, completeness-scoped -------------------------------------------------------------

def target_sites(projection, change, customer):
    if change.get("site"):
        return [change["site"]]
    return sorted({item["site"] for item in approvals(projection, part=change["part"])
                   if item["customer"] == customer and item["status"] == "approved"})


def completeness_statement(projection, site, customer, part, scope):
    """A completeness statement in force whose scope (plant x customer x commodity series x series/service)
    contains this part at this site. Absence of an approval is a blocker only inside such a scope."""
    part_series = set(projection.objects(part, "madeOfSeries"))
    for statement in projection.instances("CompletenessStatement"):
        if site not in projection.objects(statement, "completeForPlant"):
            continue
        customers = set(projection.objects(statement, "completeForCustomer"))
        if customers and customer not in customers:
            continue
        series = set(projection.objects(statement, "completeForSeries"))
        if series and not series & part_series:
            continue
        scopes = {str(value) for value in projection.objects(statement, "completeForScope")}
        if scopes and scope not in scopes:
            continue
        matched = sorted(series & part_series)
        return statement, (matched[0] if matched else None)
    return None, None


def rule_part_approval(projection, change):
    supplier, part, scope = change["to_supplier"], change["part"], change_scope(change)
    findings = []
    for customer in projection.objects(part, "deliveredTo"):
        for site in target_sites(projection, change, customer):
            matching = [item for item in approvals(projection, supplier=supplier, part=part)
                        if item["site"] == site and item["customer"] == customer]
            if any(item["status"] == "approved" for item in matching):
                continue
            evidence = [explain(projection, part, "deliveredTo", customer)]
            others = [item for item in approvals(projection, supplier=supplier) if item["status"] == "approved"]
            for item in others[:3]:
                evidence.append(explain(projection, item["id"], "approvedPart", item["part"]))
            for item in matching:
                evidence.append(explain(projection, item["id"], "approvedSupplier", supplier))
            evidence.append(policy(projection, "POL-QP11-4.2"))
            name = projection.label(supplier) if projection.is_a(supplier, "Supplier") else supplier
            only = ", ".join(sorted({f"{item['part']}@{item['site']}" for item in others}))
            revoked = [item["id"] for item in matching if item["status"] == "revoked"]
            entities = {"supplier": supplier, "part": part, "site": site, "customer": customer}
            statement, series = completeness_statement(projection, site, customer, part, scope)
            if statement is None and not revoked:
                evidence.append(policy(projection, "POL-QP15-2.2"))
                findings.append(question(projection, "source_release",
                                         f"No release of {name} for {part} at {site} for {projection.label(customer)} "
                                         f"on file, and the approved supplier list is not declared complete for "
                                         f"this plant, customer, commodity and {scope} scope", evidence, entities))
                continue
            if statement:
                evidence.append(explain(projection, statement, "completeForPlant", site))
                if customer in projection.objects(statement, "completeForCustomer"):
                    evidence.append(explain(projection, statement, "completeForCustomer", customer))
                if series:
                    evidence += [explain(projection, statement, "completeForSeries", series),
                                 explain(projection, part, "madeOfSeries", series)]
                entities["completeness"] = statement
            title = f"{name} has no approval for {part} at {site} for {projection.label(customer)}"
            if revoked:
                title += f" (approval revoked: {', '.join(revoked)})"
            elif only:
                title += f" (approved only for {only})"
            findings.append(finding("R1b", "blocker", title, evidence, entities))
    return findings


# ---- R2 customer approval, keyed on change class -----------------------------------------------------------

def covering_deviation(projection, change, change_type):
    suppliers = {change.get("to_supplier"), change.get("from_supplier")} - {None}
    if not suppliers:
        suppliers = {item["supplier"] for item in approvals(projection, part=change["part"])
                     if item["status"] == "approved"}
    for deviation in projection.instances("Deviation"):
        if projection.value(deviation, "status") != "valid":
            continue
        if change["part"] not in projection.objects(deviation, "concernsPart"):
            continue
        if change_type not in projection.objects(deviation, "permitsChangeType"):
            continue
        if not suppliers & set(projection.objects(deviation, "concernsSupplier")):
            continue
        permitted_coatings = projection.objects(deviation, "permitsCoating")
        if change.get("new_coating") and permitted_coatings and change["new_coating"] not in permitted_coatings:
            continue
        return deviation
    return None


def deviation_end(projection, deviation):
    facts = [fact for fact in projection.current_facts if fact["s"] == deviation]
    return facts[0]["valid_to"] if facts else "?"


def customer_requirements(projection, part):
    """Customer requirements in force for the part, with the customer that imposes each."""
    by_requirement = {}
    for customer in projection.objects(part, "deliveredTo"):
        for requirement in projection.objects(customer, "imposes"):
            by_requirement[requirement] = customer
    return [(requirement, by_requirement.get(requirement)) for requirement in sorted(projection.objects(part, "subjectTo"))
            if projection.is_a(requirement, "CustomerRequirement")]


def rule_customer_approval(projection, change):
    """R2. Fires whenever a requirement in force on the part covers the change's class. Whether a new supplier
    is present plays no part, except that a supplier already approved for the part and customer needs no new
    approval (source changes only)."""
    change_type, part = change["type"], change["part"]
    deviation = covering_deviation(projection, change, change_type)
    findings = []
    already_approved = {}
    if change_type == "SourceChange" and change.get("to_supplier"):
        for item in approvals(projection, supplier=change["to_supplier"], part=part):
            if item["status"] == "approved" and (not change.get("site") or item["site"] == change["site"]):
                already_approved[item["customer"]] = item["id"]
    for requirement, customer in customer_requirements(projection, part):
        if customer in already_approved:
            record = already_approved[customer]
            findings.append(finding("R2", "info",
                                    f"{change['to_supplier']} is already an approved source of {part} for "
                                    f"{projection.label(customer)} ({record}); no new customer approval needed",
                                    [explain(projection, record, "approvedForCustomer", customer)],
                                    {"requirement": requirement, "customer": customer, "record": record}))
            continue
        if change_type in projection.objects(requirement, "requiresNoticeFor"):
            days = projection.value(requirement, "leadTimeDays")
            lead = f" at least {days} days before the change" if days else " before the change"
            findings.append(finding("R2", "info", f"{change_type} on {part}: announce to the customer{lead}, "
                                    f"per {requirement}",
                                    [explain(projection, requirement, "requiresNoticeFor", change_type)],
                                    {"requirement": requirement}))
        if change_type in projection.objects(requirement, "requiresCustomerApprovalFor"):
            evidence = [explain(projection, part, "subjectTo", requirement),
                        explain(projection, requirement, "requiresCustomerApprovalFor", change_type)]
            if deviation:
                evidence.append(explain(projection, deviation, "permitsChangeType", change_type))
                findings.append(finding("R2", "info",
                                        f"Covered by valid deviation {deviation} (until "
                                        f"{deviation_end(projection, deviation)}); no new customer approval needed",
                                        evidence, {"requirement": requirement, "deviation": deviation}))
                continue
            findings.append(finding("R2", "blocker",
                                    f"{change_type} on {part} needs written customer approval (PPAP resubmission) "
                                    f"before shipping, per {requirement}", evidence,
                                    {"requirement": requirement, "change_type": change_type, "customer": customer},
                                    note="; ".join(history_note(projection, [requirement])) or None,
                                    consequence=consequence_of(projection, requirement)))
        elif change_type in projection.objects(requirement, "requiresNotificationFor"):
            evidence = [explain(projection, part, "subjectTo", requirement),
                        explain(projection, requirement, "requiresNotificationFor", change_type)]
            findings.append(finding("R2", "info", f"{change_type} on {part}: notify the customer per {requirement}",
                                    evidence, {"requirement": requirement}))
    return findings


# ---- R3 open 8D ------------------------------------------------------------------------------------------

def open_issue_policy(projection):
    """(level, policy id) of the 8D policy in force; level in alloy | series | series+feature."""
    for policy_id in projection.instances("Policy"):
        if "OpenIssueLevel" in projection.objects(policy_id, "policyFor"):
            value = literal_value(projection, policy_id, "policyValue")
            if value:
                return value, policy_id
    return DEFAULT_8D_LEVEL, None


def open_issues(projection, supplier):
    return sorted(issue for issue in projection.objects(supplier, "hasIssue")
                  if literal_value(projection, issue, "status") == "open")


def rule_supplier_issue(projection, change):
    supplier, part = change["to_supplier"], change["part"]
    part_materials = set(projection.objects(part, "madeOf")) | set(projection.objects(part, "madeOfAlloy"))
    part_series = set(projection.objects(part, "madeOfSeries"))
    part_features = set(projection.objects(part, "hasFeature"))
    level, policy_id = open_issue_policy(projection)
    findings = []
    for issue in open_issues(projection, supplier):
        materials = set(projection.objects(issue, "concernsMaterial"))
        base = [explain(projection, supplier, "hasIssue", issue),
                explain(projection, issue, "status", Literal("open"))]
        exact = sorted(materials & part_materials)
        if exact:
            material = exact[0]
            link = "madeOf" if material in projection.objects(part, "madeOf") else "madeOfAlloy"
            evidence = base + [explain(projection, issue, "concernsMaterial", material),
                               explain(projection, part, link, material), policy(projection, "POL-QP15-1.2")]
            findings.append(finding("R3", "warning",
                                    f"{projection.label(supplier)} has open {issue} on {projection.label(material)}, "
                                    f"the material of {part}", evidence,
                                    {"supplier": supplier, "issue": issue, "material": material}))
            continue
        if part in projection.objects(issue, "concernsPart"):
            evidence = base + [explain(projection, issue, "concernsPart", part)]
            findings.append(finding("R3", "warning", f"{projection.label(supplier)} has open {issue} on {part}",
                                    evidence, {"supplier": supplier, "issue": issue}))
            continue
        if level not in ("series", "series+feature"):
            continue
        for material in sorted(materials):
            shared = sorted(series_of_material(projection, material) & part_series)
            if not shared:
                continue
            series = shared[0]
            features = sorted(set(projection.objects(issue, "failureFeature")) & part_features)
            if level == "series+feature" and not features:
                continue
            evidence = base + [explain(projection, issue, "concernsMaterial", material),
                               explain(projection, part, "madeOfSeries", series)]
            alloy_link = [explain(projection, material, "inSeries", series)] if series in projection.objects(
                material, "inSeries") else [explain(projection, material, "temperOf", alloy)
                                            for alloy in projection.objects(material, "temperOf")]
            evidence += alloy_link
            title = (f"{projection.label(supplier)} has open {issue} on {projection.label(material)}, same alloy "
                     f"series {projection.label(series)} as {part}")
            if features:
                evidence += [explain(projection, issue, "failureFeature", features[0]),
                             explain(projection, part, "hasFeature", features[0])]
                title += f" and same failure feature ({projection.label(features[0])})"
            if policy_id:
                evidence.append(policy(projection, policy_id))
            findings.append(finding("R3", "warning", title, evidence,
                                    {"supplier": supplier, "issue": issue, "material": material, "series": series,
                                     "feature": features[0] if features else None, "policy": policy_id}))
            break
    return findings


# ---- R5 restricted substance -----------------------------------------------------------------------------

def rule_restricted_substance(projection, change):
    coating, part = change.get("new_coating"), change["part"]
    if not coating:
        return []
    if not projection.is_a(coating, "Coating"):
        return [question(projection, "coating_substances",
                         f"Coating '{coating}' is not in the coating catalogue: its substances are unknown",
                         [], {"coating": coating})]
    findings = []
    for law in projection.objects(part, "subjectToLaw"):
        restricted = set(projection.objects(law, "restricts"))
        for substance in projection.objects(coating, "containsSubstance"):
            if substance not in restricted:
                continue
            evidence = [explain(projection, coating, "containsSubstance", substance),
                        explain(projection, law, "restricts", substance),
                        explain(projection, part, "subjectToLaw", law)]
            findings.append(finding("R5", "blocker",
                                    f"{projection.label(coating)} contains {projection.label(substance)}, "
                                    f"restricted by {law} for vehicles sold in the market of {part}",
                                    evidence, {"coating": coating, "substance": substance, "law": law}))
    return findings


# ---- R6 material -----------------------------------------------------------------------------------------

def special_characteristic_yield(projection, part):
    for characteristic in projection.objects(part, "hasSpecialCharacteristic"):
        value = projection.value(characteristic, "minYieldMPa")
        if value:
            return characteristic, float(value)
    return None, None


def rule_material_capability(projection, change):
    supplier, part = change["to_supplier"], change["part"]
    material = projection.value(part, "madeOf")
    capabilities = records_of(projection, "SupplierCapability", "capableSupplier", supplier)
    materials = {projection.value(record, "capableMaterial"): record for record in capabilities}
    if not material or material in materials:
        return []
    evidence = [explain(projection, part, "madeOf", material)]
    for capable_material, record in sorted(materials.items()):
        evidence.append(explain(projection, record, "capableMaterial", capable_material))
    alloy = projection.value(material, "temperOf")
    same_alloy = [item for item in materials if alloy and projection.value(item, "temperOf") == alloy]
    title = f"{projection.label(supplier)} is not qualified for {projection.label(material)} " \
            f"(qualified for: {', '.join(projection.label(item) for item in sorted(materials)) or 'nothing'})"
    note = None
    characteristic, minimum = special_characteristic_yield(projection, part)
    if same_alloy:
        other = same_alloy[0]
        note = f"Same alloy {projection.label(alloy)}, different temper: {projection.label(other)} is not " \
               f"{projection.label(material)}."
        typical = projection.value(other, "typicalYieldMPa")
        if characteristic and typical and float(typical) < minimum:
            evidence.append(explain(projection, part, "hasSpecialCharacteristic", characteristic))
            note += f" Typical yield {typical} MPa is below the special characteristic minimum {minimum:.0f} MPa."
    elif characteristic:
        evidence.append(explain(projection, part, "hasSpecialCharacteristic", characteristic))
    return [finding("R6", "blocker", title, evidence,
                    {"supplier": supplier, "material": material, "capable": sorted(materials)}, note=note)]


def rule_material_change(projection, change):
    """R6 on a MaterialChange: the new material must be the drawing designation in force (blocker otherwise),
    and must meet the part's special characteristic (yield)."""
    part, new_material = change["part"], change.get("new_material")
    if not new_material:
        return []
    if not projection.is_a(new_material, "Material"):
        return [question(projection, "material_data", f"Material '{new_material}' is not in the material master",
                         [], {"material": new_material})]
    drawing = projection.value(part, "madeOf")
    off_drawing = bool(drawing and drawing != new_material)
    characteristic, minimum = special_characteristic_yield(projection, part)
    typical = projection.value(new_material, "typicalYieldMPa") if characteristic else None
    below = characteristic is not None and typical is not None and float(typical) < minimum
    yield_text = (f"{projection.label(new_material)} (typical yield {typical} MPa) is below the special "
                  f"characteristic {characteristic} of {part} (minimum {minimum:.0f} MPa)") if below else None
    findings = []
    if off_drawing:
        # One R6 blocker per material change: the drawing designation decides; a yield shortfall is added
        # to the same finding as a second reason.
        evidence = [explain(projection, part, "madeOf", drawing), policy(projection, "POL-QP15-3.5")]
        if below:
            evidence.append(explain(projection, part, "hasSpecialCharacteristic", characteristic))
        findings.append(finding("R6", "blocker",
                                f"{projection.label(new_material)} is not the material the drawing of {part} "
                                f"designates ({projection.label(drawing)}): change the drawing first",
                                evidence, {"part": part, "material": new_material, "drawing_material": drawing,
                                           "characteristic": characteristic if below else None},
                                note=yield_text))
    elif below:
        findings.append(finding("R6", "blocker", yield_text,
                                [explain(projection, part, "hasSpecialCharacteristic", characteristic)],
                                {"material": new_material, "characteristic": characteristic}))
    if characteristic and typical is None:
        findings.append(question(projection, "material_strength",
                                 f"No strength data for {projection.label(new_material)}; {part} has special "
                                 f"characteristic {characteristic} (minimum {minimum:.0f} MPa)",
                                 [explain(projection, part, "hasSpecialCharacteristic", characteristic)],
                                 {"material": new_material, "characteristic": characteristic}))
    return findings


# ---- R7 material certificate, keyed on change class --------------------------------------------------------

def certificate_policies(projection, change_type):
    """Policies in force that require a material certificate for this change class."""
    return sorted(policy_id for policy_id in projection.instances("Policy")
                  if change_type in projection.objects(policy_id, "requiresCertificateFor"))


def checking_policies(projection, change_type):
    """Policies in force that state this change class is examined (QP-15 4.1: delivery date or quantity)."""
    return sorted(policy_id for policy_id in projection.instances("Policy")
                  if change_type in projection.objects(policy_id, "checksChangeType"))


def rule_missing_certificate(projection, change):
    """A change whose class needs a certificate (policy facts), from the supplier who will deliver the material
    (the new source, else the current approved sources of the part), for the material it will deliver (the new
    material, else the drawing material). Never depends on a new supplier being present."""
    change_type, part = change["type"], change["part"]
    policies = certificate_policies(projection, change_type)
    if not policies or (change_type == "SourceChange" and not change.get("to_supplier")):
        return []
    material = change.get("new_material") or projection.value(part, "madeOf")
    if not material or not projection.is_a(material, "Material"):
        return []
    if change.get("to_supplier"):
        suppliers = [change["to_supplier"]]
    else:
        suppliers = sorted({item["supplier"] for item in approvals(projection, part=part) if item["status"] == "approved"})
    rule_steps = [explain(projection, policy_id, "requiresCertificateFor", change_type) for policy_id in policies]
    if not suppliers:
        return [question(projection, "material_certificate",
                         f"{change_type} on {part}: no supplier of {projection.label(material)} on file, so no "
                         f"material certificate (EN 10204 3.1) either", rule_steps, {"part": part, "material": material})]
    findings = []
    for supplier in suppliers:
        certificates = records_of(projection, "MaterialCertificate", "certSupplier", supplier)
        if any(projection.value(record, "certMaterial") == material for record in certificates):
            continue
        findings.append(question(projection, "material_certificate",
                                 f"No material certificate (EN 10204 3.1) from {projection.label(supplier)} for "
                                 f"{projection.label(material)} on file. Not a violation: an open question.",
                                 rule_steps, {"supplier": supplier, "material": material}))
    return findings


# ---- not checked (fix/1) -----------------------------------------------------------------------------------

def not_checked(projection, change):
    """Requirements in the change's scope that the extractor found but could not express in the ontology.
    The reasoner never saw them, so the card lists them as NOT CHECKED. Scope = documents the part is subject to."""
    scope = set(projection.objects(change["part"], "subjectTo")) if change.get("part") else set()
    items = getattr(projection, "unclassified", []) or []
    return [item for item in items if item["source"] in scope and item["source"] not in projection.replaced]


# ---- R8 sub-tier (fix/8) -----------------------------------------------------------------------------------

def tier_path(projection, start, goal):
    queue, seen = [[start]], {start}
    while queue:
        path = queue.pop(0)
        if path[-1] == goal:
            return path
        for nxt in sorted(projection.objects(path[-1], "suppliesTo")):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(path + [nxt])
    return None


def subtier_types(projection, part):
    """Change classes R8 rules on: those QP-14 4.1 names, plus any a requirement on the part names for sub-tiers."""
    found = set()
    for policy_id in projection.instances("Policy"):
        found |= set(projection.objects(policy_id, "subTierCovers"))
    for requirement, _ in customer_requirements(projection, part):
        found |= set(projection.objects(requirement, "requiresCustomerApprovalForSubTier"))
        found |= set(projection.objects(requirement, "requiresNotificationForSubTier"))
    return found


def rule_subtier(projection, change):
    sub, part, change_type = change["at_supplier"], change["part"], change["type"]
    unlinked = policy(projection, "POL-QP14-4.4")
    if not projection.is_a(sub, "Supplier"):
        return [question(projection, "supplier_record",
                         f"Supplier '{sub}' is not in our supplier master: who does it deliver to?",
                         [], {"supplier": sub}),
                question(projection, "tier_link", f"No known chain from '{sub}' to a supplier of {part}",
                         [unlinked], {"supplier": sub, "part": part})]
    feeds = set(projection.objects(sub, "feedsInto"))
    by_customer = {}
    for item in approvals(projection, part=part):
        if item["status"] == "approved" and item["supplier"] in feeds and item["supplier"] != sub:
            by_customer.setdefault(item["customer"], []).append(item)
    if not by_customer:
        return [question(projection, "tier_link",
                         f"{projection.label(sub)} has no recorded chain to an approved supplier of {part}: "
                         f"whom does it deliver to?", [unlinked], {"supplier": sub, "part": part})]
    owner = projection.value("Q-tier_link", "questionOwner")
    findings = []
    for customer, items in sorted(by_customer.items()):
        item = sorted(items, key=lambda entry: entry["id"])[0]
        top = item["supplier"]
        path = tier_path(projection, sub, top) or [sub, top]
        evidence = [explain(projection, sub, "feedsInto", top),
                    explain(projection, item["id"], "approvedSupplier", top),
                    explain(projection, item["id"], "approvedPart", part),
                    explain(projection, part, "deliveredTo", customer),
                    policy(projection, "POL-QP14-4.2"), policy(projection, "POL-QP14-4.3")]
        requirements = [name for name, by in customer_requirements(projection, part) if by == customer]
        approval = [name for name in requirements
                    if change_type in projection.objects(name, "requiresCustomerApprovalForSubTier")]
        notification = [name for name in requirements
                        if change_type in projection.objects(name, "requiresNotificationForSubTier")]
        chain_text = " -> ".join([projection.label(name) for name in path] + [f"plant {item['site']}"])
        tier = f"{len(path)} tiers below the plant"
        consequence = None
        if approval:
            evidence += [explain(projection, part, "subjectTo", approval[0]),
                         explain(projection, approval[0], "requiresCustomerApprovalForSubTier", change_type)]
            severity = "blocker"
            consequence = consequence_of(projection, approval[0])
            title = (f"{change_type} at {projection.label(sub)} ({tier}): notice must travel up the chain and "
                     f"{projection.label(customer)} must approve in writing before shipping, per {approval[0]}. "
                     f"Chain: {chain_text}")
        elif notification:
            evidence += [explain(projection, part, "subjectTo", notification[0]),
                         explain(projection, notification[0], "requiresNotificationForSubTier", change_type)]
            severity = "warning"
            title = (f"{change_type} at {projection.label(sub)} ({tier}): notice must travel up the chain and "
                     f"{projection.label(customer)} is notified, per {notification[0]}. Chain: {chain_text}")
        else:
            severity = "warning"
            title = (f"{change_type} at {projection.label(sub)} ({tier}): notice must travel up the chain to the "
                     f"plant. No requirement of {projection.label(customer)} on file covers sub-tier changes of "
                     f"this type. Chain: {chain_text}")
        findings.append(finding("R8", severity, title, evidence,
                                {"supplier": sub, "part": part, "customer": customer, "chain": path,
                                 "approval": item["id"]}, owner=owner, consequence=consequence))
    return findings


# ---- entry points ----------------------------------------------------------------------------------------

def is_subtier(projection, change):
    return bool(change.get("at_supplier")) and change["type"] in subtier_types(projection, change["part"])


def check(projection, change):
    """All findings for a change, blockers first. Finding dicts per core/contracts.py."""
    if is_subtier(projection, change):
        return sort_findings(rule_subtier(projection, change) + contested_questions(projection, change))
    findings = []
    supplier = change.get("to_supplier")
    if change["type"] == "SourceChange" and supplier:
        if not projection.is_a(supplier, "Supplier"):
            findings.append(question(projection, "supplier_record",
                                     f"Supplier '{supplier}' is not in our supplier master: no audit, capability or "
                                     f"approval on record", [], {"supplier": supplier}))
            findings += rule_part_approval(projection, change)
            # QP-11 4.4: a change of source needs the new supplier's material certificate. An unknown supplier
            # has none on file either, so that question is asked too (eval re-gold M01/M04, CHANGES.md).
            findings += rule_missing_certificate(projection, change)
        else:
            findings += rule_supplier_qualification(projection, change)
            findings += rule_part_approval(projection, change)
            findings += rule_material_capability(projection, change)
            findings += rule_supplier_issue(projection, change)
            findings += rule_missing_certificate(projection, change)
    elif not (supplier and not projection.is_a(supplier, "Supplier")):
        findings += rule_missing_certificate(projection, change)
    findings += rule_customer_approval(projection, change)
    if change["type"] == "CoatingChange":
        findings += rule_restricted_substance(projection, change)
    if change["type"] == "MaterialChange":
        findings += rule_material_change(projection, change)
    findings += contested_questions(projection, change)
    return sort_findings(findings)


def sort_findings(findings):
    return sorted(findings, key=lambda item: SEVERITY_ORDER[item["severity"]])


def covered(change, projection=None):
    """True if at least one rule covers this change's class and scope (else the decision is row R0: a person).

    Coverage is about whether a rule *applies*, not whether it fires: a source change to a known supplier is
    covered even when every check passes. Without a projection, one is built from the default data as of
    change["as_of"] (or today)."""
    if projection is None:
        projection = default_projection(change.get("as_of"))
    change_type, part = change.get("type"), change.get("part")
    if not change_type or not part:
        return False
    if change.get("at_supplier"):
        return change_type in subtier_types(projection, part)
    if change_type == "SourceChange" and change.get("to_supplier"):
        return True
    if certificate_policies(projection, change_type):
        return True
    if checking_policies(projection, change_type):
        return True
    if change_type == "CoatingChange" and change.get("new_coating"):
        return True
    if change_type == "MaterialChange" and change.get("new_material"):
        return True
    for requirement, _ in customer_requirements(projection, part):
        for predicate in ("requiresCustomerApprovalFor", "requiresNotificationFor", "requiresNoticeFor"):
            if change_type in projection.objects(requirement, predicate):
                return True
    return False


_projections = {}


def default_projection(as_of=None):
    from datetime import date
    try:
        from .factlog import default_log
        from .project import Projection
    except ImportError:
        from factlog import default_log
        from project import Projection
    as_of = as_of or date.today().isoformat()
    if as_of not in _projections:
        _projections[as_of] = Projection(extend_log(default_log()), as_of)
    return _projections[as_of]


# ---- contested values (#28) ------------------------------------------------------------------------------
# Two current values are a question for the person the policy names (Q-contradiction), never a gap and never
# a guess. Sources: (1) a functional value a rule read that the snapshot reports contested
# (projection.contested_reads, filled by Projection.objects); (2) a record the fact log stored as contested
# (factlog.write_record(on_conflict="contest")) that names an entity of this change.

def display_value(value):
    if isinstance(value, str) and value.startswith('"'):
        try:
            return str(json.loads(value))
        except ValueError:
            return value
    return value


def graph_object(raw):
    return Literal(json.loads(raw)) if isinstance(raw, str) and raw.startswith('"') else raw


def _fact_index(projection):
    found = getattr(projection, "_fact_index", None)
    if found is None:
        found = {fact["id"]: fact for fact in list(projection.current_facts) + list(projection.history_facts)}
        projection._fact_index = found
    return found


def _side_from_fact(fact, status):
    return {"value": display_value(fact["o"]), "raw": fact["o"], "fact_id": fact["id"], "record": fact["s"], "source": fact["source"],
            "quote": (fact.get("quote") or "").replace("\n", " "), "rank": fact.get("rank"),
            "valid_from": fact.get("valid_from"), "status": status}


def _snapshot_pair(projection, item):
    index = _fact_index(projection)
    sides = []
    for fact_id in item["facts"]:
        fact = index.get(fact_id)
        if fact:
            in_force = item.get("head") == fact_id
            sides.append(_side_from_fact(fact, "in force" if in_force else "contested, not in force"))
    owner = projection.value("Q-contradiction", "questionOwner")
    return {"key": list(item["key"]), "reason": item["reason"], "question": "Q-contradiction", "owner": owner,
            "sides": sides}


def _record_pair(entry, change_ids):
    question = entry["question"]
    current = [fact for fact in entry["current"] if fact["p"] not in ("type", "supersedes")]
    contested = [fact for fact in entry["contested"] if fact["p"] not in ("type", "supersedes")]
    mentioned = {fact["o"] for fact in current + contested}
    if change_ids and not mentioned & change_ids:
        return None
    current_by = {fact["p"]: fact for fact in current}
    differing = [fact for fact in contested if fact["p"] in current_by and current_by[fact["p"]]["o"] != fact["o"]]
    differing = differing or contested
    sides = [_side_from_fact(current_by[fact["p"]], "in force") for fact in differing if fact["p"] in current_by]
    sides += [_side_from_fact(fact, "contested, not in force") for fact in differing]
    predicate = differing[0]["p"] if differing else None
    return {"key": [question["current_record"], predicate], "reason": "contested_record",
            "records": [question["current_record"], question["contested_record"]],
            "question": question["id"], "owner": question["owner"], "class_name": question["class_name"],
            "owner_source": question["owner_source"], "owner_quote": question["owner_quote"], "sides": sides}


def _change_ids(change):
    return {change.get(key) for key in ("part", "to_supplier", "from_supplier", "at_supplier", "site",
                                          "new_material", "new_coating")} - {None}


def contested_pairs(projection, change):
    """Card key `contested`: both versions with source and quote. Same pairs the questions are built from."""
    pairs = getattr(projection, "contested_questioned", None)
    if pairs is None:
        pairs = _collect_contested(projection, change)
    return pairs


def _collect_contested(projection, change):
    pairs = [_snapshot_pair(projection, item) for item in getattr(projection, "contested_reads", {}).values()]
    change_ids = _change_ids(change)
    for entry in getattr(projection, "contested_records", None) or []:
        pair = _record_pair(entry, change_ids)
        if pair:
            pairs.append(pair)
    return [pair for pair in pairs if len(pair["sides"]) >= 2]


def side_text(side):
    return f"{side['value']} ({side['source']}, \"{side['quote']}\")"


def contested_questions(projection, change):
    """R7 questions "two current values: X (source, quote) vs Y (source, quote)", owner from data."""
    pairs = _collect_contested(projection, change)
    projection.contested_questioned = pairs
    findings = []
    for pair in pairs:
        subject, predicate = pair["key"]
        title = (f"Two current values for {subject} {predicate}: "
                 + " vs ".join(side_text(side) for side in pair["sides"]) + ". A person decides which one holds.")
        if pair["reason"] == "contested_record":
            item = finding("R7", "question", title, [], {"records": pair["records"], "question": pair["question"]},
                           owner=pair["owner"], note=f"{pair['records'][1]} CONTRADICTS {pair['records'][0]}; "
                                                     f"{pair['records'][0]} stays in force until decided")
            findings.append(item)
            continue
        evidence = [explain(projection, side["record"], predicate, graph_object(side["raw"]))
                    for side in pair["sides"] if side["status"] == "in force"]
        item = question(projection, "contradiction", title, evidence,
                        {"subject": subject, "facts": [side["fact_id"] for side in pair["sides"]]})
        item["note"] = ("neither value is in force" if pair["reason"] == "same_rank_same_date"
                        else "the higher-authority value stays in force; the newer lower-rank value is contested")
        findings.append(item)
    return findings
