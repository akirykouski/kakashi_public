"""Instance-level OWL 2 RL closure over a schema closed once.

owlrl re-closes the ontology (466 triples) together with the facts on every projection: ~170 ms of fixed cost
before a single fact, and every round re-scans every triple. Here the ontology is closed once by owlrl itself
(cached), the schema is read from that closed graph, and only the instance rules the ontology can trigger are
run, semi-naive, over the facts:

  cax-sco   x a C, C subClassOf D            -> x a D
  prp-dom   x p y, p domain D                -> x a D
  prp-rng   x p y, p range D (y not literal) -> y a D
  prp-spo1  x p y, p subPropertyOf q         -> x q y
  prp-inv   x p y, p inverseOf q             -> y q x
  prp-symp  x p y, p SymmetricProperty       -> y p x
  prp-trp   x p y, y p z, p TransitiveProperty -> x p z
  prp-spo2  x p1 y1 ... yn-1 pn z, p propertyChainAxiom (p1 .. pn) -> x p z
  eq-ref    x p y                            -> x sameAs x, y sameAs y   (owlrl writes these; nobody reads them)

Anything else the ontology declares that would need more (owl:sameAs from functional properties, restrictions,
hasKey, ...) is detected by `unsupported()` and makes core/project.py fall back to owlrl for that graph.
tests/test_scoped_equivalence.py checks the result triple for triple against owlrl.
"""
from collections import defaultdict

import owlrl
from rdflib import OWL, RDF, RDFS, Graph, Literal
from rdflib.collection import Collection

_schema = {}

# Constructs whose instance rules are not implemented here: if the closed ontology uses one, use owlrl.
UNSUPPORTED = (OWL.hasKey, OWL.someValuesFrom, OWL.allValuesFrom, OWL.hasValue, OWL.maxCardinality,
               OWL.maxQualifiedCardinality, OWL.intersectionOf, OWL.unionOf, OWL.oneOf, OWL.sameAs,
               OWL.propertyDisjointWith, OWL.disjointWith, OWL.complementOf, OWL.AllDisjointClasses,
               OWL.AllDisjointProperties, OWL.AllDifferent, OWL.differentFrom,
               OWL.AsymmetricProperty, OWL.IrreflexiveProperty)
# owl:equivalentClass / equivalentProperty are fine: the closed schema already has them as two-way subClassOf /
# subPropertyOf (owlrl scm-eqc1, scm-eqp1).


def schema(ontology):
    """Closed ontology graph + the schema tables, computed once per ontology graph object."""
    key = id(ontology)
    if _schema.get("key") == key:
        return _schema
    closed = Graph()
    for triple in ontology:
        closed.add(triple)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(closed)
    sup_class, sup_prop = defaultdict(set), defaultdict(set)
    domain, range_, inverse = defaultdict(set), defaultdict(set), defaultdict(set)
    for sub, sup in closed.subject_objects(RDFS.subClassOf):
        if sub != sup:
            sup_class[sub].add(sup)
    for sub, sup in closed.subject_objects(RDFS.subPropertyOf):
        if sub != sup:
            sup_prop[sub].add(sup)
    for prop, cls in closed.subject_objects(RDFS.domain):
        domain[prop].add(cls)
    for prop, cls in closed.subject_objects(RDFS.range):
        range_[prop].add(cls)
    for first, second in closed.subject_objects(OWL.inverseOf):
        inverse[first].add(second)
        inverse[second].add(first)
    chains = defaultdict(list)
    for prop, head in closed.subject_objects(OWL.propertyChainAxiom):
        chains[prop].append(tuple(Collection(closed, head)))
    unsupported = sorted({str(predicate) for predicate in UNSUPPORTED if (None, predicate, None) in closed
                          and predicate != OWL.sameAs})
    if any(first != second for first, second in closed.subject_objects(OWL.sameAs)):
        unsupported.append(str(OWL.sameAs))
    functional = set(closed.subjects(RDF.type, OWL.FunctionalProperty))
    inverse_functional = set(closed.subjects(RDF.type, OWL.InverseFunctionalProperty))
    _schema.clear()
    _schema.update(key=key, closed=closed, sup_class=sup_class, sup_prop=sup_prop, domain=domain, range=range_,
                   inverse=inverse, symmetric=set(closed.subjects(RDF.type, OWL.SymmetricProperty)),
                   transitive=set(closed.subjects(RDF.type, OWL.TransitiveProperty)), chains=chains,
                   functional=functional, inverse_functional=inverse_functional, unsupported=unsupported)
    return _schema


