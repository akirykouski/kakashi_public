"""Checks a proposed change against company memory. The checks are deductive: they query the OWL 2 RL
closure (inferred links like part -> customer requirement) and never ask a language model.

A change is a dict:
  type          SourceChange | MaterialChange | ProcessChange | CoatingChange | ScheduleChange | PackagingChange
  part          part id, e.g. BR-220
  to_supplier   new supplier id (source change), may be an unknown name
  from_supplier current supplier id (optional)
  site          our receiving site (optional; default = sites where the part is approved today)
  new_material  material id (material change)
  new_coating   coating id or free text (coating change)

Rules (see docs in ontology/RULES.md):
  R1a supplier qualification   R1b part approval       R2 customer approval (PPAP)
  R3 supplier issue on the part's alloy                R5 restricted substance (law)
  R6 material capability / special characteristic       R7 missing evidence -> question with owner
  R4 supersession is applied by the projection; findings show what was replaced (info).
"""
import json
import os

from rdflib import Literal

from explain import explain
from project import ROOT, local_name

APPROVAL_CHANGE_TYPES = {"SourceChange", "MaterialChange", "ProcessChange", "CoatingChange"}
SEVERITY_ORDER = {"blocker": 0, "warning": 1, "question": 2, "info": 3}

_corpus = {}


def corpus():
    if not _corpus:
        with open(os.path.join(ROOT, "data", "corpus.jsonl")) as file:
            for line in file:
                item = json.loads(line)
                _corpus[item["id"]] = item
    return _corpus


def cite(source, quote):
    """A citation of policy text. Fails loudly if the quote is not literally in the source."""
    text = corpus()[source]["text"]
    if quote not in text:
        raise ValueError(f"quote not found in {source}: {quote!r}")
    return {"triple": f"policy {source}", "inferred": False, "fact_id": None, "source": source, "quote": quote}


def finding(rule, severity, title, evidence, entities, owner=None, note=None):
    return {"rule": rule, "severity": severity, "title": title,
            "evidence": [step for step in evidence if step], "entities": entities, "owner": owner, "note": note}


# ---- graph helpers ---------------------------------------------------------------------------------------

def records_of(projection, class_name, predicate, value):
    rows = projection.query(
        f"SELECT ?record WHERE {{ ?record a lcc:{class_name} ; lcc:{predicate} ?value }}", value=value)
    return sorted(local_name(row[0]) for row in rows)


def approvals(projection, supplier=None, part=None):
    """Current part-approval records as dicts."""
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
    """Info about records that replaced older ones (the red edge in the UI)."""
    notes = []
    for record in record_ids:
        for older in projection.objects(record, "supersedes"):
            older_facts = projection.history_by_subject.get(older, [])
            status = next((json.loads(fact["o"]) for fact in older_facts if fact["p"] == "status"), None)
            notes.append(f"{record} supersedes {older}" + (f" (was: {status})" if status else ""))
    return notes


# ---- rules -----------------------------------------------------------------------------------------------

def rule_supplier_qualification(projection, change):
    supplier = change["to_supplier"]
    records = records_of(projection, "SupplierQualification", "qualifiedSupplier", supplier)
    if not records:
        return []
    findings = []
    for record in records:
        status = projection.value(record, "status")
        evidence = [explain(projection, record, "qualifiedSupplier", supplier),
                    explain(projection, record, "status", Literal(status))]
        notes = history_note(projection, [record])
        if status in ("conditional", "disqualified"):
            evidence.append(cite("QP-11", "4.3 A supplier with status conditional may not receive new parts."))
            findings.append(finding("R1a", "blocker",
                                    f"{projection.label(supplier)} is {status} as a supplier: no new parts",
                                    evidence, {"supplier": supplier, "record": record}, note="; ".join(notes) or None))
        elif notes:
            evidence.append(cite("QP-11", "4.1 A supplier audit qualifies the supplier as a company. It does not approve the supplier for any\npart."))
            findings.append(finding("R4", "info",
                                    f"Supplier qualification of {projection.label(supplier)} was replaced: "
                                    f"{'; '.join(notes)}. This does not approve any part.",
                                    evidence, {"supplier": supplier, "record": record}))
    return findings


