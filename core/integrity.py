"""Validate the memory graph in force against ontology/shapes.ttl with pySHACL (closed-world integrity).

Ported from research/prototypes Maksim's `core/integrity.py` (night-shift/2026-11-13-kva-plan); unchanged
except package imports and a structured result.

  python -m core.integrity [--as-of 2026-11-14]
"""
import argparse
import os
import sys
import time

from pyshacl import validate
from rdflib import Graph

try:
    from .factlog import default_log
    from .project import ROOT, Projection
except ImportError:  # run as a script from core/
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from factlog import default_log
    from project import ROOT, Projection

SHAPES_PATH = os.path.join(ROOT, "ontology", "shapes.ttl")
_shapes = {}


def shapes_graph():
    if "graph" not in _shapes:
        _shapes["graph"] = Graph().parse(SHAPES_PATH, format="turtle")
    return _shapes["graph"]


def run(projection):
    """Returns (conforms, report text, elapsed ms)."""
    started = time.perf_counter()
    conforms, _, text = validate(projection.graph, shacl_graph=shapes_graph(), advanced=True, inference="none")
    return conforms, text, (time.perf_counter() - started) * 1000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default="2026-11-14")
    args = parser.parse_args()
    projection = Projection(default_log(), args.as_of)
    conforms, text, elapsed_ms = run(projection)
    print(f"conforms={conforms} ({elapsed_ms:.0f} ms)")
    if not conforms:
        print(text)
    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
