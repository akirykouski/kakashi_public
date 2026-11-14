"""Table-aware PDF to text. Pages without a real table keep their pdftotext text unchanged. On pages with one,
each table row becomes ONE line "| cell | cell | ... |" (merged cells carried down, numbered list cells split into
one row per item, marker columns repeated on every item), under a header line, so a quote of the row holds the
marker. Text outside the tables comes from pdfplumber. Needs pdfplumber; run with python -I."""
import re
import pdfplumber

ITEM = re.compile(r"^\(\d+\)")


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
    """'(1) a\ncont\n(2) b' -> ['(1) a cont', '(2) b']; a cell without numbered items -> [cell]."""
    lines = (cell or "").split("\n")
    if sum(1 for l in lines if ITEM.match(l.strip())) < 2:
        return [clean(cell)]
    items = []
    for line in lines:
        if ITEM.match(line.strip()) or not items:
            items.append(line.strip())
        else:
            items[-1] += " " + line.strip()
    return [clean(i) for i in items]


def render_table(rows):
    """rows: pdfplumber extract() output. Returns list of lines, or None when this is not a data table."""
    rows = [r for r in rows if any(c and c.strip() for c in r)]
    if len(rows) < 3 or max(len(r) for r in rows) < 2:
        return None
    legend = [clean(c) for c in rows[0] if c and "\n" in c and ":" in c.split("\n", 1)[1]]
    # short column labels: first line of the header cell
    labels = [label(c) for c in rows[0]]
    out = ["| " + " | ".join(labels) + " |"]
    if legend:
        out.append("Legend: " + " ".join(legend))
    carry = [None] * len(labels)
    for row in rows[1:]:
        row = list(row) + [None] * (len(labels) - len(row))
        cells = []
        for i, cell in enumerate(row[:len(labels)]):
            if cell is None:
                cell = carry[i]  # vertically merged cell: the value above applies here too
            else:
                carry[i] = cell
            cells.append(cell)
        parts = [split_items(c) for c in cells]
        n = max(len(p) for p in parts)
        for k in range(n):
            vals = [p[k] if len(p) == n else (p[0] if len(p) == 1 else p[min(k, len(p) - 1)]) for p in parts]
            out.append("| " + " | ".join(vals) + " |")
    return out


def page_text(page, plain):
    """Text of one page. `plain` is the pdftotext text of the same page, returned unchanged when no table is found."""
    found = []
    for tb in page.find_tables():
        x0, top, x1, bottom = tb.bbox
        if (x1 - x0) * (bottom - top) > 0.8 * page.width * page.height:
            continue  # page frame
        lines = render_table(tb.extract())
        if lines:
            found.append((tb.bbox, lines))
    if not found:
        return plain
    def outside(obj):
        for x0, top, x1, bottom in (b for b, _ in found):
            if obj["x0"] >= x0 - 1 and obj["x1"] <= x1 + 1 and obj["top"] >= top - 1 and obj["bottom"] <= bottom + 1:
                return False
        return True
    text = (page.filter(outside).extract_text() or "").rstrip()
    blocks = ["\n".join(lines) for _, lines in sorted(found, key=lambda f: f[0][1])]
    return text + "\n\n" + "\n\n".join(blocks) + "\n"


def convert(pdf_path, plain_text):
    """Joins pages with a form feed so build_docs can treat it like pdftotext output."""
    plain_pages = plain_text.split("\f")
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page_text(p, plain_pages[i] if i < len(plain_pages) else "") for i, p in enumerate(pdf.pages)]
    return "\f".join(pages)
