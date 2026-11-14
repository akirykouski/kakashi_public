"""The fictional mini-company behind the demo and the benchmark.

Valsangone Componenti S.p.A., a tier-1 supplier near Turin, machines aluminium brackets and buys steel,
cast and plastic parts for two fictional vehicle makers. Every company, person, part and document here is
invented. Standards are paraphrased in our own words; EU law (ELV directive) is quoted.

Two kinds of sources:
  * REGISTRIES: tables exported from internal systems (one row = one record). The quote for a fact is the
    CSV row itself.
  * DOCUMENTS: text documents with a YAML header. Every fact carries a quote that must be a substring of
    the body. data/validate_world.py enforces this.

A fact is (subject, predicate, object, quote) plus optional valid-time overrides. Predicates are local names
of the ontology in ontology/lcc.ttl. Objects that start with '"' are literals.
"""

AS_OF_DEFAULT = "2026-11-14"

# ---------------------------------------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------------------------------------

REGISTRIES = {}

REGISTRIES["customers"] = {
    "title": "Customer master data (ERP export)",
    "columns": ["id", "name", "market", "imposes"],
    "class": "Customer",
    "rows": [
        ["CUST-AUR", "Aurelia Automobili S.p.A.", "MKT-EU", "CSR-AUR-R3;CSR-AUR-R4;CSR-AUR-S1"],
        ["CUST-NOR", "Nordhavn Trucks AB", "MKT-EU", "CSR-NOR-R2"],
    ],
    "map": {"imposes": "imposes"},
}

REGISTRIES["markets"] = {
    "title": "Markets",
    "columns": ["id", "name"],
    "class": "Market",
    "rows": [["MKT-EU", "European Union"]],
    "map": {},
}

REGISTRIES["programs"] = {
    "title": "Vehicle programs (ERP export)",
    "columns": ["id", "name", "customer", "market", "sop"],
    "class": "Program",
    "rows": [
        ["PRG-X", "Aurelia Torre compact SUV", "CUST-AUR", "MKT-EU", "2025-02-01"],
        ["PRG-Z", "Aurelia Corso sedan", "CUST-AUR", "MKT-EU", "2023-06-01"],
        ["PRG-Y", "Nordhavn Fjell light van", "CUST-NOR", "MKT-EU", "2024-10-01"],
    ],
    "map": {"customer": "forCustomer", "market": "soldIn"},
}

REGISTRIES["sites"] = {
    "title": "Our production sites",
    "columns": ["id", "name"],
    "class": "Site",
    "rows": [
        ["PLT-BEI", "Beinasco plant (machining, assembly)"],
        ["PLT-PIN", "Pinerolo plant (assembly)"],
    ],
    "map": {},
}

REGISTRIES["materials"] = {
    "title": "Material master (EN 573 / EN 515 designations)",
    "columns": ["id", "name", "class", "temper_of", "series", "typical_yield_mpa"],
    "class": None,
    "rows": [
        ["ALY-6082", "EN AW-6082 (AlSi1MgMn)", "Alloy", "", "Series6xxx", ""],
        ["ALY-6061", "EN AW-6061 (AlMg1SiCu)", "Alloy", "", "Series6xxx", ""],
        ["MAT-6082-T6", "EN AW-6082-T6", "AlloyTemper", "ALY-6082", "", "260"],
        ["MAT-6082-T5", "EN AW-6082-T5", "AlloyTemper", "ALY-6082", "", "230"],
        ["MAT-6061-T6", "EN AW-6061-T6", "AlloyTemper", "ALY-6061", "", "240"],
        ["MAT-ALSI9CU3", "EN AC-46000 (AlSi9Cu3(Fe))", "Material", "", "Series3xxxCast", ""],
        ["MAT-DC04", "Steel DC04 (EN 10130)", "Steel", "", "", ""],
        ["MAT-C67S", "Spring steel C67S (EN 10132)", "Steel", "", "", ""],
        ["MAT-42CRMO4", "Steel 42CrMo4", "Steel", "", "", ""],
        ["MAT-PA66GF30", "PA66-GF30", "Polymer", "", "", ""],
    ],
    "map": {"temper_of": "temperOf", "series": "inSeries", "typical_yield_mpa": "typicalYieldMPa"},
}

REGISTRIES["coatings"] = {
    "title": "Coating catalogue (process engineering)",
    "columns": ["id", "name", "substances"],
    "class": "Coating",
    "rows": [
        ["COAT-ANOD", "Sulphuric acid anodising, clear", "none"],
        ["COAT-TCP", "Trivalent chromium conversion coating on aluminium", "CrIII"],
        ["COAT-CCC-YELLOW", "Yellow chromate conversion coating on aluminium", "CrVI"],
        ["COAT-ZNNI", "Zinc-nickel 8-12 um with trivalent (Cr(III)) passivation", "Zinc;Nickel;CrIII"],
        ["COAT-ZN-YELLOW", "Zinc 8 um with yellow chromate passivation", "Zinc;CrVI"],
        ["COAT-ZNFLAKE", "Zinc flake coating, Cr(VI)-free", "Zinc"],
    ],
    "map": {"substances": "containsSubstance"},
}

REGISTRIES["parts"] = {
    "title": "Part master (PLM export: drawing material, coating, program)",
    "columns": ["id", "name", "program", "drawing_rev", "material", "coating", "special_characteristic"],
    "class": "Part",
    "rows": [
        ["BR-220", "Front subframe bracket, milled", "PRG-X", "C", "MAT-6082-T6", "COAT-ANOD", "SC-BR220-YS"],
        ["BR-225", "Rear subframe bracket, milled", "PRG-X", "B", "MAT-6082-T6", "COAT-ANOD", "SC-BR225-YS"],
        ["BR-180", "Battery tray bracket, milled", "PRG-Z", "D", "MAT-6061-T6", "COAT-ANOD", ""],
        ["BR-310", "Roof rail bracket, extruded and cut", "PRG-Y", "A", "MAT-6082-T5", "COAT-TCP", ""],
        ["HS-410", "Exhaust heat shield, stamped", "PRG-X", "B", "MAT-DC04", "COAT-ZNNI", ""],
        ["CL-115", "Cable clip, spring steel", "PRG-X;PRG-Y", "E", "MAT-C67S", "COAT-ZNNI", ""],
        ["BK-330", "Seat rail bracket, stamped", "PRG-Z", "C", "MAT-DC04", "COAT-ZNNI", "SC-BK330-WELD"],
        ["PN-050", "Hinge pin", "PRG-X", "A", "MAT-42CRMO4", "COAT-ZNFLAKE", ""],
        ["HB-620", "Gearbox mount housing, die cast", "PRG-Y", "C", "MAT-ALSI9CU3", "COAT-ANOD", "SC-HB620-POR"],
        ["SP-700", "Battery spacer, injection moulded", "PRG-Z", "A", "MAT-PA66GF30", "", ""],
    ],
    "map": {"program": "usedIn", "material": "madeOf", "coating": "hasCoating",
            "special_characteristic": "hasSpecialCharacteristic", "drawing_rev": "drawingRevision"},
}

