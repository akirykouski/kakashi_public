"""Tests of workstream F: ontology, data, fact log, snapshot, projection, integrity.

Ported tests: order independence over 200 shuffles and the stale-mention / contested cases come from
Arseniy's spike `prep/spikes/reasoning-core/run_scenario.py`; the proposal / conflict tests extend Maksim's
`tests/test_core.py`. Run: python -m pytest tests/test_memory.py -q -s
"""
import copy
import json
import os
import random
import re
import threading

import pytest
from rdflib import RDF, Graph

from core.contracts import CHANGE_TYPES
from core.factlog import ConflictError, FactLog, default_log
from core.integrity import run as run_integrity
from core.project import LCC, Projection, clear_cache, functional_predicates
from core.snapshot import snapshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FUNCTIONAL = functional_predicates()


@pytest.fixture(scope="module")
def log():
    return default_log()


def fact(fact_id, s, p, o, rank=2, kind="assert", valid_from="2026-01-01", recorded_at="2026-01-01T00:00:00",
         source="SYNTHETIC-TEST", supersedes=None):
    return {"id": fact_id, "s": s, "p": p, "o": o, "rank": rank, "kind": kind, "valid_from": valid_from,
            "valid_to": None, "recorded_at": recorded_at, "review": "accepted", "source": source,
            "quote": f"test-only: {s} {p} {o}", "supersedes": supersedes}


# ---- ontology ----------------------------------------------------------------------------------------------

def test_ontology_has_all_change_types_and_hooks():
    graph = Graph().parse(os.path.join(ROOT, "ontology", "lcc.ttl"))
    missing = [name for name in CHANGE_TYPES if (LCC[name], RDF.type, LCC.ChangeType) not in graph]
    assert missing == []
    assert (LCC.AlloySeries, None, None) in graph and (LCC.madeOfSeries, None, None) in graph
    for name in ("hasConsequence", "suppliesTo", "feedsInto", "requiresCustomerApprovalForSubTier",
                 "requiresNoticeFor", "leadTimeDays"):
        assert (LCC[name], None, None) in graph, name
    types = {str(value) for value in graph.objects(None, LCC.epistemicType)}
    assert types == {"CONSTRAINT", "DECISION", "EVIDENCE", "PLAN", "QUESTION"}
    Graph().parse(os.path.join(ROOT, "ontology", "shapes.ttl"))


# ---- data --------------------------------------------------------------------------------------------------

def test_data_rows_have_contract_fields_and_fix_data():
    with open(os.path.join(DATA, "facts.jsonl")) as file:
        rows = [json.loads(line) for line in file]
    assert all(row["kind"] in ("assert", "mention") and row["rank"] in (1, 2, 3) for row in rows)
    predicates = {row["p"] for row in rows}
    assert {"hasConsequence", "suppliesTo", "requiresCustomerApprovalForSubTier"} <= predicates  # fix/4, fix/8
    assert {row["rank"] for row in rows if row["source"].startswith("CSR-")} == {1}


def test_data_names_no_real_carmaker():
    pattern = re.compile(r"stellantis|\bfiat\b|ferrari|volkswagen|\bbmw\b|renault|toyota|\bford\b|"
                         r"general motors|mercedes|\baudi\b|lamborghini|maserati|tesla|honda|volvo|scania",
                         re.IGNORECASE)
    hits = []
    for folder, _, files in os.walk(DATA):
        for name in files:
            if name.endswith((".md", ".csv", ".json", ".jsonl", ".py")):
                with open(os.path.join(folder, name), encoding="utf-8") as file:
                    if pattern.search(file.read()):
                        hits.append(name)
    assert hits == []


# ---- snapshot ----------------------------------------------------------------------------------------------

def test_order_independence_200_shuffles(log):
    facts = log.all_facts() + [
        fact("x01", "BR-220", "madeOf", "MAT-6061-T6", rank=3, kind="mention", valid_from="2026-11-05"),
        fact("x02", "8D-25-031", "status", '"closed"', rank=3, valid_from="2026-11-13"),
        fact("x03", "PART-T", "madeOf", "MAT-A", rank=2, valid_from="2026-05-01"),
        fact("x04", "PART-T", "madeOf", "MAT-B", rank=2, valid_from="2026-05-01"),
    ]
    reference = snapshot(facts, "2026-11-14", None, FUNCTIONAL)
    rnd = random.Random(7)
    for _ in range(200):
        shuffled = copy.deepcopy(facts)
        rnd.shuffle(shuffled)
        result = snapshot(shuffled, "2026-11-14", None, FUNCTIONAL)
        assert (result["fact_ids"], result["notes"], result["contested"], result["hash"]) == \
            (reference["fact_ids"], reference["notes"], reference["contested"], reference["hash"])


