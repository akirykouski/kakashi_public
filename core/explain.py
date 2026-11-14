"""Proof chains for findings: why a triple holds, down to verbatim quotes.

Generic backward proof search over the OWL 2 RL closure (ported from Arseniy's spike
research/prototypes prep/spikes/reasoning-core/core.py `Explainer`). For a triple in the closure:
if a fact in force asserts it, it is a leaf (source + quote, + context_quote when the fact has one).
Otherwise every OWL 2 RL rule that could have produced it is tried (property chain, inverse, sub-property,
transitivity, sub-class, domain, range); each premise must itself be in the closure and provable.
Iterative deepening returns a shallowest proof. The axioms are read from the ontology, so a new axiom
needs no code change here.

Guarantee: every step returned is either a leaf with a source and a quote, or an inferred step with a rule
and at least one premise. If no such proof exists, `explain` returns None; it never invents a step.
"""
from collections import defaultdict

from rdflib import OWL, RDF, RDFS
from rdflib.collection import Collection
from rdflib.term import Identifier

try:
    from .project import LCC, local_name, node, ontology_graph
except ImportError:  # core/ on sys.path (prototype CLI style)
    from project import LCC, local_name, node, ontology_graph

MAX_DEPTH = 8


def short(term):
    return local_name(term) if isinstance(term, Identifier) else str(term)


def text_of(subject, predicate, obj):
    if predicate == RDF.type:
        return f"{short(subject)} a {short(obj)}"
    return f"{short(subject)} {short(predicate)} {short(obj)}"


class Explainer:
    """Backward prover over one projection (closure graph + provenance of asserted triples)."""

    def __init__(self, projection):
        self.graph = projection.graph
        self.provenance = projection.provenance
        tbox = ontology_graph()
        self.inverse, self.sub_properties, self.sub_classes = defaultdict(set), defaultdict(set), defaultdict(set)
        self.domain_of, self.range_of, self.chains = defaultdict(set), defaultdict(set), defaultdict(list)
        for first, second in tbox.subject_objects(OWL.inverseOf):
            self.inverse[first].add(second)
            self.inverse[second].add(first)
        for sub, sup in tbox.subject_objects(RDFS.subPropertyOf):
            if sub != sup:
                self.sub_properties[sup].add(sub)
        for sub, sup in tbox.subject_objects(RDFS.subClassOf):
            if sub != sup:
                self.sub_classes[sup].add(sub)
        for prop, cls in tbox.subject_objects(RDFS.domain):
            self.domain_of[cls].add(prop)
        for prop, cls in tbox.subject_objects(RDFS.range):
            self.range_of[cls].add(prop)
        for prop, head in tbox.subject_objects(OWL.propertyChainAxiom):
            self.chains[prop].append(list(Collection(tbox, head)))
        self.transitive = set(tbox.subjects(RDF.type, OWL.TransitiveProperty))
        self.cache = {}

    # ---- candidate rules that could have produced a triple ------------------------------------------------

    def paths(self, subject, properties, obj):
        if len(properties) == 1:
            if (subject, properties[0], obj) in self.graph:
                yield [(subject, properties[0], obj)]
            return
        for middle in sorted(self.graph.objects(subject, properties[0])):
            for rest in self.paths(middle, properties[1:], obj):
                yield [(subject, properties[0], middle)] + rest

    def candidates(self, triple):
        subject, predicate, obj = triple
        if predicate == RDF.type:
            for sub in sorted(self.sub_classes[obj]):
                if (subject, RDF.type, sub) in self.graph:
                    yield f"sub-class {short(sub)} of {short(obj)}", [(subject, RDF.type, sub)]
            for prop in sorted(self.domain_of[obj]):
                for value in sorted(self.graph.objects(subject, prop)):
                    yield f"domain of {short(prop)}", [(subject, prop, value)]
            for prop in sorted(self.range_of[obj]):
                for value in sorted(self.graph.subjects(prop, subject)):
                    yield f"range of {short(prop)}", [(value, prop, subject)]
            return
        for chain in self.chains[predicate]:
            for path in self.paths(subject, chain, obj):
                yield "property chain " + " o ".join(short(item) for item in chain), path
        for inverse in sorted(self.inverse[predicate]):
            if (obj, inverse, subject) in self.graph:
                yield f"{short(predicate)} inverseOf {short(inverse)}", [(obj, inverse, subject)]
        for sub in sorted(self.sub_properties[predicate]):
            if (subject, sub, obj) in self.graph:
                yield f"{short(sub)} subPropertyOf {short(predicate)}", [(subject, sub, obj)]
        if predicate in self.transitive:
            for middle in sorted(self.graph.objects(subject, predicate)):
                if middle not in (subject, obj) and (middle, predicate, obj) in self.graph:
                    yield f"{short(predicate)} is transitive", [(subject, predicate, middle), (middle, predicate, obj)]

    # ---- proof search ---------------------------------------------------------------------------------------

    def leaf(self, triple):
        facts = self.provenance.get(triple)
        if not facts:
            return None
        fact = sorted(facts, key=lambda row: row["id"])[0]
        if not fact.get("quote") or not fact.get("source"):
            return None
        return {"triple": text_of(*triple), "inferred": False, "source": fact["source"], "quote": fact["quote"],
                "context_quote": fact.get("context_quote"), "fact_id": fact["id"], "rule": None, "premises": []}

    def prove(self, triple, depth, stack):
        found = self.leaf(triple)
        if found:
            return found
        if depth == 0 or triple in stack:
            return None
        for rule, premises in self.candidates(triple):
            proofs = [self.prove(premise, depth - 1, stack | {triple}) for premise in premises]
            if proofs and all(proofs):
                return {"triple": text_of(*triple), "inferred": True, "source": None, "quote": None,
                        "context_quote": None, "fact_id": None, "rule": rule, "premises": proofs}
        return None

    def explain(self, triple, max_depth=MAX_DEPTH):
        if triple in self.cache:
            return self.cache[triple]
        proof = None
        if triple in self.graph:
            for depth in range(max_depth + 1):
                proof = self.prove(triple, depth, frozenset())
                if proof:
                    break
        self.cache[triple] = proof
        return proof


