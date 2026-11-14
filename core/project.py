"""Project the snapshot in force into an RDF graph, then compute the OWL 2 RL closure.

Ported from research/prototypes Maksim's `core/project.py` (night-shift/2026-11-13-kva-plan): the public
`Projection` API is kept as it was (constructor, query, objects, value, label, is_a, instances, and the
attributes as_of, unclassified, replaced, current_facts, history_facts, current_records, provenance, graph,
asserted_count, reasoning_ms, history_by_subject) so workstream R codes against it unchanged.

New today
  * "what is in force" comes from core/snapshot.py (supersession + single-valued resolution by rank and date);
  * the closure is cached by snapshot hash (same facts in force => same graph, computed once);
  * fact_ids_in_force, contested, notes, snapshot_hash, snapshot_ms, closure_ms for the DecisionRecord / Card;
  * values(), epistemic_type(), facts_for().

The cached graph is shared between projections with the same snapshot: treat `graph` as read-only (keep the
change request outside the graph, as the prototype rules do).
"""
import hashlib
import json
import os
import time
from collections import OrderedDict
from urllib.parse import quote, unquote

import owlrl
from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace, URIRef

try:
    from .snapshot import snapshot as take_snapshot
except ImportError:  # run as a script from core/
    from snapshot import snapshot as take_snapshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONTOLOGY_PATH = os.path.join(ROOT, "ontology", "lcc.ttl")
LCC = Namespace("https://lcc.example/ont#")
ID = Namespace("https://lcc.example/id/")
CACHE_SIZE = 64

_ontology_cache = {}
_closure_cache = OrderedDict()  # (ontology hash, snapshot hash, reason) -> (graph, provenance)


def ontology_graph():
    if "graph" not in _ontology_cache:
        graph = Graph()
        graph.parse(ONTOLOGY_PATH, format="turtle")
        _ontology_cache["graph"] = graph
        _ontology_cache["names"] = {str(term)[len(str(LCC)):] for term in graph.all_nodes()
                                    if isinstance(term, URIRef) and str(term).startswith(str(LCC))}
        _ontology_cache["functional"] = frozenset(
            str(term)[len(str(LCC)):] for term in graph.subjects(RDF.type, OWL.FunctionalProperty)
            if str(term).startswith(str(LCC)))
        with open(ONTOLOGY_PATH, "rb") as file:
            _ontology_cache["hash"] = hashlib.sha256(file.read()).hexdigest()
    return _ontology_cache["graph"]


def schema_names():
    ontology_graph()
    return _ontology_cache["names"]


def functional_predicates():
    """Single-valued predicates (owl:FunctionalProperty in lcc.ttl), resolved by core/snapshot.py."""
    ontology_graph()
    return _ontology_cache["functional"]


def ontology_hash():
    ontology_graph()
    return _ontology_cache["hash"]


def clear_cache():
    _closure_cache.clear()


def node(name):
    if name in schema_names():
        return LCC[name]
    return ID[quote(name, safe="-_.#")]


def local_name(term):
    text = str(term)
    for namespace in (str(LCC), str(ID)):
        if text.startswith(namespace):
            return unquote(text[len(namespace):])
    return text


def triple_for(fact):
    subject = node(fact["s"])
    if fact["p"] == "type":
        return subject, RDF.type, LCC[fact["o"]]
    if fact["p"] == "label":
        return subject, RDFS.label, Literal(json.loads(fact["o"]))
    predicate = LCC[fact["p"]]
    if fact["o"].startswith('"'):
        return subject, predicate, Literal(json.loads(fact["o"]))
    return subject, predicate, node(fact["o"])


def is_valid(fact, as_of, known_at):
    """Prototype helper, kept for callers. The snapshot applies the same test."""
    if fact["valid_from"] and fact["valid_from"] > as_of:
        return False
    if fact["valid_to"] and fact["valid_to"] < as_of:
        return False
    if known_at and fact["recorded_at"][:len(known_at)] > known_at:
        return False
    return True


