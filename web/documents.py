"""Bring your documents: upload -> extracted facts proposed -> a person reviews -> accepted facts change the card.

Routes (wired by small hooks in web/server.py):
    POST /api/documents            JSON {name, text} | {url, id?, type?} | {demo: id}, or multipart (field `file`,
                                   optional `name`); 5 MB cap; PDF goes through core/convert.py
    GET  /api/documents/demo       the committed demo documents (synthetic, fictional company)
    GET  /api/proposals            every uploaded document with its proposals and their review status
    POST /api/proposals/<id>/accept|reject   {reviewer}
    POST /api/proposals/accept     {ids: [...], reviewer}   accept several at once (a whole record)
    POST /api/documents/reset      restore the original fact log (demo)

Extraction is core/extract.py unchanged (Haiku through core/llm.py). Answers for the committed demo documents are
recorded in tests/fixtures/extract, so they replay without the key. Anything else (pasted text, a URL) is
extracted live and its answer is cached outside the repo (a temp dir): third-party text never lands in git.

Acceptance goes through the fact log (core/factlog.py accept_facts): the conflict check runs at acceptance. A fact
that contradicts a current record of the same or lower authority becomes `contested` with an open question (the
#28 path), never a silent overwrite; against a more authoritative record it is refused. Every accepted fact
commits through the log, so core/project.py's warm closure is recomputed before the next check.

Uploaded text lives in this process only (memory), never on disk in the repo. Written 14 Nov 2026 (ws/ingest).
"""
import email
import email.policy
import json
import os
import re
import sys
import tempfile
import urllib.request
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import check, extract, project  # noqa: E402
from core.factlog import ConflictError  # noqa: E402

DOCS_DIR = ROOT / "data" / "documents"
MAX_BYTES = 5 * 1024 * 1024
LIVE_FIXTURES = os.path.join(tempfile.gettempdir(), "kva_live_extract")  # never inside the repo
DEMO_DOCUMENTS = [
    {"id": "DEV-AUR-26-044", "file": "DEV-AUR-26-044.md", "scenario": "main_after_audit",
     "label": "Email: Aurelia grants a deviation for BR-220 from Chisone (2 lots)",
     "expect": "accepting it turns the R2 customer-approval blocker into a time-bounded deviation"},
    {"id": "CSR-AUR-R5", "file": "CSR-AUR-R5.md", "scenario": "rule_change_r4",
     "label": "Aurelia manual rev 5: coating changes need notification only",
     "expect": "rev 5 supersedes rev 4 (same rank, later date): the coating change needs a notification, not a PPAP"},
]
# One real public document (data_real/SOURCES.md). Fetched at runtime, extracted live: needs network and the key.
REAL_DOCUMENT = {"id": "ADIENT-SSM-Q-R10", "type": "customer_requirement",
                 "title": "Adient Global Supplier Standards Manual, Quality chapter, Rev 10.0 (public PDF)",
                 "url": "https://www.adient.com/wp-content/uploads/2023/04/"
                        "Adient-Global-Supplier-Standards-Manual-%E2%80%93-Quality-Chapter.pdf",
                 "valid_from": "2023-04-01"}
CONSTRAINT_PREDICATES = {"requiresCustomerApprovalFor", "requiresNotificationFor", "requiresNoticeFor",
                         "leadTimeDays", "appliesInMarket", "restricts", "imposes", "supersedes"}
PLAIN = {
    "requiresCustomerApprovalFor": "needs written customer approval for",
    "requiresNotificationFor": "needs only a notification for",
    "requiresNoticeFor": "needs advance notice for",
    "leadTimeDays": "notice lead time (days)",
    "appliesInMarket": "applies in market",
    "restricts": "restricts substance",
    "concernsSupplier": "concerns supplier",
    "concernsMaterial": "concerns material",
    "concernsPart": "concerns part",
    "concernsCoating": "concerns coating",
    "permitsChangeType": "permits",
    "permitsCoating": "permits coating",
    "status": "has status",
    "imposes": "imposes",
    "supersedes": "replaces",
}

_store = {"documents": OrderedDict(), "proposals": OrderedDict()}


