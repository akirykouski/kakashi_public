#!/bin/sh
# One change-type vocabulary size with a fresh cache: real documents, then synthetic traps (extraction scoring only).
# usage: sh bench/run_fix2.sh 1|2|3|2n|3n
L=$1
cd "$(dirname "$0")/.."
export CHANGE_VOCAB=${L%n}
export CHANGE_NOTICE=1
case $L in *n) export CHANGE_NOTICE=0;; esac  # "2n" = size 2 without the notice predicates
export LLM_CACHE_DIR=${TMPDIR:-/tmp}/fix2_cache_$L
export OUT_DIR=bench/results/fix2/real_$L
export RESULTS_SUFFIX=_fix2_$L
export EXTRACT_ONLY=1
rm -rf "$LLM_CACHE_DIR"
PY="uv run -q --python 3.12 --with rdflib==7.6.0 --with owlrl==7.6.2 --with pyshacl==0.40.2 --with pyyaml --with rank-bm25 --with pytest python"
$PY -I bench/extract_real.py
echo "real exit=$?"
$PY bench/extract_eval.py
echo "long exit=$?"
