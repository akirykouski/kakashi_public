#!/usr/bin/env python3
"""Mutation tests for validate.py (stdlib unittest).

Run:  python3 data/test_validate.py     or     python3 -m unittest data.test_validate

Each test copies data/ (plus ontology/README.md, which validate.py needs) to a tempdir, applies ONE
mutation, and asserts validate.py exits 1. The pristine copy must exit 0.

Two layers are tested separately. Semantic tests run validate.py with --no-lock, so they prove the
SEMANTIC layer catches the mutation, not the hash. Lock tests (TestLock) run with the lock ON. The
"relocked" tests recompute MANIFEST.lock after the mutation (what a careless relock would do) and
assert the semantic layer still fails.
"""
import hashlib, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

DATA = Path(__file__).resolve().parent
ONTO = DATA.parent / "ontology" / "README.md"
VALIDATE = DATA / "validate.py"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kva-validate-"))
        self.d = self.tmp / "data"
        shutil.copytree(DATA, self.d, ignore=shutil.ignore_patterns("__pycache__", "test_validate.py"))
        (self.tmp / "ontology").mkdir()
        shutil.copy(ONTO, self.tmp / "ontology" / "README.md")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # helpers
    def run_validate(self, *flags, lock=False):
        """Default: --no-lock, so a failure here is the semantic layer speaking. lock=True keeps the lock ON."""
        args = list(flags) + ([] if lock or "--relock" in flags else ["--no-lock"])
        return subprocess.run([sys.executable, str(VALIDATE), *args, str(self.d)], capture_output=True, text=True)

    def raw_relock(self):
        """Rewrite MANIFEST.lock WITHOUT any semantic gate (simulates a careless human relock)."""
        files = [self.d / "README.md"] + [p for sub in ("sources", "eval") for p in sorted((self.d / sub).rglob("*")) if p.is_file()]
        lock = {p.relative_to(self.d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        (self.d / "MANIFEST.lock").write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    def assert_fails(self, needle, lock=False):
        """Exit 1 AND the specific error line is reported. A needle is mandatory: a bare exit-1 can be
        caused by an unrelated error or a crash, so a Traceback is rejected explicitly."""
        self.assertTrue(needle, "every mutation test must name the error it expects")
        r = self.run_validate(lock=lock)
        self.assertNotIn("Traceback", r.stderr, "validate.py crashed instead of reporting:\n" + r.stderr)
        self.assertEqual(r.returncode, 1, f"expected exit 1, got {r.returncode}\n{r.stdout}{r.stderr}")
        lines = [l[4:] for l in r.stdout.splitlines() if l.startswith("  - ")]
        self.assertTrue(any(needle in l for l in lines), f"no error line contains {needle!r}; got:\n" + "\n".join(lines))

    def src(self, doc): return self.d / "sources" / f"{doc}.md"
    def edit_text(self, path, old, new):
        t = path.read_text(encoding="utf-8")
        self.assertIn(old, t, f"mutation anchor missing in {path.name}")
        self.assertNotEqual(old, new)
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
    def load_gold(self):
        return [json.loads(l) for l in (self.d / "eval" / "gold.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    def save_gold(self, rows):
        (self.d / "eval" / "gold.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    def mutate_gold(self, fn):
        path = self.d / "eval" / "gold.jsonl"
        before = path.read_text(encoding="utf-8")
        rows = self.load_gold(); fn({r["id"]: r for r in rows}); self.save_gold(rows)
        self.assertNotEqual(before, path.read_text(encoding="utf-8"), "mutation was a no-op")


class TestPristine(Base):
    def test_pristine_exits_0(self):
        r = self.run_validate()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK: all checks passed", r.stdout)

    def test_pristine_exits_0_with_lock_on(self):
        r = self.run_validate(lock=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("lock: 17 files hashed", r.stdout)

    def test_missing_ontology_is_an_error_not_a_skip(self):
        (self.tmp / "ontology" / "README.md").unlink()
        self.assert_fails("ontology README unreadable")


class TestNames(Base):
    def test_M06_name_in_change_requests(self):
        self.edit_text(self.d / "eval" / "change_requests.jsonl", "Can we take", "Bosch said: can we take")
        self.assert_fails("change_requests.jsonl: forbidden real-company name Bosch")

    def test_M07_name_in_gold(self):
        self.mutate_gold(lambda g: g["CR-04"].update(note="Renault asked"))
        self.assert_fails("gold.jsonl: forbidden real-company name Renault")

    def test_M08_name_in_readme(self):
        self.edit_text(self.d / "README.md", "Fictional supplier-change scenario", "Fictional Toyota supplier-change scenario")
        self.assert_fails("README.md: forbidden real-company name Toyota")

    def test_M09_volkswagen_group_in_source(self):
        self.edit_text(self.src("CSR-STL-2026-02"), "# Customer-Specific", "# Volkswagen Group Customer-Specific")
        self.assert_fails("CSR-STL-2026-02.md: forbidden real-company name Volkswagen")

    def test_M09_other_names(self):
        names = ["Renault", "Mercedes", "Toyota", "Magna", "FCA", "Fiat", "Ford", "GM", "Bosch", "BMW",
                 "VW", "Continental", "ZF", "Valeo", "Denso", "Lear", "Faurecia", "Forvia", "Brembo", "Marelli",
                 "Tesla", "Hyundai", "Kia", "Honda", "Nissan", "Volvo", "Audi", "Porsche"]
        for n in names:
            with self.subTest(name=n):
                (self.d / "RULES-copy.txt").write_text(f"supplier {n} here\n", encoding="utf-8")
                self.assert_fails(f"RULES-copy.txt: forbidden real-company name {n}")
        (self.d / "RULES-copy.txt").write_text("Gm gmail lear magna continental\n", encoding="utf-8")
        r = self.run_validate()
        self.assertEqual(r.returncode, 0, "case-sensitive short names must not false-positive:\n" + r.stdout)


class TestGoldIntegrity(Base):
    def test_M11b_rule_not_in_allowed_set(self):
        self.mutate_gold(lambda g: g["CR-09"]["expected_blockers"][0].update(rule="B_INVENTED_RULE"))
        self.assert_fails("CR-09 blocker[0]: rule 'B_INVENTED_RULE' not in allowed set")

    def test_M13_one_char_quote(self):
        self.mutate_gold(lambda g: g["CR-09"]["expected_blockers"][0]["evidence"][0].update(quote="a"))
        self.assert_fails("CR-09 blocker[0]: quote shorter than 20 chars: 'a'")

    def test_M12_claim_text_changed(self):
        self.mutate_gold(lambda g: g["CR-08"]["expected_blockers"][0].update(claim="Alloy 7075-T6 yields 999 MPa"))
        self.assert_fails("CR-08 blocker[0]: claim token")

    def test_M17_drop_expected_item_cr01(self):
        self.mutate_gold(lambda g: g["CR-01"]["expected_blockers"].pop(3))
        self.assert_fails("canonical CR-01: expected item (kind, rule, evidence docs, n quotes) ('inferred', 'B_OPEN_8D_SAME_ALLOY'")

    def test_M17_drop_expected_item_cr18(self):
        self.mutate_gold(lambda g: g["CR-18"]["expected_blockers"].pop(0))
        self.assert_fails("canonical CR-18: expected item (kind, rule, evidence docs, n quotes) ('blocker', 'B_NO_SOURCE_RELEASE'")

    def test_M17_drop_cleared_cr18(self):
        self.mutate_gold(lambda g: g["CR-18"].update(cleared=[]))
        self.assert_fails("canonical CR-18: cleared rule B_SUPPLIER_NOT_QUALIFIED missing")

    def test_inference_only_single_doc(self):
        def m(g):
            for b in g["CR-02"]["expected_blockers"]:
                first = b["evidence"][0]["doc_id"]
                b["evidence"] = [e for e in b["evidence"] if e["doc_id"] == first]
        self.mutate_gold(m)
        self.assert_fails("CR-02: inference_only needs an inferred item citing >= 2 distinct doc_ids")

    def test_superseded_doc_as_positive_evidence(self):
        q = "Material: EN AW-6061-T6 billet."
        self.assertIn(q, self.src("DWG-BR220-RevB").read_text(encoding="utf-8"))
        self.mutate_gold(lambda g: g["CR-09"]["expected_blockers"][0]["evidence"].append({"doc_id": "DWG-BR220-RevB", "quote": q}))
        self.assert_fails("CR-09 blocker[0]: positive evidence from SUPERSEDED doc DWG-BR220-RevB")

    def test_stale_trap_empty_must_not_cite(self):
        self.mutate_gold(lambda g: g["CR-03"].update(must_not_cite=[]))
        self.assert_fails("CR-03: stale_rule_trap needs non-empty must_not_cite")

    def test_quote_both_cited_and_must_not_cite(self):
        def m(g):
            e = g["CR-01"]["must_not_cite"][0]
            g["CR-01"]["expected_blockers"][0]["evidence"].append(dict(e))
        self.mutate_gold(m)
        self.assert_fails("CR-01: quote both cited and must_not_cite")

    # previously caught
    def test_corrupt_quote(self):
        self.mutate_gold(lambda g: g["CR-09"]["expected_blockers"][0]["evidence"][0].update(quote="at most 9999 pieces and at most 6 weeks"))
        self.assert_fails("CR-09 blocker[0]: quote not a literal substring")

    def test_renamed_doc_id(self):
        self.src("PRC-DEV-007").rename(self.src("PRC-DEV-777"))
        self.assert_fails("source PRC-DEV-777.md: doc_id 'PRC-DEV-007' != filename stem")

    def test_renamed_header_doc_id(self):
        self.edit_text(self.src("PRC-DEV-007"), "doc_id: PRC-DEV-007", "doc_id: PRC-DEV-777")
        self.assert_fails("source PRC-DEV-007.md: doc_id 'PRC-DEV-777' != filename stem")

    def test_category_count_change(self):
        self.edit_text(self.d / "eval" / "change_requests.jsonl", '"category": "clean_control"', '"category": "direct_conflict"')
        self.assert_fails("category counts")

    def test_verdict_flip(self):
        self.mutate_gold(lambda g: g["CR-01"].update(expected_verdict="no_blockers_found"))
        self.assert_fails("CR-01: no_blockers_found but blockers listed")


class TestSourceTampering(Base):
    def test_M10_asl_approves_meccanica_c_for_br220(self):
        self.edit_text(self.src("ASL-TO-2026-04"), "\n## 3. Summary",
                       "\nAPPROVAL AP-0999: part BR-220; plant TO1; customer STL; supplier Meccanica C S.p.A. (Chieri); billet grade EN AW-6061-T6; status APPROVED 2026-11-01 (PPAP-2026-999)\n\n## 3. Summary")
        self.assert_fails("invariant ASL-TO-2026-04: must_not_match")

    def test_M19_revb_flipped_to_released(self):
        self.edit_text(self.src("DWG-BR220-RevB"), "status: SUPERSEDED (withdrawn 2026-06-01, replaced by DWG-BR220-RevC)", "status: RELEASED, EFFECTIVE")
        self.assert_fails("invariant DWG-BR220-RevB: must_contain '^status: SUPERSEDED' missing")

    def test_8d_closed(self):
        self.edit_text(self.src("8D-25-031"), "status: OPEN", "status: CLOSED")
        self.assert_fails("invariant 8D-25-031: must_contain '^status: OPEN' missing")

    def test_revc_alloy_changed(self):
        self.edit_text(self.src("DWG-BR220-RevC"), "Material: EN AW-6082-T6 billet", "Material: EN AW-6061-T6 billet")
        self.assert_fails("invariant DWG-BR220-RevC: must_contain 'Material: EN AW-6082-T6 billet' missing")

    def test_missing_invariants_file(self):
        (self.d / "eval" / "invariants.json").unlink()
        self.assert_fails("invariants.json: cannot load")

    def test_missing_canonical_file(self):
        (self.d / "eval" / "canonical.json").unlink()
        self.assert_fails("canonical.json: cannot load")


class TestInvariantsNotVacuous(Base):
    """Every must_contain pattern must be falsifiable: deleting the text it matches must fail with
    that exact pattern named. Catches regexes that match anything or anchors that are never exercised."""
    def test_every_must_contain_pattern_is_falsifiable(self):
        import re
        inv = json.loads((DATA / "eval" / "invariants.json").read_text(encoding="utf-8"))
        n = 0
        for doc, spec in inv.items():
            if doc.startswith("_"): continue
            for pat in spec.get("must_contain", []):
                with self.subTest(doc=doc, pat=pat):
                    path = self.src(doc)
                    orig = path.read_text(encoding="utf-8")
                    m = re.search(pat, orig, re.M)
                    self.assertIsNotNone(m, "pattern does not match pristine source")
                    self.assertLess(len(m.group(0)), 400, "pattern matches an implausibly large span")
                    path.write_text(re.sub(pat, "", orig, flags=re.M), encoding="utf-8")  # remove ALL matches
                    self.assertNotEqual(orig, path.read_text(encoding="utf-8"))
                    self.assert_fails(f"invariant {doc}: must_contain {pat!r} missing")
                    path.write_text(orig, encoding="utf-8")
                    n += 1
        self.assertGreaterEqual(n, 30)

    def test_every_header_pin_is_falsifiable(self):
        inv = json.loads((DATA / "eval" / "invariants.json").read_text(encoding="utf-8"))
        n = 0
        for doc, spec in inv.items():
            if doc.startswith("_"): continue
            self.assertEqual(set(spec["header"]), {"doc_id", "revision", "status", "effective_date"})
            for k, v in spec["header"].items():
                if k == "doc_id": continue  # covered by the filename-stem tests
                with self.subTest(doc=doc, key=k):
                    path = self.src(doc); orig = path.read_text(encoding="utf-8")
                    self.assertIn(f"\n{k}: {v}\n", orig)
                    path.write_text(orig.replace(f"\n{k}: {v}\n", f"\n{k}: {v}X\n", 1), encoding="utf-8")
                    self.assert_fails(f"invariant {doc}: header {k} is {v + 'X'!r}, pinned {v!r}")
                    path.write_text(orig, encoding="utf-8"); n += 1
        self.assertEqual(n, 30)

    def test_exactly_counts_enforced(self):
        self.edit_text(self.src("ASL-TO-2026-04"), "\n## 3. Summary",
                       "\nAPPROVAL AP-0998: part BR-999; plant TO1; customer STL; supplier Alluminio B S.r.l. (Settimo Torinese)\n\n## 3. Summary")
        self.assert_fails("pattern '^APPROVAL AP-' matched 8x, expected 7")


class TestLock(Base):
    """Layer 1: byte-level tamper lock, run with the lock ON."""
    def test_lock_source_byte_change(self):
        with open(self.src("PRC-DEV-007"), "a", encoding="utf-8") as f: f.write("\n")
        self.assert_fails("lock: sha256 mismatch for sources/PRC-DEV-007.md", lock=True)

    def test_lock_eval_byte_change_semantically_neutral(self):
        # trailing whitespace in a JSON file: every semantic check still passes, only the hash sees it
        p = self.d / "eval" / "canonical.json"; p.write_text(p.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        self.assertEqual(self.run_validate().returncode, 0, "mutation must be invisible to the semantic layer")
        self.assert_fails("lock: sha256 mismatch for eval/canonical.json", lock=True)

    def test_lock_readme_change(self):
        with open(self.d / "README.md", "a", encoding="utf-8") as f: f.write("x\n")
        self.assert_fails("lock: sha256 mismatch for README.md", lock=True)

    def test_lock_extra_file_in_eval(self):
        (self.d / "eval" / "leak.jsonl").write_text("{}\n", encoding="utf-8")
        self.assert_fails("lock: file eval/leak.jsonl is not listed in MANIFEST.lock", lock=True)

    def test_lock_missing_source_file(self):
        self.src("PRC-DEV-007").unlink()
        self.assert_fails("lock: file sources/PRC-DEV-007.md listed in MANIFEST.lock is missing", lock=True)

    def test_lock_missing_lock_file(self):
        (self.d / "MANIFEST.lock").unlink()
        self.assert_fails("MANIFEST.lock unreadable", lock=True)

    def test_lock_corrupt_lock_file(self):
        (self.d / "MANIFEST.lock").write_text("not json", encoding="utf-8")
        self.assert_fails("MANIFEST.lock unreadable", lock=True)

    def test_semantic_errors_reported_before_lock(self):
        self.mutate_gold(lambda g: g["CR-09"]["expected_blockers"][0].update(rule="B_INVENTED_RULE"))
        r = self.run_validate(lock=True)
        lines = [l for l in r.stdout.splitlines() if l.startswith("  - ")]
        self.assertTrue(any("not in allowed set" in l for l in lines), r.stdout)
        self.assertTrue(any("lock: sha256 mismatch for eval/gold.jsonl" in l for l in lines), r.stdout)
        self.assertLess([i for i, l in enumerate(lines) if "not in allowed set" in l][0],
                        [i for i, l in enumerate(lines) if "lock:" in l][0], "semantic error must come first")

    def test_relock_refused_when_semantic_fails(self):
        before = (self.d / "MANIFEST.lock").read_text(encoding="utf-8")
        self.mutate_gold(lambda g: g["CR-09"]["expected_blockers"][0].update(rule="B_INVENTED_RULE"))
        r = self.run_validate("--relock")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("RELOCK REFUSED", r.stdout)
        self.assertEqual(before, (self.d / "MANIFEST.lock").read_text(encoding="utf-8"), "lock must be untouched")

    def test_relock_writes_and_prints_diff_when_clean(self):
        with open(self.d / "README.md", "a", encoding="utf-8") as f: f.write("A harmless note.\n")
        self.assert_fails("lock: sha256 mismatch for README.md", lock=True)
        r = self.run_validate("--relock")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("relock diff: changed README.md", r.stdout)
        self.assertEqual(self.run_validate(lock=True).returncode, 0, "relocked copy must pass with the lock on")

    def test_bad_flag_rejected(self):
        r = subprocess.run([sys.executable, str(VALIDATE), "--bogus", str(self.d)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage:", r.stdout + r.stderr)


class TestSemanticLayer(Base):
    """Layer 2: every mutation is checked with --no-lock (semantic layer alone). Where a careless relock
    would hide it from the hash, the *_relocked variant proves the semantic layer still fails."""
    def check_both(self, mutate, needle):
        mutate()
        self.assert_fails(needle)                      # semantic layer alone
        self.raw_relock()
        self.assert_fails(needle, lock=True)           # lock recomputed on the mutated tree: still fails

    # (a) pinned header lines
    def test_header_date_move(self):
        self.check_both(lambda: self.edit_text(self.src("ASL-TO-2026-04"), "effective_date: 2026-09-15", "effective_date: 2025-01-01"),
                        "invariant ASL-TO-2026-04: header effective_date is '2025-01-01', pinned '2026-09-15'")

    def test_header_revision_change(self):
        self.check_both(lambda: self.edit_text(self.src("DWG-BR220-RevC"), "revision: C", "revision: B"),
                        "invariant DWG-BR220-RevC: header revision is 'B', pinned 'C'")

    def test_status_flip_informal_to_controlled(self):
        self.check_both(lambda: self.edit_text(self.src("EML-SQ-2026-1105"), "status: SENT (informal correspondence)", "status: CONTROLLED, EFFECTIVE"),
                        "invariant EML-SQ-2026-1105: header status is 'CONTROLLED, EFFECTIVE', pinned 'SENT (informal correspondence)'")

    def test_8d_supplier_swapped(self):
        self.check_both(lambda: self.edit_text(self.src("8D-25-031"), "issuer: Meccanica C S.p.A. (Chieri)", "issuer: Alluminio B S.r.l. (Settimo Torinese)"),
                        "invariant 8D-25-031: must_contain '^issuer: Meccanica")

    def test_8d_failure_mode_changed(self):
        self.check_both(lambda: self.edit_text(self.src("8D-25-031"), "Cracks at fastener holes found", "Surface staining found"),
                        "invariant 8D-25-031: must_contain")

    # (b) date logic
    def test_date_logic_superseded_newer_than_controlled(self):
        self.check_both(lambda: self.edit_text(self.src("DWG-BR220-RevB"), "effective_date: 2025-09-04", "effective_date: 2026-12-04"),
                        "pair date logic: DWG-BR220-RevB (2026-12-04) must be older than DWG-BR220-RevC")

    def test_date_logic_stale_email_newer_than_revocation(self):
        self.check_both(lambda: self.edit_text(self.src("EML-SQ-2026-0814"), "effective_date: 2026-08-14", "effective_date: 2026-12-01"),
                        "pair date logic: EML-SQ-2026-0814 (2026-12-01) must be older than EML-SQ-2026-1105")

    def test_authority_stale_email_promoted(self):
        self.check_both(lambda: self.edit_text(self.src("EML-SQ-2026-0814"), "status: SENT (informal correspondence)", "status: CONTROLLED, EFFECTIVE"),
                        "pair authority: EML-SQ-2026-0814 status 'CONTROLLED, EFFECTIVE' must be superseded/informal")

    def test_authority_controlled_doc_demoted(self):
        self.check_both(lambda: self.edit_text(self.src("DWG-BR220-RevC"), "status: RELEASED, EFFECTIVE", "status: DRAFT"),
                        "pair authority: DWG-BR220-RevC status 'DRAFT' must be controlled/released and effective")

    # (c) canonical rows, exact
    def test_rule_swap_on_non_canonical_row(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-13"]["expected_blockers"][0].update(rule="B_OPEN_8D_SAME_ALLOY")),
                        "canonical CR-13: expected item (kind, rule, evidence docs, n quotes) ('blocker', 'B_MATERIAL_MISMATCH'")

    def test_rule_swap_to_unexpected_rule_reported_as_unexpected(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-08"]["expected_blockers"][0].update(rule="deviation_limit_exceeded")),
                        "canonical CR-08: unexpected expected item (kind, rule, evidence docs, n quotes) ('blocker', 'deviation_limit_exceeded'")

    def test_irrelevant_extra_evidence_doc(self):
        q = "at most 2000 pieces and at most 6 weeks"
        self.assertIn(q, self.src("PRC-DEV-007").read_text(encoding="utf-8"))
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-02"]["expected_blockers"][0]["evidence"].append({"doc_id": "PRC-DEV-007", "quote": q})),
                        "canonical CR-02: unexpected expected item")

    def test_extra_evidence_quote_from_already_cited_doc(self):
        # doc set unchanged, only the quote count moves: the n_quotes pin must see it
        line = next(l for l in self.src("CP-BR220-R3").read_text(encoding="utf-8").splitlines() if l.startswith("| 20 | Material certificate review |"))
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-02"]["expected_blockers"][0]["evidence"].append({"doc_id": "CP-BR220-R3", "quote": line})),
                        "canonical CR-02: unexpected expected item")

    def test_request_text_change(self):
        def m():
            self.edit_text(self.d / "eval" / "change_requests.jsonl", "1,800 pieces", "3,800 pieces")
        self.check_both(m, "canonical CR-15: request_text must contain '1,800")

    def test_request_supplier_change(self):
        self.check_both(lambda: self.edit_text(self.d / "eval" / "change_requests.jsonl", "Can we take BR-220 billet from Meccanica C?", "Can we take BR-220 billet from Alluminio B?"),
                        "canonical CR-01: request_text must contain 'Meccanica")

    def test_request_part_changed(self):
        def m():
            p = self.d / "eval" / "change_requests.jsonl"
            rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()]
            rows[0]["part"] = "BR-310"
            p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        self.check_both(m, "canonical CR-01: request part 'BR-310' != 'BR-220'")

    def test_change_type_changed(self):
        self.check_both(lambda: self.edit_text(self.d / "eval" / "change_requests.jsonl", '"change_type": "lot_release"', '"change_type": "other"'),
                        "canonical CR-06: request change_type 'other' != 'lot_release'")

    def test_cleared_rule_removed(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-03"].update(cleared=[])),
                        "canonical CR-03: cleared rule B_SUPPLIER_NOT_QUALIFIED missing")

    def test_cleared_rule_swapped(self):
        def m(): self.mutate_gold(lambda g: g["CR-03"]["cleared"][0].update(rule="B_NO_SOURCE_RELEASE"))
        self.check_both(m, "canonical CR-03: unexpected cleared rule B_NO_SOURCE_RELEASE")

    def test_spurious_cleared_on_clean_row(self):
        def m():
            ev = None
            def f(g):
                nonlocal ev
                ev = g["CR-03"]["cleared"][0]["evidence"]
                g["CR-04"]["cleared"] = [{"rule": "B_SUPPLIER_NOT_QUALIFIED", "claim": "Meccanica C probation does not apply to this request.", "evidence": ev}]
            self.mutate_gold(f)
        self.check_both(m, "canonical CR-04: unexpected cleared rule B_SUPPLIER_NOT_QUALIFIED")

    def test_trimmed_must_not_cite(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-05"].update(must_not_cite=g["CR-05"]["must_not_cite"][:1])),
                        "canonical CR-05: must_not_cite quote")

    def test_must_not_cite_emptied(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-05"].update(must_not_cite=[])),
                        "canonical CR-05: must_not_cite quote")

    def test_must_not_cite_extra_quote(self):
        q = "Material: EN AW-6061-T6 billet."
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-04"].update(must_not_cite=[{"doc_id": "DWG-BR220-RevB", "quote": q}])),
                        "canonical CR-04: unexpected must_not_cite quote")

    def test_canonical_row_removed(self):
        def m():
            p = self.d / "eval" / "canonical.json"; c = json.loads(p.read_text(encoding="utf-8")); c.pop("CR-07")
            p.write_text(json.dumps(c), encoding="utf-8")
        self.check_both(m, "canonical: ids ['CR-07'] differ from gold rows")

    def test_verdict_flip_on_non_canonical_row(self):
        # CR-06 stays internally consistent only if the verdict stays needs_info; flip a clean control instead
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-15"].update(expected_verdict="needs_info")),
                        "canonical CR-15: verdict 'needs_info' != 'no_blockers_found'")

    # (d) vacuous claim
    def test_vacuous_claim(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-02"]["expected_blockers"][0].update(claim="Anything goes.")),
                        "CR-02 blocker[0]: vacuous claim")

    def test_vacuous_cleared_claim(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-03"]["cleared"][0].update(claim="Fine.")),
                        "CR-03 cleared[0]: vacuous claim")

    # (e) cleared needs evidence and rule
    def test_cleared_without_evidence(self):
        self.check_both(lambda: self.mutate_gold(lambda g: g["CR-03"]["cleared"][0].update(evidence=[])),
                        "CR-03 cleared[0]: cleared item without evidence")

    def test_cleared_without_rule(self):
        def m():
            def f(g): g["CR-03"]["cleared"][0].pop("rule")
            self.mutate_gold(f)
        self.check_both(m, "CR-03 cleared[0]: missing rule")

    # (f) allowlist
    def test_allowlist_extra_eval_file(self):
        self.check_both(lambda: (self.d / "eval" / "leak.jsonl").write_text("{}\n", encoding="utf-8"),
                        "allowlist: unexpected file eval/leak.jsonl")

    def test_allowlist_extra_source_file(self):
        self.check_both(lambda: (self.d / "sources" / "NEW.md").write_text("# x\n", encoding="utf-8"),
                        "allowlist: unexpected file sources/NEW.md")

    def test_allowlist_nested_file(self):
        def m():
            (self.d / "eval" / "sub").mkdir(); (self.d / "eval" / "sub" / "gold.jsonl").write_text("{}\n", encoding="utf-8")
        self.check_both(m, "allowlist: unexpected file eval/sub/gold.jsonl")

    def test_allowlist_deleted_source(self):
        self.check_both(lambda: self.src("PRC-DEV-007").unlink(), "allowlist: source sources/PRC-DEV-007.md missing")

    # dev set
    def mutate_dev(self, fn):
        p = self.d / "eval" / "dev.jsonl"
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        fn({r["id"]: r for r in rows})
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    def test_dev_overlaps_frozen_triple(self):
        # DEV-01 becomes (BR-220, Meccanica C, material_source_change) == CR-01
        def m():
            def f(g): g["DEV-01"].update(part="BR-220", change_type="material_source_change")
            self.mutate_dev(f)
        self.check_both(m, "dev overlap: DEV-01 (part, supplier, change_type) ('BR-220', 'Meccanica C', 'material_source_change') equals frozen CR-")

    def test_dev_overlaps_frozen_request_text(self):
        def m():
            frozen = json.loads((self.d / "eval" / "change_requests.jsonl").read_text(encoding="utf-8").splitlines()[3])["request_text"]
            def f(g): g["DEV-03"].update(request_text=frozen + " ", supplier="Alluminio B")
            self.mutate_dev(f)
        self.check_both(m, "dev overlap: DEV-03 request_text identical to frozen CR-04")

    def test_dev_corrupted_quote(self):
        def m():
            def f(g): g["DEV-02"]["expected_blockers"][0]["evidence"][0]["quote"] = "5. Material certificate EN 10204 type 2.2 required with each lot."
            self.mutate_dev(f)
        self.check_both(m, "DEV-02 blocker[0]: quote not a literal substring of DWG-BR220-RevC")

    def test_dev_unknown_rule(self):
        self.check_both(lambda: self.mutate_dev(lambda g: g["DEV-01"]["expected_blockers"][0].update(rule="B_MADE_UP")),
                        "DEV-01 blocker[0]: rule 'B_MADE_UP' not in allowed set")


if __name__ == "__main__":
    unittest.main(verbosity=2)
