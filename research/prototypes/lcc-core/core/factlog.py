"""Append-only fact log with two times (bitemporal).

valid_from / valid_to : when the fact is true in the world (valid time)
recorded_at           : when we learned it (transaction time)

Rows are never updated in place except for the review status of a proposal. A newer record replaces an
older one only through an explicit `supersedes` fact; the older one stays in the log and in history.

Agents may only *propose* facts. A person accepts or rejects them. A write that conflicts with a current
record (same supplier qualification, same part approval key) is refused unless it explicitly supersedes it.
"""
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    s TEXT NOT NULL, p TEXT NOT NULL, o TEXT NOT NULL,
    source TEXT NOT NULL, quote TEXT NOT NULL,
    valid_from TEXT, valid_to TEXT,
    kind TEXT, author TEXT,
    recorded_at TEXT NOT NULL,
    review TEXT NOT NULL DEFAULT 'accepted',   -- proposed | accepted | rejected
    proposed_by TEXT, reviewed_by TEXT
);
CREATE INDEX IF NOT EXISTS facts_s ON facts(s);
CREATE INDEX IF NOT EXISTS facts_p_o ON facts(p, o);
"""

BOOTSTRAP_RECORDED_AT = "2026-11-13T00:00:00+00:00"

# Classes with at most one current record per key. Key = tuple of predicates.
SINGLE_CURRENT = {
    "SupplierQualification": ("qualifiedSupplier",),
    "PartApproval": ("approvedSupplier", "approvedPart", "approvedSite", "approvedForCustomer"),
}


class ConflictError(Exception):
    """Raised when a write contradicts a current record and does not supersede it."""


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class FactLog:
    def __init__(self, path=":memory:"):
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    # ---- loading -------------------------------------------------------------------------------------

    def load_jsonl(self, path, recorded_at=BOOTSTRAP_RECORDED_AT):
        with open(path) as file:
            rows = [json.loads(line) for line in file]
        for row in rows:
            self._insert(row, recorded_at=recorded_at, review="accepted")
        self.connection.commit()
        return len(rows)

    def _insert(self, fact, recorded_at, review, proposed_by=None):
        self.connection.execute(
            "INSERT INTO facts (id, s, p, o, source, quote, valid_from, valid_to, kind, author, recorded_at,"
            " review, proposed_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (fact["id"], fact["s"], fact["p"], fact["o"], fact["source"], fact["quote"], fact.get("valid_from"),
             fact.get("valid_to"), fact.get("kind"), fact.get("author"), recorded_at, review, proposed_by))

    # ---- reading -------------------------------------------------------------------------------------

    def all_facts(self, review="accepted"):
        with self.lock:
            cursor = self.connection.execute("SELECT * FROM facts WHERE review = ?", (review,))
            return [dict(row) for row in cursor]

    def get(self, fact_id):
        row = self.connection.execute("SELECT * FROM facts WHERE id = ?", (fact_id,)).fetchone()
        return dict(row) if row else None

    def facts_about(self, subject):
        with self.lock:
            cursor = self.connection.execute("SELECT * FROM facts WHERE s = ? AND review = 'accepted'", (subject,))
            return [dict(row) for row in cursor]

    # ---- writing a new record (people and agents) ----------------------------------------------------

    def write_record(self, record_id, class_name, properties, source, quote, valid_from, author,
                     supersedes=None, proposed_by=None, as_of=None, current_records=None):
        """Write a new record (several facts with one subject).

        properties: dict predicate -> object (entity id or JSON literal string).
        proposed_by: set for agents. Their facts are stored as 'proposed' and do not count until accepted.
        current_records: function(as_of) -> set of current record ids, used for the conflict check.
        Returns the list of fact ids written.
        """
        key_predicates = SINGLE_CURRENT.get(class_name)
        if key_predicates and current_records is not None:
            clash = self._find_current_with_same_key(class_name, key_predicates, properties,
                                                     current_records(as_of or valid_from))
            if clash and clash != supersedes:
                raise ConflictError(
                    f"{record_id} contradicts current record {clash} ({class_name} with the same "
                    f"{', '.join(key_predicates)}). Write it again with supersedes='{clash}'.")
        review = "proposed" if proposed_by else "accepted"
        recorded_at = now_iso()
        written = []
        triples = [("type", class_name)] + list(properties.items())
        if supersedes:
            triples.append(("supersedes", supersedes))
        for index, (predicate, obj) in enumerate(triples):
            fact_id = f"{record_id}#{index}"
            self._insert({"id": fact_id, "s": record_id, "p": predicate, "o": obj, "source": source,
                          "quote": quote, "valid_from": valid_from, "valid_to": None, "kind": "decision",
                          "author": author}, recorded_at=recorded_at, review=review, proposed_by=proposed_by)
            written.append(fact_id)
        self.connection.commit()
        return written

    def propose_fact(self, fact, proposed_by):
        """An agent (e.g. the extractor) proposes one fact with its source and quote. It does not count yet."""
        with self.lock:
            self._insert(fact, recorded_at=now_iso(), review="proposed", proposed_by=proposed_by)
            self.connection.commit()

    def accept_proposed(self, source, reviewer):
        """A person accepts every proposed fact from one source at once."""
        with self.lock:
            self.connection.execute(
                "UPDATE facts SET review = 'accepted', reviewed_by = ? WHERE source = ? AND review = 'proposed'",
                (reviewer, source))
            self.connection.commit()

    def review(self, record_id, decision, reviewer):
        """A person accepts or rejects an agent's proposal."""
        if decision not in ("accepted", "rejected"):
            raise ValueError("decision must be accepted or rejected")
        self.connection.execute("UPDATE facts SET review = ?, reviewed_by = ? WHERE s = ? AND review = 'proposed'",
                                (decision, reviewer, record_id))
        self.connection.commit()

    def _find_current_with_same_key(self, class_name, key_predicates, properties, current_ids):
        wanted = tuple(properties.get(predicate) for predicate in key_predicates)
        cursor = self.connection.execute(
            "SELECT s FROM facts WHERE p = 'type' AND o = ? AND review = 'accepted'", (class_name,))
        for row in cursor:
            candidate = row["s"]
            if candidate not in current_ids:
                continue
            facts = {fact["p"]: fact["o"] for fact in self.facts_about(candidate)}
            if tuple(facts.get(predicate) for predicate in key_predicates) == wanted:
                return candidate
        return None


def default_log(data_dir=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(data_dir or os.path.join(root, "data"), "facts.jsonl")
    log = FactLog()
    log.load_jsonl(data_path)
    return log
