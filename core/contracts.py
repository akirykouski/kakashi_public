"""Shared data contracts of the product core.

Every module of `core/` reads and writes these shapes. They are plain dicts (JSON-ready) so the web page,
the evaluation harness and the CLI use the same objects. The dataclasses below document the shape and
build the dicts; nothing else in the core should invent new top-level keys.

Written 14 Nov 2026 after 10:30. Design: docs/architecture.md.
"""
from dataclasses import asdict, dataclass, field
from typing import Optional

# ---- change classes ------------------------------------------------------------------------------------
# One taxonomy for the whole product. Customer approval and certificate checks key on these classes, never
# on "a new supplier is present". Names match ontology class local names (lcc:<Name>).
CHANGE_TYPES = (
    "SourceChange", "SubTierSupplierChange", "LocationChange", "ShippingLocationChange",
    "MaterialChange", "CoatingChange", "SpecialProcessChange", "ProcessChange", "EquipmentChange",
    "ToolingChange", "TestMethodChange", "SoftwareChange", "DesignChange", "PackagingChange",
    "ProductionResumptionChange", "ScheduleChange", "PriceChange",
)

# ---- OIDA epistemic types (docs/research/kva-oida-hooks.md 4.1) ------------------------------------------
# Read from the lcc:epistemicType annotation of a record's class in ontology/lcc.ttl; None when no class says.
EPISTEMIC_TYPES = ("CONSTRAINT", "DECISION", "EVIDENCE", "PLAN", "QUESTION")

# ---- outcomes ------------------------------------------------------------------------------------------
SEVERITIES = ("blocker", "warning", "question", "info")
VERDICTS = (
    "blockers_found",      # at least one blocker
    "needs_info",          # no blocker, at least one open question
    "no_blockers_found",   # rules that cover this change ran and none fired. Never "approved".
    "not_covered",         # no rule covers this change class or scope: a person decides (row R0)
)


@dataclass
class ChangeRequest:
    """A proposed change, parsed from a meeting remark or typed in a form."""
    type: str                                  # one of CHANGE_TYPES
    part: str                                  # part id, e.g. "BR-220"
    to_supplier: Optional[str] = None          # supplier id of the proposed source
    from_supplier: Optional[str] = None
    site: Optional[str] = None                 # receiving plant id
    at_supplier: Optional[str] = None          # sub-tier: the supplier where the change happens (rule R8)
    new_material: Optional[str] = None
    new_coating: Optional[str] = None
    scope: str = "series"                      # series | service
    as_of: Optional[str] = None                # ISO date the check is made for; default today
    utterance: Optional[str] = None            # the meeting remark, verbatim, if any
    speaker: Optional[str] = None
    parse_confidence: Optional[float] = None   # set by the parser; None for a typed form
    unresolved: list = field(default_factory=list)  # names the parser could not map to ids
    epistemic: Optional[str] = None            # set on the card: "PLAN" (derived; ignored on input)

    def to_dict(self):
        return {key: value for key, value in asdict(self).items() if value not in (None, [])}


@dataclass
class EvidenceStep:
    """One step of a proof chain. Leaves carry a verbatim quote; inferred steps carry their premises."""
    triple: str                                # "BR-220 subjectTo CSR-AUR-R4"
    inferred: bool
    source: Optional[str] = None               # document id
    quote: Optional[str] = None                # verbatim span in that document
    context_quote: Optional[str] = None        # governing sentence above a list item (two-span quotes)
    fact_id: Optional[str] = None
    rule: Optional[str] = None                 # axiom or rule that produced an inferred step
    premises: list = field(default_factory=list)  # list of EvidenceStep dicts
    epistemic: Optional[str] = None            # leaves: OIDA type of the record's class (else of the source)


@dataclass
class Finding:
    rule: str                                  # rule id, e.g. "R2"
    severity: str                              # one of SEVERITIES
    title: str
    evidence: list                             # list of EvidenceStep dicts
    entities: list                             # ids the finding is about
    owner: Optional[str] = None                # person or role who answers a question
    note: Optional[str] = None                 # e.g. "CSR-AUR-R4 supersedes CSR-AUR-R3"
    consequence: Optional[dict] = None         # customer's stated consequence {type, source, quote}
    # OIDA (core/oida.py), set by check.run; all optional
    epistemic: Optional[str] = None            # one of EPISTEMIC_TYPES; "QUESTION" for every question
    blocks: Optional[dict] = None              # questions: {"part", "change_type"} the question holds up
    urgency: Optional[float] = None            # questions: clamp(age/30*0.3 + blocking_edges*0.2 + stakes*0.5)
    stakes: Optional[float] = None             # questions: from rules_data/oida_stakes.json
    age_days: Optional[int] = None             # questions: days since the latest dated evidence, else 0
    blocking_edges: Optional[int] = None       # questions: blocker findings on the same card


@dataclass
class DecisionRow:
    """The matched row of the decision table."""
    row_id: str                                # e.g. "D3"; "R0" = no rule covers this
    allowed_actions: list                      # e.g. ["request customer deviation", "expedite current source"]
    decider: str                               # role who decides
    rests_on: list                             # rule ids / requirement ids the row cites


@dataclass
class Card:
    """What the page shows for one check."""
    request: dict                              # ChangeRequest dict
    verdict: str                               # one of VERDICTS
    findings: list                             # Finding dicts, blockers first
    not_checked: list                          # requirements in scope the ontology cannot express
    decision: dict                             # DecisionRow dict
    coverage: dict                             # {"input_sets": int, "to_person": int, "overlaps": int}
    record_id: str                             # id of the DecisionRecord written for this check
    timings_ms: dict                           # {"snapshot": .., "closure": .., "rules": .., "total": ..}
    # #28, optional: two current values side by side. Each item: {key: [s, p] | record, reason, question,
    # owner, sides: [{value, fact_id | record, source, quote, rank, valid_from, status}]}
    contested: list = field(default_factory=list)


@dataclass
class DecisionRecord:
    """Append-only audit record: why this answer, under which rules."""
    record_id: str
    created_at: str                            # ISO timestamp, UTC
    request: dict
    as_of: str
    rules_version: str                         # sha256 of ontology files + decision table + rules module
    facts_in_force: list                       # fact ids used by the snapshot
    rules_fired: list                          # rule ids
    verdict: str
    decision_row: str
    decided_by: Optional[str] = None           # set when a person records the decision
