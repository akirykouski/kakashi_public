"""Benchmark requests with hand-written gold findings.

Gold was written from the documents and registries by reading them, before the engine was run on these
requests. Any later change to gold is logged in bench/GOLD_CHANGES.md with the reason.
Caveat we state on the slide: the same person wrote the data, the gold and the rules (no separation).

A finding is (rule, key):
  R1a supplier not qualified (conditional)          key = supplier id
  R1b supplier has no part approval for customer     key = "supplier|part|customer"
  R2  customer approval (PPAP) needed before ship    key = customer id
  R3  supplier has an open issue on part's material   key = issue id
  R5  coating contains a substance banned by law     key = substance id
  R6  material not qualified / below special char.   key = material id (drawing material for a source change,
                                                     new material for a material change)
  R8  change at a sub-tier supplier of the part          key = "sub-tier supplier|part|customer"
  R7  missing evidence -> question with owner         key = supplier_record | coating_substances |
                                                     material_data | material_certificate
Categories: direct, inferred, stale (supersession or time decides), missing (must ask), clean (must stay quiet),
subtier (T01-T03, appended later for the tier-chain rule R8; the first 36 lines of requests.jsonl are unchanged).
R7 also has key tier_link (no known chain from the sub-tier supplier to a supplier of the part).
"""
import json
import os

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
NOW = "2026-11-14"


def request(request_id, category, as_of, utterance, change, gold):
    return {"id": request_id, "category": category, "as_of": as_of, "utterance": utterance,
            "change": change, "gold": [{"rule": rule, "key": key} for rule, key in gold]}