def _build_graph(facts, reason):
    provenance = {}
    graph = Graph()
    for triple in ontology_graph():
        graph.add(triple)
    for fact in facts:
        triple = triple_for(fact)
        graph.add(triple)
        provenance.setdefault(triple, []).append(fact)
    if reason:
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False,
                               datatype_axioms=False).expand(graph)
    return graph, provenance


# ---- request-scoped reasoning ----------------------------------------------------------------------------
# A check reads a bounded neighbourhood of the change's entities. Instead of closing the whole snapshot, a scoped
# projection closes only that neighbourhood (plus the ontology). The neighbourhood, on the entity graph of the facts
# in force (edges = facts whose object is an entity; type, label and literals are not edges):
#   F  = forward closure (every outgoing edge, no depth limit) of the seeds: the property chains of lcc.ttl
#        (usedIn.forCustomer.imposes, usedIn.soldIn.hasLaw, madeOf.temperOf, ...) and transitive suppliesTo /
#        feedsInto / supersedes all run forward from the change's entities;
#   B  = one step backward into F: the records that point at a reached entity (approvals, qualifications,
#        capabilities, certificates, 8Ds/NCRs via concernsSupplier = hasIssue, deviations, laws via appliesInMarket
#        = hasLaw, completeness statements via completeForPlant, sibling records of memory.py);
#   F2 = forward closure of B.
# `BACKWARD_ROUNDS` repeats (B, F2). Seeds: the request entities, plus every instance of a class that a reader scans
# globally (policies, completeness statements, decisions, commitments, deviations) and every Q-* question key.
# Then the source documents of the facts reached, forward. Facts in scope = facts in force whose subject is reached. tests/test_scoped_equivalence.py proves the cards equal.
GLOBAL_CLASSES = frozenset({"Policy", "CompletenessStatement", "Decision", "Commitment", "Deviation"})
REQUEST_KEYS = ("part", "to_supplier", "from_supplier", "at_supplier", "site", "new_material", "new_coating",
                "sub_supplier", "customer", "program", "material", "coating", "supplier")
BACKWARD_ROUNDS = 1
# Shared entities (many records point at them): never walked backward, except along HUB_BACKWARD. Every reader
# reaches records about a part or supplier through that part or supplier (approvals, qualifications, capabilities,
# certificates, issues), never through the plant, customer, material or person they also name. Laws are the one
# record reached from a hub: law appliesInMarket market (= market hasLaw law, chain usedIn.soldIn.hasLaw).
HUB_CLASSES = frozenset({"Person", "Organisation", "Customer", "Market", "Site", "Program", "Document", "Meeting",
                         "Material", "AlloySeries", "Alloy", "AlloyTemper", "Steel", "Polymer", "Coating",
                         "Substance", "RestrictedSubstance", "Requirement", "Law", "CustomerRequirement",
                         "InternalProcedure", "Standard"})
HUB_BACKWARD = frozenset({"appliesInMarket"})
REUSE_FULL = True   # a scoped check uses the cached full closure of the same snapshot when there is one


def request_entities(request):
    """The ids a change request names (any string value under a known entity key)."""
    found = set()
    for key, value in (request or {}).items():
        if key in ("type", "as_of", "known_at", "epistemic", "utterance", "note", "scope", "speaker"):
            continue
        if isinstance(value, str) and value:
            found.add(value)
        elif isinstance(value, (list, tuple)):
            found.update(item for item in value if isinstance(item, str) and item)
    return found


def _is_edge(fact):
    return fact["p"] not in ("type", "label") and not fact["o"].startswith('"')


