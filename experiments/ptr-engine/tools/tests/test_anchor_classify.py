#!/usr/bin/env python3
"""test_anchor_classify.py - guards for the canonical R2.1 classifier.

    python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py

Offline, stdlib only, writes nothing outside a TemporaryDirectory. Covers:

  1. the 11-cell census, compared cell-for-cell with the FROZEN table in
     experiments/ptr-engine/longrun/ANCHOR-PREREG.md (read-only) -- so the new
     classifier is pinned to the census a different author derived;
  2. the f-string divergence (resolve.py:143, FSTRING_MIDDLE) -> PROSE;
  3. the multi-line docstring divergence (resolve.py:47, continuation line of the
     STRING token opened at :44) -> PROSE;
  4. range scoping (the cited range decides, not the whole file);
  5. the attestation digest of ANCHOR-PREREG-V2.md's rule body;
  6. a RED case: `record` must NOT be satisfied by the NAME token `recording`
     (or `prerecord`). Degrade the matcher to substring containment and this
     test fails -- that is the guard on the guard.
"""
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import anchor_classify as ac  # noqa: E402

ROOT = ac.ROOT
PREREG_V1 = "experiments/ptr-engine/longrun/ANCHOR-PREREG.md"
PREREG_V2 = "experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md"
FIXTURE = "experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json"
FIXTURE_TOOLS2 = "experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json"
RESOLVE = "experiments/ptr-engine/ptr_engine/resolve.py"
ERRORS = "experiments/ptr-engine/ptr_engine/errors.py"


def _abs(rel):
    return os.path.join(ROOT, rel)


def census_cells():
    """Rows of the FROZEN census table in ANCHOR-PREREG.md section 3."""
    with open(_abs(PREREG_V1), encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"<!-- census:begin -->(.*?)<!-- census:end -->", text, re.S)
    assert m, "census markers missing from ANCHOR-PREREG.md"
    cells = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("| ") or line.startswith("|---") or "checkpoint" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 4:
            continue
        cells.append({"checkpoint": cols[0], "anchor": cols[1], "cls": cols[2],
                      "evidence_recorded": cols[3]})
    return cells


def fixture_checkpoints():
    """Ordered (checkpoint_id, source, expected) from the v4 fixture."""
    with open(_abs(FIXTURE), encoding="utf-8") as fh:
        fx = json.load(fh)
    return [
        ("cp.%d.t%d" % (i, cp["turn"]), cp["source"], cp["expected"])
        for i, cp in enumerate(fx["checkpoints"])
    ]


class CensusTest(unittest.TestCase):
    """The classifier must reproduce the frozen census 11/11 on class."""

    def test_both_fixtures_declare_the_same_checkpoints(self):
        with open(_abs(FIXTURE), encoding="utf-8") as fh:
            a = json.load(fh)["checkpoints"]
        with open(_abs(FIXTURE_TOOLS2), encoding="utf-8") as fh:
            b = json.load(fh)["checkpoints"]
        self.assertEqual(a, b, "fixture pair must declare identical checkpoints")

    def test_census_eleven_cells(self):
        cells = census_cells()
        self.assertEqual(len(cells), 11, "frozen census must have 11 cells")
        cps = {cid: (src, exp) for cid, src, exp in fixture_checkpoints()}
        got = []
        for cell in cells:
            src, _exp = cps[cell["checkpoint"]]
            c = ac.classify(cell["anchor"], src)
            got.append((cell["checkpoint"], cell["anchor"], c.cls))
            self.assertEqual(
                c.cls, cell["cls"],
                "census cell %s/%s: classifier says %s, frozen census says %s (%s)"
                % (cell["checkpoint"], cell["anchor"], c.cls, cell["cls"], c.evidence))
            self.assertTrue(c.evidence, "every cell must carry evidence")
        self.assertEqual([g[2] for g in got].count(ac.CODE_SYMBOL), 8)
        self.assertEqual([g[2] for g in got].count(ac.NUMBER), 2)
        self.assertEqual([g[2] for g in got].count(ac.PROSE_CONNECTOR), 1)

    def test_derived_anchors_equal_grade_v3_tokenizer(self):
        """R2.1 reuses grade_v3's anchor derivation; assert it verbatim."""
        longrun = os.path.join(ROOT, "experiments/ptr-engine/longrun")
        if longrun not in sys.path:
            sys.path.insert(0, longrun)
        import grade_v3  # read-only import of the frozen grader's tokenizer
        for _cid, _src, exp in fixture_checkpoints():
            self.assertEqual(ac.derive_anchors(exp), grade_v3.anchors(exp),
                             "derive_anchors drifted from grade_v3.anchors on %r" % (exp,))

    def test_cp2_has_nine_derived_anchors(self):
        exp = [e for cid, _s, e in fixture_checkpoints() if cid == "cp.2.t46"][0]
        self.assertEqual(ac.derive_anchors(exp),
                         ["ledger", "record", "refusal", "scope", "serialized",
                          "text", "code", "error", "raising"])


