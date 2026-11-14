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
CACHE_SIZE = 16

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


class Projection:
    def __init__(self, log, as_of, known_at=None, reason=True):
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
        key = (ontology_hash(), self.snapshot_hash, bool(reason))
        self.cache_hit = key in _closure_cache
        if self.cache_hit:
            _closure_cache.move_to_end(key)
            self.graph, self.provenance = _closure_cache[key]
        else:
            self.graph, self.provenance = _build_graph(self.current_facts, reason)
            _closure_cache[key] = (self.graph, self.provenance)
            while len(_closure_cache) > CACHE_SIZE:
                _closure_cache.popitem(last=False)
        self.closure_ms = (time.perf_counter() - closure_started) * 1000
        self.reasoning_ms = (time.perf_counter() - started) * 1000  # prototype name: snapshot + closure

        self.history_by_subject = {}
        for fact in self.history_facts:
            self.history_by_subject.setdefault(fact["s"], []).append(fact)

    # ---- prototype API --------------------------------------------------------------------------------

    def query(self, sparql, **bindings):
        init = {key: (node(value) if isinstance(value, str) else value) for key, value in bindings.items()}
        return list(self.graph.query(sparql, initNs={"lcc": LCC, "rdf": RDF, "rdfs": RDFS}, initBindings=init))

    def objects(self, subject, predicate):
        return sorted(local_name(term) for term in self.graph.objects(node(subject), LCC[predicate]))

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
