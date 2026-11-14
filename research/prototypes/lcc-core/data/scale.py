"""Exploratory (not pre-registered): grow the company with distractor suppliers, parts and documents.

Distractors never touch the entities of the benchmark requests (new suppliers, new parts, new programs), so
the gold findings stay the same. Only the amount of text a reader has to go through grows.

  python data/scale.py --units 90 --out data_scale     # writes the same files as build.py into data_scale/
"""
import argparse
import copy
import os
import random
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DATA_DIR)

import build  # noqa: E402
from meetings import MEETINGS  # noqa: E402
from world import DOCUMENTS, REGISTRIES  # noqa: E402

TOWNS = ["Avigliana", "Bussoleno", "Chieri", "Ciriè", "Cuorgè", "Giaveno", "Ivrea", "Lanzo", "Moncalieri",
         "Orbassano", "Rivoli", "Susa", "Trofarello", "Venaria", "Volpiano", "Carmagnola", "Bra", "Alba"]
TRADES = ["Meccanica", "Lavorazioni", "Fonderia", "Stampaggi", "Minuterie", "Tecnoplast", "Officina"]
PART_KINDS = ["bracket", "clip", "housing", "spacer", "pin", "cover", "plate", "sleeve", "bushing", "shield"]
MATERIALS = ["MAT-6082-T6", "MAT-6061-T6", "MAT-6082-T5", "MAT-ALSI9CU3", "MAT-DC04", "MAT-C67S",
             "MAT-42CRMO4", "MAT-PA66GF30"]
SAFE_COATINGS = ["COAT-ANOD", "COAT-TCP", "COAT-ZNNI", "COAT-ZNFLAKE", ""]
PROBLEMS = ["dimensional drift on the main bore", "burrs on cut edges", "surface scratches after packing",
            "late deliveries for three weeks", "wrong label on two pallets", "porosity in thick sections",
            "hardness at the lower tolerance limit", "coating thickness at the upper limit"]


def add_units(registries, documents, meetings, units, seed=7):
    rng = random.Random(seed)
    people = [row[0] for row in registries["people"]["rows"]]
    for index in range(1, units + 1):
        supplier = f"SUP-X{index:03d}"
        name = f"{rng.choice(TRADES)} {rng.choice(TOWNS)} {index} S.r.l."
        program = f"PRG-S{index:03d}"
        customer = rng.choice(["CUST-AUR", "CUST-NOR"])
        site = rng.choice(["PLT-BEI", "PLT-PIN"])
        material = rng.choice(MATERIALS)
        year = rng.choice(["2023", "2024", "2025", "2026"])
        start = f"{year}-{rng.randint(1, 9):02d}-{rng.randint(10, 28)}"
        registries["suppliers"]["rows"].append([supplier, name, "machined and formed parts"])
        registries["programs"]["rows"].append([program, f"Program S{index:03d}", customer, "MKT-EU", start])
        registries["supplier_qualification"]["rows"].append(
            [f"QS-X{index:03d}", supplier, rng.choice(["approved", "approved", "conditional"]), start, "",
             "PER-BIANCHI", "", f"audit score {rng.randint(70, 95)}"])
        registries["capabilities"]["rows"].append([f"CAP-X{index:03d}", supplier, material, start])
        if rng.random() < 0.7:
            registries["certificates"]["rows"].append([f"CERT-X{index:03d}", supplier, material, "2026-10-01"])
        for part_number in range(2):
            part = f"XP-{index:03d}{part_number}"
            kind = rng.choice(PART_KINDS)
            registries["parts"]["rows"].append(
                [part, f"{kind.capitalize()} {part}", program, rng.choice("ABCD"), material,
                 rng.choice(SAFE_COATINGS), ""])
            registries["asl"]["rows"].append(
                [f"APR-X{index:03d}{part_number}", supplier, part, site, customer, "approved", start, "",
                 "PER-BIANCHI", ""])
            documents.append({
                "id": f"PC-{part}", "type": "part_card", "title": f"Part card {part}", "date": start,
                "author": "PER-ROSSI", "valid_from": start, "valid_to": None, "supersedes": None,
                "mentions": [part, program, material, supplier],
                "body": f"Part card {part}, {kind} for program {program}. Drawing material {material}. "
                        f"Approved source: {name} ({supplier}), delivered to {site}. Standard packaging, "
                        f"no special characteristics.", "facts": []})
        issue = f"8D-X{index:03d}"
        status = rng.choice(["open", "closed", "closed"])
        documents.append({
            "id": issue, "type": "8d", "title": f"8D {issue} {name}", "date": start, "author": "PER-GALLO",
            "valid_from": start, "valid_to": None, "supersedes": None, "mentions": [supplier, material],
            "body": f"8D report {issue}. Supplier: {name} ({supplier}). Opened {start}. Status: {status}.\n"
                    f"Problem: {rng.choice(PROBLEMS)} on parts in {material} for program {program}.\n"
                    f"Root cause and corrective action documented by the supplier.",
            "facts": [(issue, "concernsSupplier", supplier, f"Supplier: {name} ({supplier})"),
                      (issue, "concernsMaterial", material, f"on parts in {material}"),
                      (issue, "status", f'"{status}"', f"Status: {status}")]})
        meetings.append({
            "id": f"MTG-X{index:03d}", "title": f"Supplier review {name}", "date": start,
            "participants": ["PER-BIANCHI", "PER-GALLO"],
            "utterances": [["PER-GALLO", f"{name}: on-time delivery {rng.randint(80, 99)}% this quarter."],
                           [rng.choice(people), f"Keep the current schedule for program {program}."]],
            "decisions": []})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--units", type=int, default=90)
    parser.add_argument("--out", default="data_scale")
    args = parser.parse_args()
    registries = copy.deepcopy(REGISTRIES)
    documents = copy.deepcopy(DOCUMENTS)
    meetings = copy.deepcopy(MEETINGS)
    add_units(registries, documents, meetings, args.units)
    out_dir = os.path.join(os.path.dirname(DATA_DIR), args.out)
    build.main(out_dir, registries, documents, meetings)


if __name__ == "__main__":
    main()