class UploadError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


# ---- document input --------------------------------------------------------------------------------------

def slug(text):
    value = re.sub(r"[^A-Za-z0-9]+", "-", str(text or "")).strip("-").upper()
    return value[:40] or "DOC"


def split_front_matter(raw):
    """Markdown with an optional YAML front matter -> (header dict or {}, body)."""
    if raw.startswith("---\n"):
        import yaml
        _, header_text, body = raw.split("---\n", 2)
        return yaml.safe_load(header_text) or {}, body
    return {}, raw


def normalise_header(header, name=None, doc_type=None):
    header = dict(header or {})
    header["id"] = str(header.get("id") or slug(name or "pasted document"))
    header["type"] = header.get("type") or doc_type or "note"
    header.setdefault("title", name or header["id"])
    for key in ("valid_from", "valid_to", "date"):
        if header.get(key) is not None:
            header[key] = str(header[key])
    header.setdefault("valid_from", None)
    header.setdefault("valid_to", None)
    header.setdefault("supersedes", None)
    return header


def pdf_to_text(data):
    from core.convert import convert
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
        handle.write(data)
        path = handle.name
    try:
        return convert(path).replace("\f", "\n\n")
    finally:
        os.unlink(path)


def bytes_to_text(data, filename=""):
    if len(data) > MAX_BYTES:
        raise UploadError("document larger than 5 MB", 413)
    if data[:5] == b"%PDF-" or filename.lower().endswith(".pdf"):
        return pdf_to_text(data)
    return data.decode("utf-8", errors="replace")


