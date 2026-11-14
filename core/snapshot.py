"""What is in force at (valid time, record time): a pure, order-independent function of the fact set.

Ported from research/prototypes Arseniy's spike `prep/spikes/reasoning-core/core.py` (snapshot(), functional
predicates, authority rank, assert vs mention, stale mentions, contested pairs) and Maksim's prototype
`core/project.py` (transitive record-level `supersedes`). New today: a lower-rank record or fact never
supersedes a higher-rank one, and both kinds of conflict come back in one `contested` list.

A fact row (core/factlog.py) carries:
  id, s, p, o, source, quote, valid_from, valid_to, recorded_at, review,
  kind  (assert | mention), rank (1 law/customer, 2 controlled record, 3 informal), supersedes (fact id or None)

Steps
  1. visible   accepted, recorded by `known_at`, valid on `as_of` (valid_to inclusive, as in the prototype).
  2. replaced  record-level: a visible `X supersedes Y` fact removes every fact whose subject is Y, following
               chains (rev D > rev C > rev B). Fact-level: the `supersedes` column removes that fact id.
               Refused when the superseding side has a worse (higher) rank than the target, or is a mention.
  3. resolve   for a single-valued predicate (owl:FunctionalProperty in lcc.ttl), per (s, p):
               only asserts hold a value; the best rank present wins; inside it the latest valid_from wins;
               two different values at that rank and date are contested and NEITHER is in force;
               a newer lower-rank assert with another value does not win: contested, head stays;
               a mention repeating an older value is a stale mention (note), never in force.
               Other predicates: every assert is in force; mentions never are.
"""
import hashlib
import json
from collections import defaultdict

ACCEPTED = "accepted"


def _date(value):
    return value or ""


def recorded_by(fact, known_at):
    """True if the fact was recorded no later than known_at (a date or a timestamp)."""
    if not known_at:
        return True
    recorded = fact.get("recorded_at") or ""
    return recorded[:len(known_at)] <= known_at


def valid_on(fact, as_of):
    if fact.get("valid_from") and fact["valid_from"] > as_of:
        return False
    if fact.get("valid_to") and fact["valid_to"] < as_of:
        return False
    return True


def _rank(fact):
    rank = fact.get("rank")
    return 3 if rank is None else int(rank)


def _kind(fact):
    return fact.get("kind") or "assert"


def _record_rank(facts_by_subject, subject):
    ranks = [_rank(fact) for fact in facts_by_subject.get(subject, ())]
    return min(ranks) if ranks else None


def _replaced_records(visible, notes):
    """Records replaced by a visible newer record, transitively, with the rank guard."""
    by_subject = defaultdict(list)
    for fact in visible:
        by_subject[fact["s"]].append(fact)
    edges = defaultdict(set)
    for fact in sorted(visible, key=lambda item: item["id"]):
        if fact["p"] != "supersedes":
            continue
        target_rank = _record_rank(by_subject, fact["o"])
        if _kind(fact) == "mention":
            notes.append({"type": "supersession_refused", "fact": fact["id"], "target": fact["o"],
                          "reason": "a mention cannot supersede"})
            continue
        if target_rank is not None and _rank(fact) > target_rank:
            notes.append({"type": "supersession_refused", "fact": fact["id"], "target": fact["o"],
                          "reason": f"rank {_rank(fact)} cannot supersede rank {target_rank}"})
            continue
        edges[fact["s"]].add(fact["o"])
    replaced = set()
    stack = sorted(target for targets in edges.values() for target in targets)
    while stack:
        record = stack.pop()
        if record in replaced:
            continue
        replaced.add(record)
        stack.extend(sorted(edges.get(record, ())))
    return replaced


def _replaced_fact_ids(visible, notes):
    by_id = {fact["id"]: fact for fact in visible}
    replaced = set()
    for fact in sorted(visible, key=lambda item: item["id"]):
        target_id = fact.get("supersedes")
        if not target_id or target_id not in by_id:
            continue
        target = by_id[target_id]
        if _kind(fact) == "mention" or _rank(fact) > _rank(target):
            notes.append({"type": "supersession_refused", "fact": fact["id"], "target": target_id,
                          "reason": "lower rank or mention cannot supersede"})
            continue
        replaced.add(target_id)
    return replaced


