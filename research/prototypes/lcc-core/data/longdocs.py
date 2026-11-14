"""Long, realistic versions of the documents whose facts feed the rules (test of fact extraction).

Each long document = generated filler sections (fictional, cached, deterministic on rerun) + the original body
copied verbatim in the middle + hand-written traps that a careless extractor turns into wrong facts:
a revision history quoting the old rule, a clause about another customer or division, a closed issue next to
the open one, an expired deviation next to the valid one.

  python data/longdocs.py            # writes data_long/docs/<id>.md and data_long/traps.json

Filler comes from `claude -p` through bench/llm.py (disk cache, no API keys). Paragraphs that state a rule,
a status, a substance or another record id are dropped, so the filler cannot carry facts of its own.
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import yaml

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DATA_DIR)
sys.path.insert(0, DATA_DIR)
sys.path.insert(0, os.path.join(ROOT, "bench"))

import llm  # noqa: E402
from world import DOCUMENTS  # noqa: E402

OUT_DIR = os.path.join(ROOT, "data_long")
MODEL = "sonnet"
SECTIONS_PER_CALL = 3

FILLER_SYSTEM = ("You write long, realistic but entirely fictional industrial documents for a software test "
                 "dataset. Companies and people are fictional. Write in plain professional English.")
FILLER_SCHEMA = {
    "type": "object",
    "properties": {"sections": {"type": "array", "items": {
        "type": "object", "properties": {"heading": {"type": "string"}, "text": {"type": "string"}},
        "required": ["heading", "text"]}}},
    "required": ["sections"],
}

MANUAL_SECTIONS = [
    ("Scope, applicability and order of precedence", "who the manual applies to, how it relates to purchase orders"),
    ("Definitions and abbreviations", "long glossary of quality terms: APQP, PPAP, PSW, control plan, MSA, SPC"),
    ("Supplier selection and onboarding", "questionnaires, capacity checks, financial checks, site visits"),
    ("Advanced product quality planning and launch", "phases, gateways, run-at-rate, launch containment"),
    ("Measurement systems and statistical process control", "gauge R&R limits, Cpk targets, sampling"),
    ("Special characteristics and control plans", "symbols, how they are marked on drawings, reaction plans"),
    ("Packaging, labelling and identification", "returnable containers, labels, barcodes, cleanliness"),
    ("Logistics, delivery performance and scheduling", "EDI, forecasts, delivery windows, premium freight"),
    ("Nonconforming product and problem solving", "complaint handling, response times, 8D format, chargebacks"),
    ("Warranty and field returns", "no-trouble-found analysis, cost recovery, return parts"),
    ("Supplier performance scorecard and escalation", "KPIs, levels of escalation, new business hold"),
    ("Traceability, records retention and audits", "retention periods, lot traceability, audit schedule"),
]
LAW_SECTIONS = [
    ("Purpose of this compliance dossier", "internal dossier of Valsangone Componenti on vehicle end-of-life rules"),
    ("Background: end-of-life vehicles in the EU", "why the rules exist, collection and treatment in general"),
    ("Collection and certificates of destruction", "what vehicle makers and dismantlers do; our role is indirect"),
    ("Reuse, recycling and recovery targets", "percent targets in general terms, how makers ask suppliers for data"),
    ("Coding standards and dismantling information", "part marking of plastics, dismantling manuals"),
    ("Material data reporting in IMDS", "how we submit material data sheets, roles, rejections, deadlines"),
    ("Supplier declarations and our sub-supplier chain", "declaration forms, frequency, follow-up of missing ones"),
    ("Monitoring of regulatory changes", "who watches legal changes, monthly review, sources we read"),
    ("Training and responsibilities", "training plan, RACI table for compliance tasks"),
    ("Internal audit of compliance", "audit checklist, sampling of parts, findings handling"),
    ("Records and evidence", "where evidence is filed, retention"),
    ("Glossary", "terms used in the dossier"),
]
EIGHTD_SECTIONS = [
    ("D0 Symptom and emergency response", "first notice, who was informed, first actions in hours"),
    ("D1 Team", "team table with fictional names and roles at Valsangone and the supplier"),
    ("D3 Containment details", "sorting plan, quantities sorted, stock locations, clean-point marking"),
    ("Measurement results", "tables of measurements per lot, sample sizes, gauges used"),
    ("D4 Ishikawa analysis", "man, machine, method, material, measurement, environment, each discussed"),
    ("D4 Five-why analysis and verification tests", "why chains, lab tests, metallography or lab results"),
    ("D5 and D6 Candidate corrective actions", "options considered, trials planned, owners and dates"),
    ("D7 Preventive actions and lessons learned", "FMEA and control plan updates planned, other lines checked"),
    ("Cost of poor quality", "sorting hours, scrap, freight, cost table"),
    ("Communication log", "dated log of calls, emails and meetings with the supplier"),
    ("Attachments list", "photos, lab reports, sorting sheets, described"),
    ("Sign-off table", "names, functions, signatures pending"),
]
DEVIATION_SECTIONS = [
    ("Request and justification", "why the deviation was requested, supply situation, alternatives considered"),
    ("Affected product and lots", "lot numbers, quantities, traceability table"),
    ("Risk assessment", "failure modes, severity, occurrence, detection, conclusion"),
    ("Corrosion test plan", "salt spray per ISO 9227, sample sizes, acceptance criteria, lab"),
    ("Additional inspection", "inspection plan, gauges, recording sheets"),
    ("Labelling and segregation", "how deviated parts are identified and kept apart"),
    ("Customer communication", "what was sent to the customer, meeting notes"),
    ("Exit plan", "rack redesign trials, milestones to return to the nominal layer"),
    ("Cost and capacity", "extra cost of testing and inspection, capacity impact"),
    ("Monitoring log", "weekly log of salt spray results per lot, all passed"),
    ("Training of operators", "who was trained, when, on what"),
    ("Approvals and distribution", "distribution list, signature table"),
]

# Per document: kind, filler sections, context sentence, where the body goes, traps (text + facts they tempt)
TARGETS = {
    "CSR-AUR-R3": {
        "sections": MANUAL_SECTIONS, "body_after": 6,
        "context": "Aurelia Automobili S.p.A. (fictional carmaker) supplier quality manual, revision 3 (2024). "
                   "The section on changes is section 7 and is not part of your text.",
        "traps": [
            {"after_body": True, "text": "Informative note (not in force). The draft of revision 4, circulated to "
             "suppliers for comment, proposes that a change of coating or surface treatment shall require approval "
             "by Aurelia. Until revision 4 is published, clause 7.2 of this revision applies.",
             "facts": [["CSR-AUR-R3", "requiresCustomerApprovalFor", "CoatingChange"]]},
            {"appendix": "Annex D Service parts supplied through Aurelia Ricambi",
             "text": "For service parts of discontinued models supplied through Aurelia Ricambi (a separate "
             "company of the group), a change of source requires notification to Aurelia Ricambi only, 30 days in "
             "advance. This annex does not apply to series production parts.",
             "facts": [["CSR-AUR-R3", "requiresNotificationFor", "SourceChange"]]},
        ]},
    "CSR-AUR-R4": {
        "sections": MANUAL_SECTIONS, "body_after": 6,
        "context": "Aurelia Automobili S.p.A. (fictional carmaker) supplier quality manual, revision 4 (July 2026). "
                   "The section on changes is section 7 and is not part of your text.",
        "traps": [
            {"appendix": "Annex A Revision history",
             "text": "| Revision | Date | Change |\n|---|---|---|\n| 2 | 2021-03-01 | First edition in English. |\n"
             "| 3 | 2024-01-01 | Clause 7.2 read: \"A change of coating or surface treatment within the same "
             "specification family requires notification to Aurelia at least 60 days before implementation; "
             "approval is not required.\" |\n| 4 | 2026-07-01 | Section 7 rewritten; see clause 7.1. |",
             "facts": [["CSR-AUR-R4", "requiresNotificationFor", "CoatingChange"]]},
            {"appendix": "Annex D Service parts supplied through Aurelia Ricambi",
             "text": "For service parts of discontinued models supplied through Aurelia Ricambi (a separate "
             "company of the group), a change of coating requires notification only. This annex does not apply "
             "to series production parts.",
             "facts": [["CSR-AUR-R4", "requiresNotificationFor", "CoatingChange"]]},
        ]},
    "CSR-NOR-R2": {
        "sections": MANUAL_SECTIONS, "body_after": 5,
        "context": "Nordhavn Trucks AB (fictional truck and van maker) customer specific requirements, revision 2 "
                   "(2025). The chapter on changes is chapter 5 and is not part of your text.",
        "traps": [
            {"after_body": True, "text": "Note on the Nordhavn Bus division. Parts for buses are governed by the "
             "separate document NB-CSR-1 and not by this document. Under NB-CSR-1 a change of material requires "
             "notification only.",
             "facts": [["CSR-NOR-R2", "requiresNotificationFor", "MaterialChange"]]},
            {"appendix": "Appendix 1 Revision history",
             "text": "| Revision | Date | Change |\n|---|---|---|\n| 1 | 2022-05-01 | Clause 5.2 read: \"A change "
             "of coating requires notification only, 30 days in advance.\" |\n| 2 | 2025-03-01 | Clause 5.2 now "
             "requires approval for coating changes. |",
             "facts": [["CSR-NOR-R2", "requiresNotificationFor", "CoatingChange"]]},
        ]},
    "LAW-ELV": {
        "sections": LAW_SECTIONS, "body_after": 6,
        "context": "Internal compliance dossier of Valsangone Componenti S.p.A. (fictional tier-1 automotive "
                   "supplier near Turin) on the EU end-of-life vehicles rules. The quoted article on hazardous "
                   "substances is in a separate section and is not part of your text.",
        "traps": [
            {"after_body": True, "text": "Substances that are not restricted. Trivalent chromium (Cr(III)) "
             "passivations are not covered by Article 4(2)(a) and are our standard replacement for chromate. "
             "Zinc and nickel in zinc-nickel coatings are not listed in Article 4(2)(a) either; nickel release "
             "is regulated elsewhere and does not concern our parts.",
             "facts": [["LAW-ELV", "restricts", "CrIII"], ["LAW-ELV", "restricts", "Zinc"],
                       ["LAW-ELV", "restricts", "Nickel"]]},
        ]},
    "8D-25-031": {
        "sections": EIGHTD_SECTIONS, "body_after": 3,
        "context": "8D report 8D-25-031 at Valsangone Componenti S.p.A. (fictional): cracks around fastening holes "
                   "on BR-310 roof rail brackets machined from EN AW-6082 extrusions delivered by Meccanica Chisone "
                   "S.r.l. (fictional supplier). Root cause still open. Do not state the report's status.",
        "traps": [
            {"section": 3, "text": "Containment action C1 (100% sort of stock at the Pinerolo plant, 2,340 parts, "
             "18 rejected). Status: closed on 2025-04-02. The 100% visual check of holes continues.",
             "facts": [["8D-25-031", "status", "\"closed\""]]},
            {"appendix": "Related reports",
             "text": "8D-24-044, Meccanica Chisone (SUP-C): burrs on BR-180 blanks in EN AW-6061-T6. Status: "
             "closed. Not related to the cracks; listed for supplier history only.",
             "facts": [["8D-25-031", "concernsMaterial", "MAT-6061-T6"], ["8D-25-031", "concernsPart", "BR-180"],
                       ["8D-24-044", "status", "\"closed\""]]},
        ]},
    "8D-26-009": {
        "sections": EIGHTD_SECTIONS, "body_after": 4,
        "context": "8D report 8D-26-009 at Valsangone Componenti S.p.A. (fictional): porosity in the mount bores "
                   "of HB-620 gearbox mount housings, die cast in AlSi9Cu3 by Fonderia Dora (fictional supplier). "
                   "Do not state the report's status.",
        "traps": [
            {"appendix": "Related reports",
             "text": "8D-25-007, Fonderia Dora (SUP-D): flash on HB-620 parting line. Status: closed in 2025. "
             "Also related: the containment sort at the Nordhavn line is closed.",
             "facts": [["8D-26-009", "status", "\"closed\""], ["8D-25-007", "status", "\"closed\""]]},
        ]},
    "NCR-26-017": {
        "sections": EIGHTD_SECTIONS[:9], "body_after": 3,
        "context": "Nonconformance report NCR-26-017 at Valsangone Componenti S.p.A. (fictional): CL-115 cable "
                   "clips in C67S spring steel from Minuterie Germanasca (fictional supplier) measured too hard. "
                   "Write it as an NCR investigation file. Do not state the report's status.",
        "traps": [
            {"appendix": "Supplier history",
             "text": "NCR-25-088, Minuterie Germanasca (SUP-G): CL-115 hardness at the upper limit in 2025. "
             "Status: closed after retraining of the heat treatment operators. A similar issue on HS-410 heat "
             "shields (DC04) at another supplier is unrelated.",
             "facts": [["NCR-26-017", "status", "\"closed\""], ["NCR-26-017", "concernsPart", "HS-410"],
                       ["NCR-26-017", "concernsMaterial", "MAT-DC04"]]},
        ]},
    "DEV-121": {
        "sections": DEVIATION_SECTIONS, "body_after": 5,
        "context": "Deviation DEV-121 at Valsangone Componenti S.p.A. (fictional): HS-410 heat shields with a "
                   "thinner zinc-nickel layer, coated by Galvanica Eporediese (fictional supplier), customer "
                   "Aurelia Automobili. Do not state the deviation's status or its validity dates.",
        "traps": [
            {"section": 1, "text": "History. This deviation follows DEV-109 (HS-410, zinc-nickel at least 7 um, "
             "valid until 2025-12-31). Status of DEV-109: expired.",
             "facts": [["DEV-121", "status", "\"expired\""], ["DEV-109", "status", "\"expired\""]]},
            {"section": 6, "text": "A separate request to apply the same relaxation to CL-115 cable clips from "
             "Minuterie Germanasca (SUP-G) was not accepted and is not covered by this deviation.",
             "facts": [["DEV-121", "concernsPart", "CL-115"], ["DEV-121", "concernsSupplier", "SUP-G"]]},
        ]},
}

FORBIDDEN_COMMON = [r"Status\s*:", r"\b(8D|NCR|DEV|CSR|QP|LAW)-[A-Z0-9-]*\d", r"\bhexavalent\b", r"\bcadmium\b",
                    r"\bmercury\b", r"\bchromate\b", r"Cr\s*\(?\s*(VI|III)"]
FORBIDDEN_RULES = [r"\bPPAP resubmission\b", r"\brequires? (written |prior )?(customer |\w+ )?approval\b",
                   r"\bnotif(y|ied|ication)\b", r"\bchange of (source|material|coating|process)\b"]
FORBIDDEN_LAW = [r"\blead\b(?! time)", r"\bnickel\b", r"\bzinc\b", r"\bchromium\b", r"\brestrict", r"\bprohibit"]


def forbidden_patterns(doc_id):
    patterns = list(FORBIDDEN_COMMON)
    if doc_id.startswith("CSR"):
        patterns += FORBIDDEN_RULES
    if doc_id == "LAW-ELV":
        patterns += FORBIDDEN_LAW
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def clean_filler(doc_id, text):
    """Drop paragraphs that could carry a fact of their own. Returns (text, dropped_count)."""
    patterns = forbidden_patterns(doc_id)
    kept, dropped = [], 0
    for paragraph in text.split("\n\n"):
        if any(pattern.search(paragraph) for pattern in patterns):
            dropped += 1
        else:
            kept.append(paragraph)
    return "\n\n".join(kept), dropped


def filler_prompt(spec, batch):
    lines = [f"Document: {spec['context']}",
             "Write the following sections of this document. Each section 1,200 to 1,600 words, with numbered "
             "subsections, concrete fictional numbers, and at least one markdown table per section.", ""]
    for heading, brief in batch:
        lines.append(f"- {heading}: {brief}")
    lines += ["", "Hard rules: do not write any rule about which changes need customer approval or notification; "
              "do not state the status of any report, deviation or document; do not name any hazardous or "
              "restricted substance; do not mention any other report, deviation or document number; do not "
              "write a revision history."]
    return "\n".join(lines)


def generate_filler(doc_id, spec):
    batches = [spec["sections"][start:start + SECTIONS_PER_CALL]
               for start in range(0, len(spec["sections"]), SECTIONS_PER_CALL)]
    sections, dropped, tokens = [], 0, 0
    for batch in batches:
        output, usage, _, _ = llm.call(MODEL, FILLER_SYSTEM, filler_prompt(spec, batch), FILLER_SCHEMA)
        tokens += usage.get("output_tokens", 0)
        for (heading, _), section in zip(batch, output["sections"]):
            text, count = clean_filler(doc_id, section["text"])
            dropped += count
            sections.append((heading, text))
    return sections, dropped, tokens


def assemble(document, spec, sections):
    parts = [f"# {document['title']}", ""]
    body_heading = "Changes" if document["type"] == "customer_requirement" else "Record"
    section_traps = {}
    for trap in spec["traps"]:
        if "section" in trap:
            section_traps.setdefault(trap["section"], []).append(trap["text"])
    for index, (heading, text) in enumerate(sections, start=1):
        parts += [f"## {index}. {heading}", "", text, ""]
        for trap_text in section_traps.get(index, []):
            parts += [trap_text, ""]
        if index == spec["body_after"]:
            parts += [f"## {body_heading}", "", document["body"].strip(), ""]
            for trap in spec["traps"]:
                if trap.get("after_body"):
                    parts += [trap["text"], ""]
    for trap in spec["traps"]:
        if "appendix" in trap:
            parts += [f"## {trap['appendix']}", "", trap["text"], ""]
    return "\n".join(parts)


def write_document(document, text):
    header = {key: document.get(key) for key in
              ("id", "type", "title", "date", "author", "valid_from", "valid_to", "supersedes", "mentions")}
    path = os.path.join(OUT_DIR, "docs", f"{document['id']}.md")
    with open(path, "w") as file:
        file.write("---\n" + yaml.safe_dump(header, sort_keys=False, allow_unicode=True) + "---\n")
        file.write(text.strip() + "\n")
    return path


def build_one(doc_id):
    document = next(item for item in DOCUMENTS if item["id"] == doc_id)
    spec = TARGETS[doc_id]
    sections, dropped, tokens = generate_filler(doc_id, spec)
    text = assemble(document, spec, sections)
    for _, _, _, quote in document["facts"]:
        if quote not in text:
            raise ValueError(f"{doc_id}: original quote lost: {quote!r}")
    write_document(document, text)
    return {"id": doc_id, "chars": len(text), "approx_tokens": len(text) // 4, "dropped_paragraphs": dropped,
            "filler_output_tokens": tokens}


def main():
    os.makedirs(os.path.join(OUT_DIR, "docs"), exist_ok=True)
    wanted = sys.argv[1].split(",") if len(sys.argv) > 1 else list(TARGETS)
    with ThreadPoolExecutor(max_workers=4) as pool:
        stats = list(pool.map(build_one, wanted))
    traps = {doc_id: [fact for trap in TARGETS[doc_id]["traps"] for fact in trap["facts"]] for doc_id in TARGETS}
    with open(os.path.join(OUT_DIR, "traps.json"), "w") as file:
        json.dump(traps, file, indent=1)
    for row in stats:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
