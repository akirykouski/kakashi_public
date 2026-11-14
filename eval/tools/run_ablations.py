"""Ablations of methodology §4 on C* (hand parse -> core), one component switched off at a time.

    python eval/tools/run_ablations.py --out eval/results/frozen_ablations

  no_inference   Projection(reason=False): direct facts only, no OWL 2 RL closure (no property chains,
                 inverse or transitive properties).
  no_supersession every fact ever recorded stays in force: `supersedes` facts and columns and valid_to are
                 dropped before the snapshot, and no single-valued predicate is resolved.
  no_questions   a question is read as "no blocker": question findings are dropped from the answer.

Switches are applied in this process only (wrappers around core functions); no core file is changed.
Output files are named <world>_Cstar.jsonl inside one directory per ablation, so score.py reads them as is.
"""
import argparse
import functools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_core  # noqa: E402

EVAL = run_core.EVAL


def strip_supersession(facts):
    kept = []
    for fact in facts:
        if fact["p"] == "supersedes":
            continue
        kept.append(dict(fact, valid_to=None, supersedes=None))
    return kept


def apply(ablation):
    from core import check, project, rules
    original_projection = project.Projection
    if ablation == "no_inference":
        check.Projection = functools.partial(original_projection, reason=False)
        rules_projection = check.Projection
    elif ablation == "no_supersession":
        original_snapshot = project.take_snapshot

        def snapshot_without_supersession(facts, as_of, known_at=None, functional=frozenset()):
            return original_snapshot(strip_supersession(facts), as_of, known_at, frozenset())
        project.take_snapshot = snapshot_without_supersession
        rules_projection = original_projection
    else:
        rules_projection = original_projection
    return rules_projection


def run(ablation, out_root):
    out = out_root / ablation
    out.mkdir(parents=True, exist_ok=True)
    rules_projection = apply(ablation)
    from core import rules
    for world in ("M", "A"):
        gold = run_core.load_jsonl(EVAL / "gold" / f"{world}.jsonl")
        run_core.use_world(world, [item["as_of"] for item in gold])
        from core import check
        rules._projections.clear()
        for as_of in sorted({item["as_of"] for item in gold}):
            rules._projections[as_of] = rules_projection(check._LOG, as_of)
        hand = {row["id"]: row for row in run_core.load_jsonl(EVAL / "parses" / f"{world}_hand.jsonl")}
        results = [run_core.run_one(world, "Cstar", item, hand, None, None) for item in gold]
        if ablation == "no_questions":
            for row in results:
                row["findings"] = [item for item in row["findings"] if item["kind"] != "question"]
        with open(out / f"{world}_Cstar.jsonl", "w") as file:
            for row in results:
                file.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(ablation, world, "errors", sum(1 for row in results if row["error"]), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--ablation", required=True, choices=["no_inference", "no_supersession", "no_questions"])
    args = parser.parse_args()
    run(args.ablation, Path(args.out))


if __name__ == "__main__":
    main()
