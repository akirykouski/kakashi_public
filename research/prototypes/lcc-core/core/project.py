"""Project the fact log into an RDF graph as of a date, then compute the OWL 2 RL closure.

current graph : facts valid on `as_of`, recorded by `known_at`, accepted, and not superseded
history       : superseded or expired records, kept for the "this was replaced" view
provenance    : (s, p, o) -> fact rows, so every asserted triple can be traced to a quote
"""
import json
import os
import time
from urllib.parse import quote, unquote

import owlrl
from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONTOLOGY_PATH = os.path.join(ROOT, "ontology", "lcc.ttl")
LCC = Namespace("https://lcc.example/ont#")
ID = Namespace("https://lcc.example/id/")

_ontology_cache = {}


def ontology_graph():
    if "graph" not in _ontology_cache:
        graph = Graph()
        graph.parse(ONTOLOGY_PATH, format="turtle")
        _ontology_cache["graph"] = graph
        _ontology_cache["names"] = {str(node)[len(str(LCC)):] for node in graph.all_nodes()
                                    if isinstance(node, URIRef) and str(node).startswith(str(LCC))}
    return _ontology_cache["graph"]


def schema_names():
    ontology_graph()
    return _ontology_cache["names"]


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
    if fact["valid_from"] and fact["valid_from"] > as_of:
        return False
    if fact["valid_to"] and fact["valid_to"] < as_of:
        return False
    if known_at and fact["recorded_at"] > known_at:
        return False
    return True


def superseded_records(facts):
    """Records replaced by a valid newer record, following chains (rev D > rev C > rev B)."""
    edges = {}
    for fact in facts:
        if fact["p"] == "supersedes":
            edges.setdefault(fact["s"], set()).add(fact["o"])
    replaced = set()
    stack = [target for targets in edges.values() for target in targets]
    while stack:
        record = stack.pop()
        if record in replaced:
            continue
        replaced.add(record)
        stack.extend(edges.get(record, ()))
    return replaced


class Projection:
    def __init__(self, log, as_of, known_at=None, reason=True):
        self.as_of = as_of
        started = time.time()
        all_facts = log.all_facts()
        self.unclassified = log.unclassified_items()  # review queue only; never added to the graph
        valid = [fact for fact in all_facts if is_valid(fact, as_of, known_at)]
        self.replaced = superseded_records(valid)
        self.current_facts = [fact for fact in valid if fact["s"] not in self.replaced]
        self.history_facts = [fact for fact in all_facts if fact not in self.current_facts]
        self.current_records = {fact["s"] for fact in self.current_facts}
        self.provenance = {}
        self.graph = Graph()
        for triple in ontology_graph():
            self.graph.add(triple)
        for fact in self.current_facts:
            triple = triple_for(fact)
            self.graph.add(triple)
            self.provenance.setdefault(triple, []).append(fact)
        self.asserted_count = len(self.current_facts)
        if reason:
            owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False,
                                   datatype_axioms=False).expand(self.graph)
        self.reasoning_ms = (time.time() - started) * 1000
        self.history_by_subject = {}
        for fact in self.history_facts:
            self.history_by_subject.setdefault(fact["s"], []).append(fact)

    def query(self, sparql, **bindings):
        init = {key: (node(value) if isinstance(value, str) else value) for key, value in bindings.items()}
        return list(self.graph.query(sparql, initNs={"lcc": LCC, "rdf": RDF, "rdfs": RDFS}, initBindings=init))

    def objects(self, subject, predicate):
        return [local_name(term) for term in self.graph.objects(node(subject), LCC[predicate])]

    def value(self, subject, predicate):
        values = self.objects(subject, predicate)
        return values[0] if values else None

    def label(self, name):
        found = self.graph.value(node(name), RDFS.label)
        return str(found) if found else name

    def is_a(self, subject, class_name):
        return (node(subject), RDF.type, LCC[class_name]) in self.graph

    def instances(self, class_name):
        return sorted(local_name(term) for term in self.graph.subjects(RDF.type, LCC[class_name]))