REGISTRIES["suppliers"] = {
    "title": "Supplier master (purchasing)",
    "columns": ["id", "name", "commodity"],
    "class": "Supplier",
    "rows": [
        ["SUP-B", "Alluminio Bormida S.r.l.", "aluminium blanks and bars"],
        ["SUP-C", "Meccanica Chisone S.r.l.", "aluminium extrusions and blanks"],
        ["SUP-D", "Fonderia Dora S.p.A.", "aluminium die castings"],
        ["SUP-E", "Galvanica Eporediese S.r.l.", "electroplating (coater)"],
        ["SUP-F", "Plastiche Fenestrelle S.r.l.", "injection moulding"],
        ["SUP-G", "Minuterie Germanasca S.r.l.", "steel stampings, clips, pins"],
        ["SUP-H", "Fonderia Pellice S.r.l.", "aluminium die castings"],
        # Sub-tier suppliers: they deliver to one of the suppliers above, never to us directly (links: SUBLIST-B, SUBLIST-C).
        ["SUP-I", "Trattamenti Termici Sangone S.r.l.", "heat treatment and T6 ageing"],
        ["SUP-J", "Billette Cumiana S.r.l.", "cast aluminium extrusion billets"],
        ["SUP-K", "Omogeneizzazione Piossasco S.r.l.", "billet homogenisation"],
    ],
    "map": {},
}

REGISTRIES["people"] = {
    "title": "People and roles",
    "columns": ["id", "name", "role"],
    "class": "Person",
    "rows": [
        ["PER-BIANCHI", "Laura Bianchi", "Supplier quality manager"],
        ["PER-ROSSI", "Marco Rossi", "Quality engineer, aluminium parts"],
        ["PER-CONTI", "Andrea Conti", "Head of plant quality (decides deviations)"],
        ["PER-FERRI", "Giulia Ferri", "Purchasing lead"],
        ["PER-GRECO", "Stefano Greco", "Program manager PRG-X"],
        ["PER-ROMANO", "Paolo Romano", "Process engineer"],
        ["PER-GALLO", "Elena Gallo", "Supplier quality engineer (SQE)"],
        ["PER-COSTA", "Riccardo Costa", "Production manager Beinasco"],
        ["PER-MARINO", "Federica Marino", "Resident engineer of Aurelia (customer side)"],
    ],
    "map": {"role": "role"},
}

# Part-level approvals: supplier x part x our site x customer. Approved Supplier List (ASL).
REGISTRIES["asl"] = {
    "title": "Approved supplier list per part (supplier quality system)",
    "columns": ["id", "supplier", "part", "site", "customer", "status", "valid_from", "valid_to",
                "approved_by", "supersedes"],
    "class": "PartApproval",
    "rows": [
        ["APR-001", "SUP-B", "BR-220", "PLT-BEI", "CUST-AUR", "approved", "2024-02-10", "", "PER-BIANCHI", ""],
        ["APR-002", "SUP-C", "BR-180", "PLT-BEI", "CUST-AUR", "approved", "2023-05-20", "", "PER-BIANCHI", ""],
        ["APR-003", "SUP-C", "BR-310", "PLT-PIN", "CUST-NOR", "approved", "2024-09-01", "", "PER-BIANCHI", ""],
        ["APR-004", "SUP-B", "BR-225", "PLT-BEI", "CUST-AUR", "approved", "2025-01-15", "", "PER-BIANCHI", ""],
        ["APR-005", "SUP-G", "HS-410", "PLT-BEI", "CUST-AUR", "approved", "2024-06-01", "", "PER-BIANCHI", ""],
        ["APR-006", "SUP-E", "HS-410", "PLT-BEI", "CUST-AUR", "approved", "2024-06-01", "", "PER-BIANCHI", ""],
        ["APR-007", "SUP-G", "CL-115", "PLT-BEI", "CUST-AUR", "approved", "2024-11-05", "", "PER-BIANCHI", ""],
        ["APR-008", "SUP-G", "CL-115", "PLT-PIN", "CUST-NOR", "approved", "2024-11-05", "", "PER-BIANCHI", ""],
        ["APR-009", "SUP-D", "HB-620", "PLT-PIN", "CUST-NOR", "approved", "2022-11-10", "", "PER-BIANCHI", ""],
        ["APR-010", "SUP-D", "HB-620", "PLT-PIN", "CUST-NOR", "revoked", "2026-09-15", "", "PER-BIANCHI", "APR-009"],
        ["APR-011", "SUP-H", "HB-620", "PLT-PIN", "CUST-NOR", "approved", "2026-10-01", "", "PER-BIANCHI", ""],
        ["APR-012", "SUP-F", "SP-700", "PLT-BEI", "CUST-AUR", "approved", "2023-04-18", "", "PER-BIANCHI", ""],
        ["APR-013", "SUP-G", "BK-330", "PLT-BEI", "CUST-AUR", "approved", "2023-03-02", "", "PER-BIANCHI", ""],
        ["APR-014", "SUP-G", "PN-050", "PLT-BEI", "CUST-AUR", "approved", "2025-02-20", "", "PER-BIANCHI", ""],
    ],
    "map": {"supplier": "approvedSupplier", "part": "approvedPart", "site": "approvedSite",
            "customer": "approvedForCustomer", "status": "status", "approved_by": "author"},
}

