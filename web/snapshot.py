"""Record the demo for offline replay: every route the demo buttons call, saved as JSON under web/static/snapshot/.

    python -m web.snapshot                       # starts its own server on a free port, records, stops it
    python -m web.snapshot --base http://127.0.0.1:8000   # record from a server that is already running

The page (web/static/app.js) switches to "offline replay" when the server is unreachable or a route errors, and
answers from these files. Only what is recorded here can be replayed: the scenarios, the demo remarks on the
dates the page sends them, the rule-change compare, time travel and table edits of every recorded request, the
decision table, the impact report of every superseded document a card shows, and the decision records. Any other remark shows "offline: parsing needs the network".

The lookup key is built the same way here and in app.js (snapshotKey): keep the two in step.

Written 14 Nov 2026 (issue #17, fallbacks).
"""
import argparse
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "static" / "snapshot"
TODAY = "2026-11-14"
# Remarks and requests the page sends that are not scenario utterances (keep in step with web/static/app.js).
RULE_CHANGE_REMARK = "Can we switch BR-220 from anodising to trivalent conversion coating?"
NO_RULE_REMARK = "Let's move the BR-220 final inspection to the new CMM next week."
NO_RULE_REQUEST = {"type": "EquipmentChange", "part": "BR-220"}
DEFAULT_REMARK = "Bormida is two weeks late. Let's take the BR-220 blanks from Chisone, same alloy."
TIME_TRAVEL_DATES = ["2026-11-05", TODAY]  # the page's default compare dates
REQUEST_FIELDS = ["type", "part", "to_supplier", "from_supplier", "site", "at_supplier", "new_material",
                  "new_coating", "scope", "known_at"]


# ---- the key (mirrors snapshotKey in app.js) ----------------------------------------------------------------

def norm(text):
    return " ".join(str(text or "").split()).lower()


def check_key(body):
    as_of = body.get("as_of") or ""
    drop = ",".join(sorted(body.get("drop_rows") or []))
    if body.get("remark"):
        return f"remark|{norm(body['remark'])}|{as_of}|{drop}"
    if body.get("scenario"):
        return f"scenario|{body['scenario']}|{as_of}|{drop}"
    request = body.get("request") or body.get("form") or {}
    as_of = as_of or request.get("as_of") or ""
    values = [str(request.get(field) or ("series" if field == "scope" else "")) for field in REQUEST_FIELDS]
    return "request|" + "|".join(values) + f"|{as_of}|{drop}"


def file_for(key):
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".json"


# ---- recorder ------------------------------------------------------------------------------------------------

