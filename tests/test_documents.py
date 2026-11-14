"""Bring your documents (web/documents.py): routes, acceptance -> card change, reset, conflict -> contested.

Runs offline: the two demo documents replay their recorded extraction answers (tests/fixtures/extract)."""
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from core import check
from web import documents


@pytest.fixture(autouse=True)
def fresh_memory():
    documents.reset()
    yield
    documents.reset()


def post(path, body, content_type="application/json"):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    return documents.handle_post(path, content_type, raw)


def findings(scenario_id):
    card, _ = check.run(check.scenario(scenario_id), record=False)
    return card, {(item["rule"], item["severity"]) for item in card["findings"]}


def fact_ids(payload, exclude=()):
    return [item["id"] for item in payload["proposals"]
            if item["kind"] != "unclassified" and item["id"] not in exclude]


def test_upload_demo_email_returns_proposals_with_offsets():
    payload, status = post("/api/documents", {"demo": "DEV-AUR-26-044"})
    assert status == 200
    assert payload["extraction"]["answers_from"][0].startswith("fixture")
    triples = {(item["s"], item["p"], item["o"]) for item in payload["proposals"]}
    assert ("DEV-AUR-26-044", "permitsChangeType", "SourceChange") in triples
    assert ("DEV-AUR-26-044", "concernsSupplier", "SUP-C") in triples
    for item in payload["proposals"]:
        start, end = item["quote_span"]
        assert payload["text"][start:end].split() == item["quote"].split()
        assert item["status"] in ("proposed", "not checked")
        assert item["epistemic"] and item["rank"] == 3
    assert any(item["kind"] == "unclassified" for item in payload["proposals"])
    listing, status = documents.handle_get("/api/proposals")
    assert status == 200 and listing["documents"][0]["id"] == "DEV-AUR-26-044"


def test_proposed_facts_do_not_count_until_accepted():
    post("/api/documents", {"demo": "DEV-AUR-26-044"})
    _, rules = findings("main_after_audit")
    assert ("R2", "blocker") in rules


def test_accepting_the_deviation_email_changes_the_card():
    _, before = findings("main_after_audit")
    payload, _ = post("/api/documents", {"demo": "DEV-AUR-26-044"})
    wrong = [item["id"] for item in payload["proposals"] if item.get("s") == "SUP-C"]
    for pid in wrong:  # the model's one wrong fact: the reviewer rejects it
        result, status = post(f"/api/proposals/{pid}/reject", {"reviewer": "PER-ROSSI"})
        assert status == 200
    result, status = post("/api/proposals/accept", {"ids": fact_ids(payload, wrong), "reviewer": "PER-ROSSI"})
    assert status == 200 and result["accepted"] and not result["contested"]
    card, after = findings("main_after_audit")
    assert ("R2", "blocker") in before and ("R2", "blocker") not in after
    covered = [item for item in card["findings"] if item["rule"] == "R2" and "DEV-AUR-26-044" in item["title"]]
    assert covered and "2026-12-31" in covered[0]["title"]  # time-bounded
    statuses = {item["id"]: item["status"] for item in documents.handle_get("/api/proposals")[0]["documents"][0]["proposals"]}
    assert all(statuses[pid] == "rejected" for pid in wrong)


def test_new_csr_revision_supersedes_by_rank_and_date():
    _, before = findings("rule_change_r4")
    payload, _ = post("/api/documents", {"demo": "CSR-AUR-R5"})
    triples = {(item["s"], item["p"], item["o"]) for item in payload["proposals"]}
    assert ("CSR-AUR-R5", "supersedes", "CSR-AUR-R4") in triples
    assert ("CSR-AUR-R5", "requiresNotificationFor", "CoatingChange") in triples
    post("/api/proposals/accept", {"ids": fact_ids(payload), "reviewer": "PER-ROSSI"})
    card, after = findings("rule_change_r4")
    assert ("R2", "blocker") in before and ("R2", "blocker") not in after
    assert any("CSR-AUR-R5" in item["title"] for item in card["findings"])
    _, main = findings("main_after_audit")  # source changes still need approval under rev 5
    assert ("R2", "blocker") in main


def test_reset_restores_the_original_memory():
    _, before = findings("main_after_audit")
    payload, _ = post("/api/documents", {"demo": "DEV-AUR-26-044"})
    post("/api/proposals/accept", {"ids": fact_ids(payload), "reviewer": "x"})
    assert findings("main_after_audit")[1] != before
    result, status = post("/api/documents/reset", {})
    assert status == 200 and result["reset"]
    assert findings("main_after_audit")[1] == before
    assert documents.handle_get("/api/proposals")[0]["documents"] == []


def test_contradicting_record_becomes_contested_never_overwrites():
    text = "Approval APR-900: Alluminio Bormida (SUP-B) for BR-220 at Beinasco for Aurelia is revoked."
    header = documents.normalise_header({"id": "APR-900", "type": "deviation"})
    common = {"source": "APR-900", "quote": text, "context_quote": None, "kind": "assert", "rank": 2,
              "valid_from": "2026-11-10", "valid_to": None, "author": "test", "proposed_by": "extractor"}
    triples = [("type", "PartApproval"), ("approvedSupplier", "SUP-B"), ("approvedPart", "BR-220"),
               ("approvedSite", "PLT-BEI"), ("approvedForCustomer", "CUST-AUR"), ("status", '"revoked"')]
    proposals = [{"id": f"X-APR-900-{index:03d}", "s": "APR-900", "p": p, "o": o, **common}
                 for index, (p, o) in enumerate(triples)]
    documents.add_document(header, text, proposals)
    result, status = post("/api/proposals/accept", {"ids": [item["id"] for item in proposals], "reviewer": "x"})
    assert status == 200
    assert not result["accepted"] and len(result["contested"]) == len(proposals)
    assert result["question"] == "Q-APR-900"
    log = check.memory()
    in_force = {row["id"] for row in log.all_facts()}
    assert not in_force & {item["id"] for item in proposals}  # contested facts are never in force
    assert {log.get(item["id"])["review"] for item in proposals} == {"contested"}
    assert any(item["contested_record"] == "APR-900" for item in log.open_questions())
    assert any(row["s"] == "APR-001" for row in log.all_facts())  # the current record stays
    payload = documents.handle_get("/api/proposals")[0]["documents"][0]
    assert {item["status"] for item in payload["proposals"]} == {"contested"}
    assert payload["questions"]


def test_bad_inputs():
    assert post("/api/documents", {})[1] == 400
    assert post("/api/documents", {"demo": "NOPE"})[1] == 404
    assert post("/api/documents", {"url": "file:///etc/passwd"})[1] == 400
    assert post("/api/proposals/NOPE/accept", {})[1] == 404
    big = {"text": "x" * (documents.MAX_BYTES + 10), "name": "big"}
    assert post("/api/documents", big)[1] == 413


def test_multipart_upload_and_http_routes():
    from web import server
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        with open(documents.DOCS_DIR / "DEV-AUR-26-044.md", "rb") as file:
            data = file.read()
        boundary = "kvaboundary"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"DEV-AUR-26-044.md\"\r\n"
                f"Content-Type: text/markdown\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(base + "/api/documents", data=body, method="POST",
                                         headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read())
        assert payload["id"] == "DEV-AUR-26-044" and payload["proposals"]
        with urllib.request.urlopen(base + "/api/documents/demo") as response:
            assert len(json.loads(response.read())["demo"]) == 2
    finally:
        httpd.shutdown()