# Supplier-level qualification after audit. Does NOT approve any part.
REGISTRIES["supplier_qualification"] = {
    "title": "Supplier qualification status after audit (supplier quality system)",
    "columns": ["id", "supplier", "status", "valid_from", "valid_to", "approved_by", "supersedes", "note"],
    "class": "SupplierQualification",
    "rows": [
        ["QS-B-2023", "SUP-B", "approved", "2023-01-20", "", "PER-BIANCHI", "", "audit score 91"],
        ["QS-C-2023", "SUP-C", "approved", "2023-03-15", "", "PER-BIANCHI", "", "audit score 84"],
        ["QS-C-2025", "SUP-C", "conditional", "2025-04-01", "", "PER-BIANCHI", "QS-C-2023",
         "no new parts until 8D-25-031 is closed and re-audit passed"],
        ["QS-C-2026", "SUP-C", "approved", "2026-11-06", "", "PER-BIANCHI", "QS-C-2025",
         "re-audit passed, score 86"],
        ["QS-D-2022", "SUP-D", "approved", "2022-09-01", "", "PER-BIANCHI", "", "audit score 88"],
        ["QS-D-2026", "SUP-D", "conditional", "2026-09-15", "", "PER-BIANCHI", "QS-D-2022",
         "porosity escapes, see 8D-26-009"],
        ["QS-E-2023", "SUP-E", "approved", "2023-02-10", "", "PER-BIANCHI", "", "audit score 89"],
        ["QS-F-2023", "SUP-F", "approved", "2023-02-28", "", "PER-BIANCHI", "", "audit score 82"],
        ["QS-G-2022", "SUP-G", "approved", "2022-05-11", "", "PER-BIANCHI", "", "audit score 90"],
        ["QS-H-2026", "SUP-H", "approved", "2026-09-28", "", "PER-BIANCHI", "", "audit score 87"],
    ],
    "map": {"supplier": "qualifiedSupplier", "status": "status", "approved_by": "author"},
}

REGISTRIES["capabilities"] = {
    "title": "Materials each supplier is qualified to deliver (supplier quality system)",
    "columns": ["id", "supplier", "material", "valid_from"],
    "class": "SupplierCapability",
    "rows": [
        ["CAP-B-01", "SUP-B", "MAT-6082-T6", "2023-01-20"],
        ["CAP-B-02", "SUP-B", "MAT-6061-T6", "2023-01-20"],
        ["CAP-C-01", "SUP-C", "MAT-6061-T6", "2023-03-15"],
        ["CAP-C-02", "SUP-C", "MAT-6082-T5", "2024-07-01"],
        ["CAP-D-01", "SUP-D", "MAT-ALSI9CU3", "2022-09-01"],
        ["CAP-H-01", "SUP-H", "MAT-ALSI9CU3", "2026-09-28"],
        ["CAP-G-01", "SUP-G", "MAT-DC04", "2022-05-11"],
        ["CAP-G-02", "SUP-G", "MAT-C67S", "2022-05-11"],
        ["CAP-G-03", "SUP-G", "MAT-42CRMO4", "2022-05-11"],
        ["CAP-F-01", "SUP-F", "MAT-PA66GF30", "2023-02-28"],
    ],
    "map": {"supplier": "capableSupplier", "material": "capableMaterial"},
}

REGISTRIES["certificates"] = {
    "title": "Material certificates on file (EN 10204 type 3.1)",
    "columns": ["id", "supplier", "material", "valid_from"],
    "class": "MaterialCertificate",
    "rows": [
        ["CERT-B-6082T6", "SUP-B", "MAT-6082-T6", "2026-10-28"],
        ["CERT-B-6061T6", "SUP-B", "MAT-6061-T6", "2026-09-30"],
        ["CERT-C-6061T6", "SUP-C", "MAT-6061-T6", "2026-10-15"],
        ["CERT-C-6082T5", "SUP-C", "MAT-6082-T5", "2026-10-15"],
        ["CERT-D-ALSI", "SUP-D", "MAT-ALSI9CU3", "2026-08-01"],
        ["CERT-H-ALSI", "SUP-H", "MAT-ALSI9CU3", "2026-10-01"],
        ["CERT-G-DC04", "SUP-G", "MAT-DC04", "2026-10-01"],
        ["CERT-G-C67S", "SUP-G", "MAT-C67S", "2026-10-01"],
        ["CERT-G-42CRMO4", "SUP-G", "MAT-42CRMO4", "2026-10-01"],
    ],
    "map": {"supplier": "certSupplier", "material": "certMaterial"},
}

REGISTRIES["special_characteristics"] = {
    "title": "Special characteristics (control plan)",
    "columns": ["id", "part", "description", "min_yield_mpa"],
    "class": "SpecialCharacteristic",
    "rows": [
        ["SC-BR220-YS", "BR-220", "Yield strength Rp0.2 at least 250 MPa", "250"],
        ["SC-BR225-YS", "BR-225", "Yield strength Rp0.2 at least 250 MPa", "250"],
        ["SC-BK330-WELD", "BK-330", "Weld nugget diameter at least 5 mm", ""],
        ["SC-HB620-POR", "HB-620", "Porosity grade 2 or better in mount bores", ""],
    ],
    "map": {"min_yield_mpa": "minYieldMPa"},
}

# ---------------------------------------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------------------------------------
# Header fields: id, type, title, date, author, valid_from, valid_to, supersedes, mentions, rank
# rank: law > customer_requirement > internal_procedure > standard > record > meeting > email

DOCUMENTS = []


def doc(**fields):
    DOCUMENTS.append(fields)


# --- Customer requirements -------------------------------------------------------------------------------

doc(id="CSR-AUR-R3", type="customer_requirement", title="Aurelia supplier quality manual, rev 3 (excerpt)",
    date="2024-01-01", author="Aurelia Automobili, supplier quality", valid_from="2024-01-01",
    valid_to="2026-06-30", supersedes=None, mentions=["CUST-AUR"],
    body="""Aurelia Automobili - Supplier Quality Manual, revision 3, section 7 "Changes".
7.1 The supplier shall obtain written approval from Aurelia (PPAP resubmission) before shipping parts
after a change of source, a change of material or a change of manufacturing process.
7.2 A change of coating or surface treatment within the same specification family requires
notification to Aurelia at least 60 days before implementation; approval is not required.
7.3 Changes at sub-suppliers are the responsibility of the supplier.""",
    facts=[
        ("CSR-AUR-R3", "requiresCustomerApprovalFor", "SourceChange", "before shipping parts\nafter a change of source"),
        ("CSR-AUR-R3", "requiresCustomerApprovalFor", "MaterialChange", "a change of material"),
        ("CSR-AUR-R3", "requiresCustomerApprovalFor", "ProcessChange", "a change of manufacturing process"),
        ("CSR-AUR-R3", "requiresNotificationFor", "CoatingChange", "requires\nnotification to Aurelia at least 60 days before implementation; approval is not required"),
    ])

