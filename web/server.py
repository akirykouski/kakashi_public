"""Demo web server: the meeting strip, the card, the decision table and the decision records.

    python -m web.server            # http://localhost:8000
    python -m web.server --port 8080

Standard library HTTP server. The browser never calls core code: every check goes through the JSON routes below,
and the model key stays on the server (core/llm.py reads .env).

    POST /api/check     {remark, speaker?, as_of?} | {form} | {request} | {scenario, as_of?}
                        a remark whose parse fails (gateway down, HTTP 402, > 8 s) returns 503 with parse_failed,
                        reason and a typed form prefilled from the closest demo request; {form} goes through
                        core.parse.parse_form (no model call).
                        optional "drop_rows": ["D2"]  -> re-check under an edited decision table kept in memory
                        (core/decision_table.yaml is never written).
    GET  /api/scenarios
    GET  /api/table     ?drop=D2,D5   decision table + coverage check + rules_version
    GET  /api/table.dmn ?drop=D2  the same table as an OMG DMN 1.3 file (download; core/dmn.py)
    GET  /api/table?format=dmn    the same XML, inline
    GET  /api/records   ?limit=50     decision records, newest first
    GET  /api/explain   ?record_id=DR-…   plain-words explanation (customer + auditor) of a past record, with
                        verified counterfactuals (core/explain_text.py); POST /api/check cards carry the same keys
    GET  /api/impact    ?doc=CSR-AUR-R3   what a superseded document affects (core/impact.py, #29)
    POST /api/meeting/line  {line, speaker?, as_of?} -> {flagged, reason, stage, mentions, card?}  (#32, core/meeting.py)
    GET  /api/meeting/demo  the demo transcript (data/meetings/demo_meeting.jsonl)

Written 14 Nov 2026 (workstream UI).
"""
import argparse
import copy
import hashlib
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import check, decision, dmn, impact, meeting, oida, parse, rules  # noqa: E402
from core.contracts import CHANGE_TYPES, Card, ChangeRequest  # noqa: E402
from core.project import Projection, warm  # noqa: E402
from web import documents  # noqa: E402  (bring your documents: /api/documents, /api/proposals)

STATIC = Path(__file__).resolve().parent / "static"
LOCK = threading.Lock()  # the core keeps per-process caches; one check at a time
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
                 ".ico": "image/x-icon", ".dmn": "application/xml; charset=utf-8",
                 ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".eot": "application/vnd.ms-fontobject"}
SUPERSEDES = re.compile(r"([A-Z][A-Za-z0-9-]+) supersedes ([A-Z][A-Za-z0-9-]+)")

_labels = None
_coverage_cache = {}


# ---- labels (fictional company registries) ----------------------------------------------------------------

def labels():
    """id -> human name, from data/registries.json (first two columns of every registry)."""
    global _labels
    if _labels is None:
        _labels = {}
        with open(ROOT / "data" / "registries.json", encoding="utf-8") as handle:
            registries = json.load(handle)
        for registry in registries.values():
            columns = registry.get("columns") or []
            if len(columns) < 2 or columns[1] not in ("name", "description"):
                continue
            for row in registry.get("rows") or []:
                if len(row) >= 2 and row[1]:
                    _labels[row[0]] = row[1]
    return _labels


def people():
    with open(ROOT / "data" / "registries.json", encoding="utf-8") as handle:
        registry = json.load(handle)["people"]
    return {row[0]: {"name": row[1], "role": row[2]} for row in registry["rows"]}


# ---- decision table: the declared one, or an edit kept in memory ------------------------------------------

def table_for(drop_rows):
    table = decision.load_table()
    if not drop_rows:
        return table, None
    edited = copy.deepcopy(table)
    edited["rows"] = [row for row in edited["rows"] if row["id"] not in drop_rows or row["id"] == "R0"]
    edited["version_note"] = f"{table.get('version_note', '')} + edit: dropped {', '.join(sorted(drop_rows))}"
    decision.validate_table(edited)
    import yaml
    text = yaml.safe_dump(edited, sort_keys=False, allow_unicode=True)
    return edited, text


