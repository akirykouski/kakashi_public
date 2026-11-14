"""Past meetings: the memory of why decisions were taken. Each decision carries a quote from the transcript."""

MEETINGS = [
    {
        "id": "MTG-2026-09-15",
        "title": "Change board, Pinerolo",
        "date": "2026-09-15",
        "participants": ["PER-CONTI", "PER-BIANCHI", "PER-GALLO", "PER-FERRI"],
        "utterances": [
            ["PER-GALLO", "Third porosity escape on HB-620 from Fonderia Dora this quarter, the 8D is still open."],
            ["PER-BIANCHI", "Then I revoke Dora's approval for HB-620 today and set Dora to conditional."],
            ["PER-CONTI", "Agreed. We move HB-620 to Fonderia Pellice once their audit and PPAP are through."],
            ["PER-FERRI", "Pellice can start in October if the audit passes."],
        ],
        "decisions": [
            {"id": "DEC-028", "about": ["HB-620", "SUP-D", "SUP-H"], "by": "PER-CONTI",
             "text": "Revoke SUP-D approval for HB-620, move HB-620 to SUP-H after qualification.",
             "reason": "Three porosity escapes with 8D-26-009 still open.",
             "quote": "We move HB-620 to Fonderia Pellice once their audit and PPAP are through."},
        ],
    },
    {
        "id": "MTG-2026-10-02",
        "title": "Change board, Beinasco",
        "date": "2026-10-02",
        "participants": ["PER-CONTI", "PER-BIANCHI", "PER-ROSSI", "PER-FERRI", "PER-GRECO"],
        "utterances": [
            ["PER-FERRI", "Deviation request DEV-127: Meccanica Chisone as temporary source for BR-220, six weeks."],
            ["PER-ROSSI", "Chisone is qualified for 6061-T6 and 6082-T5 only. BR-220 is drawn in 6082-T6, yield at least 250."],
            ["PER-BIANCHI", "And Chisone is conditional, the cracking 8D on their 6082 material is still open."],
            ["PER-CONTI", "Rejected. No temporary source for BR-220 without 6082-T6 capability and a closed 8D."],
            ["PER-GRECO", "Then we expedite Bormida and I tell Aurelia the plan."],
        ],
        "decisions": [
            {"id": "DEC-031", "about": ["BR-220", "SUP-C", "DEV-127"], "by": "PER-CONTI",
             "text": "Reject DEV-127. Expedite SUP-B for BR-220.",
             "reason": "SUP-C has no EN AW-6082-T6 capability and 8D-25-031 is open.",
             "quote": "Rejected. No temporary source for BR-220 without 6082-T6 capability and a closed 8D."},
        ],
    },
    {
        "id": "MTG-2026-10-20",
        "title": "Quality weekly",
        "date": "2026-10-20",
        "participants": ["PER-CONTI", "PER-GALLO", "PER-ROMANO", "PER-COSTA"],
        "utterances": [
            ["PER-GALLO", "NCR-26-017: CL-115 lot from Germanasca at 52 HRC, tolerance is 44 to 50."],
            ["PER-COSTA", "We have stock for four days."],
            ["PER-CONTI", "Block the lot, 100% hardness check on the next three lots, keep Germanasca as source."],
        ],
        "decisions": [
            {"id": "DEC-032", "about": ["CL-115", "SUP-G", "NCR-26-017"], "by": "PER-CONTI",
             "text": "Block lot 26-0412, 100% hardness check on next three lots.",
             "reason": "Hardness above tolerance, four days of stock left.",
             "quote": "Block the lot, 100% hardness check on the next three lots, keep Germanasca as source."},
        ],
    },
    {
        "id": "MTG-2026-11-06",
        "title": "Supplier quality review",
        "date": "2026-11-06",
        "participants": ["PER-BIANCHI", "PER-GALLO", "PER-ROSSI"],
        "utterances": [
            ["PER-BIANCHI", "Meccanica Chisone passed the re-audit yesterday, score 86. I set them back to approved."],
            ["PER-GALLO", "The 8D on the 6082 cracks is not closed yet, corrective action still being verified."],
            ["PER-BIANCHI", "Correct, the audit qualifies the company. Part approvals stay as they are."],
        ],
        "decisions": [
            {"id": "DEC-034", "about": ["SUP-C", "QS-C-2026"], "by": "PER-BIANCHI",
             "text": "SUP-C supplier qualification back to approved.",
             "reason": "Re-audit passed with score 86; part approvals unchanged.",
             "quote": "Meccanica Chisone passed the re-audit yesterday, score 86. I set them back to approved."},
        ],
    },
    {
        "id": "MTG-2026-11-10",
        "title": "Program review PRG-X",
        "date": "2026-11-10",
        "participants": ["PER-GRECO", "PER-FERRI", "PER-COSTA"],
        "utterances": [
            ["PER-FERRI", "Alluminio Bormida is two weeks late on BR-220 blanks, their saw line is down."],
            ["PER-COSTA", "We can run eight days on stock."],
            ["PER-GRECO", "Escalate to Bormida management today, and bring options to the change board."],
        ],
        "decisions": [
            {"id": "DEC-035", "about": ["BR-220", "SUP-B"], "by": "PER-GRECO",
             "text": "Escalate SUP-B delay; options to change board.",
             "reason": "Two-week delay against eight days of stock.",
             "quote": "Escalate to Bormida management today, and bring options to the change board."},
        ],
    },
]
