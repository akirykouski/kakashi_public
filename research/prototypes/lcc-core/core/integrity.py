"""Validate the current memory graph against ontology/shapes.ttl with pySHACL.

  python core/integrity.py [--as-of 2026-11-14]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyshacl import validate  # noqa: E402
from rdflib import Graph  # noqa: E402

from factlog import default_log  # noqa: E402
from project import ROOT, Projection  # noqa: E402

SHAPES_PATH = os.path.join(ROOT, "ontology", "shapes.ttl")


def run(projection):
    shapes = Graph()
    shapes.parse(SHAPES_PATH, format="turtle")
    started = time.time()
    conforms, _, text = validate(projection.graph, shacl_graph=shapes, advanced=True, inference="none")
    return conforms, text, (time.time() - started) * 1000


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
