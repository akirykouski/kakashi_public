"""Explain a triple: either the fact (source + quote) that asserts it, or the premises the reasoner used.

Reads the axioms from the ontology itself (property chains, inverse properties, sub-properties), so a new
axiom in lcc.ttl is explained without code changes.
"""
from rdflib import OWL, RDF, RDFS
from rdflib.term import Identifier
from rdflib.collection import Collection

from project import LCC, local_name, node

MAX_DEPTH = 6


def chain_of(projection, predicate_term):
    for chain_head in projection.graph.objects(predicate_term, OWL.propertyChainAxiom):
        return list(Collection(projection.graph, chain_head))
    return None


def inverses_of(projection, predicate_term):
    found = set(projection.graph.objects(predicate_term, OWL.inverseOf))
    found |= set(projection.graph.subjects(OWL.inverseOf, predicate_term))
    return found


def sub_properties_of(projection, predicate_term):
    return [term for term in projection.graph.subjects(RDFS.subPropertyOf, predicate_term)
            if term != predicate_term and str(term).startswith(str(LCC))]


def text_of(subject, predicate, obj):
    return f"{local_name(subject)} {local_name(predicate)} {local_name(obj)}"


def asserted_step(projection, triple):
    facts = projection.provenance.get(triple)
    if not facts:
        return None
    fact = facts[0]
    return {"triple": text_of(*triple), "inferred": False, "fact_id": fact["id"], "source": fact["source"],
            "quote": fact["quote"], "context_quote": fact.get("context_quote"),
            "valid_from": fact["valid_from"], "author": fact["author"]}


def explain(projection, subject, predicate, obj, depth=0):
    """Return a step dict, or None if the triple is not in the current graph."""
    subject_term = subject if isinstance(subject, Identifier) else node(subject)
    predicate_term = predicate if isinstance(predicate, Identifier) else LCC[predicate]
    object_term = obj if isinstance(obj, Identifier) else node(obj)
    triple = (subject_term, predicate_term, object_term)
    if triple not in projection.graph:
        return None
    step = asserted_step(projection, triple)
    if step or depth >= MAX_DEPTH:
        return step

    chain = chain_of(projection, predicate_term)
    if chain:
        variables = [f"?n{index}" for index in range(len(chain) - 1)]
        nodes = ["?start"] + variables + ["?end"]
        patterns = " . ".join(f"{nodes[index]} <{chain[index]}> {nodes[index + 1]}" for index in range(len(chain)))
        select = " ".join(variables) if variables else "*"
        rows = projection.graph.query(f"SELECT {select} WHERE {{ {patterns} }} LIMIT 1",
                                      initBindings={"start": subject_term, "end": object_term})
        for row in rows:
            path = [subject_term] + [row[index] for index in range(len(variables))] + [object_term]
            premises = [explain(projection, path[index], chain[index], path[index + 1], depth + 1)
                        for index in range(len(chain))]
            names = " o ".join(local_name(term) for term in chain)
            return {"triple": text_of(*triple), "inferred": True, "axiom": f"property chain {names}",
                    "premises": [premise for premise in premises if premise]}

    for inverse in inverses_of(projection, predicate_term):
        premise = explain(projection, object_term, inverse, subject_term, depth + 1)
        if premise:
            return {"triple": text_of(*triple), "inferred": True,
                    "axiom": f"{local_name(predicate_term)} inverseOf {local_name(inverse)}", "premises": [premise]}

    for sub_property in sub_properties_of(projection, predicate_term):
        premise = explain(projection, subject_term, sub_property, object_term, depth + 1)
        if premise:
            return {"triple": text_of(*triple), "inferred": True,
                    "axiom": f"{local_name(sub_property)} subPropertyOf {local_name(predicate_term)}",
                    "premises": [premise]}

    if (predicate_term, RDF.type, OWL.TransitiveProperty) in projection.graph:
        rows = projection.graph.query(f"SELECT ?middle WHERE {{ ?start <{predicate_term}> ?middle . "
                                      f"?middle <{predicate_term}> ?end }} LIMIT 1",
                                      initBindings={"start": subject_term, "end": object_term})
        for row in rows:
            premises = [explain(projection, subject_term, predicate_term, row[0], depth + 1),
                        explain(projection, row[0], predicate_term, object_term, depth + 1)]
            return {"triple": text_of(*triple), "inferred": True,
                    "axiom": f"{local_name(predicate_term)} is transitive",
                    "premises": [premise for premise in premises if premise]}
    return {"triple": text_of(*triple), "inferred": True, "axiom": "OWL 2 RL closure", "premises": []}


def flatten(step):
    """All asserted leaf steps under a step, in order."""
    if step is None:
        return []
    if not step["inferred"]:
        return [step]
    leaves = []
    for premise in step["premises"]:
        leaves.extend(flatten(premise))
    return leaves


def render(step, indent=0):
    if step is None:
        return ""
    pad = "  " * indent
    if not step["inferred"]:
        quote = step["quote"].replace(chr(10), " ")
        if step.get("context_quote"):
            context = step["context_quote"].replace(chr(10), " ")
            return f"{pad}- {step['triple']}  [{step['source']}: \"...{context}...\" -> \"{quote}\"]"
        return f"{pad}- {step['triple']}  [{step['source']}: \"{quote}\"]"
    lines = [f"{pad}- {step['triple']}  (inferred: {step['axiom']})"]
    lines += [render(premise, indent + 1) for premise in step["premises"]]
    return "\n".join(lines)
