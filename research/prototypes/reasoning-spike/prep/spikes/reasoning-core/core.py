"""PREP SPIKE (written 13 Nov 2026, before the event). Throwaway, disclosed.

Validates three design claims of docs/plan/01-solution.md on the BR-220 scenario:

  1. snapshot()  the "what is in force" view is a pure, order-independent
                 function of the append-only fact set (supersession, authority,
                 stale mentions, contested facts, time travel).
  2. check()     OWL 2 RL closure + SHACL shapes turn that view into blockers
                 and open questions.
  3. Explainer   every inferred triple gets a proof tree whose leaves are
                 asserted facts carrying a document and a verbatim quote.

No LLM anywhere in this file. Run: see run_scenario.py.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import owlrl
import pyshacl
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection

CC = Namespace("https://example.org/ctxcol#")
SH = Namespace("http://www.w3.org/ns/shacl#")
ONT = Path(__file__).resolve().parents[3] / "ontology"


# ------------------------------------------------------------------ loading

def load_tbox() -> Graph:
    g = Graph()
    g.parse(ONT / "cc-core.ttl")
    g.parse(ONT / "cc-alloys.ttl")
    g.parse(ONT / "cc-policies.ttl")
    return g


def load_shapes() -> Graph:
    return Graph().parse(ONT / "cc-shapes.ttl")


def load_facts(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


SCENARIO_FILES = ("br220.facts.jsonl", "br220.request-cr01.jsonl")
DATA = Path(__file__).resolve().parents[3] / "data"


def load_scenario() -> list[dict]:
    """Document facts plus the facts that turn change request CR-01 into a graph."""
    return [f for name in SCENARIO_FILES for f in load_facts(ONT / "scenario" / name)]


def _norm(text: str) -> str:
    return " ".join(text.split())


def quote_problems(facts: list[dict]) -> list[str]:
    """Every fact's quote must be a literal substring (whitespace-normalised) of its
    document: data/sources/<doc>.md, or, for a change-request id (CR-NN), the
    request_text in data/eval/change_requests.jsonl."""
    requests = {r["id"]: r["request_text"] for r in map(json.loads, (DATA / "eval" / "change_requests.jsonl").read_text().splitlines())}
    problems = []
    for f in facts:
        src = DATA / "sources" / f"{f['doc']}.md"
        if src.is_file():
            text = src.read_text()
        elif f["doc"] in requests:
            text = requests[f["doc"]]
        else:
            problems.append(f"{f['id']}: doc {f['doc']!r} is neither data/sources/<doc>.md nor a change request id")
            continue
        if _norm(f["quote"]) not in _norm(text):
            problems.append(f"{f['id']}: quote not found in {f['doc']}: {f['quote']!r}")
    return problems


def term(x, lit=False):
    if lit:
        return Literal(x)
    if x == "rdf:type":
        return RDF.type
    assert x.startswith("cc:"), x
    return CC[x[3:]]


def triple(f: dict):
    return (term(f["s"]), term(f["p"]), term(f["o"], f.get("lit", False)))


def functional_predicates(tbox: Graph) -> set:
    return set(tbox.subjects(RDF.type, OWL.FunctionalProperty))


# ----------------------------------------------------------------- snapshot

def without_source_doc(facts: list[dict], doc: str) -> list[dict]:
    """Facts whose source document is not `doc` (as if that document were not yet accepted)."""
    return [f for f in facts if f["doc"] != doc]


def snapshot(facts: list[dict], functional: set, valid_at: str, known_at: str) -> dict:
    """What is in force at world time `valid_at`, as recorded up to `known_at`.

    Pure function of the SET of facts: no dependence on list order, no mutation.
    Returns {"facts": [in-force facts], "notes": [...], "contested": [...]}.

    For a functional (subject, predicate) group:
      * explicit `supersedes` removes its target;
      * only kind == "assert" can hold a value; a "mention" (a document that
        merely restates something) never can;
      * the highest authority tier present (rank 1 > 2 > 3) holds the value;
        inside it the latest valid_from wins; two different values with the
        same valid_from are a conflict and NEITHER enters the graph;
      * a newer, lower-authority assertion with a different value does not win:
        the head stays, and the pair is reported as contested;
      * a mention that repeats a superseded value is reported as stale.
    """
    visible = [f for f in facts
               if f["status"] == "accepted" and f["recorded_at"] <= known_at
               and f["valid_from"] <= valid_at
               and (not f.get("valid_to") or valid_at < f["valid_to"])]
    superseded_ids = {f["supersedes"] for f in visible if f.get("supersedes")}
    visible = [f for f in visible if f["id"] not in superseded_ids]

    out, notes, contested = [], [], []
    groups = defaultdict(list)
    for f in sorted(visible, key=lambda f: f["id"]):          # canonical order
        if term(f["p"]) in functional:
            groups[(f["s"], f["p"])].append(f)
        elif f["kind"] == "assert":
            out.append(f)

    for key in sorted(groups):
        group = groups[key]
        asserts = [f for f in group if f["kind"] == "assert"]
        mentions = [f for f in group if f["kind"] == "mention"]
        if not asserts:
            for m in mentions:
                notes.append({"type": "unsupported_mention", "fact": m["id"], "key": key})
            continue
        top = min(f["rank"] for f in asserts)
        tier = [f for f in asserts if f["rank"] == top]
        latest = max(f["valid_from"] for f in tier)
        heads = [f for f in tier if f["valid_from"] == latest]
        if len({json.dumps(f["o"]) for f in heads}) > 1:
            notes.append({"type": "conflict", "key": key, "facts": sorted(f["id"] for f in heads)})
            continue                                            # quarantined
        head = heads[0]
        out.append(head)
        old_values = {json.dumps(f["o"]) for f in tier if f["valid_from"] < latest and f["o"] != head["o"]}
        for f in tier:
            if f is not head and f["o"] != head["o"]:
                notes.append({"type": "superseded", "fact": f["id"], "by": head["id"], "key": key})
        for f in asserts:
            if f["rank"] > top and f["o"] != head["o"]:
                if f["valid_from"] > head["valid_from"]:
                    contested.append({"key": key, "head": head["id"], "challenger": f["id"]})
                else:
                    notes.append({"type": "overruled", "fact": f["id"], "by": head["id"], "key": key})
        for m in mentions:
            if m["o"] != head["o"]:
                kind = "stale_mention" if json.dumps(m["o"]) in old_values else "unsupported_mention"
                notes.append({"type": kind, "fact": m["id"], "head": head["id"], "key": key})
    return {"facts": out, "notes": notes, "contested": contested}


# ---------------------------------------------------------------- reasoning

def closure(snapshot_facts: list[dict], tbox: Graph) -> tuple[Graph, dict]:
    """Returns (closure graph, asserted triple -> source)."""
    g = Graph()
    asserted = {}
    for t in tbox:
        g.add(t)
        asserted.setdefault(t, {"source": "ontology"})
    for f in snapshot_facts:
        t = triple(f)
        g.add(t)
        asserted[t] = {"source": "fact", "id": f["id"], "doc": f["doc"], "quote": f["quote"]}
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(g)
    return g, asserted


def check(g: Graph, shapes: Graph) -> list[dict]:
    """One item per (shape, focus node): severity, message, evidence triples."""
    _, report, _ = pyshacl.validate(g, shacl_graph=shapes, inference="none", advanced=True)
    items = {}
    for r in report.subjects(RDF.type, SH.ValidationResult):
        shape, focus = report.value(r, SH.sourceShape), report.value(r, SH.focusNode)
        if not isinstance(shape, URIRef):
            continue
        evidence = set()
        q = shapes.value(shape, CC.evidence)
        if q is not None:
            evidence = {t for t in g.query(str(q), initBindings={"this": focus}) if t in g}
        items[(shape, focus)] = {
            "type": shape.split("#")[1], "focus": focus.split("#")[1],
            "severity": report.value(r, SH.resultSeverity).split("#")[1],
            "derivation": str(shapes.value(shape, CC.derivation)),
            "message": str(report.value(r, SH.resultMessage)),
            "evidence": evidence,
        }
    return sorted(items.values(), key=lambda i: (i["severity"], i["type"]))


# -------------------------------------------------------------- explanation

class Explainer:
    """Backward proof search over the closure, generic in the TBox.

    For a triple t in the closure: if t is asserted it is a leaf. Otherwise try
    every OWL 2 RL rule that could have produced it (inverse, sub-property,
    transitivity, property chain, sub-class, domain, range), require each
    premise to be in the closure, and recurse. Iterative deepening returns a
    shallowest proof. No per-axiom templates: adding an axiom to the ontology
    needs no change here.
    """

    def __init__(self, tbox: Graph, g: Graph, asserted: dict):
        self.g, self.asserted = g, asserted
        self.inv, self.subp, self.subc = defaultdict(set), defaultdict(set), defaultdict(set)
        self.dom, self.rng, self.chains = defaultdict(set), defaultdict(set), defaultdict(list)
        for a, b in tbox.subject_objects(OWL.inverseOf):
            self.inv[a].add(b)
            self.inv[b].add(a)
        for a, b in tbox.subject_objects(RDFS.subPropertyOf):
            self.subp[b].add(a)
        for a, b in tbox.subject_objects(RDFS.subClassOf):
            self.subc[b].add(a)
        for p, c in tbox.subject_objects(RDFS.domain):
            self.dom[c].add(p)
        for p, c in tbox.subject_objects(RDFS.range):
            self.rng[c].add(p)
        for p, lst in tbox.subject_objects(OWL.propertyChainAxiom):
            self.chains[p].append(list(Collection(tbox, lst)))
        self.trans = set(tbox.subjects(RDF.type, OWL.TransitiveProperty))

    def _paths(self, s, props, o):
        if len(props) == 1:
            if (s, props[0], o) in self.g:
                yield [(s, props[0], o)]
            return
        for mid in self.g.objects(s, props[0]):
            for rest in self._paths(mid, props[1:], o):
                yield [(s, props[0], mid)] + rest

    def _candidates(self, t):
        s, p, o = t
        if p == RDF.type:
            for d in self.subc[o]:
                if (s, RDF.type, d) in self.g:
                    yield f"sub-class {q(d)} ⊑ {q(o)}", [(s, RDF.type, d)]
            for prop in self.dom[o]:
                for y in self.g.objects(s, prop):
                    yield f"domain of {q(prop)}", [(s, prop, y)]
            for prop in self.rng[o]:
                for x in self.g.subjects(prop, s):
                    yield f"range of {q(prop)}", [(x, prop, s)]
            return
        for chain in self.chains[p]:
            for path in self._paths(s, chain, o):
                yield "chain " + " ∘ ".join(q(c) for c in chain), path
        for inv in self.inv[p]:
            if (o, inv, s) in self.g:
                yield f"inverse of {q(inv)}", [(o, inv, s)]
        for sub in self.subp[p]:
            if (s, sub, o) in self.g:
                yield f"sub-property {q(sub)}", [(s, sub, o)]
        if p in self.trans:
            for mid in self.g.objects(s, p):
                if mid not in (s, o) and (mid, p, o) in self.g:
                    yield f"transitivity of {q(p)}", [(s, p, mid), (mid, p, o)]

    def _prove(self, t, depth, stack):
        if t in self.asserted:
            return {"triple": t, "leaf": self.asserted[t]}
        if depth == 0 or t in stack:
            return None
        for rule, premises in self._candidates(t):
            subs = [self._prove(pr, depth - 1, stack | {t}) for pr in premises]
            if all(subs):
                return {"triple": t, "rule": rule, "premises": subs}
        return None

    def explain(self, t, max_depth=8):
        assert t in self.g, f"not in closure: {t}"
        for depth in range(max_depth + 1):
            proof = self._prove(t, depth, frozenset())
            if proof:
                return proof
        return None


def q(x) -> str:
    if isinstance(x, Literal):
        return json.dumps(x.toPython())
    if x == RDF.type:
        return "a"
    return str(x).split("#")[-1]


def leaves(proof) -> list[dict]:
    if "leaf" in proof:
        return [proof["leaf"]]
    return [leaf for p in proof["premises"] for leaf in leaves(p)]


def render(proof, indent=0) -> str:
    s, p, o = proof["triple"]
    head = "  " * indent + f"{q(s)} {q(p)} {q(o)}"
    if "leaf" in proof:
        src = proof["leaf"]
        tail = f"   [{src['doc']}: \"{src['quote']}\"]" if src["source"] == "fact" else "   [ontology]"
        return head + tail
    return "\n".join([head + f"   ⊢ {proof['rule']}"] + [render(p, indent + 1) for p in proof["premises"]])