def fetch_url(url):
    if not re.match(r"^https?://", url or ""):
        raise UploadError("url must start with http:// or https://")
    request = urllib.request.Request(url, headers={"User-Agent": "change-check-demo/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (http(s) only, checked above)
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise UploadError("document larger than 5 MB", 413)
    return bytes_to_text(data, url.split("?")[0])


def parse_multipart(content_type, raw):
    message = email.message_from_bytes(b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + raw,
                                       policy=email.policy.default)
    fields, files = {}, {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename:
            files[name] = (filename, payload)
        else:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, files


def read_input(body):
    """JSON body (dict) -> (header, text, live_only)."""
    if body.get("demo"):
        demo = next((item for item in DEMO_DOCUMENTS if item["id"] == body["demo"]), None)
        if demo is None:
            raise UploadError(f"unknown demo document {body['demo']}", 404)
        header, text = split_front_matter((DOCS_DIR / demo["file"]).read_text(encoding="utf-8"))
        return normalise_header(header), text, False
    if body.get("real"):
        text = fetch_url(REAL_DOCUMENT["url"])
        header = {key: REAL_DOCUMENT[key] for key in ("id", "type", "title", "valid_from")}
        return normalise_header(header), text, True
    if body.get("url"):
        text = fetch_url(body["url"])
        name = body.get("name") or body["url"].rstrip("/").split("/")[-1]
        return normalise_header({"id": body.get("id")}, name, body.get("type")), text, True
    text = body.get("text")
    if not text or not str(text).strip():
        raise UploadError("send one of: text (with name), url, demo, or a multipart file")
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise UploadError("document larger than 5 MB", 413)
    header, text = split_front_matter(str(text))
    return normalise_header(header, body.get("name"), body.get("type")), text, True


# ---- proposals -------------------------------------------------------------------------------------------

def spans_for(text, quote, context=None):
    """(quote span, context span) as [start, end] character offsets in `text`, or None."""
    quote_spans = extract.find_spans(text, quote) if quote else []
    if not quote_spans:
        return None, None
    quote_span = list(quote_spans[0])
    if context:
        for c_start, c_end in extract.find_spans(text, context):
            for q_start, q_end in quote_spans:
                if c_start < q_start:
                    return [q_start, q_end], [c_start, c_end]
    return quote_span, None


def header_proposals(header, text, registries):
    """Facts the document's own header states (who imposes it, what it replaces), quoted from its first line."""
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    proposals = []
    customers = {row[0] for row in registries.get("customers", {}).get("rows", [])}
    if header.get("type") == "customer_requirement" and header.get("customer") in customers:
        proposals.append((header["customer"], "imposes", header["id"]))
    if header.get("supersedes"):
        proposals.append((header["id"], "supersedes", str(header["supersedes"])))
    common = {"source": header["id"], "rank": extract.document_rank(header.get("type")),
              "valid_from": header.get("valid_from"), "valid_to": header.get("valid_to"),
              "author": header.get("author"), "proposed_by": "header", "status": "proposed"}
    return [{"id": f"H-{header['id']}-{index:03d}", "s": s, "p": p, "o": o, "quote": first, "context_quote": None,
             "kind": "assert", **common} for index, (s, p, o) in enumerate(proposals) if first]


def epistemic_of(proposal):
    if proposal["kind"] == "unclassified":
        return "constraint"
    return "constraint" if proposal["p"] in CONSTRAINT_PREDICATES else "evidence"


def plain_words(proposal, labels):
    if proposal["kind"] == "unclassified":
        return proposal.get("summary") or "requirement the ontology cannot express"

    def name(value):
        if value is None:
            return ""
        if value.startswith('"'):
            return json.loads(value)
        return f"{labels.get(value, value)}" + (f" ({value})" if labels.get(value) and labels[value] != value else "")
    return f"{name(proposal['s'])} {PLAIN.get(proposal['p'], proposal['p'])} {name(proposal['o'])}"


def add_document(header, text, proposals, failed=(), extraction=None):
    """Register a document and its proposals; assert proposals go into the fact log as `proposed` (they do not
    count until a person accepts them); unclassified items join the log's unclassified queue."""
    log = check.memory()
    labels = labels_map()
    doc_id = header["id"]
    for proposal in proposals:
        proposal["epistemic"] = epistemic_of(proposal)
        proposal["plain"] = plain_words(proposal, labels)
        proposal["doc"] = doc_id
        proposal["quote_span"], proposal["context_span"] = spans_for(text, proposal["quote"],
                                                                     proposal.get("context_quote"))
        for key in ("valid_from", "valid_to"):
            if proposal.get(key) is not None:
                proposal[key] = str(proposal[key])
        if proposal["kind"] == "unclassified":
            log.propose_unclassified({"id": proposal["id"], "source": doc_id, "quote": proposal["quote"],
                                      "summary": proposal.get("summary", "")}, proposed_by="extractor")
            proposal["status"] = "not checked"
        else:
            fact = {key: proposal.get(key) for key in ("id", "s", "p", "o", "source", "quote", "context_quote",
                                                        "valid_from", "valid_to", "kind", "rank", "epistemic",
                                                        "author")}
            log.propose_fact(fact, proposed_by=proposal.get("proposed_by") or "extractor")
        _store["proposals"][proposal["id"]] = proposal
    _store["documents"][doc_id] = {"id": doc_id, "header": header, "text": text,
                                   "proposal_ids": [proposal["id"] for proposal in proposals],
                                   "failed": list(failed), "extraction": extraction or {}}
    return document_payload(doc_id)


def labels_map():
    registries = extract.load_registries()
    names = {}
    for key, registry in registries.items():
        if key.startswith("_"):
            continue
        for row in registry.get("rows", []):
            if len(row) > 1:
                names[row[0]] = row[1]
    names.update(extract.CHANGE_TYPE_LABELS)
    return names


def ingest(header, text, live_only):
    """Run the extractor on one document and register its proposals."""
    if header["id"] in _store["documents"]:
        return document_payload(header["id"])
    registries = extract.load_registries()
    original = extract.FIXTURES_DIR
    if live_only:
        extract.FIXTURES_DIR = LIVE_FIXTURES  # third-party / pasted text: cache outside the repo
    try:
        result = extract.extract_text(header, text, registries=registries, document_ids=existing_sources())
    finally:
        extract.FIXTURES_DIR = original
    proposals = header_proposals(header, text, registries) + extract.to_proposals(result)
    extraction = {key: result[key] for key in ("tokens_in", "tokens_out", "seconds", "chunks", "answers_from")}
    return add_document(header, text, proposals, failed=result["review"], extraction=extraction)


def existing_sources():
    with check.memory().lock:
        return sorted({row[0] for row in check.memory().connection.execute("SELECT DISTINCT source FROM facts")})


def status_of(proposal):
    if proposal["kind"] == "unclassified":
        return proposal.get("status", "not checked")
    row = check.memory().get(proposal["id"])
    return row["review"] if row else proposal.get("status", "proposed")


def get_fact(fact_id):
    with check.memory().lock:
        row = check.memory().connection.execute("SELECT * FROM facts WHERE id = ?", (fact_id,)).fetchone()
    return dict(row) if row else None


def document_payload(doc_id):
    document = _store["documents"][doc_id]
    proposals = []
    for proposal_id in document["proposal_ids"]:
        proposal = dict(_store["proposals"][proposal_id])
        proposal["status"] = status_of(proposal)
        proposals.append(proposal)
    return {"id": doc_id, "header": document["header"], "text": document["text"], "proposals": proposals,
            "failed": document["failed"], "extraction": document["extraction"],
            "questions": questions_for(document["proposal_ids"])}


def questions_for(proposal_ids):
    subjects = {_store["proposals"][pid]["s"] for pid in proposal_ids if _store["proposals"][pid].get("s")}
    return [item for item in check.memory().open_questions() if item["contested_record"] in subjects]


# ---- review ----------------------------------------------------------------------------------------------

def accept(proposal_ids, reviewer):
    """A person accepts proposals. The fact log runs the conflict check at acceptance. On a conflict the facts
    become `contested` (never in force) with an open question, if the current record is not more authoritative;
    otherwise nothing is accepted and the reason comes back."""
    reviewer = reviewer or "reviewer"
    ids = [pid for pid in proposal_ids if pid in _store["proposals"]
           and _store["proposals"][pid]["kind"] != "unclassified"]
    if not ids:
        raise UploadError("no such proposal", 404)
    log = check.memory()
    try:
        accepted = log.accept_facts(ids, reviewer)
        return {"accepted": accepted, "contested": [], "refused": None}
    except ConflictError as conflict:
        rows = [get_fact(pid) for pid in ids]
        rank = min(int(row["rank"]) for row in rows if row)
        if log._record_rank(conflict.current) < rank:
            return {"accepted": [], "contested": [], "refused": f"{conflict} The current record is more "
                                                                "authoritative: write a superseding record."}
        with log._transaction():
            for pid in ids:
                log.connection.execute("UPDATE facts SET review = 'contested', reviewed_by = ? "
                                       "WHERE id = ? AND review = 'proposed'", (reviewer, pid))
            log._open_contradiction(conflict.record, conflict.current, conflict.class_name)
        return {"accepted": [], "contested": ids, "refused": None, "question": f"Q-{conflict.record}",
                "message": str(conflict)}


def reject(proposal_ids, reviewer):
    reviewer = reviewer or "reviewer"
    log = check.memory()
    rejected = []
    with log._transaction():
        for pid in proposal_ids:
            proposal = _store["proposals"].get(pid)
            if proposal is None:
                continue
            if proposal["kind"] == "unclassified":
                log.connection.execute("UPDATE unclassified SET review = 'dismissed' WHERE id = ?", (pid,))
                proposal["status"] = "dismissed"
            else:
                log.connection.execute("UPDATE facts SET review = 'rejected', reviewed_by = ? "
                                       "WHERE id = ? AND review = 'proposed'", (reviewer, pid))
            rejected.append(pid)
    if not rejected:
        raise UploadError("no such proposal", 404)
    return {"rejected": rejected}


def reset():
    """Restore the original fact log (demo): drop every uploaded document and review, re-warm the closure."""
    project._warm.clear()
    project.clear_cache()
    check._LOG = None
    _store["documents"].clear()
    _store["proposals"].clear()
    project.warm(check.memory(), check.DEFAULT_AS_OF)
    return {"reset": True, "facts": len(check.memory().all_facts())}


def all_payload():
    return {"documents": [document_payload(doc_id) for doc_id in _store["documents"]],
            "demo": demo_list(), "real": {key: REAL_DOCUMENT[key] for key in ("id", "title", "url")}}


def demo_list():
    return [{key: item[key] for key in ("id", "label", "scenario", "expect")} for item in DEMO_DOCUMENTS]


# ---- HTTP entry points (called from web/server.py under its LOCK) -----------------------------------------

def handle_get(path):
    if path == "/api/documents/demo":
        return {"demo": demo_list(), "real": {key: REAL_DOCUMENT[key] for key in ("id", "title", "url")}}, 200
    if path in ("/api/proposals", "/api/documents"):
        return all_payload(), 200
    return None


def handle_post(path, content_type, raw):
    """Returns (payload, status) for a documents route, or None when the path is not one of ours."""
    if not (path.startswith("/api/documents") or path.startswith("/api/proposals")):
        return None
    try:
        if len(raw) > MAX_BYTES + 65536:
            raise UploadError("document larger than 5 MB", 413)
        if (content_type or "").startswith("multipart/form-data"):
            fields, files = parse_multipart(content_type, raw)
            if not files:
                raise UploadError("multipart upload without a file")
            filename, data = next(iter(files.values()))
            text = bytes_to_text(data, filename)
            body = {"text": text, "name": fields.get("name") or filename, "type": fields.get("type")}
        else:
            body = json.loads(raw or b"{}")
        if path == "/api/documents":
            header, text, live_only = read_input(body)
            return ingest(header, text, live_only), 200
        if path == "/api/documents/reset":
            return reset(), 200
        if path == "/api/proposals/accept":
            return accept(list(body.get("ids") or []), body.get("reviewer")), 200
        if path == "/api/proposals/reject":
            return reject(list(body.get("ids") or []), body.get("reviewer")), 200
        match = re.match(r"^/api/proposals/([^/]+)/(accept|reject)$", path)
        if match:
            pid = urllib.request.unquote(match.group(1))
            if match.group(2) == "accept":
                return accept([pid], body.get("reviewer")), 200
            return reject([pid], body.get("reviewer")), 200
        return {"error": "not found"}, 404
    except UploadError as error:
        return {"error": str(error)}, error.status
    except Exception as error:  # the page shows the error, never a blank
        return {"error": f"{type(error).__name__}: {error}"}, 400


# ---- offline replay (web/snapshot.py) -----------------------------------------------------------------------

def record_offline(recorder, out_dir):
    """Record the two synthetic demo documents for offline replay into <out_dir>/documents.json: the upload
    response (proposals, offsets), and the card of the document's change before and after accepting every proposed
    fact. The page labels the offline re-check as exactly that. Leaves the server's memory reset."""
    bundle = {"demo": demo_list(), "real": {key: REAL_DOCUMENT[key] for key in ("id", "title", "url")}, "docs": {}}
    for item in DEMO_DOCUMENTS:
        recorder.call("/api/documents/reset", {})
        before = recorder.call("/api/check", {"scenario": item["scenario"]})
        upload = recorder.call("/api/documents", {"demo": item["id"]})
        ids = [p["id"] for p in upload.get("proposals", []) if p["kind"] != "unclassified"]
        accepted = recorder.call("/api/proposals/accept", {"ids": ids, "reviewer": "offline-recording"})
        after = recorder.call("/api/check", {"request": before["card"]["request"]})
        for payload in (before, after):
            payload.pop("labels", None)
        bundle["docs"][item["id"]] = {"upload": upload, "accepted": accepted, "before": before, "after": after}
    recorder.call("/api/documents/reset", {})
    (Path(out_dir) / "documents.json").write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    return len(bundle["docs"])


def main():
    """python -m web.documents   re-record only web/static/snapshot/documents.json (starts its own server)."""
    from web import snapshot
    process, base = snapshot.start_server()
    try:
        count = record_offline(snapshot.Recorder(base), snapshot.OUT)
    finally:
        process.terminate()
    print(f"recorded {count} demo documents -> {snapshot.OUT / 'documents.json'}")


if __name__ == "__main__":
    main()
