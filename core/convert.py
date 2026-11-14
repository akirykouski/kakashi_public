"""PDF -> text for extract.py, table-aware. pdfplumber is an optional dependency (pip install pdfplumber).

  python core/convert.py manual.pdf --id CSR-X --type customer_requirement --title "..." --valid-from 2026-01-01

Pages without a real table keep their plain text unchanged. On a page with one, each table row becomes ONE line
"| cell | cell | ... |" under a header line (merged cells carried down, numbered list cells split into one row
per item, marker columns repeated on every item), so a quote of the row holds the marker and passes the verbatim
quote check of extract.py. Text outside the tables comes from pdfplumber.

Ported from research/prototypes/data_real/tables.py (fix/6-tables). Changed: pdfplumber imported lazily; the plain
text may be given (pdftotext output, pages split by form feed) or is taken from pdfplumber; to_document() wraps the
text in the front matter extract.read_document() expects (from research/prototypes/data_real/build_docs.py).
"""
import argparse
import json
import re

ITEM = re.compile(r"^\(\d+\)")


def require_pdfplumber():
    try:
        import pdfplumber
    except ImportError as error:  # optional dependency
        raise ImportError("core/convert.py needs pdfplumber for PDF input: pip install pdfplumber") from error
    return pdfplumber


def clean(cell):
    return re.sub(r"\s+", " ", cell or "").strip()


def label(cell):
    """Column label: header lines up to the first legend or example line (starts with '(' or holds ':' or a marker)."""
    kept = []
    for line in (cell or "").split("\n"):
        if kept and (line.strip().startswith("(") or ":" in line or "＊" in line):
            break
        kept.append(line.strip())
    return clean(" ".join(kept))


def split_items(cell):
    """'(1) a\\ncont\\n(2) b' -> ['(1) a cont', '(2) b']; a cell without numbered items -> [cell]."""
    lines = (cell or "").split("\n")
    if sum(1 for line in lines if ITEM.match(line.strip())) < 2:
        return [clean(cell)]
    items = []
    for line in lines:
        if ITEM.match(line.strip()) or not items:
            items.append(line.strip())
        else:
            items[-1] += " " + line.strip()
    return [clean(item) for item in items]


def render_table(rows):
    """rows: pdfplumber extract() output. Returns a list of lines, or None when this is not a data table."""
    rows = [row for row in rows if any(cell and cell.strip() for cell in row)]
    if len(rows) < 3 or max(len(row) for row in rows) < 2:
        return None
    legend = [clean(cell) for cell in rows[0] if cell and "\n" in cell and ":" in cell.split("\n", 1)[1]]
    labels = [label(cell) for cell in rows[0]]
    out = ["| " + " | ".join(labels) + " |"]
    if legend:
        out.append("Legend: " + " ".join(legend))
    carry = [None] * len(labels)
    for row in rows[1:]:
        row = list(row) + [None] * (len(labels) - len(row))
        cells = []
        for index, cell in enumerate(row[:len(labels)]):
            if cell is None:
                cell = carry[index]  # vertically merged cell: the value above applies here too
            else:
                carry[index] = cell
            cells.append(cell)
        parts = [split_items(cell) for cell in cells]
        count = max(len(part) for part in parts)
        for k in range(count):
            values = [part[k] if len(part) == count else (part[0] if len(part) == 1 else part[min(k, len(part) - 1)])
                      for part in parts]
            out.append("| " + " | ".join(values) + " |")
    return out


def page_text(page, plain):
    """Text of one page. `plain` is the plain text of the same page, returned unchanged when no table is found."""
    found = []
    for table in page.find_tables():
        x0, top, x1, bottom = table.bbox
        if (x1 - x0) * (bottom - top) > 0.8 * page.width * page.height:
            continue  # page frame
        lines = render_table(table.extract())
        if lines:
            found.append((table.bbox, lines))
    if not found:
        return plain

    def outside(obj):
        for x0, top, x1, bottom in (bbox for bbox, _ in found):
            if obj["x0"] >= x0 - 1 and obj["x1"] <= x1 + 1 and obj["top"] >= top - 1 and obj["bottom"] <= bottom + 1:
                return False
        return True

    text = (page.filter(outside).extract_text() or "").rstrip()
    blocks = ["\n".join(lines) for _, lines in sorted(found, key=lambda item: item[0][1])]
    return text + "\n\n" + "\n\n".join(blocks) + "\n"


def convert(pdf_path, plain_text=None):
    """PDF -> text, pages joined by a form feed. `plain_text`: pdftotext output of the same file (pages split by
    form feed); without it each page's plain text comes from pdfplumber."""
    pdfplumber = require_pdfplumber()
    plain_pages = plain_text.split("\f") if plain_text is not None else None
    with pdfplumber.open(pdf_path) as pdf:
        pages = []
        for index, page in enumerate(pdf.pages):
            if plain_pages is None:
                plain = page.extract_text() or ""
            else:
                plain = plain_pages[index] if index < len(plain_pages) else ""
            pages.append(page_text(page, plain))
    return "\f".join(pages)


def to_document(text, doc_id, doc_type, title, valid_from, author="", supersedes=None, valid_to=None):
    """Wrap converted text in the front matter extract.read_document() expects. Form feeds become blank lines."""
    head = ["---", f"id: {doc_id}", f"type: {doc_type}", f"title: {json.dumps(title)}", f"date: '{valid_from}'",
            f"author: {json.dumps(author)}", f"valid_from: '{valid_from}'",
            f"valid_to: {json.dumps(valid_to) if valid_to else 'null'}",
            f"supersedes: {supersedes or 'null'}", "---", ""]
    return "\n".join(head) + text.replace("\f", "\n\n")


def main():
    parser = argparse.ArgumentParser(description="Table-aware PDF to extractor input.")
    parser.add_argument("pdf")
    parser.add_argument("--plain", help="pdftotext output of the same PDF (optional)")
    parser.add_argument("--id", required=True)
    parser.add_argument("--type", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--valid-from", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--supersedes")
    args = parser.parse_args()
    plain = open(args.plain, encoding="utf-8").read() if args.plain else None
    print(to_document(convert(args.pdf, plain), args.id, args.type, args.title, args.valid_from, args.author,
                      args.supersedes))


if __name__ == "__main__":
    main()
