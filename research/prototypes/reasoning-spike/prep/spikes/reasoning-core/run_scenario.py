"""PREP SPIKE test. Exits 0 only if every assertion holds.

Run from the repo root:
  uv run --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 \
      python prep/spikes/reasoning-core/run_scenario.py
"""
import copy
import random
import sys
import time
from pathlib import Path

from rdflib import RDF

sys.path.insert(0, str(Path(__file__).parent))
from core import (CC, DATA, Explainer, check, closure, functional_predicates, leaves,  # noqa: E402
                  load_scenario, load_shapes, load_tbox, quote_problems, render, snapshot, without_source_doc)

tbox, shapes = load_tbox(), load_shapes()
functional = functional_predicates(tbox)
facts = load_scenario()
passed = 0


def ok(cond, label):
    global passed
    if not cond:
        print(f"FAIL  {label}")
        sys.exit(1)
    passed += 1
    print(f"PASS  {label}")


def card(fs, valid_at, known_at, tb=None):
    snap = snapshot(fs, functional, valid_at, known_at)
    g, asserted = closure(snap["facts"], tb or tbox)
    return snap, g, asserted, check(g, shapes)


def types(items, severity):
    return sorted(i["type"] for i in items if i["severity"] == severity)


# ------------------------------------------------- quotes against documents
problems = quote_problems(facts)
for p in problems:
    print(f"      {p}")
ok(not problems, f"every quote of all {len(facts)} facts is a literal substring of its data/sources document (or of the CR-01 request text)")
ok(all((DATA / "sources" / f"{f['doc']}.md").is_file() for f in facts if not f["doc"].startswith("CR-")),
   "every fact's doc id is a data/sources doc_id (only CR-NN request ids are allowed beside them)")
mut = copy.deepcopy(facts)
mut[0]["quote"] = mut[0]["quote"] + " (altered)"
ok(len(quote_problems(mut)) == 1, "the quote check is live: one altered quote is reported")

# ---------------------------------------------------------------- state 1
t0 = time.time()
snap1, g1, asserted1, items1 = card(facts, "2026-11-10", "2026-11-10T23:59")
ms = (time.time() - t0) * 1000
print(f"\n== State 1: known on 10 Nov ({len(snap1['facts'])} facts in force, {len(g1)} triples after closure, {ms:.0f} ms)")
# 4 blockers, not 5: EML-SQ-2026-1105 revoked the probation on 5 Nov, before this request (data gold CR-01 lists these four)
ok(types(items1, "Blocker") == ["B_CUSTOMER_APPROVAL_REQUIRED", "B_MATERIAL_MISMATCH", "B_NO_SOURCE_RELEASE",
                                "B_OPEN_8D_SAME_ALLOY"], "state 1: exactly the four expected blockers (probation already revoked)")
ok(types(items1, "Question") == ["Q_NO_MATERIAL_CERT"], "state 1: exactly one open question (missing certificate)")

# ------------------------------------------------ product path: 1105 not yet accepted
# The product reads the e-mail as a document; until EML-SQ-2026-1105 is accepted its facts are absent.
DOC = "EML-SQ-2026-1105"
n1105 = [f for f in facts if f["doc"] == DOC]
ok(len(n1105) > 0, f"the scenario holds facts sourced from {DOC} ({len(n1105)})")
_, _, _, items_w = card(without_source_doc(facts, DOC), "2026-11-10", "2026-11-10T23:59")
four = ["B_CUSTOMER_APPROVAL_REQUIRED", "B_MATERIAL_MISMATCH", "B_NO_SOURCE_RELEASE", "B_OPEN_8D_SAME_ALLOY"]
ok(types(items_w, "Blocker") == sorted(four + ["B_SUPPLIER_NOT_QUALIFIED"]) and len(types(items_w, "Blocker")) == 5
   and types(items_w, "Question") == ["Q_NO_MATERIAL_CERT"],
   f"CR-01 at 10 Nov with all {DOC} facts withheld: exactly 4 blockers + B_SUPPLIER_NOT_QUALIFIED (5) + Q_NO_MATERIAL_CERT")
_, _, _, items_i = card(facts, "2026-11-10", "2026-11-10T23:59")
ok(types(items_i, "Blocker") == four and len(types(items_i, "Blocker")) == 4 and types(items_i, "Question") == ["Q_NO_MATERIAL_CERT"],
   f"CR-01 at 10 Nov with {DOC} facts included: exactly 4 blockers + Q_NO_MATERIAL_CERT")

