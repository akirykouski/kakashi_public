"""Check the mini-company for consistency. Exit code 1 on any error.

Checks: every quote is a substring of its source text; every entity id used as an object exists;
every supersedes target exists; valid_from <= valid_to.
"""
import json
import os
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_INDIVIDUALS = {
    "SourceChange", "MaterialChange", "ProcessChange", "CoatingChange", "ScheduleChange", "PackagingChange",
    "NewBusinessHold", "RegistrarNotification", "Chargeback", "ControlledShipping",
    "Series6xxx", "Series3xxxCast", "CrVI", "CrIII", "Lead", "Cadmium", "Mercury", "Zinc", "Nickel", "MKT-EU",
}
CLASS_NAMES = {
    "Part", "Material", "Alloy", "AlloyTemper", "Steel", "Polymer", "Coating", "Supplier", "Customer", "Site",
    "Program", "Market", "Person", "PartApproval", "SupplierQualification", "SupplierCapability", "MaterialCertificate",
    "SpecialCharacteristic", "CustomerRequirement", "Law", "Standard", "InternalProcedure", "Document",
    "EightD", "NCR", "Deviation", "Decision",
}


def load_jsonl(name):
    with open(os.path.join(DATA_DIR, name)) as file:
        return [json.loads(line) for line in file]


def main():
    facts = load_jsonl("facts.jsonl")
    corpus = {item["id"]: item for item in load_jsonl("corpus.jsonl")}
    errors = []
    subjects = {fact["s"] for fact in facts} | set(corpus) | SCHEMA_INDIVIDUALS
    for fact in facts:
        text = corpus.get(fact["source"], {}).get("text")
        if text is None:
            errors.append(f"{fact['id']}: unknown source {fact['source']}")
        elif fact["quote"] not in text:
            errors.append(f"{fact['id']}: quote not in {fact['source']}: {fact['quote']!r}")
        obj = fact["o"]
        if fact["p"] == "type":
            if obj not in CLASS_NAMES:
                errors.append(f"{fact['id']}: unknown class {obj}")
        elif not obj.startswith('"') and obj not in subjects:
            errors.append(f"{fact['id']}: unknown object {obj} ({fact['s']} {fact['p']})")
        if fact["valid_from"] and fact["valid_to"] and fact["valid_from"] > fact["valid_to"]:
            errors.append(f"{fact['id']}: valid_from after valid_to")
    for error in errors:
        print("ERROR", error)
    print(f"{len(facts)} facts, {len(corpus)} sources, {len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
