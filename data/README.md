# Valsangone: the synthetic company (workstream F)

Fictional tier-1 supplier near Turin that machines aluminium brackets (BR-220, BR-310, CL-115...) for two
fictional customers, Aurelia Automobili and Nordhavn Trucks. All companies, people, parts and documents are
invented; IATF 16949 and AIAG PPAP are cited by clause number only, never quoted.

- `world.py` (registries + documents), `meetings.py` (past meetings): the source of truth.
- `build.py` renders `registry/*.csv`, `docs/*.md`, `meetings/*.json`, `facts.jsonl`, `corpus.jsonl`, `registries.json`.
  Every fact carries `kind` (assert | mention; e-mail content is a mention), `rank` (1 law/customer requirement,
  2 controlled record, 3 informal) and `epistemic` (the earlier evidence/decision/constraint label).
- `validate_world.py`: every quote is a substring of its source, every id exists.
- `scenarios.json`: the five demo checks (`main`, `main_after_audit`, `elv`, `silence`, `subtier`).

Includes Arseniy's fix/4 (customer-stated consequence in CSR-AUR-R4) and fix/8 (sub-tier chain:
SUBLIST-B, SUBLIST-C, CSR-AUR-S1, QP-14, sub-tier suppliers in the registry).

Regenerate: `python data/build.py && python data/validate_world.py`.
