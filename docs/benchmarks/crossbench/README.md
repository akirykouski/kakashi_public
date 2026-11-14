# Cross-benchmark of the two reasoning cores (14 Nov 2026, morning)

Results only. The runners, encoders and engine copies stay outside this repo.

| Folder | What ran | Gold |
|---|---|---|
| `arseniy_on_both/` | Core A on A's 20 change requests | A's `data/eval/gold.jsonl` |
| `maksim_on_arseniy/` | Core M on A's 20 change requests | A's gold |
| `arseniy_on_maksim/` | Core A on 10 of M's 36 requests (2 per category) | M's `bench/requests.jsonl` |
| `REVIEW.md` | Independent review (Claude Fable 5) of both cores and the three runs, with a merge plan | — |

Each engine ran unchanged, with requests parsed by hand (no LLM). Worlds were encoded by third-party agents; every quote checked as a literal substring of its source. Each author wrote his own gold, and both encoders saw some gold: read the numbers as a list of gaps, not a ranking. Summary: `SUMMARY.md`.
