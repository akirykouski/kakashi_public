"""Builds rules_data/facts.jsonl and rules_data/corpus.jsonl: the policy facts the rules read (workstream R).

Rules never hard-code a policy quote, an owner id, a policy level or a completeness scope: they read these facts.
Every fact quotes its source verbatim; the build fails if a quote is not literally in the source text.
Sources: QP-11 and QP-14 (data/corpus.jsonl, prototype copy), 8D-25-031 and FMEA-BR220 (same), and QP-15
(rules_data/docs/QP-15.md, a synthetic procedure of the fictional company, written 14 Nov 2026).

  python rules_data/build.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def read_doc(path):
    text = open(path).read()
    _, header, body = text.split("---\n", 2)
    fields = {}
    for line in header.splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("'")
    return fields, body.rstrip("\n")


def corpus():
    items = {}
    with open(os.path.join(ROOT, "data", "corpus.jsonl")) as file:
        for line in file:
            item = json.loads(line)
            items[item["id"]] = item
    fields, body = read_doc(os.path.join(HERE, "docs", "QP-15.md"))
    items["QP-15"] = {"id": "QP-15", "type": fields["type"], "title": fields["title"], "date": fields["date"],
                      "valid_from": fields["valid_from"], "valid_to": None, "supersedes": None, "rank": 3,
                      "text": body}
    return items


QP11_41 = "4.1 A supplier audit qualifies the supplier as a company. It does not approve the supplier for any\npart."
QP11_42 = ("4.2 A supplier may deliver a part only if the approved supplier list contains an approval for that\n"
           "supplier, that part, the receiving site and the customer.")
QP11_43 = "4.3 A supplier with status conditional may not receive new parts."
QP11_44 = ("4.4 A change of source requires a material certificate (EN 10204 type 3.1) from the new supplier for\n"
           "the drawing material.")
QP11_CERT_OWNER = "Missing certificates are an open question for the supplier quality engineer."
QP14_42 = "4.2 The supplier passes every sub-supplier change notice to Valsangone before the change is implemented."
QP14_43 = ("4.3 The plant checks the notice against the customer requirement for the part and informs the "
           "customer, or asks for written approval, before the first shipment.")
QP14_44 = ("4.4 A change at a supplier whose link to a supplier of the part is not on file is an open "
           "question for the supplier quality engineer.")


def qp15(number):
    for line in CORPUS["QP-15"]["text"].splitlines():
        if line.startswith(number + " "):
            return line
    raise KeyError(number)


CORPUS = corpus()


def facts():
    rows = []

    def add(s, p, o, source, quote, valid_from=None, literal=False):
        rows.append({"s": s, "p": p, "o": json.dumps(o) if literal else o, "source": source, "quote": quote,
                     "valid_from": valid_from, "valid_to": None, "kind": "assert", "epistemic": "evidence", "rank": 2,
                     "author": None,
                     "id": f"RD{len(rows):04d}"})

    # Policy statements each rule rests on (rule code names the policy id, never the text).
    policies = {"POL-QP11-4.1": ("QP-11", QP11_41), "POL-QP11-4.2": ("QP-11", QP11_42),
                "POL-QP11-4.3": ("QP-11", QP11_43), "POL-QP11-4.4": ("QP-11", QP11_44),
                "POL-QP14-4.2": ("QP-14", QP14_42), "POL-QP14-4.3": ("QP-14", QP14_43),
                "POL-QP14-4.4": ("QP-14", QP14_44)}
    for number in ("1.1", "1.2", "2.1", "2.2", "3.1", "3.5", "4.1"):
        policies[f"POL-QP15-{number}"] = ("QP-15", qp15(number))
    for policy, (source, quote) in policies.items():
        add(policy, "type", "Policy", source, quote)
        add(policy, "statedIn", source, source, quote)

    # Change classes a sub-tier change can be (QP-14 4.1): R8 covers these at any sub-supplier.
    qp14_41 = "4.1 A change of material, manufacturing process, coating or source at any sub-supplier of a part is a change of that part."
    for change_type in ("MaterialChange", "ProcessChange", "CoatingChange", "SourceChange", "SubTierSupplierChange"):
        add("POL-QP14-4.1", "subTierCovers", change_type, "QP-14", qp14_41)

    # Which change classes need a material certificate (keyed on change class, not on "new supplier").
    add("POL-QP11-4.4", "requiresCertificateFor", "SourceChange", "QP-11", QP11_44)
    add("POL-QP15-3.1", "requiresCertificateFor", "MaterialChange", "QP-15", qp15("3.1"))
    # Change classes the procedure examines even when no customer requirement names them (rules.covered()).
    add("POL-QP15-4.1", "checksChangeType", "ScheduleChange", "QP-15", qp15("4.1"))

    # Open-8D policy level: alloy | series | series+feature (exact alloy always counts, QP-15 1.2).
    add("POL-QP15-1.1", "policyValue", "series+feature", "QP-15", qp15("1.1"), literal=True)
    add("POL-QP15-1.1", "policyFor", "OpenIssueLevel", "QP-15", qp15("1.1"))

    # Failure features: the 8D's failure and the part's feature at risk.
    add("8D-25-031", "failureFeature", "FEAT-FASTENING-HOLE", "8D-25-031", "cracks around fastening holes",
        valid_from="2025-03-20")
    add("BR-220", "hasFeature", "FEAT-FASTENING-HOLE", "FMEA-BR220", "crack at the fastening holes under fatigue load")

    # Completeness of the approved supplier list: plant x customer x commodity (alloy series) x scope.
    # An absent dimension means "all".
    statement = "CS-ASL-SERIES"
    quote = qp15("2.1")
    add(statement, "type", "CompletenessStatement", "QP-15", quote)
    add(statement, "completeForPlant", "PLT-BEI", "QP-15", quote)
    add(statement, "completeForPlant", "PLT-PIN", "QP-15", quote)
    add(statement, "completeForScope", "series", "QP-15", quote, literal=True)
    # No completeForCustomer / completeForSeries: the statement covers every customer and commodity.
    # A narrower list states them (completeForCustomer CUST-x, completeForSeries Series6xxx).

    # Owners of open questions, by kind of missing data.
    owners = [("Q-material_certificate", "PER-GALLO", "QP-11", QP11_CERT_OWNER),
              ("Q-tier_link", "PER-GALLO", "QP-14", QP14_44),
              ("Q-source_release", "PER-GALLO", "QP-15", qp15("2.2")),
              ("Q-material_data", "PER-ROSSI", "QP-15", qp15("3.2")),
              ("Q-material_strength", "PER-ROSSI", "QP-15", qp15("3.6")),
              ("Q-coating_substances", "PER-ROMANO", "QP-15", qp15("3.3")),
              ("Q-supplier_record", "PER-GALLO", "QP-15", qp15("3.4"))]
    for question, person, source, quote in owners:
        add(question, "questionOwner", person, source, quote)
    return rows


def main():
    rows = facts()
    for row in rows:
        if row["quote"] not in CORPUS[row["source"]]["text"]:
            raise SystemExit(f"quote not in {row['source']}: {row['quote']!r}")
    with open(os.path.join(HERE, "facts.jsonl"), "w") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")
    with open(os.path.join(HERE, "corpus.jsonl"), "w") as file:
        file.write(json.dumps(CORPUS["QP-15"]) + "\n")
    print(f"{len(rows)} policy facts")


if __name__ == "__main__":
    main()
