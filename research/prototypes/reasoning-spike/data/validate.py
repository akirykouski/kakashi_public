#!/usr/bin/env python3
"""Stdlib-only validator for the KVA synthetic dataset. Exit 1 on any failure.

Usage: python3 validate.py [--no-lock | --relock] [DATA_DIR] [ONTOLOGY_README]
  DATA_DIR default: directory of this file.
  Two layers. Layer 2 (semantic: shape, quotes, invariants, canonical rows, claim fidelity) runs and
  is reported FIRST. Layer 1 (tamper lock) then recomputes sha256 of README.md, sources/*, eval/* and
  compares with MANIFEST.lock: any changed, missing or unlisted file fails.
  --no-lock  skip layer 1 (used by the tests to prove the semantic layer on its own).
  --relock   rewrite MANIFEST.lock, ONLY if every semantic check passed; prints the file diff.
             A relock is a human-reviewed step: read the diff in the commit.
  ONTOLOGY_README default: DATA_DIR/../ontology/README.md (a missing file is an error,
  never a silent skip: the allowed rule-id set depends on it).
"""
import datetime, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

_flags = {a for a in sys.argv[1:] if a.startswith("--")}
_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
if _flags - {"--no-lock", "--relock"} or {"--no-lock", "--relock"} <= _flags:
    sys.exit("usage: validate.py [--no-lock | --relock] [DATA_DIR] [ONTOLOGY_README]")
NO_LOCK, RELOCK = "--no-lock" in _flags, "--relock" in _flags
ROOT = Path(_pos[0]) if len(_pos) > 0 else Path(__file__).resolve().parent
ONTO = Path(_pos[1]) if len(_pos) > 1 else ROOT.resolve().parent / "ontology" / "README.md"
LOCK = ROOT / "MANIFEST.lock"
EVAL_ALLOWED = {"RULES.md", "canonical.json", "change_requests.jsonl", "dev.jsonl", "gold.jsonl", "invariants.json"}
SUPPLIER_NAMES = ["Alluminio B", "Meccanica C", "Anodica Veneta", "Rivestimenti Nord", "Termica Nord",
                  "Laboratorio Sigma", "Ferrotec D", "Trafilerie E"]  # to derive suppliers of the frozen 20
STOPWORDS = set("""that this with from have been were which when then than there their they them will would
should could must shall also only same into over under such each both does done more most less other
what whose where while these those about after before because between being below above again further
once here very just like need needs used uses using make made take taken give given still even
""".split())
MIN_QUOTE = 20  # shortest legitimate quote in the set is 20 chars; one-char "quotes" match anything
EXPECTED_CATS = {"direct_conflict": 5, "inference_only": 6, "stale_rule_trap": 4,
                 "missing_data": 3, "clean_control": 2}
VERDICTS = {"blockers_found", "no_blockers_found", "needs_info"}
KINDS = {"blocker", "inferred", "question"}
# Real OEM / tier names, blocked in EVERY text file under data/ (except this validator and its
# test, which must name them). IGNORECASE = distinctive names; CASE = short or common-word names
# matched case-sensitively so "Gm", "lear", "magna" do not false-positive.
FORBIDDEN_CI = ["Fiat", "Volkswagen", "Renault", "Mercedes", "Toyota", "Bosch",
                "Faurecia", "Forvia", "Brembo", "Marelli", "Tesla", "Hyundai", "Honda", "Nissan",
                "Volvo", "Audi", "Porsche", "Denso", "Valeo"]
FORBIDDEN_CS = ["FCA", "Ford", "GM", "BMW", "VW", "ZF", "Magna", "Continental", "Lear", "Kia"]
SCAN_EXCLUDE = {"validate.py", "test_validate.py"}
HEADER_KEYS = ["doc_id", "type", "revision", "effective_date", "owner", "status"]
errors = []

def err(m): errors.append(m)

def load_jsonl(p):
    rows = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            err(f"{p.name}:{n} invalid JSON: {e}")
    return rows