def rules_version_for(table_text):
    """sha256 over the same files as core.decision.rules_version, with the edited table in place of the file."""
    if table_text is None:
        return decision.rules_version()
    digest = hashlib.sha256()
    for pattern in decision.RULES_VERSION_PATTERNS:
        matches = sorted(ROOT.glob(pattern))
        if not matches:
            digest.update(f"missing:{pattern}\n".encode())
            continue
        for path in matches:
            relative = path.relative_to(ROOT).as_posix()
            digest.update(f"file:{relative}\n".encode())
            if relative == "core/decision_table.yaml":
                digest.update(table_text.encode())
            else:
                digest.update(path.read_bytes())
            digest.update(b"\n")
    return digest.hexdigest()


def coverage_for(table, key):
    if key not in _coverage_cache:
        _coverage_cache[key] = decision.coverage_check(table)
    return _coverage_cache[key]


# ---- the check --------------------------------------------------------------------------------------------

def replaced_records(projection, findings):
    """Records a finding says were superseded: shown struck through on the card with date and author."""
    found = {}
    for finding in findings:
        text = " ".join(filter(None, [finding.get("note"), finding.get("title")]))
        for new_id, old_id in SUPERSEDES.findall(text):
            facts = projection.history_by_subject.get(old_id) or []
            if not facts:
                continue
            first = facts[0]
            props = {fact["p"]: fact["o"] for fact in facts if fact["p"] not in ("type",)}
            found.setdefault(finding["rule"], []).append({
                "id": old_id, "replaced_by": new_id, "source": first.get("source"),
                "quote": first.get("quote"), "valid_from": first.get("valid_from"),
                "valid_to": first.get("valid_to"), "author": first.get("author"),
                "status": props.get("status"),
            })
    return found


REG_NAMES = {"REG-ASL": "Approved supplier list", "REG-CAPABILITIES": "Supplier register",
             "REG-SUPPLIER_QUALIFICATION": "Supplier register", "REG-CERTIFICATES": "Certificate register",
             "REG-PARTS": "Parts register", "REG-PROGRAMS": "Programs register",
             "REG-CUSTOMERS": "Customer register", "REG-MATERIALS": "Materials register"}
DOC_TYPE_NAMES = {"customer_requirement": "Customer manual", "internal_procedure": "Quality procedure"}
_doc_cache = {}


def _doc(doc_id):
    """(type, body lines) of data/docs/<id>.md, or None."""
    if doc_id not in _doc_cache:
        path = ROOT / "data" / "docs" / f"{doc_id}.md"
        entry = None
        if re.fullmatch(r"[A-Za-z0-9._-]+", doc_id or "") and path.exists():
            text = path.read_text(encoding="utf-8")
            kind = re.search(r"^type:\s*(\S+)", text, re.M)
            body = text.split("\n---\n", 1)[1] if text.startswith("---") and "\n---\n" in text else text
            entry = (kind.group(1) if kind else "", body.splitlines())
        _doc_cache[doc_id] = entry
    return _doc_cache[doc_id]


def _clause(doc_id, quote):
    """Section number ('7.1') of the body line holding the start of `quote`, else None."""
    direct = re.match(r"\s*(\d+(?:\.\d+)+)\s", quote or "")
    if direct:
        return direct.group(1)
    entry = _doc(doc_id)
    if not entry or not quote:
        return None
    lines = entry[1]
    needle = " ".join(quote.split())[:40].lower()
    flat = [" ".join(line.split()).lower() for line in lines]
    starts = [i for i, line in enumerate(flat) if needle[:20] in line] or \
             [i for i in range(len(flat)) if needle in " ".join(flat[i:i + 2])]
    for index in starts[:1]:
        if True:
            for back in range(index, -1, -1):
                found = re.match(r"\s*(\d+(?:\.\d+)+)\s", lines[back])
                if found:
                    return found.group(1)
            return None
    return None


