# Fix 6: table-aware document conversion (EXTRACTION_real.md, finding 5)

## What changed
- `data_real/tables.py` (new): per PDF page, pdfplumber finds ruled tables. Pages without a table keep the pdftotext text unchanged. On pages with one, each table row becomes ONE line `| cell | cell | ... |` under a header line (`| Area | Object of Change | Item | Example | Application to Astemo |`, legend line below it). Vertically merged cells are carried down, a cell holding numbered items `(1)..(n)` is split into one row per item, and the marker column is repeated on every item row. Text outside the table comes from pdfplumber.
- `data_real/build_docs.py`: Adient manual and Astemo guidebook go through it (`TABLE_AWARE`). The Adient letter and the Ford report stay on plain pdftotext (their tables are forms, not matrices). Rebuild: `uv run --with pdfplumber python -I data_real/build_docs.py`.
- The converted text is the stored document, so every quote is verbatim against it (`extract.py` unchanged).
- `bench/llm.py`: accepts the CLI's JSON-array output (takes the `result` event). `bench/run_extract_real.sh`: `cd` to the repo it lives in, not the main checkout.

## Result on the Astemo matrix (guidebook pages 15 to 17)
Before: pdftotext detached the markers (`○`, `＊○`, `－`) from their rows; the extractor read the list as requirements. After: 77 table lines in the Astemo doc (50 in the Adient manual), e.g. `| Other | Tier 2, 3 and subsequent suppliers | | (2) Change of Tier 2, 3 and subsequent suppliers (...) | ○ |`; 32 rows end in `○` or `＊○`, 12 in `－`.
Extractor, fresh run: 4 Astemo facts kept, all 4 from rows marked `○` (Tier 2/3 supplier change, Material, Production method, Packaging); 0 from `－` or `＊○` rows. The marker column was read correctly. Limit: the model still quotes the Example cell, not the whole row, so the stored quote does not contain the marker (the prompt asks for the shortest span; not changed here).

## Numbers (real docs, fresh, run A registry; one run, model nondeterminism applies)
| Metric | Before | After |
|---|---|---|
| Kept | 12 | 11 (Adient manual 2, letter 5, Astemo 4, Ford 0) |
| Review share | 4 of 16 (25%), all Ford | 4 of 15 (27%), all Ford |
| Wrong (strict audit, one auditor) | 0 | 0 |
| Partial | 1 | 1 to 2 (letter Packaging and Schedule share one quote; manual Process fact quotes "all product or process changes" but stores ProcessChange only) |
| Recall, 10 rules | 5 of 10 | 5 of 10 (gained #3, the general rule, now quoted as the full sentence; lost #7 Material/PPAP) |

Astemo rows read correctly: 4 of 4 kept facts. Adient manual tables (contents, MQR levels, containment) are rendered as rows too; no fact depends on them.

## Synthetic traps (bench/extract_eval.py, data_long, fresh)
Precision 0.94 (33 of 35 found, 2 wrong extra), recall 0.94, traps 0 of 15 taken (baseline 0.97 / 0.91 / 0). Unaffected by design: `data_long` does not go through `build_docs.py` and `extract.py` is untouched; the delta is model run-to-run noise (one fact either way). Tracked outputs of extract_eval were reverted after reading.

## Checks
`pytest tests -q`: 15 passed. `core/check.py --scenario main | main_after_audit | elv | silence`: exit 0, 0, 0, 0.

## Not done
- The quote is still a fragment, not the full row (prompt change, separate fix).
- pdfplumber is a new dependency of `build_docs.py` only, not of the product pipeline. Unruled or scanned tables are not detected; Ford and the letter are untouched.
- One auditor, 4 documents, one run.