class DivergenceTest(unittest.TestCase):
    """The two families on which R2's stated rule and its checker disagreed."""

    def test_fstring_middle_is_prose_not_code(self):
        c = ac.classify("spent", RESOLVE)
        self.assertEqual(c.cls, ac.PROSE_CONNECTOR, c.as_dict())
        self.assertEqual(c.occurrence_lines, [143])
        self.assertEqual(c.prose[0].kind, "FSTRING_MIDDLE" if ac.FSTRING_TYPES else "STRING")
        # ^ the word lives in f"resolve budget spent: {...}" -- prose, not code.

    def test_multiline_docstring_continuation_is_prose_not_code(self):
        c = ac.classify("budget", RESOLVE + "#L44-L50")
        self.assertEqual(c.cls, ac.PROSE_CONNECTOR, c.as_dict())
        self.assertEqual(c.occurrence_lines, [47], "must point at the continuation line")
        self.assertEqual(c.prose[0].kind, "STRING")
        self.assertEqual((c.prose[0].line, c.prose[0].end_line), (47, 50),
                         "occurrence is on :47, inside a STRING token spanning :44-:50")
        # the frozen checker's prose_lines() keys on the token's START line only,
        # which is why :47 used to look like unmarked code:
        import anchor_prereg_check as old
        self.assertNotIn(47, old.prose_lines(_abs(RESOLVE)),
                         "frozen prose_lines already covers :47 -- divergence claim void")
        self.assertNotIn(143, old.prose_lines(_abs(RESOLVE)))

    def test_budget_is_prose_in_both_divergence_families(self):
        """One anchor proving both families at once: :47 (docstring) and :143 (f-string)."""
        c = ac.classify("budget", RESOLVE)
        self.assertEqual(c.cls, ac.PROSE_CONNECTOR, c.as_dict())
        self.assertEqual(sorted(c.occurrence_lines), [36, 47, 143])
        self.assertEqual(c.code, [])
        self.assertEqual([o.kind for o in c.prose],
                         ["COMMENT", "STRING", "FSTRING_MIDDLE"])


class ScopeTest(unittest.TestCase):
    """The matching unit is the cited range, per occurrence, NAME-parts."""

    def test_range_scoping_moves_evidence_but_not_class(self):
        ranged = ac.classify("ledger", RESOLVE + "#L66-L71")
        filewide = ac.classify("ledger", RESOLVE)
        self.assertEqual(ranged.cls, filewide.cls)
        self.assertEqual(ranged.evidence.split(":")[-1], "66")
        self.assertEqual(filewide.evidence.split(":")[-1], "33")

    def test_single_line_citation_is_a_one_line_range(self):
        c = ac.classify("64", RESOLVE + "#L39")
        self.assertEqual(c.cls, ac.NUMBER)
        self.assertEqual(c.occurrence_lines, [39])

    def test_number_by_form_even_without_a_literal(self):
        c = ac.classify("31", ERRORS + "#L15-L250")
        self.assertEqual(c.cls, ac.NUMBER)
        self.assertEqual((c.code[0].line, c.code[0].end_line), (15, 247))
        self.assertEqual(c.code[0].basis, "class-count")

    def test_out_of_range_occurrence_does_not_count(self):
        """`ledger` does not occur in L39..L39, so it is prose *for that range*."""
        c = ac.classify("ledger", RESOLVE + "#L39")
        self.assertEqual(c.cls, ac.PROSE_CONNECTOR)

    def test_underscore_part_matching(self):
        self.assertEqual(ac.classify("refusal", RESOLVE + "#L66-L71").cls, ac.CODE_SYMBOL)
        self.assertEqual(ac.classify("record", RESOLVE + "#L66-L71").cls, ac.CODE_SYMBOL)


class RedTest(unittest.TestCase):
    """RED CASE -- degrade the matcher to substring containment and this fails.

    R2.1's unit is a NAME token's underscore part (`record_refusal` carries
    `record`). Substring containment would additionally let any token merely
    *containing* the anchor satisfy it. `record` must not be satisfied by the NAME
    `recording`.
    """

    def test_record_is_not_satisfied_by_recording(self):
        src = (
            "def recording(value):\n"
            "    # a comment mentioning record is prose\n"
            "    prerecord = value\n"
            "    return prerecord\n"
        )
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "sample.py")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(src)
            c = ac.classify("record", path)
        self.assertEqual(
            c.cls, ac.PROSE_CONNECTOR,
            "R2.1 degraded to substring containment: `record` matched a NAME that only "
            "contains it (%s)" % (c.as_dict(),))
        self.assertEqual(c.code, [], "no NAME part equals `record` in this sample")
        self.assertTrue(c.prose, "the comment does mention it (as prose)")
        # what a substring matcher would wrongly say, asserted explicitly:
        self.assertTrue(any("record" in o.token.lower() for o in c.prose))


class AttestationTest(unittest.TestCase):
    """The rule body's digest must reproduce from the text on disk."""

    def test_rule_digest_is_recorded_in_the_doc(self):
        digest = ac.rule_digest(PREREG_V2)
        self.assertEqual(len(digest), 64)
        with open(_abs(PREREG_V2), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(digest, text,
                      "ANCHOR-PREREG-V2.md does not record its own rule-body digest")

    def test_rule_body_is_normative_and_complete(self):
        body = ac.rule_text(PREREG_V2)
        for needle in ("CODE-SYMBOL", "PROSE-CONNECTOR", "NUMBER",
                       "FSTRING_MIDDLE", "continuation line", "per occurrence",
                       "mention", "semantic"):
            self.assertIn(needle, body, "rule body missing %r" % (needle,))


if __name__ == "__main__":
    unittest.main(verbosity=2)