def source_chips(finding):
    """Source documents behind one finding: [{name, id, clause}], policy documents first, then the decisive
    register rows (not the generic part -> program -> customer chain)."""
    leaves = []

    def walk(steps):
        for step in steps or []:
            if step.get("quote") and step.get("source"):
                leaves.append(step)
            walk(step.get("premises"))
    walk(finding.get("evidence"))
    chips, seen = [], set()
    chain = {"REG-PROGRAMS", "REG-CUSTOMERS"}
    for step in sorted(leaves, key=lambda l: l["source"].startswith("REG-")):
        source, quote = step["source"], step["quote"]
        if source.startswith("REG-"):
            if source in chain or (source == "REG-PARTS" and any(not l["source"].startswith("REG-") or
                                                                 l["source"] != "REG-PARTS" for l in leaves
                                                                 if l is not step)):
                continue
            ident = quote.split(",", 1)[0]
            chip = {"name": REG_NAMES.get(source, source[4:].replace("_", " ").title() + " register"), "id": ident}
        else:
            entry = _doc(source)
            name = DOC_TYPE_NAMES.get(entry[0]) if entry else None
            if not name:
                name = ("Quality procedure" if source.startswith("QP-") else "8D report" if source.startswith("8D-")
                        else "Deviation" if source.startswith("DEV-") else "Document")
            chip = {"name": name, "id": source, "clause": _clause(source, quote)}
        key = (chip["name"], chip["id"], chip.get("clause"))
        if key not in seen:
            seen.add(key)
            chips.append(chip)
    return chips[:4]


def run_check(request, drop_rows=None, explain=True):
    """core.check.run with an optional in-memory table edit. Returns the response for the page. explain=True adds
    the verified counterfactuals and the two-register explanation to the card (core/explain_text.py)."""
    drop_rows = sorted(set(drop_rows or []))
    table, table_text = table_for(drop_rows)
    report = coverage_for(table, ",".join(drop_rows))
    card, entry, projection = check.evaluate(request, table=table, rules_version_value=rules_version_for(table_text),
                                             coverage_value=decision.coverage_summary(report), explain=explain)
    row = card["decision"]
    findings = card["findings"]
    return {
        "card": card,
        "record": entry,
        "row_meaning": decision.row_meaning(row["row_id"], table),
        "table_note": table.get("version_note"),
        "drop_rows": drop_rows,
        "replaced": replaced_records(projection, findings),
        "labels": labels(),
        "finding_sources": [source_chips(f) if f.get("severity") == "blocker" else [] for f in findings],
    }


# ---- model-gateway fallback (#17) ---------------------------------------------------------------------------

PARSE_TIMEOUT_S = 8
_parse_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="parse")
# Remarks the demo page sends that are not scenario utterances (web/static/app.js).
DEMO_REMARKS = [
    {"remark": "Can we switch BR-220 from anodising to trivalent conversion coating?",
     "change": {"type": "CoatingChange", "part": "BR-220", "new_coating": "COAT-TCP"}},
    {"remark": "Let's move the BR-220 final inspection to the new CMM next week.",
     "change": {"type": "EquipmentChange", "part": "BR-220"}},
]


class ParseFailed(Exception):
    """The remark could not be parsed (model gateway down, out of credits, slow). The page offers the typed form."""

    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


def classify_parse_error(error):
    """(reason, message) for the page. Never guesses a request."""
    status = getattr(error, "status_code", None)
    name = type(error).__name__
    if status == 402:
        return "credits", "Model gateway: credits used up (HTTP 402)."
    if status in (401, 403):
        return "auth", f"Model gateway refused the key (HTTP {status})."
    if status is not None:
        return "gateway", f"Model gateway error (HTTP {status})."
    if name == "FixtureMissing":
        return "no_key", "No recorded parse for this remark and no model key on the server."
    if name in ("APIConnectionError", "APITimeoutError") or isinstance(error, OSError):
        return "network", "Model gateway unreachable (network)."
    return "error", f"Parse failed: {name}: {error}"


def parse_remark(remark, as_of):
    """check.from_remark with a hard timeout. Raises ParseFailed."""
    future = _parse_pool.submit(check.from_remark, remark, as_of)
    try:
        return future.result(timeout=PARSE_TIMEOUT_S)
    except FutureTimeout:
        raise ParseFailed("timeout", f"Model gateway did not answer in {PARSE_TIMEOUT_S} s.")
    except Exception as error:
        reason, message = classify_parse_error(error)
        raise ParseFailed(reason, message)


