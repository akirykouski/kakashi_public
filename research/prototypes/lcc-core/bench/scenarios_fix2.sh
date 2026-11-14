#!/bin/sh
# Run the four check.py scenarios in a tree; print exit code and sorted (severity, rule) pairs.
# usage: sh bench/scenarios_fix2.sh <tree-root>
cd "$1" || exit 1
for S in main main_after_audit elv silence; do
  OUT=$(uv run -q --python 3.12 --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 --with pyyaml --with rank-bm25 python core/check.py --scenario $S --json)
  CODE=$?
  echo "$S exit=$CODE"
  printf "%s" "$OUT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(sorted((f["severity"],f["rule"]) for f in d["findings"]))'
done
