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
    review TEXT NOT NULL DEFAULT 'accepted',   -- proposed | accepted | rejected
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


class ConflictError(Exception):
    """Raised when a write contradicts a current record and does not supersede it."""


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
                    f"{', '.join(key_predicates)}). Write it again with supersedes='{candidate}'.")

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
                     kind="assert", context_quote=None):
        """Write a new record (several facts with one subject).

        properties : dict predicate -> object (entity id or JSON literal string).
        proposed_by: set for agents. Their facts are stored as 'proposed' and do not count until a person
                     accepts them; the conflict check then runs at acceptance.
        current_records: optional function(as_of) -> set of current record ids (prototype signature). When
                     omitted, the snapshot of the accepted log is used. Either way the check runs inside the
                     same transaction as the insert.
        Returns the list of fact ids written.
        """
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
                self._check_record(record_id, class_name, properties, {supersedes} if supersedes else set(),
                                   check_as_of, current_ids)
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