doc(id="CSR-AUR-R4", type="customer_requirement", title="Aurelia supplier quality manual, rev 4 (excerpt)",
    date="2026-07-01", author="Aurelia Automobili, supplier quality", valid_from="2026-07-01",
    valid_to=None, supersedes="CSR-AUR-R3", mentions=["CUST-AUR"],
    body="""Aurelia Automobili - Supplier Quality Manual, revision 4, section 7 "Changes". Replaces revision 3.
7.1 The supplier shall obtain written approval from Aurelia (PPAP resubmission) before shipping parts
after any of: a change of source, a change of material, a change of manufacturing process, or a change
of coating or surface treatment.
7.2 Aurelia shall be notified of every planned change at least 90 days before implementation.
7.3 Approval is granted per part number and per manufacturing site. An approval for one part does not
extend to another part, even if made of the same material.
7.4 A temporary deviation may be requested from the Aurelia resident engineer. It is limited in
quantity and time and requires 100% inspection of the affected characteristic.
7.5 Parts shipped after a change that Aurelia has not approved place Aurelia in a nonconforming
position. Aurelia may place the supplier on New Business Hold, may notify the supplier's IATF
registrar, and will charge back all resulting costs.""",
    facts=[
        ("CSR-AUR-R4", "hasConsequence", "NewBusinessHold", "may place the supplier on New Business Hold"),
        ("CSR-AUR-R4", "hasConsequence", "RegistrarNotification", "may notify the supplier's IATF\nregistrar"),
        ("CSR-AUR-R4", "hasConsequence", "Chargeback", "will charge back all resulting costs"),
        ("CSR-AUR-R4", "requiresCustomerApprovalFor", "SourceChange", "a change of source"),
        ("CSR-AUR-R4", "requiresCustomerApprovalFor", "MaterialChange", "a change of material"),
        ("CSR-AUR-R4", "requiresCustomerApprovalFor", "ProcessChange", "a change of manufacturing process"),
        ("CSR-AUR-R4", "requiresCustomerApprovalFor", "CoatingChange", "a change\nof coating or surface treatment"),
        ("CSR-AUR-R4", "requiresNotificationFor", "SourceChange", "notified of every planned change at least 90 days before implementation"),
    ])

doc(id="CSR-NOR-R2", type="customer_requirement", title="Nordhavn supplier requirements, rev 2 (excerpt)",
    date="2025-03-01", author="Nordhavn Trucks AB, purchasing quality", valid_from="2025-03-01",
    valid_to=None, supersedes=None, mentions=["CUST-NOR"],
    body="""Nordhavn Trucks - Customer Specific Requirements, revision 2, chapter 5.
5.1 A change of source or a change of material requires Nordhavn approval (PPAP resubmission) before
the first shipment.
5.2 A change of coating requires Nordhavn approval before the first shipment.
5.3 A change of manufacturing process at the same approved site requires notification only, 30 days
in advance. Moving production to another site is a change of source.""",
    facts=[
        ("CSR-NOR-R2", "requiresCustomerApprovalFor", "SourceChange", "A change of source or a change of material requires Nordhavn approval"),
        ("CSR-NOR-R2", "requiresCustomerApprovalFor", "MaterialChange", "a change of material requires Nordhavn approval"),
        ("CSR-NOR-R2", "requiresCustomerApprovalFor", "CoatingChange", "A change of coating requires Nordhavn approval"),
        ("CSR-NOR-R2", "requiresNotificationFor", "ProcessChange", "requires notification only, 30 days\nin advance"),
    ])

doc(id="CSR-AUR-S1", type="customer_requirement", title="Aurelia supplier quality manual, annex S: sub-suppliers (excerpt)",
    date="2026-07-01", author="Aurelia Automobili, supplier quality", valid_from="2026-07-01",
    valid_to=None, supersedes=None, mentions=["CUST-AUR"],
    body="""Aurelia Automobili - Supplier Quality Manual, revision 4, annex S "Sub-suppliers". Supplements section 7.
S.1 The supplier is responsible for every change at its sub-suppliers, at every tier, as if it had made the change itself.
S.2 A change of material, a change of manufacturing process or a change of coating at a sub-supplier requires written approval from Aurelia (PPAP resubmission) before shipping parts.
S.3 A change of source at a sub-supplier is notified to Aurelia at least 90 days before implementation.
S.4 The supplier shall require each sub-supplier to report every planned change before implementation. A change learned of after implementation is reported to Aurelia within 24 hours.""",
    facts=[
        ("CSR-AUR-S1", "requiresCustomerApprovalForSubTier", "MaterialChange", "A change of material, a change of manufacturing process or a change of coating at a sub-supplier requires written approval from Aurelia"),
        ("CSR-AUR-S1", "requiresCustomerApprovalForSubTier", "ProcessChange", "a change of manufacturing process or a change of coating at a sub-supplier requires written approval from Aurelia"),
        ("CSR-AUR-S1", "requiresCustomerApprovalForSubTier", "CoatingChange", "a change of coating at a sub-supplier requires written approval from Aurelia"),
        ("CSR-AUR-S1", "requiresNotificationForSubTier", "SourceChange", "A change of source at a sub-supplier is notified to Aurelia at least 90 days before implementation"),
    ])

# --- Law and standards -----------------------------------------------------------------------------------

doc(id="LAW-ELV", type="law", title="Directive 2000/53/EC on end-of-life vehicles (ELV), Article 4(2)(a)",
    date="2000-09-18", author="European Parliament and Council", valid_from="2000-10-21", valid_to=None,
    supersedes=None, mentions=["MKT-EU", "CrVI", "Lead", "Cadmium", "Mercury"],
    body="""Directive 2000/53/EC, Article 4(2)(a), quoted:
"Member States shall ensure that materials and components of vehicles put on the market after 1 July
2003 do not contain lead, mercury, cadmium or hexavalent chromium other than in cases listed in
Annex II under the conditions specified therein."
Our note: the Annex II exemption for hexavalent chromium in corrosion-preventive coatings has expired,
so a coating containing hexavalent chromium may not be used on our parts. The directive is replaced
by Regulation (EU) 2026/1738 on end-of-life vehicles (applicable from 1 September 2028); the ban on
these four substances continues there. Check the Official Journal text before quoting dates.""",
    facts=[
        ("LAW-ELV", "appliesInMarket", "MKT-EU", "Member States shall ensure that materials and components of vehicles"),
        ("LAW-ELV", "restricts", "CrVI", "hexavalent chromium other than in cases listed in"),
        ("LAW-ELV", "restricts", "Lead", "do not contain lead"),
        ("LAW-ELV", "restricts", "Cadmium", "cadmium"),
        ("LAW-ELV", "restricts", "Mercury", "mercury"),
    ])