class Recorder:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.index = {}
        self.labels = {}
        self.failures = []
        self.impact_docs = set()  # superseded documents shown on a card: their "what does this affect" report

    def call(self, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.base + path, data=data,
                                         headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            return {"error": f"HTTP {error.code}: {error.read()[:300].decode('utf-8', 'replace')}"}

    def save(self, key, payload):
        if "labels" in payload:
            self.labels.update(payload.pop("labels"))
        name = file_for(key)
        (OUT / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.index[key] = name

    def get(self, path):
        key = f"GET {path}"
        if key in self.index:
            return None
        payload = self.call(path)
        if payload.get("error"):
            self.failures.append((key, payload["error"]))
            return None
        self.save(key, payload)
        return payload

    def check(self, body):
        key = check_key(body)
        if key in self.index:
            return None
        payload = self.call("/api/check", body)
        if payload.get("error"):
            self.failures.append((key, payload["error"]))
            return None
        for items in (payload.get("replaced") or {}).values():
            self.impact_docs.update(item["id"] for item in items if item.get("id"))
        self.save(key, payload)
        return payload


def request_of(card_request):
    return {field: card_request.get(field) for field in REQUEST_FIELDS + ["utterance", "as_of"] if card_request.get(field)}


def record_all(recorder, records_limit=40):
    scenarios = recorder.get("/api/scenarios")["scenarios"]
    table = recorder.get("/api/table")["table"]
    droppable = [row["id"] for row in table["rows"] if row["id"] != "R0"]
    ids = {item["id"] for item in scenarios}
    requests = {}  # check_key of the request -> request, every "current request" the page can hold

    def keep(payload):
        if payload:
            request = request_of(payload["card"]["request"])
            requests[check_key({"request": request})] = request

    # 1. demo buttons: one per scenario, and the remark typed for it (on its own date and today)
    for item in scenarios:
        keep(recorder.check({"scenario": item["id"]}))
        if item.get("utterance"):
            for as_of in sorted({item.get("as_of") or TODAY, TODAY}):
                keep(recorder.check({"remark": item["utterance"], "as_of": as_of}))
    # 2. the page's built-in demos (when scenarios.json has no entry for them)
    if "no_rule" not in ids:
        keep(recorder.check({"request": {**NO_RULE_REQUEST, "utterance": NO_RULE_REMARK, "as_of": TODAY}}))
    keep(recorder.check({"remark": NO_RULE_REMARK, "as_of": TODAY}))
    if "rule_change_r3" not in ids or "rule_change_r4" not in ids:
        keep(recorder.check({"remark": RULE_CHANGE_REMARK, "as_of": "2026-06-15"}))
        keep(recorder.check({"remark": RULE_CHANGE_REMARK, "as_of": TODAY}))
    for as_of in ("2026-11-05", TODAY):
        keep(recorder.check({"remark": DEFAULT_REMARK, "as_of": as_of}))
    # 3. time travel and table edits of every request the page can hold
    dates = sorted(set(TIME_TRAVEL_DATES) | {item.get("as_of") for item in scenarios if item.get("as_of")})
    for request in list(requests.values()):
        for as_of in dates:
            recorder.check({"request": {**request, "as_of": as_of}})
        recorder.check({"request": request})
        for row in droppable:
            recorder.check({"request": request, "drop_rows": [row]})
    # 4. the impact report (#29) of every superseded document a card shows
    for doc in sorted(recorder.impact_docs):
        recorder.get(f"/api/impact?doc={urllib.parse.quote(doc)}")
    # 5. the records list last, so it shows the checks above
    recorder.get(f"/api/records?limit={records_limit}")
    return len(scenarios), len(requests)


# ---- server ----------------------------------------------------------------------------------------------------

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_server():
    port = free_port()
    process = subprocess.Popen([sys.executable, "-m", "web.server", "--port", str(port)], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(240):
        try:
            urllib.request.urlopen(base + "/api/scenarios", timeout=2).read()
            return process, base
        except OSError:
            if process.poll() is not None:
                raise SystemExit("the demo server exited while starting")
            time.sleep(0.5)
    process.terminate()
    raise SystemExit("the demo server did not start in 120 s")


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True).stdout.strip()
    except OSError:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Record the demo routes for offline replay")
    parser.add_argument("--base", help="a running server, e.g. http://127.0.0.1:8000 (default: start one)")
    args = parser.parse_args()
    process = None
    base = args.base
    if not base:
        process, base = start_server()
    started = time.time()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    recorder = Recorder(base)
    try:
        scenario_count, request_count = record_all(recorder)
    finally:
        if process:
            process.terminate()
    manifest = {"created_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "commit": git_commit(),
                "count": len(recorder.index), "labels": recorder.labels, "index": recorder.index,
                "failures": [{"key": key, "error": error} for key, error in recorder.failures]}
    (OUT / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
    size = sum(path.stat().st_size for path in OUT.iterdir())
    print(f"recorded {len(recorder.index)} responses ({scenario_count} scenarios, {request_count} requests) "
          f"in {time.time() - started:.0f} s, {size / 1e6:.1f} MB -> {OUT.relative_to(ROOT)}")
    for key, error in recorder.failures:
        print(f"  FAILED {key}: {error[:200]}")


if __name__ == "__main__":
    main()