def scope_subjects(facts, seeds, rounds=BACKWARD_ROUNDS):
    """Subjects of the bounded neighbourhood of `seeds` (see the comment above)."""
    outgoing, incoming, hubs = {}, {}, set(schema_names())
    for fact in facts:
        if fact["p"] == "type" and fact["o"] in GLOBAL_CLASSES:
            seeds = set(seeds) | {fact["s"]}
        if fact["p"] == "type" and fact["o"] in HUB_CLASSES:
            hubs.add(fact["s"])
    for fact in facts:
        if not _is_edge(fact) or fact["o"] in schema_names():
            continue
        outgoing.setdefault(fact["s"], set()).add(fact["o"])
        incoming.setdefault(fact["o"], set()).add((fact["s"], fact["p"]))
    seeds = set(seeds) | {fact["s"] for fact in facts if fact["s"].startswith("Q-")}

    def forward(start, reached):
        stack = [item for item in start if item not in reached]
        reached.update(stack)
        while stack:
            for nxt in outgoing.get(stack.pop(), ()):
                if nxt not in reached:
                    reached.add(nxt)
                    stack.append(nxt)

    reached = set()
    forward(seeds, reached)
    for _ in range(rounds):
        back = {source for item in list(reached) for source, predicate in incoming.get(item, ())
                if item not in hubs or predicate in HUB_BACKWARD} - reached
        if not back:
            break
        forward(back, reached)
    # the documents the facts in scope come from (oida reads their class for the evidence badge)
    forward({fact["source"] for fact in facts if fact["s"] in reached and fact.get("source")}, reached)
    return reached


def scope_facts(facts, seeds, rounds=BACKWARD_ROUNDS):
    subjects = scope_subjects(facts, seeds, rounds)
    return [fact for fact in facts if fact["s"] in subjects]


_warm = {}  # id(log) -> (log, as_of): full closures kept warm, recomputed when the log accepts facts


def warm(log, as_of):
    """Compute the full closure of `log` on `as_of` now (server start) and again whenever the fact log commits a
    write (acceptance, a record written by a person, a review): the cache key is the snapshot hash, so the old
    closure simply stops matching and the new one is ready before the next check. Returns the projection."""
    _warm[id(log)] = (log, as_of)
    if hasattr(log, "on_commit") and _rewarm not in log.on_commit:
        log.on_commit.append(_rewarm)
    return Projection(log, as_of)


def _rewarm(log):
    entry = _warm.get(id(log))
    if entry and entry[0] is log:
        Projection(log, entry[1])