doc(id="STD-IATF-8561", type="standard", title="IATF 16949 clause 8.5.6.1 in our words",
    date="2023-01-01", author="PER-CONTI", valid_from="2023-01-01", valid_to=None, supersedes=None,
    mentions=[],
    body="""IATF 16949, clause 8.5.6.1 (control of changes), summarised in our own words, not quoted:
before a change to a product or a production process is implemented, the organisation evaluates its
effect, documents it, verifies and validates it, and obtains customer approval where the customer
requires it. This also covers changes made by suppliers.""",
    facts=[])

doc(id="STD-PPAP-TRIGGERS", type="standard", title="When a PPAP resubmission is needed (our summary)",
    date="2023-01-01", author="PER-CONTI", valid_from="2023-01-01", valid_to=None, supersedes=None,
    mentions=[],
    body="""Typical triggers for a PPAP resubmission, summarised from public supplier manuals:
new source of material or components, change of material, change of process or process sequence,
change of coating, production moved to another site, tooling transfer or refurbishment, and
correction of a discrepancy on a previously approved part. The customer's own requirements decide.""",
    facts=[])

# --- Internal procedures ---------------------------------------------------------------------------------

doc(id="QP-07-B", type="internal_procedure", title="QP-07 Change management, rev B",
    date="2023-02-01", author="PER-CONTI", valid_from="2023-02-01", valid_to="2026-02-28", supersedes=None,
    mentions=["PER-ROSSI"],
    body="""QP-07 Change management, revision B.
Every engineering change request (ECR) is reviewed by the change board. The responsible quality
engineer signs off changes on parts with special characteristics.""",
    facts=[])

doc(id="QP-07-C", type="internal_procedure", title="QP-07 Change management, rev C",
    date="2026-03-01", author="PER-CONTI", valid_from="2026-03-01", valid_to=None, supersedes="QP-07-B",
    mentions=["PER-CONTI"],
    body="""QP-07 Change management, revision C. Replaces revision B.
Every engineering change request (ECR) is reviewed by the change board before implementation.
Changes on parts with special characteristics are signed off by the head of plant quality, not by
the quality engineer. Deviations are decided by the head of plant quality.
A missing document is recorded as an open question with an owner, not as a violation.""",
    facts=[])

doc(id="QP-11", type="internal_procedure", title="QP-11 Supplier qualification and part approval",
    date="2024-05-01", author="PER-BIANCHI", valid_from="2024-05-01", valid_to=None, supersedes=None,
    mentions=["PER-BIANCHI"],
    body="""QP-11 Supplier qualification and part approval, revision A.
4.1 A supplier audit qualifies the supplier as a company. It does not approve the supplier for any
part.
4.2 A supplier may deliver a part only if the approved supplier list contains an approval for that
supplier, that part, the receiving site and the customer.
4.3 A supplier with status conditional may not receive new parts.
4.4 A change of source requires a material certificate (EN 10204 type 3.1) from the new supplier for
the drawing material. Missing certificates are an open question for the supplier quality engineer.""",
    facts=[])

doc(id="QA-SUP-C", type="contract", title="Quality agreement with Meccanica Chisone (excerpt)",
    date="2023-03-15", author="PER-FERRI", valid_from="2023-03-15", valid_to=None, supersedes=None,
    mentions=["SUP-C"],
    body="""Quality assurance agreement between Valsangone Componenti and Meccanica Chisone S.r.l.
Clause 6.2: the supplier shall notify Valsangone of any change of material, process, sub-supplier or
manufacturing site at least 90 days before the change.""",
    facts=[])

doc(id="CON-AUR", type="contract", title="Supply contract with Aurelia (excerpt)",
    date="2024-01-10", author="PER-FERRI", valid_from="2024-01-10", valid_to=None, supersedes=None,
    mentions=["CUST-AUR"],
    body="""Supply contract Aurelia Automobili / Valsangone Componenti, clause 14.3: no change to an
approved part or its process may be implemented without the written approval of Aurelia. Parts
shipped after an unapproved change are treated as nonconforming and the cost of containment is
charged to the supplier.""",
    facts=[])

doc(id="QP-14", type="internal_procedure", title="QP-14 Changes at sub-suppliers",
    date="2026-09-01", author="PER-BIANCHI", valid_from="2026-09-01", valid_to=None, supersedes=None,
    mentions=["PER-BIANCHI", "PER-GALLO"],
    body="""QP-14 Changes at sub-suppliers, revision A.
4.1 A change of material, manufacturing process, coating or source at any sub-supplier of a part is a change of that part.
4.2 The supplier passes every sub-supplier change notice to Valsangone before the change is implemented. A change learned of after implementation is reported to the plant within 24 hours.
4.3 The plant checks the notice against the customer requirement for the part and informs the customer, or asks for written approval, before the first shipment.
4.4 A change at a supplier whose link to a supplier of the part is not on file is an open question for the supplier quality engineer.""",
    facts=[])

doc(id="SUBLIST-B", type="contract", title="Sub-supplier list of Alluminio Bormida for BR-220 and BR-225 blanks (PPAP element)",
    date="2024-01-30", author="PER-GALLO", valid_from="2024-01-30", valid_to=None, supersedes=None,
    mentions=["SUP-B", "SUP-I", "BR-220", "BR-225"],
    body="""Sub-supplier list of Alluminio Bormida S.r.l. to Valsangone Componenti, EN AW-6082-T6 blanks for BR-220 and BR-225.
Sawing and packing are done at Alluminio Bormida. Solution heat treatment and T6 ageing of the sawn blanks are done by Trattamenti Termici Sangone S.r.l. (SUP-I), which delivers the treated blanks to Alluminio Bormida.""",
    facts=[
        ("SUP-I", "suppliesTo", "SUP-B", "Trattamenti Termici Sangone S.r.l. (SUP-I), which delivers the treated blanks to Alluminio Bormida"),
    ])

doc(id="SUBLIST-C", type="contract", title="Sub-supplier list of Meccanica Chisone for BR-310 extrusions (PPAP element)",
    date="2024-08-01", author="PER-GALLO", valid_from="2024-08-01", valid_to=None, supersedes=None,
    mentions=["SUP-C", "SUP-J", "SUP-K", "BR-310"],
    body="""Sub-supplier list of Meccanica Chisone S.r.l. to Valsangone Componenti, EN AW-6082-T5 extrusions for BR-310.
Extrusion, cutting and ageing are done at Meccanica Chisone. The extrusion billets are cast by Billette Cumiana S.r.l. (SUP-J), which delivers them to Meccanica Chisone.
Billette Cumiana buys the homogenisation of its billets from Omogeneizzazione Piossasco S.r.l. (SUP-K), which delivers the homogenised billets to Billette Cumiana.""",
    facts=[
        ("SUP-J", "suppliesTo", "SUP-C", "Billette Cumiana S.r.l. (SUP-J), which delivers them to Meccanica Chisone"),
        ("SUP-K", "suppliesTo", "SUP-J", "Omogeneizzazione Piossasco S.r.l. (SUP-K), which delivers the homogenised billets to Billette Cumiana"),
    ])

