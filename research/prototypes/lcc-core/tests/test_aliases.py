"""Alias grounding and the onboarding helper. Run: python -m pytest tests/ -q"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))

from aliases import candidates, pending, recheck  # noqa: E402
from extract import grounded, grounding_aliases, grounding_names  # noqa: E402

REGISTRY = {
    "parts": {"columns": ["id", "name"], "rows": [["PART-X", "Driver airbag cover"]]},
    "suppliers": {"columns": ["id", "name"], "rows": [["SUP-DEMO", "DEMO, Tier 3 supplier"]],
                  "aliases": {"SUP-DEMO": ["DEMO"]}},
}
QUOTE = "the Tier 3 supplier (DEMO) made adjustments"


def test_id_name_rule_unchanged_without_alias():
    names = grounding_names({k: {"rows": v["rows"]} for k, v in REGISTRY.items()})
    assert not grounded("SUP-DEMO", QUOTE, names)
    assert grounded("SUP-DEMO", "see SUP-DEMO here", names)


def test_alias_is_case_insensitive_whole_word_only():
    names, aliases = grounding_names(REGISTRY), grounding_aliases(REGISTRY)
    assert grounded("SUP-DEMO", QUOTE, names, aliases)
    assert grounded("SUP-DEMO", "demo made changes", names, aliases)
    assert not grounded("SUP-DEMO", "a demonstration run", names, aliases)  # no fuzzy / substring match
    assert not grounded("SUP-DEMO", "the Tier 3 supplier made changes", names, aliases)


def test_alias_does_not_ground_other_entities():
    registry = {**REGISTRY, "parts": {**REGISTRY["parts"], "rows": REGISTRY["parts"]["rows"]}}
    assert not grounded("PART-X", QUOTE, grounding_names(registry), grounding_aliases(registry))


def test_candidates_and_recheck():
    registry = {k: {kk: vv for kk, vv in v.items() if kk != "aliases"} for k, v in REGISTRY.items()}
    assert "DEMO" in candidates(registry, "SUP-DEMO", QUOTE)
    result = {"accepted": [], "review": [{"s": "D", "p": "concernsSupplier", "o": "SUP-DEMO", "quote": QUOTE,
                                          "reason": "ungrounded: quote does not name SUP-DEMO"}]}
    assert len(list(pending([("p", result)]))) == 1
    assert recheck(registry, [("p", result)]) == [] and len(result["review"]) == 1
    registry["suppliers"]["aliases"] = {"SUP-DEMO": ["DEMO"]}
    assert len(recheck(registry, [("p", result)])) == 1
    assert result["review"] == [] and result["accepted"][0]["o"] == "SUP-DEMO"
    assert "reason" not in result["accepted"][0]
    json.dumps(result)