# ------------------------------------------------ inferred facts and proofs
ex = Explainer(tbox, g1, asserted1)
hist = (CC.MeccanicaC, CC.hasSeriesQualityHistoryOn, CC.BR220)
ok(hist in g1 and hist not in asserted1, "series-level quality-history link is inferred, never asserted")
ok((CC.MeccanicaC, CC.hasQualityHistoryOn, CC.BR220) not in g1,
   "the alloy-level link is NOT derived: the 8D is on 6061, the part on 6082, they only share series 6xxx")
proof = ex.explain(hist)
docs = sorted({leaf["doc"] for leaf in leaves(proof) if leaf["source"] == "fact"})
ok(docs == ["8D-25-031", "DWG-BR220-RevC"], "its proof rests on the 8D report and the drawing, two documents that never mention each other")
ok(all(leaf.get("quote") for leaf in leaves(proof) if leaf["source"] == "fact"), "every fact leaf of the proof carries a quote")
print(render(proof, 1))

subj = (CC.BR220, CC.subjectTo, CC.CSR_STL_8_5_6_1)
proof2 = ex.explain(subj)
ok(sorted({leaf["doc"] for leaf in leaves(proof2)}) == ["BOM-STL-TORINO-27", "CSR-STL-2026-02"], "customer clause reaches the part through programme and customer")
print(render(proof2, 1))
cls = (CC.ECN_26_0147, RDF.type, CC.ProductOrProcessChange)
proof3 = ex.explain(cls)
ok(proof3 is not None and "rule" in proof3, "a raw-material source change is classified as a product-or-process change by subsumption")
print(render(proof3, 1))

for item in items1:
    for t in item["evidence"]:
        ok(ex.explain(t) is not None, f"evidence explained: {item['type']}: {t[1].split('#')[-1]}")

# ------------------------------------------- probation era (same request, replayed)
replay = copy.deepcopy(facts)
for f in replay:
    if f["id"].startswith("c"):
        f["valid_from"], f["recorded_at"] = "2026-10-20", "2026-10-20T08:30"
_, _, _, items0 = card(replay, "2026-10-20", "2026-11-14T08:00")
# known_at is today: the document facts were recorded on 1 Nov, the replay asks "had the request come on 20 Oct, as we know it now"
ok(types(items0, "Blocker") == sorted(types(items1, "Blocker") + ["B_SUPPLIER_NOT_QUALIFIED"]),
   "same request filed 20 Oct (probation in force): the four plus the supplier-level blocker")

# ---------------------------------------------------------------- state 2
snap2, g2, asserted2, items2 = card(facts, "2026-11-14", "2026-11-14T08:00")
print("\n== State 2: known on 14 Nov (probation revoked, Rev B superseded, one e-mail restating the Rev B alloy)")
ok(types(items2, "Blocker") == types(items1, "Blocker"), "14 Nov: same four blockers; the revocation clears ONLY the supplier-level one")
note_types = sorted(n["type"] for n in snap2["notes"])
ok("superseded" in note_types, "old standing (probation) and Rev B alloy are superseded, not deleted")
ok("stale_mention" in note_types, "the e-mail restating the Rev B alloy 6061-T6 is a stale mention and does not win")
ok(snap2["contested"] == [], "the document set has no contested fact")
contest = copy.deepcopy(facts) + [dict(id="x02", s="cc:R8D_25_031", p="cc:reportStatus", o="closed", lit=True, kind="assert", rank=3,
                                       valid_from="2026-11-13", recorded_at="2026-11-13T11:00", doc="SYNTHETIC-TEST",
                                       quote="test-only: supplier claims the 8D is closed", author="agent:test", status="accepted")]
snap_x, *_ = card(contest, "2026-11-14", "2026-11-14T08:00")
# test-only injection: the frozen data holds no such e-mail, so the contested path is exercised with a synthetic fact
ok(snap_x["contested"] == [{"key": ("cc:R8D_25_031", "cc:reportStatus"), "head": "f33", "challenger": "x02"}],
   "a newer lower-authority 'closed' claim cannot overrule the controlled 8D record; reported as contested")

# ------------------------------------------------------------- time travel
_, _, _, back = card(facts, "2026-11-01", "2026-11-14T08:00")
ok(types(back, "Blocker") == [],
   "valid time 1 Nov: the change request does not exist yet, nothing fires")