# real-company guard over every text file in data/
for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or p.name in SCAN_EXCLUDE or "__pycache__" in p.parts: continue
    try: t = p.read_text(encoding="utf-8")
    except UnicodeDecodeError: err(f"{p.relative_to(ROOT)}: not valid UTF-8 text"); continue
    for name in FORBIDDEN_CI + FORBIDDEN_CS:
        flags = re.I if name in FORBIDDEN_CI else 0
        if re.search(rf"\b{re.escape(name)}\b", t, flags):
            err(f"{p.relative_to(ROOT)}: forbidden real-company name {name}")

def load_json(p):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        err(f"{p.name}: cannot load: {e}"); return {}

# allowed rule ids = ontology README ids UNION slugs documented in eval/RULES.md
allowed_rules = set()
try:
    allowed_rules |= set(re.findall(r"^\| `([BQ]_[A-Z0-9_]+)` \|", ONTO.read_text(encoding="utf-8"), re.M))
except OSError as e:
    err(f"ontology README unreadable ({ONTO}): {e}")
if not allowed_rules: err("no blocker ids parsed from ontology README")
try:
    allowed_rules |= set(re.findall(r"^\| `([A-Za-z0-9_]+)`", (ROOT / "eval" / "RULES.md").read_text(encoding="utf-8"), re.M))
except OSError as e:
    err(f"eval/RULES.md unreadable: {e}")

# (f) allowlist: nothing but the known files may exist under eval/ and sources/
_ev = ROOT / "eval"
for p in sorted(_ev.rglob("*")) if _ev.is_dir() else []:
    if p.is_file() and (p.parent != _ev or p.name not in EVAL_ALLOWED):
        err(f"allowlist: unexpected file eval/{p.relative_to(_ev).as_posix()}")
for n in sorted(EVAL_ALLOWED):
    if not (_ev / n).is_file(): err(f"allowlist: required file eval/{n} missing")
_sr = ROOT / "sources"
_inv_keys = None
try:
    _inv_keys = {k for k in json.loads((_ev / "invariants.json").read_text(encoding="utf-8")) if not k.startswith("_")}
except (OSError, json.JSONDecodeError): pass  # reported below as invariants.json: cannot load
for p in sorted(_sr.rglob("*")) if _sr.is_dir() else []:
    if p.is_file() and _inv_keys is not None and (p.parent != _sr or p.name[:-3] not in _inv_keys or not p.name.endswith(".md")):
        err(f"allowlist: unexpected file sources/{p.relative_to(_sr).as_posix()}")
for k in sorted(_inv_keys or []):
    if not (_sr / f"{k}.md").is_file(): err(f"allowlist: source sources/{k}.md missing (listed in invariants.json)")

superseded_docs = set()
# sources
docs = {}
for p in sorted((ROOT / "sources").glob("*.md")):
    t = p.read_text(encoding="utf-8")
    docs[p.stem] = t
    hdr = dict(re.findall(r"^(\w+): (.+)$", t, re.M))
    for k in HEADER_KEYS:
        if k not in hdr:
            err(f"source {p.name}: missing header field {k}")
    if hdr.get("doc_id") != p.stem:
        err(f"source {p.name}: doc_id {hdr.get('doc_id')!r} != filename stem")
    if re.search(r"^status: SUPERSEDED", t, re.M): superseded_docs.add(p.stem)

reqs = load_jsonl(ROOT / "eval" / "change_requests.jsonl")
gold = load_jsonl(ROOT / "eval" / "gold.jsonl")

if len(reqs) != 20: err(f"expected 20 requests, got {len(reqs)}")
if len(gold) != 20: err(f"expected 20 gold rows, got {len(gold)}")
cats = Counter(r.get("category") for r in reqs)
if dict(cats) != EXPECTED_CATS: err(f"category counts {dict(cats)} != {EXPECTED_CATS}")
for r in reqs:
    for k in ("id", "category", "request_text", "part", "change_type"):
        if not r.get(k): err(f"request {r.get('id')}: missing {k}")
rid = [r["id"] for r in reqs]; gid = [g["id"] for g in gold]
if len(set(rid)) != len(rid): err("duplicate request ids")
if rid != gid: err("request ids and gold ids differ or are in a different order")
cat_of = {r["id"]: r.get("category") for r in reqs}