def test_stale_mention_never_wins():
    facts = [fact("a1", "P", "madeOf", "MAT-6061-T6", valid_from="2025-01-01"),            # drawing rev B
             fact("a2", "P", "madeOf", "MAT-6082-T6", valid_from="2026-03-01"),            # drawing rev C
             fact("m1", "P", "madeOf", "MAT-6061-T6", rank=3, kind="mention", valid_from="2026-11-05")]
    result = snapshot(facts, "2026-11-14", None, FUNCTIONAL)
    assert [item["o"] for item in result["facts"]] == ["MAT-6082-T6"]
    assert {note["type"] for note in result["notes"]} == {"superseded", "stale_mention"}
    assert result["contested"] == []
    # a mention alone holds no value either
    alone = snapshot([fact("m2", "Q", "madeOf", "MAT-X", rank=3, kind="mention")], "2026-11-14", None, FUNCTIONAL)
    assert alone["facts"] == [] and alone["notes"][0]["type"] == "unsupported_mention"


def test_lower_rank_never_supersedes_higher():
    facts = [fact("c1", "8D-T", "status", '"open"', rank=2, valid_from="2026-10-01"),
             fact("c2", "8D-T", "status", '"closed"', rank=3, valid_from="2026-11-13")]
    result = snapshot(facts, "2026-11-14", None, FUNCTIONAL)
    assert result["fact_ids"] == ["c1"]
    assert result["contested"] == [{"key": ["8D-T", "status"], "reason": "lower_rank_newer", "head": "c1",
                                    "facts": ["c1", "c2"], "values": ['"open"', '"closed"'], "rank": 3,
                                    "valid_from": "2026-11-13"}]
    # record level: an informal record cannot supersede a customer requirement
    records = [fact("r1", "CSR-T", "type", "CustomerRequirement", rank=1),
               fact("r2", "EML-T", "supersedes", "CSR-T", rank=3, valid_from="2026-11-01")]
    result = snapshot(records, "2026-11-14", None, FUNCTIONAL)
    assert "r1" in result["fact_ids"] and result["replaced"] == []
    assert result["notes"][0]["type"] == "supersession_refused"
    # fact level: same guard
    pair = [fact("f1", "S", "status", '"approved"', rank=1),
            fact("f2", "S", "status", '"revoked"', rank=2, valid_from="2026-06-01", supersedes="f1")]
    assert snapshot(pair, "2026-11-14", None, FUNCTIONAL)["fact_ids"] == ["f1"]


def test_same_rank_same_date_conflict_is_contested_not_guessed():
    facts = [fact("d1", "P", "madeOf", "MAT-A", valid_from="2026-05-01"),
             fact("d2", "P", "madeOf", "MAT-B", valid_from="2026-05-01")]
    result = snapshot(facts, "2026-11-14", None, FUNCTIONAL)
    assert result["facts"] == []
    assert result["contested"][0]["reason"] == "same_rank_same_date"
    assert result["contested"][0]["facts"] == ["d1", "d2"]


def test_transitive_record_supersession_and_time_travel():
    facts = [fact("b", "REV-B", "type", "Document", valid_from="2024-01-01"),
             fact("c", "REV-C", "supersedes", "REV-B", valid_from="2025-01-01"),
             fact("d", "REV-D", "supersedes", "REV-C", valid_from="2026-01-01",
                  recorded_at="2026-06-01T10:00:00")]
    now = snapshot(facts, "2026-11-14", None, FUNCTIONAL)
    assert set(now["replaced"]) == {"REV-B", "REV-C"} and now["fact_ids"] == ["d"]
    known_before = snapshot(facts, "2026-11-14", "2026-05-31", FUNCTIONAL)      # rev D not yet recorded
    assert known_before["replaced"] == ["REV-B"] and known_before["fact_ids"] == ["c"]
    in_2024 = snapshot(facts, "2024-06-01", None, FUNCTIONAL)
    assert in_2024["fact_ids"] == ["b"]


# ---- fact log ----------------------------------------------------------------------------------------------

QUAL = {"qualifiedSupplier": "SUP-Z", "status": '"approved"'}


def test_proposal_does_not_count_until_accepted():
    log = FactLog()
    log.propose_fact(fact("p1", "BR-T", "madeOf", "MAT-A") | {"review": None}, proposed_by="extractor")
    assert Projection(log, "2026-11-14").value("BR-T", "madeOf") is None
    log.accept_proposed("SYNTHETIC-TEST", reviewer="PER-BIANCHI")
    assert Projection(log, "2026-11-14").value("BR-T", "madeOf") == "MAT-A"


