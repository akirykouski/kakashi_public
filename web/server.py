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
    GET  /api/records   ?limit=50     decision records, newest first
    GET  /api/impact    ?doc=CSR-AUR-R3   what a superseded document affects (core/impact.py, #29)

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

from core import check, decision, impact, oida, parse, rules  # noqa: E402
from core.contracts import CHANGE_TYPES, Card, ChangeRequest  # noqa: E402
from core.project import Projection  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
LOCK = threading.Lock()  # the core keeps per-process caches; one check at a time
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
                 ".ico": "image/x-icon"}
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


def run_check(request, drop_rows=None):
    """core.check.run with an optional in-memory table edit. Returns the response for the page."""
    drop_rows = sorted(set(drop_rows or []))
    table, table_text = table_for(drop_rows)
    report = coverage_for(table, ",".join(drop_rows))
    card, entry, projection = check.evaluate(request, table=table, rules_version_value=rules_version_for(table_text),
                                             coverage_value=decision.coverage_summary(report))
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
    response = run_check(request, drop_rows)
    if parse_ms is not None:
        response["card"]["timings_ms"] = {"parse": parse_ms, **response["card"]["timings_ms"]}
    return response


def handle_table(query):
    drop_rows = sorted(set(filter(None, (query.get("drop", [""])[0]).split(","))))
    table, table_text = table_for(drop_rows)
    report = coverage_for(table, ",".join(drop_rows))
    return {"table": table, "coverage": report, "rules_version": rules_version_for(table_text),
            "drop_rows": drop_rows, "labels": labels()}


def handle_scenarios():
    with open(ROOT / "data" / "scenarios.json", encoding="utf-8") as handle:
        return {"scenarios": json.load(handle), "people": people()}


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
            elif url.path == "/api/table":
                with LOCK:
                    self.send_json(handle_table(query))
            elif url.path == "/api/records":
                self.send_json(handle_records(query))
            elif url.path == "/api/impact":
                with LOCK:
                    self.send_json(handle_impact(query))
            else:
                self.send_json({"error": "not found"}, 404)
        except Exception as error:  # the demo shows the error, never a blank page
            self.send_json({"error": f"{type(error).__name__}: {error}"}, 500)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/check":
            self.send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
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
        coverage_for(decision.load_table(), "")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"demo on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
