"""Two-span quotes: context_quote + quote, both verbatim, context before quote within 1500 characters."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "data"))

from extract import check_fact  # noqa: E402

DOC = "Intro.\n\nThe following changes   require Adient approval:\n- Change in sub-supplier\n- Change of site\n"
PREDICATES = {"requiresCustomerApprovalFor"}
IDS = {"DOC", "SourceChange"}


def fact(**extra):
    return {"s": "DOC", "p": "requiresCustomerApprovalFor", "o": "SourceChange",
            "quote": "Change in sub-supplier", **extra}


def test_context_and_quote_both_verbatim_pass():
    checked, reason = check_fact(fact(context_quote="The following changes require Adient approval:"),
                                 DOC, PREDICATES, IDS)
    assert reason is None
    assert checked["context_quote"] == "The following changes   require Adient approval:"  # document's own text


def test_invented_context_is_rejected():
    _, reason = check_fact(fact(context_quote="All changes require approval:"), DOC, PREDICATES, IDS)
    assert reason == "context quote not found in document"


def test_context_after_quote_is_rejected():
    _, reason = check_fact(fact(context_quote="Change of site"), DOC, PREDICATES, IDS)
    assert reason and reason.startswith("context quote not before quote")


def test_context_too_far_before_quote_is_rejected():
    doc = "Rule: approval needed.\n\n" + "filler. " * 400 + "\n- Change in sub-supplier\n"
    _, reason = check_fact(fact(context_quote="Rule: approval needed."), doc, PREDICATES, IDS)
    assert reason and reason.startswith("context quote not before quote")


def test_context_outside_chunk_is_rejected():
    scope = DOC[DOC.index("- Change in"):]
    _, reason = check_fact(fact(context_quote="The following changes require Adient approval:"),
                           DOC, PREDICATES, IDS, scope=scope)
    assert reason and reason.startswith("context quote not before quote")


def test_no_context_unchanged():
    checked, reason = check_fact(fact(), DOC, PREDICATES, IDS)
    assert reason is None and "context_quote" not in checked


def test_context_running_into_quote_passes():
    doc = "7.1 The supplier shall obtain written approval after any of: a change of source, a change of material."
    checked, reason = check_fact(fact(quote="a change of source",
                                      context_quote="7.1 The supplier shall obtain written approval after any of:"),
                                 doc, PREDICATES, IDS)
    assert reason is None and checked["context_quote"].endswith("any of:")