# --- Part cards and FMEA ---------------------------------------------------------------------------------

doc(id="PC-BR220", type="part_card", title="Part card BR-220 front subframe bracket",
    date="2024-02-01", author="PER-ROSSI", valid_from="2024-02-01", valid_to=None, supersedes=None,
    mentions=["BR-220", "PRG-X", "MAT-6082-T6", "SC-BR220-YS", "SUP-B"],
    body="""Part card BR-220, front subframe bracket for the Aurelia Torre (PRG-X). Drawing revision C.
Material: EN AW-6082-T6. Not interchangeable with EN AW-6061: different alloy, lower yield.
Special characteristic SC-BR220-YS: yield strength Rp0.2 at least 250 MPa, see control plan line 30.
Surface: clear anodising. Approved blank source: Alluminio Bormida (SUP-B), single source.""",
    facts=[])

doc(id="PC-BR310", type="part_card", title="Part card BR-310 roof rail bracket",
    date="2024-08-15", author="PER-ROSSI", valid_from="2024-08-15", valid_to=None, supersedes=None,
    mentions=["BR-310", "PRG-Y", "MAT-6082-T5", "SUP-C"],
    body="""Part card BR-310, roof rail bracket for the Nordhavn Fjell (PRG-Y). Drawing revision A.
Material: EN AW-6082-T5 extrusion. Surface: trivalent conversion coating. Source: Meccanica Chisone (SUP-C).""",
    facts=[])

doc(id="PC-CL115", type="part_card", title="Part card CL-115 cable clip",
    date="2024-11-01", author="PER-ROMANO", valid_from="2024-11-01", valid_to=None, supersedes=None,
    mentions=["CL-115", "PRG-X", "PRG-Y", "MAT-C67S", "COAT-ZNNI", "SUP-G"],
    body="""Part card CL-115, cable clip used on PRG-X and PRG-Y. Spring steel C67S, hardened.
Surface: zinc-nickel with trivalent passivation (COAT-ZNNI). Source: Minuterie Germanasca (SUP-G).""",
    facts=[])

doc(id="FMEA-BR220", type="fmea", title="Process FMEA BR-220 (excerpt)",
    date="2024-01-20", author="PER-ROSSI", valid_from="2024-01-20", valid_to=None, supersedes=None,
    mentions=["BR-220", "MAT-6082-T6", "SC-BR220-YS"],
    body="""PFMEA BR-220, line 12. Failure mode: crack at the fastening holes under fatigue load.
Cause: wrong alloy or temper of the blank (yield below 250 MPa). Severity 9.
Prevention: blanks only from sources approved for EN AW-6082-T6; material certificate 3.1 per lot.
Detection: hardness check per lot, control plan line 30.""",
    facts=[])

# --- Issues: 8D, NCR, deviations -------------------------------------------------------------------------

doc(id="8D-25-031", type="8d", title="8D-25-031 Cracks at fastening holes, Meccanica Chisone",
    date="2025-03-20", author="PER-GALLO", valid_from="2025-03-20", valid_to=None, supersedes=None,
    mentions=["SUP-C", "ALY-6082", "BR-310"],
    body="""8D report 8D-25-031. Supplier: Meccanica Chisone (SUP-C). Opened 2025-03-20. Status: open.
D2 Problem: cracks around fastening holes on brackets machined from EN AW-6082 material delivered by
the supplier; found at incoming inspection on BR-310.
D4 Root cause: under investigation, suspected inconsistent ageing at the supplier's heat treatment.
D5 Corrective action not yet verified. Containment: 100% visual check of holes.""",
    facts=[
        ("8D-25-031", "concernsSupplier", "SUP-C", "Supplier: Meccanica Chisone (SUP-C)"),
        ("8D-25-031", "concernsMaterial", "ALY-6082", "EN AW-6082 material delivered by\nthe supplier"),
        ("8D-25-031", "concernsPart", "BR-310", "found at incoming inspection on BR-310"),
        ("8D-25-031", "status", '"open"', "Status: open"),
    ])

doc(id="8D-25-019", type="8d", title="8D-25-019 Burrs on BR-220, Alluminio Bormida",
    date="2025-01-14", author="PER-GALLO", valid_from="2025-01-14", valid_to=None, supersedes=None,
    mentions=["SUP-B", "BR-220"],
    body="""8D report 8D-25-019. Supplier: Alluminio Bormida (SUP-B). Opened 2025-01-14, closed 2025-02-21.
Status: closed. Problem: burrs on saw-cut blanks for BR-220. Root cause: worn saw blade. Corrective
action: blade change interval, verified.""",
    facts=[
        ("8D-25-019", "concernsSupplier", "SUP-B", "Supplier: Alluminio Bormida (SUP-B)"),
        ("8D-25-019", "concernsPart", "BR-220", "blanks for BR-220"),
        ("8D-25-019", "status", '"closed"', "Status: closed"),
    ])

doc(id="8D-26-009", type="8d", title="8D-26-009 Porosity in HB-620 mount bores, Fonderia Dora",
    date="2026-08-20", author="PER-GALLO", valid_from="2026-08-20", valid_to=None, supersedes=None,
    mentions=["SUP-D", "HB-620", "MAT-ALSI9CU3"],
    body="""8D report 8D-26-009. Supplier: Fonderia Dora (SUP-D). Opened 2026-08-20. Status: open.
Problem: porosity grade 4 in the mount bores of HB-620 castings (AlSi9Cu3), three escapes to the
Nordhavn line. Root cause: die temperature control. Approval for HB-620 revoked on 2026-09-15.""",
    facts=[
        ("8D-26-009", "concernsSupplier", "SUP-D", "Supplier: Fonderia Dora (SUP-D)"),
        ("8D-26-009", "concernsMaterial", "MAT-ALSI9CU3", "castings (AlSi9Cu3)"),
        ("8D-26-009", "concernsPart", "HB-620", "mount bores of HB-620"),
        ("8D-26-009", "status", '"open"', "Status: open"),
    ])