def demo_requests():
    """[(utterance, change dict)] for every demo remark: scenario utterances and the page's built-in remarks."""
    with open(ROOT / "data" / "scenarios.json", encoding="utf-8") as handle:
        scenarios = json.load(handle)
    items = [(item.get("utterance") or item.get("title") or "", item["change"]) for item in scenarios]
    items += [(item["remark"], item["change"]) for item in DEMO_REMARKS]
    return items


def closest_form(remark, as_of=None):
    """The typed form prefilled with the demo request whose remark is closest to `remark` (difflib ratio)."""
    text = (remark or "").lower()
    best, best_score = None, -1.0
    for utterance, change in demo_requests():
        score = SequenceMatcher(None, text, utterance.lower()).ratio()
        if score > best_score:
            best, best_score = (utterance, change), score
    utterance, change = best
    form = {key: value for key, value in change.items() if key in parse.FORM_FIELDS and value}
    form["as_of"] = as_of or time.strftime("%Y-%m-%d")
    form["utterance"] = remark
    return {"form": form, "closest_remark": utterance, "similarity": round(best_score, 2)}


def parse_failure_payload(failure, body):
    payload = {"error": str(failure), "parse_failed": True, "reason": failure.reason,
               "change_types": list(CHANGE_TYPES), "form_fields": sorted(parse.FORM_FIELDS),
               "labels": labels()}
    payload.update(closest_form(body.get("remark"), body.get("as_of")))
    return payload


def handle_check(body):
    drop_rows = body.get("drop_rows") or []
    parse_ms = None
    if body.get("remark"):
        started = time.time()
        request = parse_remark(body["remark"], body.get("as_of"))
        parse_ms = round((time.time() - started) * 1000, 1)
        if body.get("speaker"):
            request["speaker"] = body["speaker"]
    elif body.get("form"):
        request = parse.parse_form({key: value for key, value in body["form"].items() if value not in (None, "")})
    elif body.get("scenario"):
        request = check.scenario(body["scenario"])
    elif body.get("request"):
        request = dict(body["request"])
    else:
        raise ValueError("send one of: remark, form, scenario, request")
    if body.get("as_of"):
        request["as_of"] = body["as_of"]
    response = run_check(request, drop_rows, explain=body.get("explain", True) is not False)
    if parse_ms is not None:
        response["card"]["timings_ms"] = {"parse": parse_ms, **response["card"]["timings_ms"]}
    return response


def handle_table(query):
    drop_rows = sorted(set(filter(None, (query.get("drop", [""])[0]).split(","))))
    table, table_text = table_for(drop_rows)
    report = coverage_for(table, ",".join(drop_rows))
    return {"table": table, "coverage": report, "rules_version": rules_version_for(table_text),
            "drop_rows": drop_rows, "labels": labels()}


def handle_table_dmn(query):
    """The same table (and the same in-memory edit) as /api/table, as an OMG DMN 1.3 XML string (core/dmn.py)."""
    drop_rows = sorted(set(filter(None, (query.get("drop", [""])[0]).split(","))))
    table, table_text = table_for(drop_rows)
    return dmn.export(table, rules_version_value=rules_version_for(table_text))


def handle_names():
    """Plain names for the page (read-only): short labels, part -> program -> customer, change-type labels."""
    from core.extract import CHANGE_TYPE_LABELS
    with open(ROOT / "data" / "registries.json", encoding="utf-8") as handle:
        registries = json.load(handle)
    programs = {row[0]: {"name": row[1], "customer": row[2]} for row in registries["programs"]["rows"]}
    parts = {}
    for row in registries["parts"]["rows"]:
        program = programs.get(row[2], {})
        parts[row[0]] = {"name": row[1], "program": row[2], "customer": program.get("customer")}
    return {"parts": parts, "people": people(), "change_types": CHANGE_TYPE_LABELS}


def handle_scenarios():
    with open(ROOT / "data" / "scenarios.json", encoding="utf-8") as handle:
        return {"scenarios": json.load(handle), "people": people()}


