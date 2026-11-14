"""Encode world A (eval/worlds/A/sources) as facts for the merged core (eval/worlds/A/core/facts.jsonl).

Ported from the cross-benchmark encoder (docs/benchmarks/crossbench/maksim_on_arseniy, written by a third-party
encoder agent "WITHOUT reading gold.jsonl"; the crossbench README discloses that encoders saw some gold), and
adapted 14 Nov by the eval track to the merged core's vocabulary: fact rows carry kind/epistemic/rank; customer
requirement clauses map to the core's 17 change classes; world-A policy facts (completeness, certificate) quote
world-A documents. World M's rules_data/ is NOT loaded for world A (ids collide: 8D-25-031 differs).
Every quote is checked to be a literal substring of its source file.

  python eval/tools/encode_A.py
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); EVAL = os.path.dirname(HERE)
SRC = os.path.join(EVAL, "worlds", "A", "sources")
OUT = os.path.join(EVAL, "worlds", "A", "core")
DOCS = {f[:-3]: open(os.path.join(SRC, f)).read() for f in sorted(os.listdir(SRC)) if f.endswith(".md")}
EFF = {"8D-25-031": "2026-10-02", "ASL-TO-2026-04": "2026-09-15", "BOM-STL-TORINO-27": "2026-08-31",
       "CP-BR220-R3": "2026-06-15", "CSR-STL-2026-02": "2026-01-01", "DWG-BR220-RevB": "2025-09-04",
       "DWG-BR220-RevC": "2026-06-01", "EML-SQ-2026-0814": "2026-08-14", "EML-SQ-2026-1105": "2026-11-05",
       "PRC-DEV-007": "2025-11-01"}
facts = []

def f(s, p, o, src, quote, vf=None, vt=None):
    facts.append({"s": s, "p": p, "o": o, "source": src, "quote": quote,
                  "valid_from": vf if vf is not None else EFF[src], "valid_to": vt, "kind": "assert",
                  "epistemic": "evidence", "rank": RANK.get(src, 2), "author": None})

RANK = {"CSR-STL-2026-02": 1, "EML-SQ-2026-0814": 3, "EML-SQ-2026-1105": 3}

def lit(x):
    return json.dumps(x)

# --- documents as records
for doc_id in DOCS:
    f(doc_id, "type", "Document", doc_id, f"doc_id: {doc_id}",
      vt="2026-05-31" if doc_id == "DWG-BR220-RevB" else None)
f("DWG-BR220-RevC", "supersedes", "DWG-BR220-RevB", "DWG-BR220-RevC", "supersedes: DWG-BR220-RevB")

# --- customers, programs, sites (BOM, CSR, ASL)
f("CUST-STL", "type", "Customer", "ASL-TO-2026-04", "Stellantis (STL)")
f("CUST-STL", "label", lit("Stellantis"), "ASL-TO-2026-04", "Stellantis (STL)")
f("CUST-CLM", "type", "Customer", "ASL-TO-2026-04", "Cantieri Lombardi Mobility S.p.A. (CLM)")
f("CUST-CLM", "label", lit("Cantieri Lombardi Mobility S.p.A."), "ASL-TO-2026-04", "Cantieri Lombardi Mobility S.p.A. (CLM)")
for prg, q in [("STL-Torino-27", "Annex A: programs STL-Torino-27 and STL-Torino-31."),
               ("STL-Torino-31", "Annex A: programs STL-Torino-27 and STL-Torino-31.")]:
    f(prg, "type", "Program", "CSR-STL-2026-02", q)
    f(prg, "forCustomer", "CUST-STL", "CSR-STL-2026-02", q)
f("STL-Torino-27", "forCustomer", "CUST-STL", "BOM-STL-TORINO-27", "Program: STL-Torino-27\nCustomer: Stellantis (STL)")
f("CLM-Lombardia-26", "type", "Program", "BOM-STL-TORINO-27", "belongs to program CLM-Lombardia-26 for customer CLM at TO2")
f("CLM-Lombardia-26", "forCustomer", "CUST-CLM", "BOM-STL-TORINO-27", "belongs to program CLM-Lombardia-26 for customer CLM at TO2")
for site, q in [("TO1", "Torino Plant 1 (TO1)"), ("TO2", "Torino Plant 2 (TO2)"), ("TO3", "Torino Plant 3 (TO3)")]:
    f(site, "type", "Site", "ASL-TO-2026-04", q)

# --- customer requirement CSR-STL-2026-02 (clause -> closest Maksim change type)
C = "CSR-STL-2026-02"
f(C, "type", "CustomerRequirement", C, "doc_id: CSR-STL-2026-02")
f("CUST-STL", "imposes", C, C, "These requirements apply to every part delivered to Stellantis for a program listed in Annex A.")
Q8561 = "8.5.6.1 A change of material source, of a sub-supplier, or of the manufacturing location of a sub-supplier needs a documented risk analysis and written approval from Stellantis before any shipment of affected parts."
Q8361 = "8.3.6.1 Any change to a requirement stated on a customer drawing, including material and finish, needs written approval from Stellantis before the change is implemented."
Q8421 = "8.4.2.1 A change of subcontracted process, including surface treatment, needs notification to Stellantis and approval before shipment."
Q8333 = "8.3.3.3 Any change to a characteristic designated special, to its control method or to its sampling frequency needs written approval from Stellantis before the change is implemented."
Q71532 = "7.1.5.3.2 Verification of a special characteristic by an external laboratory needs prior notification to Stellantis and acceptance of the laboratory scope."
for change_type, quote in [("SourceChange", Q8561), ("SubTierSupplierChange", Q8561), ("LocationChange", Q8561),
                           ("MaterialChange", Q8361), ("CoatingChange", Q8361), ("DesignChange", Q8361),
                           ("SpecialProcessChange", Q8421), ("TestMethodChange", Q8333), ("TestMethodChange", Q71532)]:
    f(C, "requiresCustomerApprovalFor", change_type, C, quote)

# --- materials
f("Series6xxx", "type", "AlloySeries", "DWG-BR220-RevC", "alloy group 6xxx, Al-Mg-Si")
for mat, aly, src, q in [("MAT-6082-T6", "ALY-6082", "DWG-BR220-RevC", "EN AW-6082-T6 billet (alloy group 6xxx, Al-Mg-Si)"),
                         ("MAT-6061-T6", "ALY-6061", "8D-25-031", "EN AW-6061-T6 (alloy group 6xxx)")]:
    f(mat, "type", "AlloyTemper", src, q); f(mat, "label", lit(q.split(" (")[0].replace(" billet", "")), src, q)
    f(mat, "temperOf", aly, src, q); f(aly, "type", "Alloy", src, q); f(aly, "inSeries", "Series6xxx", src, q)
f("MAT-5083-H111", "type", "AlloyTemper", "BOM-STL-TORINO-27", "EN AW-5083-H111")
f("MAT-5083-H111", "temperOf", "ALY-5083", "BOM-STL-TORINO-27", "EN AW-5083-H111")
f("ALY-5083", "type", "Alloy", "BOM-STL-TORINO-27", "EN AW-5083-H111")
f("MAT-S355J2", "type", "Steel", "ASL-TO-2026-04", "bar grade S355J2")
f("MAT-CUZN39PB3", "type", "Material", "BOM-STL-TORINO-27", "material CuZn39Pb3")

# --- parts
B = "BOM-STL-TORINO-27"
for part, line, mat in [("BR-180", "BOM-LINE 110: part BR-180 (drawing Rev F); program STL-Torino-27; customer STL; material EN AW-6061-T6", "MAT-6061-T6"),
                        ("BR-220", "BOM-LINE 120: part BR-220 (drawing Rev C); program STL-Torino-27; customer STL; material EN AW-6082-T6", "MAT-6082-T6"),
                        ("CV-015", "BOM-LINE 130: part CV-015 (drawing Rev A); program STL-Torino-27; customer STL; material CuZn39Pb3", "MAT-CUZN39PB3")]:
    f(part, "type", "Part", B, line); f(part, "usedIn", "STL-Torino-27", B, line); f(part, "madeOf", mat, B, line)
q = "BR-310 (EN AW-5083-H111, milled pocket, no fastener holes) belongs to program CLM-Lombardia-26 for customer CLM at TO2"
f("BR-310", "type", "Part", B, q); f("BR-310", "usedIn", "CLM-Lombardia-26", B, q); f("BR-310", "madeOf", "MAT-5083-H111", B, q)
f("HS-040", "type", "Part", "ASL-TO-2026-04", "part HS-040; plant TO2; customer CLM")
R = "DWG-BR220-RevC"
f("BR-220", "madeOf", "MAT-6082-T6", R, "1. Material: EN AW-6082-T6 billet")
f("BR-220", "drawingRevision", lit("C"), R, "Revision: C")
f("BR-220", "hasSpecialCharacteristic", "SC-01", R, "SPECIAL CHARACTERISTIC SC-01")
f("SC-01", "type", "SpecialCharacteristic", R, "2. Yield strength Rp0.2 >= 250 MPa. SPECIAL CHARACTERISTIC SC-01")
f("SC-01", "label", lit("Yield strength Rp0.2 >= 250 MPa"), R, "Yield strength Rp0.2 >= 250 MPa")
f("SC-01", "minYieldMPa", lit("250"), R, "Yield strength Rp0.2 >= 250 MPa")
f("SC-01", "minYieldMPa", lit("250"), "CP-BR220-R3", ">= 250 MPa, SPECIAL CHARACTERISTIC SC-01")
f("COAT-ANOD-II", "type", "Coating", R, "anodise type II, thickness 10 to 15 micrometres, black, per specification SPEC-FIN-12")
f("BR-220", "hasCoating", "COAT-ANOD-II", R, "4. Finish: anodise type II")
# superseded drawing Rev B: valid only until withdrawal
RB = "DWG-BR220-RevB"
f("BR-220", "madeOf", "MAT-6061-T6", RB, "1. Material: EN AW-6061-T6 billet.", vt="2026-05-31")
f("BR-220", "drawingRevision", lit("B"), RB, "Revision: B", vt="2026-05-31")

# --- suppliers (location-qualified: ASL says approval covers the named manufacturing location only)
A = "ASL-TO-2026-04"
for sup, name, q in [("SUP-AB", "Alluminio B S.r.l. (Settimo Torinese)", "Alluminio B S.r.l. (Settimo Torinese)"),
                     ("SUP-MC", "Meccanica C S.p.A. (Chieri)", "Meccanica C S.p.A. (Chieri)"),
                     ("SUP-FD", "Ferrotec D S.r.l. (Pinerolo)", "Ferrotec D S.r.l. (Pinerolo)"),
                     ("SUP-TE", "Trafilerie E S.p.A. (Biella)", "Trafilerie E S.p.A. (Biella)")]:
    f(sup, "type", "Supplier", A, q); f(sup, "label", lit(name), A, q)
f("SUP-AV", "type", "Supplier", "CP-BR220-R3", "subcontracted to Anodica Veneta S.r.l.")
f("SUP-AV", "label", lit("Anodica Veneta S.r.l."), "CP-BR220-R3", "subcontracted to Anodica Veneta S.r.l.")

# --- approvals (ASL rows) and the billet grade each approved source delivers (-> SupplierCapability)
SUPMAP = {"Alluminio B S.r.l. (Settimo Torinese)": "SUP-AB", "Meccanica C S.p.A. (Chieri)": "SUP-MC",
          "Ferrotec D S.r.l. (Pinerolo)": "SUP-FD", "Trafilerie E S.p.A. (Biella)": "SUP-TE"}
MATMAP = {"EN AW-6082-T6": "MAT-6082-T6", "EN AW-6061-T6": "MAT-6061-T6", "EN AW-5083-H111": "MAT-5083-H111",
          "S355J2": "MAT-S355J2", "CuZn39Pb3": "MAT-CUZN39PB3"}
CUSTMAP = {"STL": "CUST-STL", "CLM": "CUST-CLM"}
import re
for line in DOCS[A].splitlines():
    m = re.match(r"APPROVAL (AP-\d+): part (\S+); plant (\S+); customer (\S+); supplier (.+?); \w+ grade ([^;]+); status APPROVED (\d{4}-\d\d-\d\d)", line)
    if not m:
        continue
    ap, part, plant, cust, sup, grade, date = m.groups()
    for p, o in [("type", "PartApproval"), ("approvedSupplier", SUPMAP[sup]), ("approvedPart", part),
                 ("approvedSite", plant), ("approvedForCustomer", CUSTMAP[cust]), ("status", lit("approved"))]:
        f(ap, p, o, A, line, vf=date)
    cap = "CAP-" + ap
    for p, o in [("type", "SupplierCapability"), ("capableSupplier", SUPMAP[sup]), ("capableMaterial", MATMAP[grade])]:
        f(cap, p, o, A, line, vf=date)
f("ASL-TO-2026-04", "supersedes", "ASL-TO-2026-03", A, "supersedes: ASL-TO-2026-03")

# --- supplier standing (probation -> Maksim status "conditional")
E1, E2 = "EML-SQ-2026-0814", "EML-SQ-2026-1105"
for p, o in [("type", "SupplierQualification"), ("qualifiedSupplier", "SUP-MC"), ("status", lit("conditional"))]:
    f("QS-MC-2026-08", p, o, E1, "effective today Meccanica C S.p.A. is on probation (supplier rating C minus)")
for p, o in [("type", "SupplierQualification"), ("qualifiedSupplier", "SUP-MC"), ("status", lit("approved")),
             ("supersedes", "QS-MC-2026-08")]:
    f("QS-MC-2026-11", p, o, E2, "La probation comunicata con EML-SQ-2026-0814 e' revocata da oggi.")
# NOT encoded on purpose: EML-SQ-2026-1105 'per il BR-220 il materiale e' EN AW-6061-T6 ...' (informal restatement
# of drawing Rev B; Maksim's own world encodes emails without part-master facts, e.g. EML-2026-10-29 facts=[])

# --- 8D
D = "8D-25-031"
f(D, "type", "EightD", D, "# 8D Report 8D-25-031")
f(D, "concernsSupplier", "SUP-MC", D, "issuer: Meccanica C S.p.A. (Chieri)")
f(D, "concernsMaterial", "MAT-6061-T6", D, "machined brackets made from EN AW-6061-T6 (alloy group 6xxx)")
f(D, "concernsPart", "BK-077", D, "Part: BK-077")
f(D, "status", lit("open"), D, "status: OPEN")

# --- deviation history (PRC-DEV-007 section 4); limits in section 2 have no engine concept
f("DEV-2025-019", "type", "Deviation", "PRC-DEV-007", "DEV-2025-019 (part HS-040, 600 pieces, 3 weeks) was approved on 2025-12-09.", vf="2025-12-09", vt="2025-12-30")
f("DEV-2025-019", "concernsPart", "HS-040", "PRC-DEV-007", "DEV-2025-019 (part HS-040, 600 pieces, 3 weeks)", vf="2025-12-09", vt="2025-12-30")

# --- features (BOM) and the 8D's failure feature: the 8D level policy itself is not stated in any A document,
# so the core's built-in default applies
f("FEAT-FASTENER-HOLE", "type", "Feature", B, "features: 4 fastener holes")
f("FEAT-FASTENER-HOLE", "label", lit("fastener holes"), B, "features: 4 fastener holes")
f("BR-180", "hasFeature", "FEAT-FASTENER-HOLE", B, "BOM-LINE 110: part BR-180 (drawing Rev F); program STL-Torino-27; customer STL; material EN AW-6061-T6; features: 4 fastener holes")
f("BR-220", "hasFeature", "FEAT-FASTENER-HOLE", B, "BOM-LINE 120: part BR-220 (drawing Rev C); program STL-Torino-27; customer STL; material EN AW-6082-T6; features: 4 fastener holes")
f(D, "failureFeature", "FEAT-FASTENER-HOLE", D, "Cracks at fastener holes found on machined brackets made from EN AW-6061-T6 (alloy group 6xxx).")

# --- world-A policy facts (same policy kinds as the core's rules_data for world M, quoted from A documents)
QC = "This record is the complete list of approved material sources for the parts, plants and customers in scope."
QS = "Scope: series production parts released at Torino Plant 1 (TO1) and Torino Plant 2 (TO2) for customers Stellantis (STL) and Cantieri Lombardi Mobility S.p.A. (CLM)."
f("CS-ASL-A", "type", "CompletenessStatement", A, QC)
for plant in ("TO1", "TO2"):
    f("CS-ASL-A", "completeForPlant", plant, A, QS)
for cust in ("CUST-STL", "CUST-CLM"):
    f("CS-ASL-A", "completeForCustomer", cust, A, QS)
f("CS-ASL-A", "completeForScope", lit("series"), A, QS)
QCERT = "5. Material certificate EN 10204 type 3.1 required with each lot."
f("POL-A-CERT", "type", "Policy", R, QCERT)
f("POL-A-CERT", "statedIn", R, R, QCERT)
for change_type in ("SourceChange", "MaterialChange"):  # the same classes as the core's world-M policies
    f("POL-A-CERT", "requiresCertificateFor", change_type, R, QCERT)

# --- validate quotes
bad = [x for x in facts if x["quote"] not in DOCS[x["source"]]]
for x in bad:
    print("QUOTE NOT FOUND", x["source"], repr(x["quote"]))
if bad:
    sys.exit(1)
for i, x in enumerate(facts):
    x["id"] = f"A{i:04d}"
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "facts.jsonl"), "w") as out:
    for x in facts:
        out.write(json.dumps(x) + "\n")
with open(os.path.join(OUT, "key_names.json"), "w") as out:
    json.dump({"SUP-MC": "Meccanica C", "SUP-AB": "Alluminio B", "SUP-FD": "Ferrotec D", "SUP-TE": "Trafilerie E",
               "SUP-AV": "Anodica Veneta"}, out, indent=1)
# registries for the core parser (names as the A documents write them), used by condition C
REGISTRIES = {
    "parts": {"rows": [["BR-180", "BR-180 bracket"], ["BR-220", "BR-220 bracket"], ["BR-310", "BR-310 bracket"],
                       ["CV-015", "CV-015"], ["HS-040", "HS-040"]]},
    "suppliers": {"rows": [["SUP-AB", "Alluminio B S.r.l."], ["SUP-MC", "Meccanica C S.p.A."],
                           ["SUP-FD", "Ferrotec D S.r.l."], ["SUP-TE", "Trafilerie E S.p.A."],
                           ["SUP-AV", "Anodica Veneta S.r.l."]]},
    "sites": {"rows": [["TO1", "Torino Plant 1"], ["TO2", "Torino Plant 2"], ["TO3", "Torino Plant 3"]]},
    "materials": {"rows": [["MAT-6082-T6", "EN AW-6082-T6"], ["MAT-6061-T6", "EN AW-6061-T6"],
                           ["MAT-5083-H111", "EN AW-5083-H111"], ["MAT-S355J2", "S355J2"],
                           ["MAT-CUZN39PB3", "CuZn39Pb3"]]},
    "coatings": {"rows": [["COAT-ANOD-II", "anodise type II"]]},
    "customers": {"rows": [["CUST-STL", "Stellantis"], ["CUST-CLM", "Cantieri Lombardi Mobility S.p.A."]]},
}
with open(os.path.join(OUT, "registries.json"), "w") as out:
    json.dump(REGISTRIES, out, indent=1)
with open(os.path.join(OUT, "aliases.json"), "w") as out:
    json.dump({"Meccanica C": "SUP-MC", "Alluminio B": "SUP-AB", "Alluminio B (Settimo Torinese)": "SUP-AB",
               "Anodica Veneta": "SUP-AV", "EN AW-6061-T6": "MAT-6061-T6", "EN AW-6082-T6": "MAT-6082-T6"}, out, indent=1)
print(f"{len(facts)} facts, all quotes literal substrings of {len(DOCS)} sources")
