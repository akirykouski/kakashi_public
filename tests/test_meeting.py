"""Meeting mode (#32). Run: python -m pytest tests/test_meeting.py -q

The classifier answers replay from tests/fixtures/meeting/ (recorded live through the Vercel AI Gateway,
anthropic/claude-haiku-5.5), the parser's from tests/fixtures/parse/: no key needed.
"""
import json
import os
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import meeting  # noqa: E402
from core.llm import FixtureMissing  # noqa: E402

DEMO = meeting.load_demo()


@pytest.mark.parametrize("line,reason", [
    ("Good morning everyone.", "short line"),
    ("Good morning everyone, let's start, we have four items today.", "greeting or acknowledgement"),
    ("Good, I'll bring these to the decision with the cards. Thanks everyone.",
     "names no part, supplier, material, coating, site or process"),
    ("We re-audited Chisone last week, they passed with a score of 86.", "no change verb"),
])
def test_prefilter_stops(line, reason):
    gate = meeting.prefilter(line)
    assert gate == {**gate, "passed": False, "reason": reason}


def test_prefilter_passes_change_lines():
    for line in ("Let's take the BR-220 blanks from Chisone, same alloy.",
                 "Can we switch BR-220 from anodising to trivalent conversion coating?",
                 "Let's move the BR-220 final inspection to the new CMM next week."):
        assert meeting.prefilter(line)["passed"], line


def test_mentions():
    assert meeting.mentions("Bormida is late, take BR-220 from Chisone") == ["BR-220", "SUP-B", "SUP-C"]
    assert meeting.mentions("We can run eight days on stock at Beinasco.") == ["PLT-BEI"]


def test_prefilter_lines_never_call_the_model():
    def boom(*args):
        raise AssertionError("model called")
    result = meeting.classify("We re-audited Chisone last week, they passed with a score of 86.", call=boom)
    assert result["stage"] == "prefilter" and result["is_change_proposal"] is False
    assert result["mentions"] == ["SUP-C"]


@pytest.mark.parametrize("item", DEMO, ids=[item["text"][:40] for item in DEMO])
def test_demo_transcript_classification(item):
    result = meeting.classify(item["text"])
    assert result["is_change_proposal"] is item["expect"], result["reason"]


def test_most_demo_lines_cost_nothing():
    stages = [meeting.classify(item["text"])["stage"] for item in DEMO]
    assert stages.count("prefilter") > len(DEMO) / 2


def test_unseen_line_without_key_raises(monkeypatch):
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.setattr("core.llm.load_dotenv", lambda *args, **kwargs: None)
    with pytest.raises(FixtureMissing):
        meeting.classify("Let's switch HS-410 to zinc flake from Galvanica next month, totally new line 7781.")


# ---- the route ---------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def server():
    from web import server as web_server
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web_server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def post(base, path, body):
    request = urllib.request.Request(base + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def test_route_demo(server):
    with urllib.request.urlopen(server + "/api/meeting/demo") as response:
        data = json.loads(response.read())
    assert len(data["lines"]) == len(DEMO) and "PER-ROSSI" in data["people"]


def test_route_ordinary_line_has_no_card(server):
    data = post(server, "/api/meeting/line", {"line": "We can run eight days on stock at Beinasco.",
                                              "speaker": "PER-COSTA", "as_of": "2026-11-14"})
    assert data["flagged"] is False and "card" not in data and data["stage"] == "prefilter"


def test_route_model_rejected_line_has_no_card(server):
    line = "If Bormida slips again next quarter we might look at a second source for BR-225, but not today."
    data = post(server, "/api/meeting/line", {"line": line, "as_of": "2026-11-05"})
    assert data["flagged"] is False and data["stage"] == "model" and "card" not in data


def test_route_flagged_line_gets_a_card(server):
    line = "Bormida is two weeks late. Let's take the BR-220 blanks from Chisone, same alloy."
    data = post(server, "/api/meeting/line", {"line": line, "speaker": "PER-FERRI", "as_of": "2026-11-05"})
    assert data["flagged"] is True
    card = data["card"]
    assert card["request"]["to_supplier"] == "SUP-C" and card["request"]["speaker"] == "PER-FERRI"
    assert card["verdict"] == "blockers_found"
    assert "R1a" in {finding["rule"] for finding in card["findings"]}


def test_route_r0_line(server):
    data = post(server, "/api/meeting/line", {"line": "Let's move the BR-220 final inspection to the new CMM next week.",
                                              "as_of": "2026-11-14"})
    assert data["flagged"] is True and data["card"]["decision"]["row_id"] == "R0"