REQUESTS = [
    # ---- direct ----------------------------------------------------------------------------------------
    request("D01", "direct", NOW, "Galvanica Eporediese offered to cast the HB-620 housings for us. Let's do it.",
            {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-E"},
            [("R1b", "SUP-E|HB-620|CUST-NOR"), ("R6", "MAT-ALSI9CU3"), ("R7", "material_certificate"),
             ("R2", "CUST-NOR")]),
    request("D02", "direct", NOW, "Move the SP-700 spacers from Plastiche Fenestrelle to Minuterie Germanasca.",
            {"type": "SourceChange", "part": "SP-700", "to_supplier": "SUP-G", "from_supplier": "SUP-F"},
            [("R1b", "SUP-G|SP-700|CUST-AUR"), ("R6", "MAT-PA66GF30"), ("R7", "material_certificate"),
             ("R2", "CUST-AUR")]),
    request("D03", "direct", NOW, "Let's add Alluminio Bormida as a second source for BR-180.",
            {"type": "SourceChange", "part": "BR-180", "to_supplier": "SUP-B"},
            [("R1b", "SUP-B|BR-180|CUST-AUR"), ("R2", "CUST-AUR")]),
    request("D04", "direct", NOW, "On HS-410 we replace zinc-nickel with zinc flake, it's cheaper.",
            {"type": "CoatingChange", "part": "HS-410", "new_coating": "COAT-ZNFLAKE"},
            [("R2", "CUST-AUR")]),
    request("D05", "direct", NOW, "PN-050 pins: switch to zinc with yellow chromate passivation.",
            {"type": "CoatingChange", "part": "PN-050", "new_coating": "COAT-ZN-YELLOW"},
            [("R5", "CrVI"), ("R2", "CUST-AUR")]),
    request("D06", "direct", NOW, "BR-310: use the yellow chromate conversion coating instead of the trivalent one.",
            {"type": "CoatingChange", "part": "BR-310", "new_coating": "COAT-CCC-YELLOW"},
            [("R5", "CrVI"), ("R2", "CUST-NOR")]),
    request("D07", "direct", NOW, "Meccanica Chisone can stamp the HS-410 heat shields, let's move them there.",
            {"type": "SourceChange", "part": "HS-410", "to_supplier": "SUP-C"},
            [("R1b", "SUP-C|HS-410|CUST-AUR"), ("R6", "MAT-DC04"), ("R7", "material_certificate"),
             ("R2", "CUST-AUR")]),
    request("D08", "direct", NOW, "To save cost, make BR-220 from EN AW-6061-T6 instead.",
            {"type": "MaterialChange", "part": "BR-220", "new_material": "MAT-6061-T6"},
            [("R6", "MAT-6061-T6"), ("R2", "CUST-AUR")]),
    # ---- inferred --------------------------------------------------------------------------------------
    request("I01", "inferred", "2026-11-05",
            "Alluminio Bormida is two weeks late. Let's take the BR-220 blanks from Meccanica Chisone, it's the same alloy.",
            {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C", "from_supplier": "SUP-B"},
            [("R1a", "SUP-C"), ("R1b", "SUP-C|BR-220|CUST-AUR"), ("R6", "MAT-6082-T6"), ("R2", "CUST-AUR"),
             ("R3", "8D-25-031"), ("R7", "material_certificate")]),
    request("I02", "inferred", "2026-10-01", "Can Meccanica Chisone take over the BR-225 blanks?",
            {"type": "SourceChange", "part": "BR-225", "to_supplier": "SUP-C"},
            [("R1a", "SUP-C"), ("R1b", "SUP-C|BR-225|CUST-AUR"), ("R6", "MAT-6082-T6"), ("R2", "CUST-AUR"),
             ("R3", "8D-25-031"), ("R7", "material_certificate")]),
    request("I03", "inferred", NOW, "Chisone will deliver BR-180 to Pinerolo from now on instead of Beinasco.",
            {"type": "SourceChange", "part": "BR-180", "to_supplier": "SUP-C", "site": "PLT-PIN"},
            [("R1b", "SUP-C|BR-180|CUST-AUR"), ("R2", "CUST-AUR")]),
    request("I04", "inferred", NOW, "Instead of zinc-nickel on CL-115, let's use the cheap yellow chromate passivation.",
            {"type": "CoatingChange", "part": "CL-115", "new_coating": "COAT-ZN-YELLOW"},
            [("R5", "CrVI"), ("R2", "CUST-AUR"), ("R2", "CUST-NOR")]),
    request("I05", "inferred", NOW, "We change the CNC program and fixture for BR-220 machining next week.",
            {"type": "ProcessChange", "part": "BR-220"},
            [("R2", "CUST-AUR")]),
    request("I06", "inferred", NOW, "Buy the BR-310 extrusions from Alluminio Bormida instead of Chisone.",
            {"type": "SourceChange", "part": "BR-310", "to_supplier": "SUP-B", "from_supplier": "SUP-C"},
            [("R1b", "SUP-B|BR-310|CUST-NOR"), ("R6", "MAT-6082-T5"), ("R7", "material_certificate"),
             ("R2", "CUST-NOR")]),
    request("I07", "inferred", NOW, "Meccanica Chisone could also make the PN-050 pins.",
            {"type": "SourceChange", "part": "PN-050", "to_supplier": "SUP-C"},
            [("R1b", "SUP-C|PN-050|CUST-AUR"), ("R6", "MAT-42CRMO4"), ("R7", "material_certificate"),
             ("R2", "CUST-AUR")]),
    request("I08", "inferred", NOW, "Chisone should ship BR-310 to Beinasco instead of Pinerolo.",
            {"type": "SourceChange", "part": "BR-310", "to_supplier": "SUP-C", "site": "PLT-BEI"},
            [("R1b", "SUP-C|BR-310|CUST-NOR"), ("R2", "CUST-NOR"), ("R3", "8D-25-031")]),
    request("I09", "inferred", NOW, "Fonderia Pellice can deliver HB-620 castings directly to Beinasco.",
            {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-H", "site": "PLT-BEI"},
            [("R1b", "SUP-H|HB-620|CUST-NOR"), ("R2", "CUST-NOR")]),
    # ---- stale -----------------------------------------------------------------------------------------
    request("S01", "stale", NOW, "Quality approved Chisone last week, so we can move BR-220 to them.",
            {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-C", "from_supplier": "SUP-B"},
            [("R1b", "SUP-C|BR-220|CUST-AUR"), ("R6", "MAT-6082-T6"), ("R2", "CUST-AUR"),
             ("R3", "8D-25-031"), ("R7", "material_certificate")]),
    request("S02", "stale", NOW, "Switch the BR-220 anodising to a trivalent conversion coating.",
            {"type": "CoatingChange", "part": "BR-220", "new_coating": "COAT-TCP"},
            [("R2", "CUST-AUR")]),
    request("S03", "stale", "2026-05-01", "Switch the BR-220 anodising to a trivalent conversion coating.",
            {"type": "CoatingChange", "part": "BR-220", "new_coating": "COAT-TCP"},
            []),
    request("S04", "stale", NOW, "Fonderia Dora is still on the approved list for HB-620, let's order from them again.",
            {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-D", "from_supplier": "SUP-H"},
            [("R1a", "SUP-D"), ("R1b", "SUP-D|HB-620|CUST-NOR"), ("R2", "CUST-NOR"), ("R3", "8D-26-009")]),
    request("S05", "stale", NOW, "Chisone passed the re-audit, so they can take over the BR-225 blanks.",
            {"type": "SourceChange", "part": "BR-225", "to_supplier": "SUP-C"},
            [("R1b", "SUP-C|BR-225|CUST-AUR"), ("R6", "MAT-6082-T6"), ("R2", "CUST-AUR"),
             ("R3", "8D-25-031"), ("R7", "material_certificate")]),
    request("S06", "stale", NOW,
            "Aurelia's manual says a coating change only needs notification, so we switch BK-330 to zinc flake.",
            {"type": "CoatingChange", "part": "BK-330", "new_coating": "COAT-ZNFLAKE"},
            [("R2", "CUST-AUR")]),
    request("S07", "stale", "2026-09-01", "Keep ordering HB-620 castings from Fonderia Dora.",
            {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-D"},
            [("R3", "8D-26-009")]),
    # ---- missing ---------------------------------------------------------------------------------------
    request("M01", "missing", NOW, "Viteria Lanzo quoted 20% less for the CL-115 clips, let's switch.",
            {"type": "SourceChange", "part": "CL-115", "to_supplier": "Viteria Lanzo"},
            [("R7", "supplier_record"), ("R1b", "Viteria Lanzo|CL-115|CUST-AUR"),
             ("R1b", "Viteria Lanzo|CL-115|CUST-NOR"), ("R2", "CUST-AUR"), ("R2", "CUST-NOR")]),
    request("M02", "missing", NOW, "Let's coat BR-180 with the new Nanoceram finish the coater showed us.",
            {"type": "CoatingChange", "part": "BR-180", "new_coating": "Nanoceram"},
            [("R7", "coating_substances"), ("R2", "CUST-AUR")]),
    request("M03", "missing", NOW, "Could we make BR-225 from EN AW-7075 instead?",
            {"type": "MaterialChange", "part": "BR-225", "new_material": "EN AW-7075"},
            [("R7", "material_data"), ("R2", "CUST-AUR")]),
    request("M04", "missing", NOW, "Viteria Lanzo can also cast HB-620, let's ask them for the next batch.",
            {"type": "SourceChange", "part": "HB-620", "to_supplier": "Viteria Lanzo"},
            [("R7", "supplier_record"), ("R1b", "Viteria Lanzo|HB-620|CUST-NOR"), ("R2", "CUST-NOR")]),
    # ---- clean -----------------------------------------------------------------------------------------
    request("C01", "clean", NOW, "We postpone the BR-220 delivery to Aurelia by one week.",
            {"type": "ScheduleChange", "part": "BR-220"}, []),
    request("C02", "clean", NOW, "Next HS-410 lot from Galvanica Eporediese comes with 6 um zinc-nickel again.",
            {"type": "CoatingChange", "part": "HS-410", "from_supplier": "SUP-E", "new_coating": "COAT-ZNNI"}, []),
    request("C03", "clean", NOW, "Chisone will pack BR-310 forty per layer from next week.",
            {"type": "PackagingChange", "part": "BR-310", "from_supplier": "SUP-C"}, []),
    request("C04", "clean", NOW, "BR-310 coating moves to the new trivalent line at Pinerolo, same process spec.",
            {"type": "ProcessChange", "part": "BR-310"}, []),
    request("C05", "clean", NOW, "HB-620 castings come from Fonderia Pellice from now on.",
            {"type": "SourceChange", "part": "HB-620", "to_supplier": "SUP-H", "from_supplier": "SUP-D"}, []),
    request("C06", "clean", NOW, "Double the CL-115 order for December.",
            {"type": "ScheduleChange", "part": "CL-115"}, []),
    request("C07", "clean", NOW, "Expedite the BR-220 blanks from Alluminio Bormida, pay the express freight.",
            {"type": "SourceChange", "part": "BR-220", "to_supplier": "SUP-B"}, []),
    request("C08", "clean", NOW, "Move the BK-330 delivery slot from Monday to Wednesday.",
            {"type": "ScheduleChange", "part": "BK-330"}, []),
    # ---- subtier (R8, appended after the first 36) -----------------------------------------------------
    request("T01", "subtier", NOW,
            "Trattamenti Termici Sangone, who age the BR-220 blanks for Bormida, will change their T6 ageing cycle from next month.",
            {"type": "ProcessChange", "part": "BR-220", "at_supplier": "SUP-I"},
            [("R8", "SUP-I|BR-220|CUST-AUR")]),
    request("T02", "subtier", NOW,
            "The billet homogeniser behind Chisone, Omogeneizzazione Piossasco, is moving to a new furnace and a shorter soak for the BR-310 billets.",
            {"type": "ProcessChange", "part": "BR-310", "at_supplier": "SUP-K"},
            [("R8", "SUP-K|BR-310|CUST-NOR")]),
    request("T03", "subtier", NOW,
            "A coater called Anodica Susa, who work for one of our suppliers, will change the passivation on BR-310.",
            {"type": "CoatingChange", "part": "BR-310", "at_supplier": "Anodica Susa"},
            [("R7", "supplier_record"), ("R7", "tier_link")]),
]


def main():
    path = os.path.join(BENCH_DIR, "requests.jsonl")
    with open(path, "w") as file:
        for item in REQUESTS:
            file.write(json.dumps(item) + "\n")
    counts = {}
    for item in REQUESTS:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    print(f"{len(REQUESTS)} requests {counts}, {sum(len(item['gold']) for item in REQUESTS)} gold findings")


if __name__ == "__main__":
    main()