def explainer_for(projection):
    found = getattr(projection, "_rules_explainer", None)
    if found is None:
        found = Explainer(projection)
        projection._rules_explainer = found
    return found


def term(value, predicate=False):
    if isinstance(value, Identifier):
        return value
    return LCC[value] if predicate else node(value)


def explain(projection, subject, predicate, obj):
    """EvidenceStep dict (core/contracts.py) proving subject-predicate-object, or None when no proof exists."""
    predicate_term = RDF.type if predicate == "type" else term(predicate, predicate=True)
    object_term = LCC[obj] if predicate == "type" and not isinstance(obj, Identifier) else term(obj)
    return explainer_for(projection).explain((term(subject), predicate_term, object_term))


def leaves(step):
    """All asserted leaf steps under a step, in order."""
    if step is None:
        return []
    if not step["inferred"]:
        return [step]
    found = []
    for premise in step["premises"]:
        found.extend(leaves(premise))
    return found


def valid_step(step):
    """True if the step and every step under it has a quote (leaf) or premises (inferred)."""
    if not step:
        return False
    if not step["inferred"]:
        return bool(step.get("source") and step.get("quote"))
    return bool(step.get("rule") and step["premises"]) and all(valid_step(item) for item in step["premises"])


def render(step, indent=0):
    if step is None:
        return ""
    pad = "  " * indent
    if not step["inferred"]:
        context = f" (context: \"{step['context_quote']}\")" if step.get("context_quote") else ""
        return f"{pad}- {step['triple']}  [{step['source']}: \"{step['quote'].replace(chr(10), ' ')}\"]{context}"
    lines = [f"{pad}- {step['triple']}  (inferred: {step['rule']})"]
    lines += [render(premise, indent + 1) for premise in step["premises"]]
    return "\n".join(lines)