def test_conflict_check_runs_at_acceptance():
    log = FactLog()
    log.write_record("QUAL-Z1", "SupplierQualification", QUAL, "REG", "q", "2026-01-01", "PER-BIANCHI")
    log.propose_record("QUAL-Z2", "SupplierQualification", dict(QUAL, status='"conditional"'), "AUDIT-9", "q",
                       "2026-11-01", "PER-BIANCHI", proposed_by="agent:extractor")
    with pytest.raises(ConflictError):
        log.accept_proposed("AUDIT-9", reviewer="PER-BIANCHI")
    assert log.proposed("AUDIT-9")                                     # rolled back: still proposed
    with pytest.raises(ConflictError):
        log.review("QUAL-Z2", "accepted", "PER-BIANCHI")
    # the same proposal with supersedes is accepted
    log.propose_record("QUAL-Z3", "SupplierQualification", dict(QUAL, status='"conditional"'), "AUDIT-10", "q",
                       "2026-11-01", "PER-BIANCHI", proposed_by="agent:extractor", supersedes="QUAL-Z1")
    assert log.accept_proposed("AUDIT-10", reviewer="PER-BIANCHI")
    projection = Projection(log, "2026-11-14")
    assert projection.instances("SupplierQualification") == ["QUAL-Z3"]
    conforms, text, _ = run_integrity(projection)
    assert conforms, text


def test_two_conflicting_proposals_cannot_both_be_accepted():
    log = FactLog()
    for index in (1, 2):
        log.propose_record(f"QUAL-N{index}", "SupplierQualification", QUAL, f"SRC-{index}", "q", "2026-11-01",
                           "PER-BIANCHI", proposed_by="agent:extractor")
    log.accept_proposed("SRC-1", reviewer="PER-BIANCHI")
    with pytest.raises(ConflictError):
        log.accept_proposed("SRC-2", reviewer="PER-BIANCHI")


def test_concurrent_writers_one_wins():
    log = FactLog()
    results = []
    barrier = threading.Barrier(8)

    def writer(index):
        barrier.wait()
        try:
            log.write_record(f"QUAL-C{index}", "SupplierQualification", QUAL, "REG", "q", "2026-11-01", "PER-X")
            results.append("ok")
        except ConflictError:
            results.append("conflict")

    threads = [threading.Thread(target=writer, args=(index,)) for index in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results) == ["conflict"] * 7 + ["ok"]
    assert len(Projection(log, "2026-11-14").instances("SupplierQualification")) == 1


def test_unclassified_queue_never_reaches_graph():
    log = FactLog()
    log.propose_unclassified({"id": "U1", "source": "CSR-T", "quote": "Suppliers shall keep records 15 years."},
                             proposed_by="extractor")
    projection = Projection(log, "2026-11-14")
    assert [item["id"] for item in projection.unclassified] == ["U1"]
    assert projection.asserted_count == 0
    log.close_unclassified("U1", "dismissed")
    assert log.unclassified_items() == []


def test_fact_validation():
    log = FactLog()
    with pytest.raises(ValueError):
        log.propose_fact(fact("v1", "A", "madeOf", "B", kind="rumour"), proposed_by="agent")
    with pytest.raises(ValueError):
        log.propose_fact(fact("v2", "A", "madeOf", "B", rank=7), proposed_by="agent")


# ---- projection --------------------------------------------------------------------------------------------

def test_prototype_scenarios_project(log):
    with open(os.path.join(DATA, "scenarios.json")) as file:
        scenarios = json.load(file)
    clear_cache()
    lines = []
    for scenario in scenarios:
        projection = Projection(log, scenario["as_of"])
        change = scenario["change"]
        assert projection.is_a(change["part"], "Part")
        assert projection.value(change["part"], "madeOf")
        assert projection.fact_ids_in_force and projection.contested == []
        lines.append(f"{scenario['id']}: snapshot {projection.snapshot_ms:.1f} ms, "
                     f"closure {projection.closure_ms:.1f} ms{' (cached)' if projection.cache_hit else ''}, "
                     f"{len(projection.fact_ids_in_force)} facts in force, {len(projection.graph)} triples")
    print("\nTIMING " + "\nTIMING ".join(lines))


def test_projection_api_and_inference(log):
    projection = Projection(log, "2026-11-14")
    assert projection.value("BR-220", "madeOf") == "MAT-6082-T6"
    assert "Series6xxx" in projection.objects("BR-220", "madeOfSeries")      # 8D at series level
    assert "CSR-AUR-R4" in projection.objects("BR-220", "subjectTo")         # chain part > program > customer
    assert projection.objects("CSR-AUR-R4", "hasConsequence")               # fix/4
    assert projection.query("SELECT ?s WHERE { ?s lcc:feedsInto ?t }")       # fix/8
    assert projection.epistemic_type("CSR-AUR-R4") == "CONSTRAINT"
    assert projection.epistemic_type("ChangeRequest") == "PLAN"
    assert projection.label("BR-220") != "BR-220"
    for fact_id in projection.fact_ids_in_force[:20]:
        assert log.get(fact_id)["review"] == "accepted"
    again = Projection(log, "2026-11-14")
    assert again.cache_hit and again.graph is projection.graph
    assert again.snapshot_hash == projection.snapshot_hash
    conforms, text, _ = run_integrity(projection)
    assert conforms, text


def test_superseded_requirement_is_history(log):
    projection = Projection(log, "2026-11-14")
    assert "CSR-AUR-R3" in projection.replaced or not projection.facts_for("CSR-AUR-R3", "type")
    assert projection.history_by_subject.get("CSR-AUR-R3")