def target_sites(projection, change, customer):
    if change.get("site"):
        return [change["site"]]
    sites = sorted({item["site"] for item in approvals(projection, part=change["part"])
                    if item["customer"] == customer and item["status"] == "approved"})
    return sites


def rule_part_approval(projection, change):
    supplier, part = change["to_supplier"], change["part"]
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
            evidence.append(cite("QP-11", "4.2 A supplier may deliver a part only if the approved supplier list contains an approval for that\nsupplier, that part, the receiving site and the customer."))
            only = ", ".join(sorted({f"{item['part']}@{item['site']}" for item in others}))
            revoked = [item["id"] for item in matching if item["status"] == "revoked"]
            title = f"{projection.label(supplier) if projection.is_a(supplier, 'Supplier') else supplier} " \
                    f"has no approval for {part} at {site} for {projection.label(customer)}"
            if revoked:
                title += f" (approval revoked: {', '.join(revoked)})"
            elif only:
                title += f" (approved only for {only})"
            findings.append(finding("R1b", "blocker", title, evidence,
                                    {"supplier": supplier, "part": part, "site": site, "customer": customer}))
    return findings


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


def rule_customer_approval(projection, change):
    change_type, part = change["type"], change["part"]
    if change_type not in APPROVAL_CHANGE_TYPES:
        return []
    deviation = covering_deviation(projection, change, change_type)
    findings = []
    already_approved = {}
    if change_type == "SourceChange" and change.get("to_supplier"):
        for item in approvals(projection, supplier=change["to_supplier"], part=part):
            if item["status"] == "approved" and (not change.get("site") or item["site"] == change["site"]):
                already_approved[item["customer"]] = item["id"]
    customers_of_requirement = {}
    for customer in projection.objects(part, "deliveredTo"):
        for requirement in projection.objects(customer, "imposes"):
            customers_of_requirement[requirement] = customer
    for requirement in projection.objects(part, "subjectTo"):
        if not projection.is_a(requirement, "CustomerRequirement"):
            continue
        customer = customers_of_requirement.get(requirement)
        if customer in already_approved:
            record = already_approved[customer]
            findings.append(finding("R2", "info",
                                    f"{change['to_supplier']} is already an approved source of {part} for "
                                    f"{projection.label(customer)} ({record}); no new customer approval needed",
                                    [explain(projection, record, "approvedForCustomer", customer)],
                                    {"requirement": requirement, "customer": customer, "record": record}))
            continue
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
            note = "; ".join(history_note(projection, [requirement])) or None
            findings.append(finding("R2", "blocker",
                                    f"{change_type} on {part} needs written customer approval (PPAP resubmission) "
                                    f"before shipping, per {requirement}", evidence,
                                    {"requirement": requirement, "change_type": change_type,
                                     "customer": customer}, note=note))
        elif change_type in projection.objects(requirement, "requiresNotificationFor"):
            evidence = [explain(projection, part, "subjectTo", requirement),
                        explain(projection, requirement, "requiresNotificationFor", change_type)]
            findings.append(finding("R2", "info", f"{change_type} on {part}: notify the customer per {requirement}",
                                    evidence, {"requirement": requirement}))
    return findings


def deviation_end(projection, deviation):
    facts = [fact for fact in projection.current_facts if fact["s"] == deviation]
    return facts[0]["valid_to"] if facts else "?"


def rule_supplier_issue(projection, change):
    supplier, part = change["to_supplier"], change["part"]
    rows = projection.query(
        """SELECT DISTINCT ?issue ?material WHERE {
               ?supplier lcc:hasIssue ?issue .
               ?issue lcc:status "open" ; lcc:concernsMaterial ?material .
               { ?part lcc:madeOf ?material } UNION { ?part lcc:madeOfAlloy ?material }
           }""", supplier=supplier, part=part)
    findings = []
    seen = set()
    for issue_term, material_term in rows:
        issue = local_name(issue_term)
        material = local_name(material_term)
        seen.add(issue)
        link = "madeOf" if material in projection.objects(part, "madeOf") else "madeOfAlloy"
        evidence = [explain(projection, supplier, "hasIssue", issue),
                    explain(projection, issue, "concernsMaterial", material),
                    explain(projection, part, link, material)]
        findings.append(finding("R3", "warning",
                                f"{projection.label(supplier)} has open {issue} on {projection.label(material)}, "
                                f"the material of {part}", evidence,
                                {"supplier": supplier, "issue": issue, "material": material}))
    direct = projection.query(
        """SELECT DISTINCT ?issue WHERE { ?supplier lcc:hasIssue ?issue . ?issue lcc:status "open" ;
               lcc:concernsPart ?part }""", supplier=supplier, part=part)
    for (issue_term,) in direct:
        issue = local_name(issue_term)
        if issue in seen:
            continue
        evidence = [explain(projection, supplier, "hasIssue", issue), explain(projection, issue, "concernsPart", part)]
        findings.append(finding("R3", "warning", f"{projection.label(supplier)} has open {issue} on {part}",
                                evidence, {"supplier": supplier, "issue": issue}))
    return findings