def handle_explain(query):
    """Two-register explanation of any past decision record (core/explain_text.py for_record); writes nothing."""
    from core import explain_text
    record_id = (query.get("record_id", [""])[0] or "").strip()
    if not record_id:
        raise ValueError("send ?record_id=<decision record id>")
    try:
        result = explain_text.for_record(record_id)
    except KeyError as error:
        return {"error": str(error)}, 404
    return {"record": result["record"], "explanation": result["explanation"],
            "counterfactuals": result["card"].get("counterfactuals"),
            "counterfactual_all": result["card"].get("counterfactual_all")}, 200


def handle_records(query):
    limit = int(query.get("limit", ["50"])[0])
    return {"records": list(reversed(decision.read_records()))[:limit]}


def handle_impact(query):
    """#29: facts, table rows, recorded and past decisions resting on a document; read-only."""
    doc = (query.get("doc", [""])[0] or "").strip()
    if not doc:
        raise ValueError("send ?doc=<document id>")
    facts = check.memory().all_facts(review=None)
    return {"impact": impact.impact(doc, facts=facts), "labels": labels()}


# ---- meeting mode (#32) ------------------------------------------------------------------------------------

def classify_line(line):
    """core.meeting.classify with the same hard timeout as the parser. Raises ParseFailed."""
    future = _parse_pool.submit(meeting.classify, line)
    try:
        return future.result(timeout=PARSE_TIMEOUT_S)
    except FutureTimeout:
        raise ParseFailed("timeout", f"Model gateway did not answer in {PARSE_TIMEOUT_S} s.")
    except Exception as error:
        reason, message = classify_parse_error(error)
        raise ParseFailed(reason, message)


def handle_meeting_line(body):
    """One transcript line -> classification; a flagged line goes through parse -> check. Never a card for a line
    the model did not flag; a line that could not be classified says so."""
    line = " ".join(str(body.get("line") or "").split())
    if not line:
        raise ValueError("send {line, speaker?, as_of?}")
    as_of = body.get("as_of") or check.DEFAULT_AS_OF
    response = {"line": line, "speaker": body.get("speaker"), "as_of": as_of, "flagged": False, "classified": True}
    clock = time.perf_counter()
    try:
        result = classify_line(line)
    except ParseFailed as failure:
        gate = meeting.prefilter(line)
        response.update({"classified": False, "reason": f"not classified: {failure}", "stage": "model",
                         "mentions": gate["mentions"]})
        return response
    response.update({"flagged": result["is_change_proposal"], "reason": result["reason"], "stage": result["stage"],
                     "mentions": result["mentions"]})
    timing = {"classify": round((time.perf_counter() - clock) * 1000)}  # wall-clock ms for the page's step trail
    response["timing_ms"] = timing
    if not response["flagged"]:
        return response
    clock = time.perf_counter()
    try:
        request = parse_remark(line, as_of)
    except ParseFailed as failure:
        response["card_error"] = f"flagged, but the line was not parsed: {failure}"
        return response
    if body.get("speaker"):
        request["speaker"] = body["speaker"]
    if not request.get("type") or not request.get("part"):
        response.update({"request": request, "labels": labels(),
                         "card_error": "flagged, but the parser found no change type or part: a person reads it"})
        return response
    timing["parse"] = round((time.perf_counter() - clock) * 1000)
    response.update(run_check(request))
    return response


def handle_meeting_demo():
    return {"lines": meeting.load_demo(), "people": people()}