def unsupported(ontology):
    return schema(ontology)["unsupported"]


def functional_clash(triples, ontology):
    """True if a functional property has two values for one subject, or an inverse-functional one two subjects
    for one value: owlrl would then infer owl:sameAs between them, which close() does not do."""
    tables = schema(ontology)
    functional, inverse_functional = tables["functional"], tables["inverse_functional"]
    seen, seen_inverse = {}, {}
    for subject, predicate, obj in triples:
        if predicate in functional and seen.setdefault((subject, predicate), obj) != obj:
            return True
        if predicate in inverse_functional and seen_inverse.setdefault((obj, predicate), subject) != subject:
            return True
    return False


def close(triples, ontology):
    """Closed ontology + the instance closure of `triples` (a Graph, like owlrl's result), or None when the
    ontology uses a construct not implemented here or a functional property clashes (use owlrl then)."""
    if unsupported(ontology):
        return None
    tables = schema(ontology)
    sup_class, sup_prop = tables["sup_class"], tables["sup_prop"]
    domain, range_, inverse = tables["domain"], tables["range"], tables["inverse"]
    symmetric, transitive, chains = tables["symmetric"], tables["transitive"], tables["chains"]
    chain_steps = defaultdict(list)          # predicate -> (chain property, chain, position)
    for prop, items in chains.items():
        for chain in items:
            for position, step in enumerate(chain):
                chain_steps[step].append((prop, chain, position))

    known = set()
    by_sp = defaultdict(set)                 # (s, p) -> {o}
    by_po = defaultdict(set)                 # (p, o) -> {s}
    pending = list(triples)

    def add(triple):
        if triple not in known:
            pending.append(triple)

    def follow(start, chain):
        """Ends of chain from start."""
        frontier = {start}
        for step in chain:
            frontier = {obj for node in frontier for obj in by_sp.get((node, step), ())}
            if not frontier:
                break
        return frontier

    def back(end, chain):
        """Starts of chain ending at end."""
        frontier = {end}
        for step in reversed(chain):
            frontier = {subject for node in frontier for subject in by_po.get((step, node), ())}
            if not frontier:
                break
        return frontier

    while pending:
        triple = pending.pop()
        if triple in known:
            continue
        known.add(triple)
        subject, predicate, obj = triple
        by_sp[(subject, predicate)].add(obj)
        by_po[(predicate, obj)].add(subject)
        if predicate == RDF.type:
            for cls in sup_class.get(obj, ()):
                add((subject, RDF.type, cls))
            continue
        literal = isinstance(obj, Literal)
        for cls in domain.get(predicate, ()):
            add((subject, RDF.type, cls))
        if not literal:
            for cls in range_.get(predicate, ()):
                add((obj, RDF.type, cls))
        for sup in sup_prop.get(predicate, ()):
            add((subject, sup, obj))
        if not literal:
            for inv in inverse.get(predicate, ()):
                add((obj, inv, subject))
            if predicate in symmetric:
                add((obj, predicate, subject))
        if predicate in transitive and not literal:
            for nxt in list(by_sp.get((obj, predicate), ())):
                add((subject, predicate, nxt))
            for prev in list(by_po.get((predicate, subject), ())):
                add((prev, predicate, obj))
        for prop, chain, position in chain_steps.get(predicate, ()):
            starts = back(subject, chain[:position])
            ends = follow(obj, chain[position + 1:])
            for start in starts:
                for end in ends:
                    add((start, prop, end))

    if functional_clash(known, ontology):
        return None                                      # owl:sameAs territory: the caller uses owlrl
    graph = Graph()
    for item in tables["closed"]:
        graph.add(item)
    for subject, predicate, obj in known:
        graph.add((subject, predicate, obj))
        graph.add((subject, OWL.sameAs, subject))       # eq-ref, as owlrl writes it
        graph.add((predicate, OWL.sameAs, predicate))
        graph.add((obj, OWL.sameAs, obj))
    return graph