def rule_restricted_substance(projection, change):
    coating, part = change.get("new_coating"), change["part"]
    if not coating:
        return []
    if not projection.is_a(coating, "Coating"):
        return [finding("R7", "question",
                        f"Coating '{coating}' is not in the coating catalogue: its substances are unknown",
                        [], {"coating": coating, "missing": "coating_substances"}, owner="PER-ROMANO")]
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
    part, new_material = change["part"], change.get("new_material")
    if not new_material:
        return []
    if not projection.is_a(new_material, "Material"):
        return [finding("R7", "question", f"Material '{new_material}' is not in the material master",
                        [], {"material": new_material, "missing": "material_data"}, owner="PER-ROSSI")]
    characteristic, minimum = special_characteristic_yield(projection, part)
    if not characteristic:
        return []
    typical = projection.value(new_material, "typicalYieldMPa")
    if typical is None:
        return [finding("R7", "question",
                        f"No strength data for {projection.label(new_material)}; {part} has special characteristic "
                        f"{characteristic} (minimum {minimum:.0f} MPa)",
                        [explain(projection, part, "hasSpecialCharacteristic", characteristic)],
                        {"material": new_material, "missing": "material_strength"}, owner="PER-ROSSI")]
    if float(typical) >= minimum:
        return []
    evidence = [explain(projection, part, "hasSpecialCharacteristic", characteristic)]
    return [finding("R6", "blocker",
                    f"{projection.label(new_material)} (typical yield {typical} MPa) is below the special "
                    f"characteristic {characteristic} of {part} (minimum {minimum:.0f} MPa)",
                    evidence, {"material": new_material, "characteristic": characteristic})]


def rule_missing_certificate(projection, change):
    supplier, part = change["to_supplier"], change["part"]
    material = projection.value(part, "madeOf")
    certificates = records_of(projection, "MaterialCertificate", "certSupplier", supplier)
    if any(projection.value(record, "certMaterial") == material for record in certificates):
        return []
    return [finding("R7", "question",
                    f"No material certificate (EN 10204 3.1) from {projection.label(supplier)} for "
                    f"{projection.label(material)} on file. Not a violation: an open question.",
                    [cite("QP-11", "Missing certificates are an open question for the supplier quality engineer.")],
                    {"supplier": supplier, "material": material, "missing": "material_certificate"},
                    owner="PER-GALLO")]


def check(projection, change):
    findings = []
    supplier = change.get("to_supplier")
    if change["type"] == "SourceChange" and supplier:
        if not projection.is_a(supplier, "Supplier"):
            findings.append(finding("R7", "question",
                                    f"Supplier '{supplier}' is not in our supplier master: no audit, capability or "
                                    f"approval on record", [], {"supplier": supplier, "missing": "supplier_record"},
                                    owner="PER-GALLO"))
            findings += rule_part_approval(projection, change)
        else:
            findings += rule_supplier_qualification(projection, change)
            findings += rule_part_approval(projection, change)
            findings += rule_material_capability(projection, change)
            findings += rule_supplier_issue(projection, change)
            findings += rule_missing_certificate(projection, change)
    findings += rule_customer_approval(projection, change)
    if change["type"] == "CoatingChange":
        findings += rule_restricted_substance(projection, change)
    if change["type"] == "MaterialChange":
        findings += rule_material_change(projection, change)
    findings.sort(key=lambda item: SEVERITY_ORDER[item["severity"]])
    return findings