# ---- HTTP -------------------------------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "kakashi-demo/1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_dmn(self, xml_text, download):
        data = xml_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if download:
            self.send_header("Content-Disposition", 'attachment; filename="decision.dmn"')
        self.end_headers()
        self.wfile.write(data)

    def send_static(self, relative):
        path = (STATIC / relative).resolve()
        if STATIC.resolve() not in path.parents or not path.is_file():
            self.send_json({"error": "not found"}, 404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        try:
            if url.path == "/healthz":
                self.send_json({"ok": True})
            elif url.path in ("/", "/index.html"):
                self.send_static("index.html")
            elif url.path.startswith("/static/"):
                self.send_static(url.path[len("/static/"):])
            elif url.path == "/api/scenarios":
                self.send_json(handle_scenarios())
            elif url.path == "/api/names":
                self.send_json(handle_names())
            elif url.path == "/api/table.dmn" or (url.path == "/api/table" and query.get("format") == ["dmn"]):
                with LOCK:
                    self.send_dmn(handle_table_dmn(query), download=url.path.endswith(".dmn"))
            elif url.path == "/api/table":
                with LOCK:
                    self.send_json(handle_table(query))
            elif url.path == "/api/records":
                self.send_json(handle_records(query))
            elif url.path == "/api/explain":
                with LOCK:
                    payload, status = handle_explain(query)
                self.send_json(payload, status)
            elif url.path == "/api/meeting/demo":
                self.send_json(handle_meeting_demo())
            elif documents.handle_get(url.path) is not None:
                with LOCK:
                    payload, status = documents.handle_get(url.path)
                self.send_json(payload, status)
            elif url.path == "/api/impact":
                with LOCK:
                    self.send_json(handle_impact(query))
            else:
                self.send_json({"error": "not found"}, 404)
        except Exception as error:  # the demo shows the error, never a blank page
            self.send_json({"error": f"{type(error).__name__}: {error}"}, 500)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path.startswith(("/api/documents", "/api/proposals")):
            length = int(self.headers.get("Content-Length") or 0)
            if length > documents.MAX_BYTES + 65536:
                self.send_json({"error": "document larger than 5 MB"}, 413)
                return
            raw = self.rfile.read(length)
            with LOCK:
                payload, status = documents.handle_post(url.path, self.headers.get("Content-Type"), raw)
            self.send_json(payload, status)
            return
        if url.path not in ("/api/check", "/api/meeting/line"):
            self.send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            if url.path == "/api/meeting/line":
                self.handle_line(body)
                return
            refusal = remark_budget_refusal(body, self.client_address[0])
            if refusal:
                self.send_json({"error": refusal}, 429)
                return
            with LOCK:
                self.send_json(handle_check(body))
        except ParseFailed as failure:  # gateway down / 402 / slow: the page offers the typed form, never a fake
            self.send_json(parse_failure_payload(failure, body), 503)
        except Exception as error:
            self.send_json({"error": f"{type(error).__name__}: {error}"}, 400)


    def handle_line(self, body):
        line = str(body.get("line") or "")
        if meeting.prefilter(line)["passed"]:  # only lines that may reach the model count against the budget
            refusal = remark_budget_refusal({"remark": line}, self.client_address[0])
            if refusal:
                self.send_json({"error": refusal}, 429)
                return
        with LOCK:
            self.send_json(handle_meeting_line(body))


# ---- public deployment guard: remarks may call the model on the team key, so cap them ----------------------
REMARK_MAX_CHARS = int(os.environ.get("REMARK_MAX_CHARS", 600))
REMARKS_PER_IP_PER_10_MIN = int(os.environ.get("REMARKS_PER_IP_PER_10_MIN", 30))
REMARKS_TOTAL_CAP = int(os.environ.get("REMARKS_TOTAL_CAP", 1000))
_remark_times = {}
_remark_total = [0]


def remark_budget_refusal(body, client_ip):
    """None if this request may go on; else a message. Only free-text remarks are counted."""
    remark = body.get("remark")
    if not remark:
        return None
    if len(remark) > REMARK_MAX_CHARS:
        return f"remark too long (max {REMARK_MAX_CHARS} characters)"
    now = time.time()
    with LOCK:
        recent = [moment for moment in _remark_times.get(client_ip, []) if now - moment < 600]
        if len(recent) >= REMARKS_PER_IP_PER_10_MIN:
            return "too many remarks from this address; try again in a few minutes or use a demo button"
        if _remark_total[0] >= REMARKS_TOTAL_CAP:
            return "the public demo reached its remark budget; demo buttons still work"
        recent.append(now)
        _remark_times[client_ip] = recent
        _remark_total[0] += 1
    return None


def main():
    parser = argparse.ArgumentParser(description="Demo page for the change check")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    args = parser.parse_args()
    print("warming up (fact log, closure, table coverage)...", flush=True)
    with LOCK:
        check.memory()
        warm(check.memory(), check.DEFAULT_AS_OF)  # full closure for today; recomputed when facts are accepted
        coverage_for(decision.load_table(), "")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"demo on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
