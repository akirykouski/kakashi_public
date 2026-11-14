"""Memory of decisions and maintenance: two card keys computed from facts only (issue #19).

    past_decisions  earlier decisions on the same part / supplier / change, each reason re-checked against the
                    snapshot: "still holds" | "superseded" (by X on date) | "no longer in force" | "changed".
    maintenance     what needs a person's attention at as_of (as known at known_at):
                      promise_overdue / promise_pending  a PLAN (Commitment) with a horizon and no closing record
                      deviation_expiring / deviation_expired  a deviation ending within 60 days, or ended and
                                                         its blocker back (re-run through rules.check)
                      decision_review                    a decision whose reason record changed or was superseded
                      decided_before_known               a record valid before a decision but recorded after it
                      contradiction                      two current records of the same rank give two values

Deterministic: the same fact log, as_of and known_at give the same items. Every item carries evidence with a
source id and a verbatim quote (a fact's quote, or a line of the source text that contains the date). Called
from check.evaluate after the rules and the decision; it never changes findings, the verdict or the table.
Written 14 Nov 2026 (workstream: maintenance).
"""
from datetime import date

try:
    from . import oida, rules
    from .project import functional_predicates
    from .snapshot import recorded_by, snapshot, valid_on
except ImportError:  # core/ on sys.path
    import oida
    import rules
    from project import functional_predicates
    from snapshot import recorded_by, snapshot, valid_on

WINDOW_DAYS = 60                      # a deviation ending within this many days is flagged; also how long
                                      # an expired deviation stays on the strip
SEVERITY_ORDER = {"blocker": 0, "question": 1, "warning": 2, "info": 3}
# Records that come in families: a new sibling (same class, same key value) can break a reason that relied on
# the absence of something (e.g. "no 6082-T6 capability").
SIBLING_KEY = {"SupplierCapability": "capableSupplier", "SupplierQualification": "qualifiedSupplier",
               "MaterialCertificate": "certSupplier"}
# Same part and proposed supplier first; the supplier being replaced counts less.
MATCH_WEIGHT = {"part": 2, "to_supplier": 2, "at_supplier": 2, "from_supplier": 1}
HOLDS, SUPERSEDED, GONE, CHANGED = "still holds", "superseded", "no longer in force", "changed"


def days_between(start, end):
    return (date.fromisoformat(end[:10]) - date.fromisoformat(start[:10])).days


def evidence_of(fact):
    return {"source": fact["source"], "quote": fact["quote"], "fact_id": fact["id"]}


def line_with(source, needle):
    """First line of a source text that contains `needle`, verbatim; None if there is none."""
    text = (rules.corpus().get(source) or {}).get("text") or ""
    for line in text.splitlines():
        if needle in line:
            return line.strip()
    return None


def quoted_leaves(steps):
    for step in steps or []:
        if step.get("quote") and step.get("source"):
            yield step
        yield from quoted_leaves(step.get("premises"))


def first_quoted(finding):
    """The proof leaf with a verbatim quote that best stands for a finding: one from a source the title names,
    else the first, depth first."""
    leaves = list(quoted_leaves(finding["evidence"]))
    named = [step for step in leaves if step["source"] in finding["title"]]
    return (named or leaves or [None])[0]