req_text = {r.get("id"): r.get("request_text", "") for r in reqs}
WORD = re.compile(r"[A-Za-z0-9]+(?:[-/.,][A-Za-z0-9]+)*")
def tokens(text):
    """Digit-bearing tokens; trailing digit-free segments are dropped ('6xxx-group' -> '6xxx')."""
    out = set()
    for w in WORD.findall(text):
        if not re.search(r"\d", w): continue
        parts = re.split(r"([-/.,])", w)
        while len(parts) > 1 and not re.search(r"\d", parts[-1]): parts = parts[:-2]
        out.add("".join(parts))
    return out
def norm(x): return re.sub(r"\s+", " ", x).lower()

def check_claim_tokens(where, b, rtext):
    """Distinctive tokens (anything containing a digit: numbers, alloys, doc/part ids) of the claim
    must appear in one of the item's quotes or in the request text."""
    hay = norm(" ".join([e.get("quote") or "" for e in b.get("evidence", [])]
                        + [e.get("doc_id") or "" for e in b.get("evidence", [])] + [rtext]))
    hay += " " + " ".join(f"to{n}" for n in re.findall(r"plant (\d)", hay))  # TO1 == Plant 1
    for tok in sorted(tokens(b.get("claim", ""))):
        t = tok.rstrip(".,-/")
        if t and norm(t) not in hay:
            err(f"{where}: claim token {t!r} not found in any of its quotes or the request text")

def content_words(text): return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOPWORDS}
def check_claim_words(where, b, rtext):
    """(d) a claim must share >= 2 content words (len >= 4, not stopwords) with its quotes, the request or
    its named owner (question items)."""
    hay = content_words(" ".join([e.get("quote") or "" for e in b.get("evidence", [])] + [rtext, b.get("owner") or ""]))
    shared = content_words(b.get("claim", "")) & hay
    if len(shared) < 2: err(f"{where}: vacuous claim, shares {len(shared)} content word(s) with its quotes/request (need >= 2)")

nquotes = 0
def check_quote(where, e):
    global nquotes
    d, q = e.get("doc_id"), e.get("quote")
    if d not in docs: err(f"{where}: doc_id {d!r} does not exist in sources"); return
    if isinstance(q, str) and 0 < len(q) < MIN_QUOTE: err(f"{where}: quote shorter than {MIN_QUOTE} chars: {q!r}"); return
    if not q or q not in docs[d]: err(f"{where}: quote not a literal substring of {d}: {q!r}"); return
    nquotes += 1

