# Demo runbook (17:05, 5 minutes)

What to do when the wifi, the model gateway or the laptop fails during the live demo. Issue #17.

## Before the slot

```sh
cd kakashi_public
git pull                                   # the merged main
python -m web.snapshot                     # re-record the offline replay from this exact code and data
python -m web.server                       # http://localhost:8000
```

`web/snapshot.py` starts its own server on a free port, calls every route the demo buttons use and saves the
answers to `web/static/snapshot/` (about 160 responses, 2 MB, a few seconds). Record it again after every merge
that touches `data/`, `core/` or `data/scenarios.json`; the label on the page shows when it was recorded.
`python -m web.snapshot --base http://127.0.0.1:8000` records from a server that is already running.

Open http://localhost:8000 at 1440×900, click every demo button once (warms the cache), then reload.

## Offline replay

The page answers from the snapshot when:

- the **"Offline replay"** switch in the top bar is on (click it), or the URL has `?offline=1`;
- automatically, when the server is unreachable or a route returns an error and the snapshot has the answer.

An amber **"offline replay · recorded …"** label stays in the bottom-right corner while it is on. Click the switch
again to go back to the live server.

What replays offline: every demo button (scenarios and the built-in rule-change and CMM demos), the demo remarks
typed into the strip on the dates the page sends them (the scenario's own date and 14 Nov), the rule-change
compare (15 Jun vs 14 Nov), time travel with the default dates and every scenario date, "Edit the decision table"
for every row of every recorded request, the decision table and the decision records. Any other remark shows
"offline: parsing needs the network"; nothing is invented.

**If the server process died but the laptop is fine**, serve the static page and the snapshot without Python
dependencies:

```sh
cd kakashi_public/web && python3 -m http.server 8000
# open http://localhost:8000/static/index.html  -> the API routes 404, the page switches to offline replay
```

## The model gateway fails (402 = credits used up, network, > 8 s)

Only remarks that are not recorded call the model: the demo remarks parse from fixtures
(`tests/fixtures/parse/`) and need no key and no network. When a new remark's parse fails, the server answers
503 with the reason (`credits` for HTTP 402, `network`, `timeout` after 8 s, `auth`, `no_key`) and the page shows
**"The remark was not parsed"** with a typed form prefilled from the closest demo request. Nothing is guessed: check
the fields, change any of them (ids such as `SUP-C` or registry names), and press **Check typed form**. The form
goes through `core.parse.parse_form` (no model call).

What to say: "The model only reads the sentence. The gateway is down, so I type the change: the check itself is
deterministic and does not need the model."

## The laptop dies

Play the recorded run from another laptop or a phone. It is not in the repo (local files only):

- `~/Desktop/kva_hackathon/demo_backup/demo_run.mp4` (QuickTime) and `demo_run.webm` — the demo order of issue #19, 1440×900, ~40 s, no sound
- `~/Desktop/kva_hackathon/demo_backup/NN_*.png` — one screenshot per step
- `~/Desktop/kva_hackathon/demo_backup/DEMO_SCRIPT.md` — each step: what to click, what the jury sees, one line to say

Copy the folder to a USB stick and a second laptop before 17:00.
