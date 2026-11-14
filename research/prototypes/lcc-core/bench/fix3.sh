#!/bin/sh
# usage: sh bench/fix3.sh <python args...>   (run from anywhere)
cd "$(dirname "$0")/.."
exec uv run -q --python 3.12 --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 --with pyyaml --with rank-bm25 --with pytest python "$@"