def check_gold_rows(rows, cat_of, req_text):
    for g in rows:
        i = g["id"]
        if g.get("expected_verdict") not in VERDICTS: err(f"{i}: bad verdict {g.get('expected_verdict')!r}")
        bl = g.get("expected_blockers", [])
        kinds = [b.get("kind") for b in bl]
        for n, b in enumerate(bl):
            w = f"{i} blocker[{n}]"
            if b.get("kind") not in KINDS: err(f"{w}: bad kind {b.get('kind')!r}")
            for k in ("claim", "rule"):
                if not b.get(k): err(f"{w}: missing {k}")
            if b.get("rule") and b["rule"] not in allowed_rules: err(f"{w}: rule {b['rule']!r} not in allowed set (ontology README + RULES.md)")
            if not b.get("evidence"): err(f"{w}: no evidence")
            for e in b.get("evidence", []):
                if e.get("doc_id") in superseded_docs: err(f"{w}: positive evidence from SUPERSEDED doc {e.get('doc_id')}")
            check_claim_tokens(w, b, req_text.get(i, ""))
            check_claim_words(w, b, req_text.get(i, ""))
            if b.get("kind") == "question" and not b.get("owner"): err(f"{w}: question without owner")
            for e in b.get("evidence", []): check_quote(w, e)
        for n, e in enumerate(g.get("must_not_cite", [])): check_quote(f"{i} must_not_cite[{n}]", e)
        for n, c in enumerate(g.get("cleared", [])):
            if not c.get("rule"): err(f"{i} cleared[{n}]: missing rule")
            elif c["rule"] not in allowed_rules: err(f"{i} cleared[{n}]: rule {c['rule']!r} not in allowed set")
            if not c.get("evidence"): err(f"{i} cleared[{n}]: cleared item without evidence")
            if not c.get("claim"): err(f"{i} cleared[{n}]: missing claim")
            else:
                check_claim_words(f"{i} cleared[{n}]", c, req_text.get(i, ""))
            for e in c.get("evidence", []):
                check_quote(f"{i} cleared[{n}]", e)
                if e.get("doc_id") in superseded_docs: err(f"{i} cleared[{n}]: evidence from SUPERSEDED doc {e.get('doc_id')}")
        # verdict consistency
        v = g.get("expected_verdict")
        has_b = any(k in ("blocker", "inferred") for k in kinds)
        if v == "blockers_found" and not has_b: err(f"{i}: blockers_found without blocker/inferred")
        if v == "no_blockers_found" and bl: err(f"{i}: no_blockers_found but blockers listed")
        if v == "needs_info" and (has_b or "question" not in kinds): err(f"{i}: needs_info must have only question items")
        if cat_of.get(i) == "clean_control" and v != "no_blockers_found": err(f"{i}: clean control must be no_blockers_found")
        if cat_of.get(i) == "missing_data" and v != "needs_info": err(f"{i}: missing_data must be needs_info")
        if cat_of.get(i) == "inference_only" and (not has_b or any(k == "blocker" for k in kinds)):
            err(f"{i}: inference_only must contain only 'inferred' blockers")
        if cat_of.get(i) == "direct_conflict" and "blocker" not in kinds: err(f"{i}: direct_conflict needs a direct blocker")
        if cat_of.get(i) == "inference_only" and not any(
                b.get("kind") == "inferred" and len({e.get("doc_id") for e in b.get("evidence", [])}) >= 2 for b in bl):
            err(f"{i}: inference_only needs an inferred item citing >= 2 distinct doc_ids")
        if cat_of.get(i) == "stale_rule_trap" and not g.get("must_not_cite"):
            err(f"{i}: stale_rule_trap needs non-empty must_not_cite")
        # a must_not_cite quote must never also be used as positive evidence
        bad = {(e["doc_id"], e["quote"]) for e in g.get("must_not_cite", [])}
        for b in bl:
            for e in b.get("evidence", []):
                if (e.get("doc_id"), e.get("quote")) in bad: err(f"{i}: quote both cited and must_not_cite")

check_gold_rows(gold, cat_of, req_text)

# dev set: 4 tuning rows (request + gold in one object), must not overlap the frozen 20
DEV_CATS = {"direct_conflict": 1, "inference_only": 1, "clean_control": 1, "missing_data": 1}
DEV_FIELDS = ("id", "category", "request_text", "part", "supplier", "change_type")
dev = load_jsonl(ROOT / "eval" / "dev.jsonl")
if len(dev) != 4: err(f"dev: expected 4 rows, got {len(dev)}")
if dict(Counter(d.get("category") for d in dev)) != DEV_CATS: err(f"dev: category counts {dict(Counter(d.get('category') for d in dev))} != {DEV_CATS}")
dev_ids = [d.get("id") for d in dev]
if len(set(dev_ids)) != len(dev_ids): err("dev: duplicate ids")
for d in dev:
    if not re.fullmatch(r"DEV-\d\d", str(d.get("id"))): err(f"dev {d.get('id')}: id must look like DEV-NN")
    for k in DEV_FIELDS:
        if not d.get(k): err(f"dev {d.get('id')}: missing {k}")
    if d.get("supplier") and d["supplier"] not in d.get("request_text", ""): err(f"dev {d.get('id')}: supplier {d['supplier']!r} not named in request_text")
frozen_triples = {}
for r in reqs:
    for s in (s for s in SUPPLIER_NAMES if s in r.get("request_text", "")):
        frozen_triples[(r.get("part"), s, r.get("change_type"))] = r["id"]