doc(id="8D-26-004", type="8d", title="8D-26-004 Zinc-nickel thickness on HS-410, Galvanica Eporediese",
    date="2026-02-02", author="PER-GALLO", valid_from="2026-02-02", valid_to=None, supersedes=None,
    mentions=["SUP-E", "HS-410", "COAT-ZNNI"],
    body="""8D report 8D-26-004. Supplier: Galvanica Eporediese (SUP-E). Opened 2026-02-02, closed 2026-03-10.
Status: closed. Problem: zinc-nickel layer 6 um instead of 8 um minimum on HS-410 edges. Corrective
action: rack redesign. Interim: deviation DEV-121.""",
    facts=[
        ("8D-26-004", "concernsSupplier", "SUP-E", "Supplier: Galvanica Eporediese (SUP-E)"),
        ("8D-26-004", "concernsPart", "HS-410", "on HS-410 edges"),
        ("8D-26-004", "status", '"closed"', "Status: closed"),
    ])

doc(id="8D-26-012", type="8d", title="8D-26-012 Moisture in SP-700 spacers, Plastiche Fenestrelle",
    date="2026-10-05", author="PER-GALLO", valid_from="2026-10-05", valid_to=None, supersedes=None,
    mentions=["SUP-F", "SP-700", "MAT-PA66GF30"],
    body="""8D report 8D-26-012. Supplier: Plastiche Fenestrelle (SUP-F). Opened 2026-10-05. Status: open.
Problem: brittle SP-700 spacers, PA66-GF30 moulded with too much moisture. Containment: dry-as-moulded
check per lot.""",
    facts=[
        ("8D-26-012", "concernsSupplier", "SUP-F", "Supplier: Plastiche Fenestrelle (SUP-F)"),
        ("8D-26-012", "concernsMaterial", "MAT-PA66GF30", "PA66-GF30 moulded with too much moisture"),
        ("8D-26-012", "concernsPart", "SP-700", "brittle SP-700 spacers"),
        ("8D-26-012", "status", '"open"', "Status: open"),
    ])

doc(id="NCR-26-017", type="ncr", title="NCR-26-017 CL-115 hardness out of tolerance",
    date="2026-10-20", author="PER-GALLO", valid_from="2026-10-20", valid_to=None, supersedes=None,
    mentions=["SUP-G", "CL-115", "MAT-C67S"],
    body="""Nonconformance report NCR-26-017. Supplier: Minuterie Germanasca (SUP-G). Status: open.
Lot 26-0412 of CL-115 clips in C67S spring steel measured 52 HRC, tolerance 44-50 HRC. Lot blocked,
100% hardness check on the next three lots.""",
    facts=[
        ("NCR-26-017", "concernsSupplier", "SUP-G", "Supplier: Minuterie Germanasca (SUP-G)"),
        ("NCR-26-017", "concernsMaterial", "MAT-C67S", "C67S spring steel"),
        ("NCR-26-017", "concernsPart", "CL-115", "CL-115 clips"),
        ("NCR-26-017", "status", '"open"', "Status: open"),
    ])

doc(id="DEV-114", type="deviation", title="DEV-114 BR-180 hardness deviation, Meccanica Chisone",
    date="2025-03-12", author="PER-ROSSI", valid_from="2025-03-12", valid_to="2025-06-30", supersedes=None,
    mentions=["SUP-C", "MAT-6061-T6", "BR-180", "PRG-Z"],
    body="""Deviation DEV-114. Temporary permit to accept BR-180 brackets from Meccanica Chisone (SUP-C)
with hardness of the EN AW-6061-T6 blanks 3 HB below drawing minimum. Valid from 2025-03-12 to
2025-06-30, maximum 1500 parts, 100% hardness check. Approved by Aurelia resident engineer.
Status: expired.""",
    facts=[
        ("DEV-114", "concernsSupplier", "SUP-C", "Meccanica Chisone (SUP-C)"),
        ("DEV-114", "concernsMaterial", "MAT-6061-T6", "EN AW-6061-T6 blanks"),
        ("DEV-114", "concernsPart", "BR-180", "BR-180 brackets"),
        ("DEV-114", "status", '"expired"', "Status: expired"),
    ])

doc(id="DEV-118", type="deviation", title="DEV-118 BR-220 alternative packaging",
    date="2025-09-01", author="PER-ROSSI", valid_from="2025-09-01", valid_to="2025-10-31", supersedes=None,
    mentions=["SUP-B", "BR-220"],
    body="""Deviation DEV-118. BR-220 blanks from Alluminio Bormida (SUP-B) may arrive in cardboard boxes
instead of returnable crates. Valid from 2025-09-01 to 2025-10-31. Status: expired.""",
    facts=[
        ("DEV-118", "concernsSupplier", "SUP-B", "Alluminio Bormida (SUP-B)"),
        ("DEV-118", "concernsPart", "BR-220", "BR-220 blanks"),
        ("DEV-118", "permitsChangeType", "PackagingChange", "in cardboard boxes\ninstead of returnable crates"),
        ("DEV-118", "status", '"expired"', "Status: expired"),
    ])

doc(id="DEV-121", type="deviation", title="DEV-121 HS-410 zinc-nickel minimum 6 um, Galvanica Eporediese",
    date="2026-03-01", author="PER-CONTI", valid_from="2026-03-01", valid_to="2026-12-31", supersedes=None,
    mentions=["SUP-E", "HS-410", "COAT-ZNNI", "CUST-AUR"],
    body="""Deviation DEV-121. HS-410 heat shields coated by Galvanica Eporediese (SUP-E) may be shipped with
a zinc-nickel layer of at least 6 um instead of 8 um, provided every lot passes a 480 h salt spray
sample test. Valid from 2026-03-01 to 2026-12-31. Agreed in writing with Aurelia (F. Marino).
Decided by A. Conti. Status: valid.""",
    facts=[
        ("DEV-121", "concernsSupplier", "SUP-E", "Galvanica Eporediese (SUP-E)"),
        ("DEV-121", "concernsPart", "HS-410", "HS-410 heat shields"),
        ("DEV-121", "permitsChangeType", "CoatingChange", "a zinc-nickel layer of at least 6 um instead of 8 um"),
        ("DEV-121", "permitsCoating", "COAT-ZNNI", "a zinc-nickel layer of at least 6 um"),
        ("DEV-121", "status", '"valid"', "Status: valid"),
    ])

