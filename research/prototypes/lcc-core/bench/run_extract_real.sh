#!/bin/sh
cd "$(dirname "$0")/.."
uv run -q --python 3.12 --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 --with pyyaml --with rank-bm25 python -I bench/extract_real.py
echo "exit=$?"