frozen_text = {norm(r.get("request_text", "")).strip(): r["id"] for r in reqs}
for d in dev:
    if norm(d.get("request_text", "")).strip() in frozen_text:
        err(f"dev overlap: {d.get('id')} request_text identical to frozen {frozen_text[norm(d['request_text']).strip()]}")
    k = (d.get("part"), d.get("supplier"), d.get("change_type"))
    if k in frozen_triples: err(f"dev overlap: {d.get('id')} (part, supplier, change_type) {k} equals frozen {frozen_triples[k]}")
check_gold_rows(dev, {d.get("id"): d.get("category") for d in dev}, {d.get("id"): d.get("request_text", "") for d in dev})

# declarative source invariants + canonical expected items
inv = load_json(ROOT / "eval" / "invariants.json")
ninv = 0
for doc, spec in inv.items():
    if doc.startswith("_"): continue
    if doc not in docs: err(f"invariants: doc {doc} not in sources"); continue
    t = docs[doc]
    # (a) pinned header lines, parsed from the header block only (before the first '## ' section)
    head = dict(re.findall(r"^(\w+): (.+)$", t.split("\n## ")[0], re.M))
    pin = spec.get("header", {})
    for k in ("doc_id", "revision", "status", "effective_date"):
        ninv += 1
        if k not in pin: err(f"invariant {doc}: header pin for {k} missing from invariants.json")
        elif head.get(k) != pin[k]: err(f"invariant {doc}: header {k} is {head.get(k)!r}, pinned {pin[k]!r}")
    for pat in spec.get("must_contain", []):
        ninv += 1
        if not re.search(pat, t, re.M): err(f"invariant {doc}: must_contain {pat!r} missing")
    for pat in spec.get("must_not_match", []):
        ninv += 1
        if re.search(pat, t, re.M): err(f"invariant {doc}: must_not_match {pat!r} matched")
    for ex in spec.get("exactly", []):
        ninv += 1
        n = len(re.findall(ex["pattern"], t, re.M))
        if n != ex["count"]: err(f"invariant {doc}: pattern {ex['pattern']!r} matched {n}x, expected {ex['count']}")
for d in docs:
    if d not in inv: err(f"invariants: no invariants for source {d}")

# (b) date / authority logic between document pairs
def hdr_of(d): return dict(re.findall(r"^(\w+): (.+)$", docs[d].split("\n## ")[0], re.M))
def day(d):
    try: return datetime.date.fromisoformat(hdr_of(d).get("effective_date", ""))
    except ValueError: return None
WEAK = re.compile(r"SUPERSEDED|SENT|DRAFT|WITHDRAWN")
STRONG = re.compile(r"(CONTROLLED|RELEASED), EFFECTIVE$")
pairs = inv.get("_pairs", [])
if not pairs: err("invariants: _pairs missing or empty")
for pr in pairs:
    ninv += 1
    if pr.get("kind") == "older_than":
        a, b = pr.get("older"), pr.get("newer")
        if a not in docs or b not in docs: err(f"pair {a} < {b}: doc missing"); continue
        da, db = day(a), day(b)
        if da is None or db is None: err(f"pair {a} < {b}: unparseable effective_date")
        elif not da < db: err(f"pair date logic: {a} ({da}) must be older than {b} ({db})")
    elif pr.get("kind") == "lower_authority":
        w, c = pr.get("weak"), pr.get("controlled")
        if w not in docs or c not in docs: err(f"pair {w} / {c}: doc missing"); continue
        if not WEAK.match(hdr_of(w).get("status", "")): err(f"pair authority: {w} status {hdr_of(w).get('status')!r} must be superseded/informal")
        if not STRONG.search(hdr_of(c).get("status", "")): err(f"pair authority: {c} status {hdr_of(c).get('status')!r} must be controlled/released and effective")
    else: err(f"invariants: unknown pair kind {pr.get('kind')!r}")