class Projection:
    def __init__(self, log, as_of, known_at=None, reason=True, scope=None):
        """scope: None = close the whole snapshot; a set of entity ids = close only their neighbourhood
        (scope_facts). Every other attribute (current_facts, history_facts, contested, provenance of the
        facts in scope...) is the same as for the full projection."""
        self.as_of = as_of
        self.known_at = known_at
        started = time.perf_counter()
        all_facts = log.all_facts()
        self.unclassified = log.unclassified_items()  # review queue only; never added to the graph
        self.snapshot = take_snapshot(all_facts, as_of, known_at, functional_predicates())
        self.snapshot_ms = (time.perf_counter() - started) * 1000

        self.current_facts = self.snapshot["facts"]
        self.fact_ids_in_force = list(self.snapshot["fact_ids"])
        self.snapshot_hash = self.snapshot["hash"]
        self.contested = self.snapshot["contested"]
        self.notes = self.snapshot["notes"]
        self.replaced = set(self.snapshot["replaced"])
        in_force = set(self.fact_ids_in_force)
        self.history_facts = [fact for fact in all_facts if fact["id"] not in in_force]
        self.current_records = {fact["s"] for fact in self.current_facts}
        self.asserted_count = len(self.current_facts)

        closure_started = time.perf_counter()
        self.scope = None if scope is None else frozenset(scope)
        graph_facts = self.current_facts
        scope_hash = None
        if self.scope is not None:
            graph_facts = scope_facts(self.current_facts, self.scope)
            scope_hash = hashlib.sha256(json.dumps([fact["id"] for fact in graph_facts]).encode()).hexdigest()
        self.scoped_count = len(graph_facts)
        key = (ontology_hash(), self.snapshot_hash, bool(reason), scope_hash)
        full_key = (ontology_hash(), self.snapshot_hash, bool(reason), None)
        if REUSE_FULL and scope_hash is not None and key not in _closure_cache and full_key in _closure_cache:
            key = full_key           # the warm full closure of this snapshot answers every scoped reader the same
            self.scoped_count = len(self.current_facts)
        self.cache_hit = key in _closure_cache
        if self.cache_hit:
            _closure_cache.move_to_end(key)
            self.graph, self.provenance = _closure_cache[key]
        else:
            self.graph, self.provenance = _build_graph(graph_facts, reason)
            _closure_cache[key] = (self.graph, self.provenance)
            while len(_closure_cache) > CACHE_SIZE:
                _closure_cache.popitem(last=False)
        self.closure_ms = (time.perf_counter() - closure_started) * 1000
        self.reasoning_ms = (time.perf_counter() - started) * 1000  # prototype name: snapshot + closure

        # #28: contradictions the fact log stored as contested (never in force), and contested keys rules read
        self.contested_records = log.contested_records() if hasattr(log, "contested_records") else []
        self.contested_reads = OrderedDict()

        self.history_by_subject = {}
        for fact in self.history_facts:
            self.history_by_subject.setdefault(fact["s"], []).append(fact)

    # ---- prototype API --------------------------------------------------------------------------------

    def query(self, sparql, **bindings):
        init = {key: (node(value) if isinstance(value, str) else value) for key, value in bindings.items()}
        return list(self.graph.query(sparql, initNs={"lcc": LCC, "rdf": RDF, "rdfs": RDFS}, initBindings=init))

    def objects(self, subject, predicate):
        found = sorted(local_name(term) for term in self.graph.objects(node(subject), LCC[predicate]))
        if self.contested:
            self._note_contested_read(subject, predicate)
        return found

    def _note_contested_read(self, subject, predicate):
        """#28: remember every contested (subject, predicate) a rule read, so it becomes a question, not a gap."""
        for item in self.contested_for(subject, predicate):
            self.contested_reads.setdefault(tuple(item["key"]), item)

    def value(self, subject, predicate):
        """The one value in force, or None. None also when the value is contested (see `contested_for`)."""
        values = self.objects(subject, predicate)
        return values[0] if values else None

    def label(self, name):
        found = self.graph.value(node(name), RDFS.label)
        return str(found) if found else name

    def is_a(self, subject, class_name):
        return (node(subject), RDF.type, LCC[class_name]) in self.graph

    def instances(self, class_name):
        return sorted(local_name(term) for term in self.graph.subjects(RDF.type, LCC[class_name]))

    # ---- new today ------------------------------------------------------------------------------------

    def values(self, subject, predicate):
        """Alias of objects(): every value in force (multi-valued predicates)."""
        return self.objects(subject, predicate)

    def contested_for(self, subject, predicate=None):
        """Contested pairs about this subject (and predicate): turn them into questions, never guess."""
        return [item for item in self.contested
                if item["key"][0] == subject and (predicate is None or item["key"][1] == predicate)]

    def facts_for(self, subject, predicate, obj=None):
        """Fact rows (source, quote, rank...) behind an asserted triple in force."""
        return [fact for fact in self.current_facts
                if fact["s"] == subject and fact["p"] == predicate and (obj is None or fact["o"] == obj)]

    def epistemic_type(self, name):
        """OIDA type of an entity (via its classes) or of a class: CONSTRAINT | DECISION | EVIDENCE | PLAN |
        QUESTION, or None."""
        ontology = ontology_graph()
        found = ontology.value(LCC[name], LCC.epistemicType) if name in schema_names() else None
        if found:
            return str(found)
        for class_term in sorted(self.graph.objects(node(name), RDF.type)):
            found = ontology.value(class_term, LCC.epistemicType)
            if found:
                return str(found)
        return None

    def timings(self):
        return {"snapshot": round(self.snapshot_ms, 1), "closure": round(self.closure_ms, 1)}