def snapshot(facts, as_of, known_at=None, functional=frozenset()):
    """Facts in force on `as_of` as recorded up to `known_at`.

    facts      : iterable of fact dicts (any order; the result does not depend on it)
    functional : set of single-valued predicate local names (project.functional_predicates())
    Returns {"as_of", "known_at", "facts", "fact_ids", "replaced", "notes", "contested", "hash"}.
    """
    notes, contested = [], []
    visible = [fact for fact in facts
               if (fact.get("review") or ACCEPTED) == ACCEPTED and recorded_by(fact, known_at)
               and valid_on(fact, as_of)]
    visible.sort(key=lambda fact: fact["id"])                      # canonical order
    replaced_records = _replaced_records(visible, notes)
    replaced_ids = _replaced_fact_ids(visible, notes)
    live = [fact for fact in visible if fact["s"] not in replaced_records and fact["id"] not in replaced_ids]

    out = []
    groups = defaultdict(list)
    for fact in live:
        if fact["p"] in functional:
            groups[(fact["s"], fact["p"])].append(fact)
        elif _kind(fact) == "assert":
            out.append(fact)

    for key in sorted(groups):
        group = groups[key]
        asserts = [fact for fact in group if _kind(fact) == "assert"]
        mentions = [fact for fact in group if _kind(fact) == "mention"]
        if not asserts:
            for mention in mentions:
                notes.append({"type": "unsupported_mention", "fact": mention["id"], "key": list(key)})
            continue
        top = min(_rank(fact) for fact in asserts)
        tier = [fact for fact in asserts if _rank(fact) == top]
        latest = max(_date(fact.get("valid_from")) for fact in tier)
        heads = [fact for fact in tier if _date(fact.get("valid_from")) == latest]
        head_values = sorted({fact["o"] for fact in heads})
        if len(head_values) > 1:
            contested.append({"key": list(key), "reason": "same_rank_same_date", "head": None,
                              "facts": sorted(fact["id"] for fact in heads), "values": head_values,
                              "rank": top, "valid_from": latest or None})
            continue                                                # quarantined: neither value in force
        head = heads[0]                                             # lowest id: canonical
        out.append(head)
        older_values = {fact["o"] for fact in asserts if fact["o"] != head["o"]}
        for fact in asserts:
            if fact is head or fact["o"] == head["o"]:
                continue
            if _rank(fact) == top:
                notes.append({"type": "superseded", "fact": fact["id"], "by": head["id"], "key": list(key)})
            elif _date(fact.get("valid_from")) > _date(head.get("valid_from")):
                contested.append({"key": list(key), "reason": "lower_rank_newer", "head": head["id"],
                                  "facts": [head["id"], fact["id"]], "values": [head["o"], fact["o"]],
                                  "rank": _rank(fact), "valid_from": fact.get("valid_from")})
            else:
                notes.append({"type": "overruled", "fact": fact["id"], "by": head["id"], "key": list(key)})
        for mention in mentions:
            if mention["o"] == head["o"]:
                continue
            kind = "stale_mention" if mention["o"] in older_values else "unsupported_mention"
            notes.append({"type": kind, "fact": mention["id"], "head": head["id"], "key": list(key)})

    out.sort(key=lambda fact: fact["id"])
    fact_ids = [fact["id"] for fact in out]
    notes.sort(key=lambda note: json.dumps(note, sort_keys=True))
    contested.sort(key=lambda item: json.dumps(item, sort_keys=True))
    digest = hashlib.sha256(json.dumps({"facts": fact_ids, "contested": contested,
                                        "o": [(fact["s"], fact["p"], fact["o"]) for fact in out]},
                                       sort_keys=True).encode()).hexdigest()
    return {"as_of": as_of, "known_at": known_at, "facts": out, "fact_ids": fact_ids,
            "replaced": sorted(replaced_records), "notes": notes, "contested": contested, "hash": digest}
