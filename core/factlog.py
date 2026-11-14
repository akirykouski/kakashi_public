"""Append-only fact log with two times (bitemporal), in SQLite.

Ported from research/prototypes Maksim's `core/factlog.py` (night-shift/2026-11-13-kva-plan), with the
`unclassified` queue of fix/1-catchall and the `context_quote` column of fix/3-two-span-quotes. New today:
`kind` (assert | mention), `rank` (1 law/customer, 2 controlled record, 3 informal), fact-level `supersedes`,
and the conflict check at acceptance.

valid_from / valid_to : when the fact is true in the world (valid time)
recorded_at           : when we learned it (record time)

Rows are never updated in place except for the review status of a proposal. Agents only *propose*
(review = 'proposed'); a person accepts or rejects. Proposed facts are never in force.

Write safety (fixes the prototype gap, REVIEW.md section 1 "Write path"): every write that can make a fact
count (write_record by a person, accept_proposed, review) runs the conflict check and the insert or update
inside ONE transaction (`BEGIN IMMEDIATE`) while holding the log's lock. A conflict rolls the whole write back.
"""
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    s TEXT NOT NULL, p TEXT NOT NULL, o TEXT NOT NULL,
    source TEXT NOT NULL, quote TEXT NOT NULL, context_quote TEXT,
    valid_from TEXT, valid_to TEXT,
    kind TEXT NOT NULL DEFAULT 'assert',       -- assert | mention
    rank INTEGER NOT NULL DEFAULT 3,           -- 1 law/customer, 2 controlled record, 3 informal
    supersedes TEXT,                           -- fact id this fact replaces (fact-level supersession)
    epistemic TEXT, author TEXT,
    recorded_at TEXT NOT NULL,
    review TEXT NOT NULL DEFAULT 'accepted',   -- proposed | accepted | rejected | contested (#28)
    proposed_by TEXT, reviewed_by TEXT
);
-- Obligations the extractor found that fit no ontology predicate (fix/1). Never read by the projection.
CREATE TABLE IF NOT EXISTS unclassified (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL, quote TEXT NOT NULL, summary TEXT,
    recorded_at TEXT NOT NULL,
    review TEXT NOT NULL DEFAULT 'proposed',   -- proposed | dismissed | classified
    proposed_by TEXT
);
-- Typed links between records (#28). CONTRADICTS: a contested record -> the current record it contradicts.
CREATE TABLE IF NOT EXISTS links (
    s TEXT NOT NULL, kind TEXT NOT NULL, o TEXT NOT NULL,
    weight REAL, recorded_at TEXT NOT NULL,
    PRIMARY KEY (s, kind, o)
);
-- Open questions the log itself raises (#28): who decides between a contested and a current record.
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,                        -- contradiction
    contested_record TEXT NOT NULL, current_record TEXT NOT NULL, class_name TEXT,
    owner TEXT, owner_source TEXT, owner_quote TEXT,
    status TEXT NOT NULL DEFAULT 'open',       -- open | kept_current | took_contested
    recorded_at TEXT NOT NULL, decided_by TEXT, decided_at TEXT
);
CREATE INDEX IF NOT EXISTS facts_s ON facts(s);
CREATE INDEX IF NOT EXISTS facts_p_o ON facts(p, o);
CREATE INDEX IF NOT EXISTS facts_source ON facts(source);
"""

BOOTSTRAP_RECORDED_AT = "2026-11-13T00:00:00+00:00"
KINDS = ("assert", "mention")
RANKS = (1, 2, 3)

# Classes with at most one current record per key. Key = tuple of predicates.
SINGLE_CURRENT = {
    "SupplierQualification": ("qualifiedSupplier",),
    "PartApproval": ("approvedSupplier", "approvedPart", "approvedSite", "approvedForCustomer"),
}


CONTRADICTS_WEIGHT = -0.6   # OIDA edge weight (docs/research/kva-oida-hooks.md 4.3)
ON_CONFLICT = ("refuse", "contest")


class ConflictError(Exception):
    """Raised when a write contradicts a current record and does not supersede it."""

    def __init__(self, message, record=None, current=None, class_name=None):
        super().__init__(message)
        self.record, self.current, self.class_name = record, current, class_name


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today():
    return datetime.now(timezone.utc).date().isoformat()


class FactLog:
    def __init__(self, path=":memory:"):
        # isolation_level=None: we issue BEGIN / COMMIT ourselves, so check + write share one transaction.
        self.connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=30)
        self.lock = threading.RLock()
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    @contextmanager
    def _transaction(self):
        """Lock + BEGIN IMMEDIATE (takes SQLite's write lock up front, also across processes)."""
        with self.lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield self.connection
            except BaseException:
                self.connection.execute("ROLLBACK")
                raise
            else:
                self.connection.execute("COMMIT")

    # ---- loading -------------------------------------------------------------------------------------

    def load_jsonl(self, path, recorded_at=BOOTSTRAP_RECORDED_AT):
        with open(path) as file:
            rows = [json.loads(line) for line in file if line.strip()]
        with self._transaction():
            for row in rows:
                self._insert(row, recorded_at=row.get("recorded_at") or recorded_at, review="accepted")
        return len(rows)

    def _insert(self, fact, recorded_at, review, proposed_by=None):
        kind = fact.get("kind") or "assert"
        if kind not in KINDS:
            raise ValueError(f"fact {fact['id']}: kind must be assert or mention, got {kind!r}")
        rank = int(fact.get("rank") or 3)
        if rank not in RANKS:
            raise ValueError(f"fact {fact['id']}: rank must be 1, 2 or 3, got {rank!r}")
        self.connection.execute(
            "INSERT INTO facts (id, s, p, o, source, quote, context_quote, valid_from, valid_to, kind, rank,"
            " supersedes, epistemic, author, recorded_at, review, proposed_by)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (fact["id"], fact["s"], fact["p"], fact["o"], fact["source"], fact["quote"], fact.get("context_quote"),
             fact.get("valid_from"), fact.get("valid_to"), kind, rank, fact.get("supersedes"),
             fact.get("epistemic"), fact.get("author"), recorded_at, review, proposed_by))

    # ---- reading -------------------------------------------------------------------------------------

    def all_facts(self, review="accepted"):
        with self.lock:
            if review is None:
                cursor = self.connection.execute("SELECT * FROM facts ORDER BY id")
            else:
                cursor = self.connection.execute("SELECT * FROM facts WHERE review = ? ORDER BY id", (review,))
            return [dict(row) for row in cursor]

    def get(self, fact_id):
        with self.lock:
            row = self.connection.execute("SELECT * FROM facts WHERE id = ?", (fact_id,)).fetchone()
        return dict(row) if row else None

    def facts_about(self, subject, review="accepted"):
        with self.lock:
            cursor = self.connection.execute("SELECT * FROM facts WHERE s = ? AND review = ? ORDER BY id",
                                             (subject, review))
            return [dict(row) for row in cursor]

    def proposed(self, source=None):
        with self.lock:
            if source is None:
                cursor = self.connection.execute("SELECT * FROM facts WHERE review = 'proposed' ORDER BY id")
            else:
                cursor = self.connection.execute(
                    "SELECT * FROM facts WHERE review = 'proposed' AND source = ? ORDER BY id", (source,))
            return [dict(row) for row in cursor]

    # ---- conflict check (always called inside _transaction) -------------------------------------------

    def _current_record_ids(self, as_of, exclude=()):
        try:
            from .snapshot import snapshot
        except ImportError:  # run as a script from core/
            from snapshot import snapshot
        facts = [dict(row) for row in self.connection.execute("SELECT * FROM facts WHERE review = 'accepted'")]
        facts = [fact for fact in facts if fact["id"] not in exclude]
        return {fact["s"] for fact in snapshot(facts, as_of)["facts"]}

    def _record_properties(self, subject):
        cursor = self.connection.execute(
            "SELECT p, o FROM facts WHERE s = ? AND review = 'accepted'", (subject,))
        return {row["p"]: row["o"] for row in cursor}

    def _check_record(self, record_id, class_name, properties, supersedes, as_of, current_ids):
        key_predicates = SINGLE_CURRENT.get(class_name)
        if not key_predicates:
            return
        wanted = tuple(properties.get(predicate) for predicate in key_predicates)
        cursor = self.connection.execute(
            "SELECT DISTINCT s FROM facts WHERE p = 'type' AND o = ? AND review = 'accepted' AND s != ? ORDER BY s",
            (class_name, record_id))
        for row in cursor.fetchall():
            candidate = row["s"]
            if candidate not in current_ids or candidate in supersedes:
                continue
            existing = self._record_properties(candidate)
            if tuple(existing.get(predicate) for predicate in key_predicates) == wanted:
                raise ConflictError(
                    f"{record_id} contradicts current record {candidate} ({class_name} with the same "
                    f"{', '.join(key_predicates)}). Write it again with supersedes='{candidate}'.",
                    record=record_id, current=candidate, class_name=class_name)

    def _check_records_in(self, fact_rows):
        """Group facts by subject; check every record that has a SINGLE_CURRENT class."""
        by_subject = {}
        for fact in fact_rows:
            by_subject.setdefault(fact["s"], []).append(fact)
        ids = {fact["id"] for fact in fact_rows}
        for subject, facts in sorted(by_subject.items()):
            properties = {fact["p"]: fact["o"] for fact in facts if fact["p"] not in ("type", "supersedes")}
            classes = [fact["o"] for fact in facts if fact["p"] == "type"]
            if not classes:
                properties.update(self._record_properties(subject))
                classes = [properties.get("type")]
            supersedes = {fact["o"] for fact in facts if fact["p"] == "supersedes"}
            as_of = max((fact.get("valid_from") or today()) for fact in facts)
            current_ids = self._current_record_ids(as_of, exclude=ids)
            for class_name in classes:
                self._check_record(subject, class_name, properties, supersedes, as_of, current_ids)

    # ---- writing a new record (people) ---------------------------------------------------------------

    def write_record(self, record_id, class_name, properties, source, quote, valid_from, author,
                     supersedes=None, proposed_by=None, as_of=None, current_records=None, rank=2,
                     kind="assert", context_quote=None, on_conflict="refuse"):
        """Write a new record (several facts with one subject).

        properties : dict predicate -> object (entity id or JSON literal string).
        proposed_by: set for agents. Their facts are stored as 'proposed' and do not count until a person
                     accepts them; the conflict check then runs at acceptance.
        current_records: optional function(as_of) -> set of current record ids (prototype signature). When
                     omitted, the snapshot of the accepted log is used. Either way the check runs inside the
                     same transaction as the insert.
        on_conflict: "refuse" (default) raises ConflictError; "contest" (#28) stores the record as `contested`
                     (never in force), links it CONTRADICTS -> the current record, keeps the current one in force
                     and opens a QUESTION owned by the person the policy data names (see open_questions()).
                     Contest is allowed only against a current record of the same or higher authority (rank
                     number <= the write's); a more authoritative write must supersede explicitly.
        Returns the list of fact ids written.
        """
        if on_conflict not in ON_CONFLICT:
            raise ValueError(f"on_conflict must be one of {ON_CONFLICT}")
        review = "proposed" if proposed_by else "accepted"
        recorded_at = now_iso()
        triples = [("type", class_name)] + list(properties.items())
        if supersedes:
            triples.append(("supersedes", supersedes))
        with self._transaction():
            if review == "accepted":
                check_as_of = as_of or valid_from or today()
                current_ids = (set(current_records(check_as_of)) if current_records is not None
                               else self._current_record_ids(check_as_of))
                try:
                    self._check_record(record_id, class_name, properties, {supersedes} if supersedes else set(),
                                       check_as_of, current_ids)
                except ConflictError as conflict:
                    if on_conflict != "contest" or self._record_rank(conflict.current) > int(rank):
                        raise
                    review = "contested"
                    self._open_contradiction(record_id, conflict.current, class_name)
            written = []
            for index, (predicate, obj) in enumerate(triples):
                fact_id = f"{record_id}#{index}"
                self._insert({"id": fact_id, "s": record_id, "p": predicate, "o": obj, "source": source,
                              "quote": quote, "context_quote": context_quote, "valid_from": valid_from,
                              "valid_to": None, "kind": kind, "rank": rank, "epistemic": "decision",
                              "author": author}, recorded_at=recorded_at, review=review, proposed_by=proposed_by)
                written.append(fact_id)
        return written

    def propose_record(self, record_id, class_name, properties, source, quote, valid_from, author, proposed_by,
                       **options):
        """An agent proposes a whole record. Same as write_record with proposed_by set."""
        return self.write_record(record_id, class_name, properties, source, quote, valid_from, author,
                                 proposed_by=proposed_by, **options)

    def propose_fact(self, fact, proposed_by):
        """An agent (e.g. the extractor) proposes one fact with its source and quote. It does not count yet."""
        with self._transaction():
            self._insert(fact, recorded_at=fact.get("recorded_at") or now_iso(), review="proposed",
                         proposed_by=proposed_by)

    # ---- contested records (#28) -----------------------------------------------------------------------

    def _record_rank(self, subject):
        row = self.connection.execute(
            "SELECT MIN(rank) AS rank FROM facts WHERE s = ? AND review = 'accepted'", (subject,)).fetchone()
        return row["rank"] if row and row["rank"] is not None else 3

    def _question_owner(self, class_name):
        """Owner of a contradiction question, from policy data: `Q-contradiction-<Class> questionOwner`, else
        `Q-contradiction questionOwner`. Returns (owner, source, quote); (None, None, None) if no fact says."""
        for subject in (f"Q-contradiction-{class_name}", "Q-contradiction"):
            row = self.connection.execute(
                "SELECT o, source, quote FROM facts WHERE s = ? AND p = 'questionOwner' AND review = 'accepted'"
                " ORDER BY rank, id LIMIT 1", (subject,)).fetchone()
            if row:
                return row["o"], row["source"], row["quote"]
        return None, None, None

    def _open_contradiction(self, record_id, current_id, class_name):
        recorded_at = now_iso()
        self.connection.execute(
            "INSERT OR REPLACE INTO links (s, kind, o, weight, recorded_at) VALUES (?, 'CONTRADICTS', ?, ?, ?)",
            (record_id, current_id, CONTRADICTS_WEIGHT, recorded_at))
        owner, owner_source, owner_quote = self._question_owner(class_name)
        self.connection.execute(
            "INSERT OR REPLACE INTO questions (id, kind, contested_record, current_record, class_name, owner,"
            " owner_source, owner_quote, status, recorded_at) VALUES (?, 'contradiction', ?, ?, ?, ?, ?, ?, 'open', ?)",
            (f"Q-{record_id}", record_id, current_id, class_name, owner, owner_source, owner_quote, recorded_at))

    def links(self, kind=None):
        with self.lock:
            if kind is None:
                cursor = self.connection.execute("SELECT * FROM links ORDER BY s, kind, o")
            else:
                cursor = self.connection.execute("SELECT * FROM links WHERE kind = ? ORDER BY s, o", (kind,))
            return [dict(row) for row in cursor]

    def open_questions(self):
        with self.lock:
            return [dict(row) for row in self.connection.execute(
                "SELECT * FROM questions WHERE status = 'open' ORDER BY id")]

    def contested_records(self):
        """Open contradictions with both sides: [{question, contested: [facts], current: [facts]}]."""
        with self.lock:
            questions = [dict(row) for row in self.connection.execute(
                "SELECT * FROM questions WHERE status = 'open' ORDER BY id")]
            result = []
            for item in questions:
                contested = [dict(row) for row in self.connection.execute(
                    "SELECT * FROM facts WHERE s = ? AND review = 'contested' ORDER BY id", (item["contested_record"],))]
                current = [dict(row) for row in self.connection.execute(
                    "SELECT * FROM facts WHERE s = ? AND review = 'accepted' ORDER BY id", (item["current_record"],))]
                result.append({"question": item, "contested": contested, "current": current})
            return result

    def resolve_contradiction(self, question_id, decision, decided_by):
        """The question's owner decides. decision: 'keep_current' (contested facts rejected) or 'take_contested'
        (contested facts accepted with a supersedes fact to the current record)."""
        if decision not in ("keep_current", "take_contested"):
            raise ValueError("decision must be keep_current or take_contested")
        with self._transaction():
            row = self.connection.execute("SELECT * FROM questions WHERE id = ? AND status = 'open'",
                                          (question_id,)).fetchone()
            if not row:
                raise KeyError(f"no open question {question_id}")
            if row["owner"] and row["owner"] != decided_by:
                raise PermissionError(f"{question_id} is decided by {row['owner']}, not {decided_by}")
            record_id, current_id = row["contested_record"], row["current_record"]
            decided_at = now_iso()
            if decision == "keep_current":
                self.connection.execute("UPDATE facts SET review = 'rejected', reviewed_by = ? WHERE s = ? AND "
                                        "review = 'contested'", (decided_by, record_id))
                status = "kept_current"
            else:
                facts = [dict(item) for item in self.connection.execute(
                    "SELECT * FROM facts WHERE s = ? AND review = 'contested' ORDER BY id", (record_id,))]
                self.connection.execute("UPDATE facts SET review = 'accepted', reviewed_by = ?, recorded_at = ? "
                                        "WHERE s = ? AND review = 'contested'", (decided_by, decided_at, record_id))
                first = facts[0]
                self._insert({"id": f"{record_id}#supersedes", "s": record_id, "p": "supersedes", "o": current_id,
                              "source": first["source"], "quote": first["quote"], "valid_from": first["valid_from"],
                              "kind": "assert", "rank": first["rank"], "epistemic": "decision", "author": decided_by},
                             recorded_at=decided_at, review="accepted")
                status = "took_contested"
            self.connection.execute("UPDATE questions SET status = ?, decided_by = ?, decided_at = ? WHERE id = ?",
                                    (status, decided_by, decided_at, question_id))
        return status

    # ---- acceptance (people) -------------------------------------------------------------------------

    def _accept_rows(self, rows, reviewer):
        if not rows:
            return []
        self._check_records_in(rows)
        recorded_at = now_iso()
        for row in rows:
            # Record time of an accepted fact = when a person accepted it (it did not count before).
            self.connection.execute(
                "UPDATE facts SET review = 'accepted', reviewed_by = ?, recorded_at = ? WHERE id = ?",
                (reviewer, recorded_at, row["id"]))
        return [row["id"] for row in rows]

    def accept_proposed(self, source, reviewer):
        """A person accepts every proposed fact from one source at once. Raises ConflictError (nothing accepted)."""
        with self._transaction():
            rows = [dict(row) for row in self.connection.execute(
                "SELECT * FROM facts WHERE source = ? AND review = 'proposed' ORDER BY id", (source,))]
            return self._accept_rows(rows, reviewer)

    def accept_facts(self, fact_ids, reviewer):
        """A person accepts the given proposed facts. Raises ConflictError (nothing accepted)."""
        with self._transaction():
            rows = []
            for fact_id in fact_ids:
                row = self.connection.execute(
                    "SELECT * FROM facts WHERE id = ? AND review = 'proposed'", (fact_id,)).fetchone()
                if row:
                    rows.append(dict(row))
            return self._accept_rows(rows, reviewer)

    def review(self, record_id, decision, reviewer):
        """A person accepts or rejects an agent's proposed record (all its facts)."""
        if decision not in ("accepted", "rejected"):
            raise ValueError("decision must be accepted or rejected")
        with self._transaction():
            rows = [dict(row) for row in self.connection.execute(
                "SELECT * FROM facts WHERE s = ? AND review = 'proposed' ORDER BY id", (record_id,))]
            if decision == "accepted":
                return self._accept_rows(rows, reviewer)
            self.connection.execute(
                "UPDATE facts SET review = 'rejected', reviewed_by = ? WHERE s = ? AND review = 'proposed'",
                (reviewer, record_id))
            return [row["id"] for row in rows]

    # ---- unclassified queue (fix/1) ------------------------------------------------------------------

    def propose_unclassified(self, item, proposed_by):
        """An unclassified requirement (quote + summary) goes to the review queue. It never reaches the reasoner."""
        with self._transaction():
            self.connection.execute(
                "INSERT OR REPLACE INTO unclassified (id, source, quote, summary, recorded_at, review, proposed_by)"
                " VALUES (?,?,?,?,?,?,?)",
                (item["id"], item["source"], item["quote"], item.get("summary", ""),
                 item.get("recorded_at") or now_iso(), item.get("review", "proposed"), proposed_by))

    def unclassified_items(self, sources=None):
        """Open unclassified requirements, optionally only those of the given source documents."""
        with self.lock:
            rows = [dict(row) for row in self.connection.execute(
                "SELECT * FROM unclassified WHERE review = 'proposed' ORDER BY id")]
        return [row for row in rows if sources is None or row["source"] in sources]

    def close_unclassified(self, item_id, decision, reviewer=None):
        if decision not in ("dismissed", "classified"):
            raise ValueError("decision must be dismissed or classified")
        with self._transaction():
            self.connection.execute("UPDATE unclassified SET review = ? WHERE id = ?", (decision, item_id))


def default_log(data_dir=None, path=":memory:"):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(data_dir or os.path.join(root, "data"), "facts.jsonl")
    log = FactLog(path)
    log.load_jsonl(data_path)
    extra = os.path.join(os.path.dirname(data_path), "unclassified.jsonl")
    if os.path.exists(extra):
        with open(extra) as file:
            for line in file:
                if line.strip():
                    log.propose_unclassified(json.loads(line), proposed_by="extractor")
    return log