class Memory:
    """Read-only view over the fact log as known at projection.known_at."""

    def __init__(self, projection):
        self.projection = projection
        self.as_of = projection.as_of
        self.known_at = projection.known_at
        facts = projection.current_facts + projection.history_facts
        self.known = sorted((fact for fact in facts if recorded_by(fact, self.known_at)), key=lambda f: f["id"])
        self.by_subject = {}
        for fact in self.known:
            self.by_subject.setdefault(fact["s"], []).append(fact)
        self.now = projection.snapshot
        self._then = {}

    # ---- helpers --------------------------------------------------------------------------------------------

    def first(self, subject, predicate, facts=None):
        for fact in facts if facts is not None else self.by_subject.get(subject, ()):
            if fact["s"] == subject and fact["p"] == predicate:
                return fact
        return None

    def literal(self, fact):
        value = fact["o"]
        return value[1:-1] if value.startswith('"') else value

    def then(self, day):
        """What was in force on `day`, as recorded by that day (what the decider could know)."""
        if day not in self._then:
            known_at = min(day, self.known_at) if self.known_at else day
            self._then[day] = snapshot(self.known, day, known_at, functional_predicates())
        return self._then[day]

    def in_force(self, snap, subject):
        return [fact for fact in snap["facts"] if fact["s"] == subject]

    def decision_date(self, decision):
        fact = self.first(decision, "type")
        return fact["valid_from"] if fact else None

    # ---- reasons ------------------------------------------------------------------------------------------

    def recheck(self, record, day):
        """State today of a record a decision relied on, with the fact that shows it."""
        now_facts = self.in_force(self.now, record)
        then_snapshot = self.then(day)
        then_facts = self.in_force(then_snapshot, record)
        if record in self.now["replaced"]:
            by = sorted((fact for fact in self.projection.current_facts
                         if fact["p"] == "supersedes" and fact["o"] == record), key=lambda f: f["id"])
            if by:
                fact = by[0]
                return {"record": record, "state": SUPERSEDED, "by": fact["s"], "on": fact["valid_from"],
                        "recorded_at": fact.get("recorded_at"),
                        "detail": f"superseded by {fact['s']} on {fact['valid_from']}", **evidence_of(fact)}
        if not now_facts:
            last = self.first(record, "type")
            detail = f"no longer in force (valid to {last['valid_to']})" if last and last.get("valid_to") \
                else "no longer in force"
            return {"record": record, "state": GONE, "detail": detail, **(evidence_of(last) if last else {})}
        functional = functional_predicates()
        before = {fact["p"]: fact for fact in then_facts if fact["p"] in functional}
        for fact in now_facts:
            old = before.get(fact["p"])
            if fact["p"] in functional and old and old["o"] != fact["o"]:
                return {"record": record, "state": CHANGED,
                        "detail": f"{fact['p']} was {self.literal(old)}, now {self.literal(fact)}",
                        **evidence_of(fact)}
        sibling = self.new_sibling(record, now_facts, then_snapshot)
        if sibling:
            return {"record": record, "state": CHANGED, "detail": f"new record {sibling['s']} since the decision",
                    **evidence_of(sibling)}
        anchor = next((fact for fact in now_facts if fact["p"] == "status"), None) or \
            next((fact for fact in now_facts if fact["p"] not in ("type", "label")), now_facts[0])
        return {"record": record, "state": HOLDS, "detail": "still holds", **evidence_of(anchor)}

    def new_sibling(self, record, now_facts, then_snapshot):
        then_records = {fact["s"] for fact in then_snapshot["facts"]}
        for class_name in [fact["o"] for fact in now_facts if fact["p"] == "type"]:
            key = SIBLING_KEY.get(class_name)
            key_fact = self.first(record, key, now_facts) if key else None
            if not key_fact:
                continue
            for fact in self.projection.current_facts:
                if fact["p"] == key and fact["o"] == key_fact["o"] and fact["s"] not in then_records \
                        and self.projection.is_a(fact["s"], class_name):
                    return fact
        return None

    def decision(self, decision_id, matched=()):
        day = self.decision_date(decision_id)
        type_fact = self.first(decision_id, "type")
        by = self.first(decision_id, "decidedBy")
        reason = self.first(decision_id, "reason")
        links = sorted({fact["o"] for fact in self.by_subject.get(decision_id, ()) if fact["p"] == "reasonRef"
                        and valid_on(fact, self.as_of)})
        reasons = [self.recheck(record, day) for record in links]
        stale = [item for item in reasons if item["state"] != HOLDS]
        return {
            "id": decision_id, "date": day, "by": by["o"] if by else None,
            "meeting": type_fact["source"] if type_fact else None,
            "title": type_fact["quote"] if type_fact else decision_id,
            "reason": self.literal(reason) if reason else None,
            "about": self.projection.objects(decision_id, "about"), "matched": sorted(matched),
            "reasons": reasons,
            "status": "review" if stale else ("stands" if reasons else "reasons not linked"),
            "epistemic": "DECISION", **(evidence_of(type_fact) if type_fact else {}),
        }

    # ---- card keys ----------------------------------------------------------------------------------------

    def past_decisions(self, request):
        entities = {request.get(key) for key in ("part", "to_supplier", "from_supplier", "at_supplier")} - {None}
        out = []
        for decision_id in self.projection.instances("Decision"):
            day = self.decision_date(decision_id)
            if not day or day > self.as_of:
                continue
            matched = entities & set(self.projection.objects(decision_id, "about"))
            if matched:
                entry = self.decision(decision_id, matched)
                entry["match_score"] = sum(MATCH_WEIGHT.get(key, 1) for key in ("part", "to_supplier", "from_supplier",
                                                                               "at_supplier")
                                           if request.get(key) in matched)
                out.append(entry)
        out.sort(key=lambda item: item["date"] or "", reverse=True)    # newest first ...
        out.sort(key=lambda item: -item["match_score"])                 # ... inside the best match (stable)
        return out

    def maintenance(self, request, findings):
        items = []
        items += self.promises(findings)
        items += self.deviations()
        items += self.decisions_to_review()
        items += self.contradictions()
        scope = {request.get(key) for key in ("part", "to_supplier", "from_supplier", "at_supplier")} - {None}
        for item in items:
            item["related"] = bool(scope & set(item.get("entities") or []))
        items.sort(key=lambda item: (not item["related"], SEVERITY_ORDER.get(item["severity"], 9),
                                     -(item.get("urgency") or 0), item["id"]))
        return items

    def item(self, kind, record, severity, title, evidence, entities, owner=None, **extra):
        return {"id": f"{kind}:{record}", "kind": kind, "record": record, "severity": severity, "title": title,
                "owner": owner, "entities": sorted(set(entities)), "evidence": evidence, **extra}

    def urgency(self, entities, age, findings):
        blocking = sum(1 for finding in findings if finding.get("severity") == "blocker"
                       and set(finding.get("entities") or []) & set(entities))
        stakes = oida.stakes(self.projection, {"entities": list(entities), "evidence": []}, {})
        return oida.urgency(max(age, 0), blocking, stakes), blocking

    def promises(self, findings):
        out = []
        for promise in self.projection.instances("Commitment"):
            horizon_fact = self.first(promise, "horizon")
            if not horizon_fact:
                continue
            horizon = self.literal(horizon_fact)
            by = self.projection.value(promise, "promisedBy")
            owner = self.projection.value(promise, "followedUpBy")
            claim = self.first(promise, "type")
            target = self.projection.value(promise, "promisesClosureOf")
            material = self.projection.value(promise, "promisesCapability")
            closing = self.closing_record(by, target, material)
            entities = [item for item in (promise, by, target, material) if item]
            evidence = [evidence_of(claim), evidence_of(horizon_fact)]
            what = f"close {target}" if target else f"be capable for {self.projection.label(material)}"
            if closing:
                continue                                    # kept: the closing record is in force
            days = days_between(horizon, self.as_of)
            if days > 0:
                urgency, blocking = self.urgency(entities, days, findings)
                out.append(self.item(
                    "promise_overdue", promise, "question",
                    f"{self.projection.label(by)} promised to {what} by {horizon}; {days} days past the horizon "
                    f"and no record shows it: ask {self.projection.label(owner) if owner else 'the owner'}",
                    evidence, entities, owner, horizon=horizon, days_overdue=days, urgency=urgency,
                    blocking_edges=blocking, epistemic="QUESTION"))
            else:
                out.append(self.item(
                    "promise_pending", promise, "info",
                    f"{self.projection.label(by)} promised to {what} by {horizon} (in {-days} days): a plan, "
                    f"not a fact; the current findings stay until a record shows it",
                    evidence, entities, owner, horizon=horizon, due_in_days=-days, epistemic="PLAN"))
        return out

    def closing_record(self, supplier, target, material):
        if target:
            status = self.projection.facts_for(target, "status")
            if status and self.literal(status[0]) == "closed":
                return status[0]
            return None
        if material:
            for record in self.projection.instances("SupplierCapability"):
                if self.projection.value(record, "capableSupplier") == supplier and \
                        self.projection.value(record, "capableMaterial") == material:
                    return self.projection.facts_for(record, "capableMaterial")[0]
        return None

    def deviation_window(self, deviation):
        type_fact = self.first(deviation, "type")
        if not type_fact or not type_fact.get("valid_to"):
            return None, None
        end = type_fact["valid_to"]
        line = line_with(type_fact["source"], end)
        evidence = {"source": type_fact["source"], "quote": line or type_fact["quote"], "fact_id": type_fact["id"]}
        return end, evidence

    def deviations(self):
        out = []
        current = set(self.projection.instances("Deviation"))
        candidates = sorted({fact["s"] for fact in self.known if fact["p"] == "type" and fact["o"] == "Deviation"})
        for deviation in candidates:
            end, evidence = self.deviation_window(deviation)
            if not end:
                continue
            facts = self.by_subject.get(deviation, [])
            status = self.first(deviation, "status")
            if status and self.literal(status) not in ("valid",):
                continue                                    # rejected / already expired on paper
            parts = sorted({fact["o"] for fact in facts if fact["p"] == "concernsPart"})
            suppliers = sorted({fact["o"] for fact in facts if fact["p"] == "concernsSupplier"})
            owner = (self.first(deviation, "type") or {}).get("author")
            days = days_between(self.as_of, end)
            if deviation in current and 0 <= days <= WINDOW_DAYS:
                out.append(self.item("deviation_expiring", deviation, "warning",
                                     f"{deviation} expires in {days} days ({end})", [evidence],
                                     [deviation, *parts, *suppliers], owner, expires=end, days_left=days))
            elif deviation not in current and days < 0 and -days <= WINDOW_DAYS:
                blockers = self.blockers_back(facts)
                title = f"{deviation} expired {-days} days ago ({end})"
                if blockers:
                    title += ": its blocker is back: " + "; ".join(finding["title"] for finding in blockers)
                back = [step for step in (first_quoted(finding) for finding in blockers) if step]
                out.append(self.item("deviation_expired", deviation, "blocker" if blockers else "warning", title,
                                     [evidence] + [{"source": step["source"], "quote": step["quote"],
                                                    "fact_id": step.get("fact_id")} for step in back],
                                     [deviation, *parts, *suppliers], owner, expired=end,
                                     blockers_back=[finding["rule"] for finding in blockers]))
        return out

    def blockers_back(self, facts):
        """Re-run the rules on the change the expired deviation used to permit."""
        values = {}
        for fact in facts:
            values.setdefault(fact["p"], fact["o"])
        if not values.get("permitsChangeType") or not values.get("concernsPart"):
            return []
        change = {"type": values["permitsChangeType"], "part": values["concernsPart"],
                  "to_supplier": values.get("concernsSupplier"), "new_coating": values.get("permitsCoating"),
                  "as_of": self.as_of}
        change = {key: value for key, value in change.items() if value}
        return [finding for finding in rules.check(self.projection, change) if finding["severity"] == "blocker"]

    def decisions_to_review(self):
        out = []
        for decision_id in self.projection.instances("Decision"):
            day = self.decision_date(decision_id)
            if not day or day > self.as_of:
                continue
            entry = self.decision(decision_id)
            for reason in entry["reasons"]:
                if reason["state"] == HOLDS:
                    continue
                evidence = [{"source": entry["source"], "quote": entry["quote"], "fact_id": entry["fact_id"]},
                            {key: reason.get(key) for key in ("source", "quote", "fact_id")}]
                entities = [decision_id, reason["record"], *entry["about"]]
                out.append(self.item("decision_review", f"{decision_id}/{reason['record']}", "question",
                                     f"Review {decision_id} ({day}): its reason {reason['record']} is "
                                     f"{reason['detail']}", evidence, entities, entry["by"], decision=decision_id))
                recorded = (reason.get("recorded_at") or "")[:10]
                if reason["state"] == SUPERSEDED and reason.get("on") and reason["on"] <= day < recorded:
                    out.append(self.item(
                        "decided_before_known", f"{decision_id}/{reason['by']}", "info",
                        f"{decision_id} was decided on {day} before we knew {reason['by']}: valid from "
                        f"{reason['on']}, recorded {recorded}. Right for what was known; review it now",
                        evidence, entities + [reason["by"]], entry["by"], decision=decision_id))
        return out

    def contradictions(self):
        """Two current records of the same rank give two values for one single-valued key."""
        functional = functional_predicates()
        replaced = set(self.now["replaced"])
        already = {tuple(item["key"]) for item in self.projection.contested}   # R7 questions already (#28)
        owner_fact = (self.projection.facts_for("Q-contradiction", "questionOwner") or [None])[0]  # QP-15 5.1
        groups = {}
        for fact in self.known:
            if fact["p"] not in functional or not valid_on(fact, self.as_of) or fact["s"] in replaced \
                    or fact["source"] in replaced:
                continue
            if (fact["s"], fact["p"]) not in already:
                groups.setdefault((fact["s"], fact["p"]), []).append(fact)
        out = []
        for (subject, predicate), facts in sorted(groups.items()):
            by_rank = {}
            for fact in facts:
                by_rank.setdefault(int(fact.get("rank") or 3), []).append(fact)
            for rank, tier in sorted(by_rank.items()):
                if rank > 2 or len({fact["o"] for fact in tier}) < 2 or len({fact["source"] for fact in tier}) < 2:
                    continue
                tier = sorted(tier, key=lambda fact: (fact.get("valid_from") or "", fact["id"]))
                in_force = self.projection.value(subject, predicate)
                sides = ", ".join(f"{self.literal(fact)} ({fact['source']})" for fact in tier)
                out.append(self.item(
                    "contradiction", f"{subject}/{predicate}", "question",
                    f"{subject} {predicate}: {sides}; same rank, both current. In force now: "
                    f"{in_force if in_force is not None else 'none'} (stays until a person decides). Which is right?",
                    [evidence_of(fact) for fact in tier] + ([evidence_of(owner_fact)] if owner_fact else []),
                    [subject, *self.parts_of(subject)], owner_fact["o"] if owner_fact else None,
                    values=[self.literal(fact) for fact in tier], in_force=in_force, epistemic="QUESTION"))
                break
        return out

    def parts_of(self, subject):
        return [fact["s"] for fact in self.projection.current_facts
                if fact["p"] == "hasSpecialCharacteristic" and fact["o"] == subject]


def annotate(projection, request, findings):
    """Card keys {past_decisions, maintenance} for one check."""
    memory = Memory(projection)
    return {"past_decisions": memory.past_decisions(request), "maintenance": memory.maintenance(request, findings)}


# ---- generic readers (core/impact.py reads these: no-arg functions that list records) ------------------------

def _today_memory(as_of=None, known_at=None):
    from core import check  # lazy: core.check imports this module
    from core.project import Projection
    return Memory(Projection(check.memory(), as_of or check.DEFAULT_AS_OF, known_at=known_at))


def past_decision_records(as_of=None, known_at=None):
    """Every decision in force at as_of (default: today), each reason re-checked: for the impact report."""
    memory = _today_memory(as_of, known_at)
    return [memory.decision(decision_id) for decision_id in memory.projection.instances("Decision")
            if (memory.decision_date(decision_id) or "9999") <= memory.as_of]


def maintenance_items(as_of=None, known_at=None):
    """The whole maintenance strip at as_of (default: today), not scoped to a change request."""
    return _today_memory(as_of, known_at).maintenance({}, [])
