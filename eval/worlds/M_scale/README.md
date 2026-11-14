# World M at 8× size (H3)

World M grown with distractor suppliers, parts, programs and documents by the pre-event generator `data/scale.py` (private repo, `--units 90`, output `data_scale/` at commit in `../SOURCE.txt`). Distractors never touch the entities of the 36 requests, so the gold is `eval/gold/M.jsonl` unchanged. Size: corpus 219,880 vs 27,009 bytes (8.1×), facts 4,718 vs 510 (9.3×).

`core/facts.jsonl`: the 510 frozen world-M facts in the core's encoding, plus the 4,208 distractor facts converted to the core's row format (kind assert, rank 2).