snap_v, *_ = card(facts, "2026-11-04", "2026-11-14T08:00")
grade = [f["o"] for f in snap_v["facts"] if f["p"] == "cc:supplierStanding"]
ok(grade == ["probation"], "as we know today, the standing in force on 4 Nov was still probation (revoked 5 Nov)")

# ------------------------------------------------------- order independence
ref = [f["id"] for f in snap2["facts"]], snap2["notes"], snap2["contested"]
rnd = random.Random(7)
same = True
for _ in range(200):
    shuffled = copy.deepcopy(facts)
    rnd.shuffle(shuffled)
    s = snapshot(shuffled, functional, "2026-11-14", "2026-11-14T08:00")
    same &= ([f["id"] for f in s["facts"]], s["notes"], s["contested"]) == ref
ok(same, "snapshot identical under 200 random write orders")

# ------------------------------------------------------- taxonomy, not text
alt = copy.deepcopy(facts)
for f in alt:
    if f["id"] == "c08":
        f["o"] = "cc:EN_AW_6082_T651"
_, _, _, items_alt = card(alt, "2026-11-10", "2026-11-10T23:59")
ok("B_MATERIAL_MISMATCH" not in types(items_alt, "Blocker"), "6082-T651 offered against a 6082-T6 drawing: no mismatch (refinement)")

# ------------------------------------------------------ scoped closed world
no_cs = [f for f in facts if f["id"] not in ("f24", "f25", "f26", "f27")]
_, _, _, items_ncs = card(no_cs, "2026-11-10", "2026-11-10T23:59")
ok("B_NO_SOURCE_RELEASE" not in types(items_ncs, "Blocker") and "Q_SOURCE_RELEASE_UNKNOWN" in types(items_ncs, "Question"),
   "without a completeness statement the missing release is a question, not a blocker")

# ---------------------------------------------------------- rules as data
tbox_np = load_tbox()
tbox_np.remove((CC.Policy_8D_SERIES, RDF.type, CC.CompanyPolicy))
_, _, _, items_np = card(facts, "2026-11-10", "2026-11-10T23:59", tbox_np)
ok("B_OPEN_8D_SAME_ALLOY" not in types(items_np, "Blocker"), "retiring rule SERIES-8D (policy 8D) switches its blocker off with no code change")

# ------------------------------------------- series-level match is a named rule
other_series = copy.deepcopy(facts)
for f in other_series:
    if f["id"] == "f31":
        f["o"] = "cc:EN_AW_5083_H111"
_, _, _, items_os = card(other_series, "2026-11-10", "2026-11-10T23:59")
ok("B_OPEN_8D_SAME_ALLOY" not in types(items_os, "Blocker"), "SERIES-8D: an 8D on a 5xxx alloy does not block a 6xxx part")
no_feat = [f for f in facts if f["id"] != "f32"]
_, _, _, items_nf = card(no_feat, "2026-11-10", "2026-11-10T23:59")
ok("B_OPEN_8D_SAME_ALLOY" not in types(items_nf, "Blocker"), "SERIES-8D: same series without the same failure feature does not block")
closed = copy.deepcopy(facts)
for f in closed:
    if f["id"] == "f33":
        f["o"] = "closed"
_, _, _, items_cl = card(closed, "2026-11-10", "2026-11-10T23:59")
ok("B_OPEN_8D_SAME_ALLOY" not in types(items_cl, "Blocker"), "SERIES-8D: a closed 8D does not block")

# ---------------------------------------------------------- hard conflict
clash = copy.deepcopy(facts) + [dict(id="x01", s="cc:MeccanicaC", p="cc:supplierStanding", o="probation", lit=True, kind="assert", rank=3,
                                     valid_from="2026-11-05", recorded_at="2026-11-13T12:00", doc="SYNTHETIC-TEST",
                                     quote="test-only: second e-mail, same day, opposite standing", author="agent:b", status="accepted")]
snap_c, _, _, items_c = card(clash, "2026-11-14", "2026-11-14T08:00")
ok(any(n["type"] == "conflict" for n in snap_c["notes"]) and "Q_SUPPLIER_QUALIFICATION_UNKNOWN" in types(items_c, "Question"),
   "two same-authority, same-date standings: neither is in force, the card asks instead of guessing")

print(f"\n{passed} checks passed")
