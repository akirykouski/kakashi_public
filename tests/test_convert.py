"""Table-aware conversion (core/convert.py). Pure table rendering runs everywhere; the PDF round trip needs the
optional pdfplumber (and reportlab to draw a synthetic PDF) and is skipped without them."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))

from convert import render_table, split_items, to_document  # noqa: E402
from extract import find_quote  # noqa: E402


def test_one_line_per_row_with_merged_cells_carried_down():
    rows = [["Change", "Approval", "Notice"],
            ["Change of sub-supplier", "X", "90 days"],
            ["Change of tooling", None, None],
            ["", "", ""]]
    assert render_table(rows) == ["| Change | Approval | Notice |",
                                  "| Change of sub-supplier | X | 90 days |",
                                  "| Change of tooling | X | 90 days |"]


def test_numbered_items_split_and_marker_repeated():
    rows = [["Situation", "Notify"],
            ["(1) New tooling\nor fixtures\n(2) Change of site", "X"],
            ["(3) Price", ""]]
    lines = render_table(rows)
    assert "| (1) New tooling or fixtures | X |" in lines and "| (2) Change of site | X |" in lines


def test_not_a_table():
    assert render_table([["a", "b"], ["c", "d"]]) is None
    assert render_table([["a"], ["b"], ["c"]]) is None
    assert split_items("plain cell") == ["plain cell"]


def test_row_is_quotable_by_extractor():
    lines = render_table([["Change", "Approval"], ["Change of sub-supplier", "X"], ["Change of site", "X"]])
    document = to_document("Section 5\n\f" + "\n".join(lines), "DOC-T", "customer_requirement", "T", "2026-11-01")
    assert document.startswith("---\nid: DOC-T\n")
    assert find_quote(document, "| Change of sub-supplier | X |") is not None


def test_pdf_round_trip(tmp_path):
    pytest.importorskip("pdfplumber")
    pytest.importorskip("reportlab")
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from convert import convert
    path = str(tmp_path / "t.pdf")
    table = Table([["Change", "Approval"], ["Change of sub-supplier", "X"], ["Change of site", "X"]])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, "black")]))
    SimpleDocTemplate(path, pagesize=A4).build([Paragraph("The following changes need approval.",
                                                          getSampleStyleSheet()["Normal"]), table])
    text = convert(path)
    assert "| Change of sub-supplier | X |" in text and "The following changes need approval." in text