doc(id="DEV-125", type="deviation", title="DEV-125 BR-310 alternative packaging",
    date="2026-08-01", author="PER-ROSSI", valid_from="2026-08-01", valid_to="2027-01-31", supersedes=None,
    mentions=["SUP-C", "BR-310"],
    body="""Deviation DEV-125. BR-310 brackets from Meccanica Chisone (SUP-C) may be packed 40 per layer
instead of 30 per layer. Valid from 2026-08-01 to 2027-01-31. Status: valid.""",
    facts=[
        ("DEV-125", "concernsSupplier", "SUP-C", "Meccanica Chisone (SUP-C)"),
        ("DEV-125", "concernsPart", "BR-310", "BR-310 brackets"),
        ("DEV-125", "permitsChangeType", "PackagingChange", "packed 40 per layer\ninstead of 30 per layer"),
        ("DEV-125", "status", '"valid"', "Status: valid"),
    ])

doc(id="DEV-127", type="deviation", title="DEV-127 request: Meccanica Chisone as temporary source for BR-220",
    date="2026-09-28", author="PER-FERRI", valid_from="2026-09-28", valid_to=None, supersedes=None,
    mentions=["SUP-C", "BR-220", "MAT-6061-T6"],
    body="""Deviation request DEV-127. Purchasing asked to take BR-220 blanks from Meccanica Chisone (SUP-C)
for six weeks while Alluminio Bormida recovers capacity. Status: rejected on 2026-10-02 by A. Conti,
see decision DEC-031.""",
    facts=[
        ("DEV-127", "concernsSupplier", "SUP-C", "Meccanica Chisone (SUP-C)"),
        ("DEV-127", "concernsPart", "BR-220", "BR-220 blanks"),
        ("DEV-127", "status", '"rejected"', "Status: rejected"),
    ])

# --- Emails (lowest rank; may state outdated or wrong things on purpose) ---------------------------------

doc(id="EML-2026-10-29", type="email", title="Email: re BR-220 shortage",
    date="2026-10-29", author="PER-FERRI", valid_from="2026-10-29", valid_to=None, supersedes=None,
    mentions=["SUP-C", "BR-220"],
    body="""From: Giulia Ferri. To: change board. Subject: re BR-220 shortage.
Meccanica Chisone told me on the phone they can make BR-220 blanks from the same alloy they use for
BR-310, so it should be a formality. Can we put it on the agenda?""",
    facts=[])

# ---------------------------------------------------------------------------------------------------------
# Additions from issue #19 (maintenance: record time, promises, contradiction). Data additions for
# Valentina's review. Rendered by build.py AFTER the meetings, so every existing fact id stays the same.
# ---------------------------------------------------------------------------------------------------------

# Record time (when the system learned a record) where it differs from valid time. Every other fact is taken
# as recorded on its valid_from date (undated registry rows: on the first date of the world).
RECORDED_AT = {
    "QS-C-2026": "2026-11-10T09:00:00+00:00",  # re-audit passed 6 Nov, entered into the system on 10 Nov
}

# Decision reasons stored as links to the records they rely on, so a reason can be re-checked later.
# decision id -> records the reason relies on.
REASON_LINKS = {
    "DEC-031": ["CAP-C-01", "CAP-C-02", "8D-25-031"],  # "no EN AW-6082-T6 capability and 8D-25-031 is open"
    "DEC-033": ["QS-C-2025"],                          # "Chisone is still conditional (QS-C-2025)"
}

ADDITIONAL_DOCUMENTS = [
    dict(id="EML-2026-11-12", type="email", title="Email from Meccanica Chisone: 8D-25-031 and 6082-T6",
         date="2026-11-12", author="SUP-C", valid_from="2026-11-12", valid_to=None, supersedes=None,
         mentions=["SUP-C", "8D-25-031", "MAT-6082-T6", "PER-GALLO"],
         body="""From: Meccanica Chisone, quality office. To: Elena Gallo. Subject: 8D-25-031 and BR-220.
We expect to have 8D-25-031 closed by 20 Nov: the corrective action on the ageing furnace is installed and in verification.
We plan to be qualified for EN AW-6082-T6 from December, the first trial lot is planned for 1 December.
Until then please keep us in mind for BR-220.""",
         # Two promises, typed PLAN (class Commitment). Asserted: the e-mail is the record that the promise was
         # made; it is not evidence that the 8D is closed or the capability exists.
         facts=[
             ("PRM-C-8D-CLOSE", "type", "Commitment", "8D-25-031 closed by 20 Nov", "assert"),
             ("PRM-C-8D-CLOSE", "promisedBy", "SUP-C", "From: Meccanica Chisone", "assert"),
             ("PRM-C-8D-CLOSE", "promisesClosureOf", "8D-25-031", "8D-25-031 closed by 20 Nov", "assert"),
             ("PRM-C-8D-CLOSE", "horizon", '"2026-11-20"', "closed by 20 Nov", "assert"),
             ("PRM-C-8D-CLOSE", "followedUpBy", "PER-GALLO", "To: Elena Gallo", "assert"),
             ("PRM-C-6082T6", "type", "Commitment", "qualified for EN AW-6082-T6 from December", "assert"),
             ("PRM-C-6082T6", "promisedBy", "SUP-C", "From: Meccanica Chisone", "assert"),
             ("PRM-C-6082T6", "promisesCapability", "MAT-6082-T6", "qualified for EN AW-6082-T6 from December",
              "assert"),
             ("PRM-C-6082T6", "horizon", '"2026-12-01"', "the first trial lot is planned for 1 December", "assert"),
             ("PRM-C-6082T6", "followedUpBy", "PER-GALLO", "To: Elena Gallo", "assert"),
         ]),
    dict(id="FMEA-BR220-B", type="fmea", title="Process FMEA BR-220, revision B (excerpt)",
         date="2026-11-12", author="PER-ROMANO", valid_from="2026-11-12", valid_to=None, supersedes="FMEA-BR220",
         mentions=["BR-220", "MAT-6082-T6", "SC-BR220-YS"],
         body="""PFMEA BR-220 revision B, line 12. Failure mode: crack at the fastening holes under fatigue load.
Cause: wrong alloy or temper of the blank (yield below 240 MPa). Severity 9.
Special characteristic SC-BR220-YS: minimum yield 240 MPa.
Prevention: blanks only from sources approved for EN AW-6082-T6; material certificate 3.1 per lot.
Detection: hardness check per lot, control plan line 30.""",
         # A mention: the FMEA restates the characteristic owned by the control plan (250 MPa). The control-plan
         # value stays in force; core/memory.py shows the two side by side as a contradiction for a person.
         facts=[
             ("SC-BR220-YS", "minYieldMPa", '"240"', "Special characteristic SC-BR220-YS: minimum yield 240 MPa",
              "mention"),
         ]),
]