canon = load_json(ROOT / "eval" / "canonical.json")
grow = {g.get("id"): g for g in gold}
rrow = {r.get("id"): r for r in reqs}
if not canon: err("canonical.json empty or missing")
if set(canon) != set(grow): err(f"canonical: ids {sorted(set(canon) ^ set(grow))} differ from gold rows (every row must be pinned)")
for cid, spec in canon.items():
    g = grow.get(cid)
    if g is None: err(f"canonical {cid}: no gold row"); continue
    if g.get("expected_verdict") != spec.get("verdict"): err(f"canonical {cid}: verdict {g.get('expected_verdict')!r} != {spec.get('verdict')!r}")
    r = rrow.get(cid, {})
    for k in ("part", "change_type"):
        if r.get(k) != spec.get(k): err(f"canonical {cid}: request {k} {r.get(k)!r} != {spec.get(k)!r}")
    for pat in spec.get("request_must_contain", []):
        if not re.search(pat, r.get("request_text", "")): err(f"canonical {cid}: request_text must contain {pat!r}")
    if not spec.get("request_must_contain"): err(f"canonical {cid}: no request_must_contain patterns")
    def multiset_diff(label, want, have):
        cw, ch = Counter(want), Counter(have)
        for k in sorted((cw - ch).elements(), key=str): err(f"canonical {cid}: {label} {k} missing from gold")
        for k in sorted((ch - cw).elements(), key=str): err(f"canonical {cid}: unexpected {label} {k} in gold")
    key = lambda kind, rule, docs_, n: (kind, rule, tuple(sorted(docs_)), n)
    multiset_diff("expected item (kind, rule, evidence docs, n quotes)",
                  [key(i_["kind"], i_["rule"], i_["docs"], i_.get("n_quotes")) for i_ in spec.get("items", [])],
                  [key(b.get("kind"), b.get("rule"), {e.get("doc_id") for e in b.get("evidence", [])}, len(b.get("evidence", []))) for b in g.get("expected_blockers", [])])
    multiset_diff("cleared rule", spec.get("cleared_rules", []), [c.get("rule") for c in g.get("cleared", [])])
    multiset_diff("must_not_cite quote", [(m["doc_id"], m["quote"]) for m in spec.get("must_not_cite", [])],
                  [(m.get("doc_id"), m.get("quote")) for m in g.get("must_not_cite", [])])

def manifest():
    files = [ROOT / "README.md"] + [p for d in ("sources", "eval") for p in sorted((ROOT / d).rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
lock_msg = "lock: SKIPPED (--no-lock)"
if not NO_LOCK:
    cur = manifest()
    try: locked = json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e: locked = None; lock_err = f"MANIFEST.lock unreadable ({e}); run --relock after review"
    if RELOCK:
        if errors: print("RELOCK REFUSED: semantic checks failed, lock not written")
        else:
            old = locked or {}
            for f in sorted(set(cur) | set(old)):
                tag = "added" if f not in old else "removed" if f not in cur else "changed" if old[f] != cur[f] else None
                if tag: print(f"relock diff: {tag} {f}")
            LOCK.write_text(json.dumps(cur, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(f"relock: wrote MANIFEST.lock ({len(cur)} files). Review the diff in the commit.")
            lock_msg = f"lock: rewritten ({len(cur)} files)"
    elif locked is None: err(lock_err)
    else:
        for f in sorted(set(cur) | set(locked)):
            if f not in locked: err(f"lock: file {f} is not listed in MANIFEST.lock (extra file)")
            elif f not in cur: err(f"lock: file {f} listed in MANIFEST.lock is missing")
            elif cur[f] != locked[f]: err(f"lock: sha256 mismatch for {f}")
        lock_msg = f"lock: {len(cur)} files hashed"
print(lock_msg)
print(f"sources: {len(docs)} | requests: {len(reqs)} | gold: {len(gold)} | categories: {dict(cats)}")
print(f"dev rows: {len(dev)}")
print(f"verdicts: {dict(Counter(g.get('expected_verdict') for g in gold))} | quotes verified: {nquotes} | invariants checked: {ninv}")
if errors:
    print(f"FAIL: {len(errors)} error(s)")
    for e in errors: print("  - " + e)
    sys.exit(1)
print("OK: all checks passed")
