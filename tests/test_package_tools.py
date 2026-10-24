#!/usr/bin/env python3
"""Regression tests for tools/package/.  Runnable: python3 tests/test_package_tools.py -v

Every test states its RED CONDITION: the change that makes it fail.
Temporary trees are written only under scratch/upipe1/testtmp/ (inside this unit's write paths).

The shipped package used as the known-good fixture is scratch/uneutral10/package -- a 29-file
tree.  The figure "inside 2,171" belongs to a 45-file tree and is NOT expected here.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import unittest

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(WS, "tools", "package")
PKG = os.path.join(WS, "scratch", "uneutral10", "package")
BEFORE = os.path.join(WS, "scratch", "uneutral9", "before_pkg")
TMP = os.path.join(WS, "scratch", "upipe1", "testtmp")


def run(args, cwd=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(args, cwd=cwd or WS, capture_output=True, text=True, env=e)


def sha_tree(root):
    out = {}
    for dp, dn, fns in os.walk(root):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in sorted(fns):
            p = os.path.join(dp, f)
            with open(p, "rb") as h:
                out[os.path.relpath(p, root)] = hashlib.sha256(h.read()).hexdigest()
    return out


class PackageTools(unittest.TestCase):
    def setUp(self):
        if os.path.isdir(TMP):
            shutil.rmtree(TMP)
        os.makedirs(TMP)

    # ------------------------------------------------------------------ idempotence
    def test_idempotence(self):
        """RED: census output is order-unstable across runs (the old census_one.py used Python
        set order for equal totals, so two runs differed), or regen_manifest writes different
        bytes on a second pinned run."""
        a = run([sys.executable, "tools/package/census.py", "--package", PKG])
        b = run([sys.executable, "tools/package/census.py", "--package", PKG])
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(a.stdout, b.stdout, "census.py is not byte-idempotent")

        p = os.path.join(TMP, "regen")
        shutil.copytree(PKG, p)
        args = [sys.executable, "tools/package/regen_manifest.py", "--package", p,
                "--generated-utc", "2026-10-16T18:56:15Z"]
        self.assertEqual(run(args).returncode, 0)
        first = open(os.path.join(p, "MANIFEST.json"), "rb").read()
        self.assertEqual(run(args).returncode, 0)
        self.assertEqual(first, open(os.path.join(p, "MANIFEST.json"), "rb").read(),
                         "regen_manifest.py is not byte-idempotent under a pinned utc")

        src = os.path.join(TMP, "nt_src")
        shutil.copytree(BEFORE, src)
        for n in ("nt_a", "nt_b"):
            self.assertEqual(run([sys.executable, "tools/package/neutralise.py",
                                  "--package", src, "--out", os.path.join(TMP, n)]).returncode, 0)
        self.assertEqual(sha_tree(os.path.join(TMP, "nt_a")), sha_tree(os.path.join(TMP, "nt_b")),
                         "neutralise.py is not idempotent")

    # ------------------------------------------------- neutralisation is inert
    def test_neutralisation_is_inert(self):
        """RED: the selected diagnostic moves under the rename (recompute-claims.py exits
        non-zero, or its fixture-correctness digest changes), i.e. neutralise.py returns 4
        instead of 0."""
        # The shipped package is the tree where the diagnostic itself exits 0
        # (scratch/uneutral9/before_pkg exits 1 with ALL CLAIM NUMBERS PRESERVED: False).
        src = os.path.join(TMP, "inert_src")
        out = os.path.join(TMP, "inert_out")
        shutil.copytree(PKG, src)
        diag = "python3 verify/recompute-claims.py"
        before = run(["bash", "-c", diag], cwd=src)
        self.assertEqual(before.returncode, 0, before.stderr)
        got = run([sys.executable, "tools/package/neutralise.py", "--package", src, "--out", out,
                   "--diagnostic", diag])
        self.assertEqual(got.returncode, 0,
                         "diagnostic moved under neutralisation (rc=%d):\n%s" % (got.returncode,
                                                                               got.stderr))
        after = run(["bash", "-c", diag], cwd=out)
        self.assertEqual(before.returncode, after.returncode)
        self.assertEqual(before.stdout, after.stdout,
                         "fixture-correctness diagnostic output changed: %r -> %r"
                         % (before.stdout[:200], after.stdout[:200]))
        digests = re.findall(r"[0-9a-f]{64}", before.stdout)
        self.assertTrue(digests, "recompute-claims.py printed no digest to compare")

    # ------------------------------------------------- census totals
    def test_census_reproduces_documented_totals_on_shipped_package(self):
        """RED: any count below changes -- this pins the 29-file scratch/uneutral10/package tree
        (NOT the 45-file tree where inside 2,171 belongs).

        These totals legitimately moved on 2026-10-16 (UFIXPKG10): recent units removed
        identifiers from the shipped tree (and five comments were removed from
        fixture/reflex-decisions.ts), dropping the totals from 18/75 to 15/66 and shifting the
        by-class split.  A further move is a real regression unless another unit again changes
        the shipped tree, in which case the authoritative totals in tools/package/README.md must
        be updated in the same change.
        """
        r = run([sys.executable, "tools/package/census.py", "--package", PKG])
        self.assertEqual(r.returncode, 0, r.stderr)
        o = r.stdout
        self.assertIn("tree: %s" % PKG, o)
        self.assertIn("files scanned: 29", o)
        self.assertIn("distinct identifiers hit: 15 of 184", o)
        self.assertIn("TOTAL OCCURRENCES (decoded walk): 66", o)
        self.assertIn("inside stimulus (question/options/situation values): 20  distinct=1", o)
        self.assertIn("outside stimulus (all other values + non-JSON text): 46", o)
        self.assertIn("JSON object keys: 0", o)
        for cls, total in (("data-jsonl-other", 2), ("json", 35), ("prose-md", 12),
                           ("tooling", 11), ("ts", 6)):
            self.assertRegex(o, r"%s\s+inside=\s*\d+\s+outside=\s*\d+\s+keys=\s*\d+\s+"
                                r"total=\s*%d" % (cls, total))
        self.assertNotIn("2,171", o)

    # ------------------------------------------------- checker sensitivity
    def test_checker_is_sensitive(self):
        """RED: check_manifest.py still reports 0/0/0/0/0 (exit 0) after 1 byte is appended to a
        listed file -- i.e. it is not re-hashing independently."""
        good = os.path.join(TMP, "good")
        shutil.copytree(PKG, good)
        r = run([sys.executable, "tools/package/check_manifest.py", "--package", good])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0",
                      r.stdout)

        bad = os.path.join(TMP, "bad")
        shutil.copytree(PKG, bad)
        with open(os.path.join(bad, "results", "REPORT.md"), "ab") as fh:
            fh.write(b"X")
        r = run([sys.executable, "tools/package/check_manifest.py", "--package", bad])
        self.assertNotEqual(r.returncode, 0, "checker passed a tampered tree")
        self.assertIn("hash_mismatch=1", r.stdout)
        self.assertIn("size_mismatch=1", r.stdout)
        self.assertIn("HASH: results/REPORT.md", r.stdout)

    # ------------------------------------------------- gate fail-closed
    def test_gate_fails_closed_on_missing_or_empty_vocabulary(self):
        """RED: gate.sh exits 0 (silent PASS) when its vocabulary inputs are absent or empty."""
        r = run(["bash", "tools/package/gate.sh", "--package", PKG])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("FATAL:", r.stderr)

        tree = os.path.join(TMP, "vocab")
        shutil.copytree(PKG, tree)
        os.makedirs(os.path.join(tree, "vocabulary"))
        for name in ("english.txt", "code.txt", "public.txt", "data.txt"):
            open(os.path.join(tree, "vocabulary", name), "w").close()
        r = run(["bash", "tools/package/gate.sh", "--package", tree])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("FATAL: vocabulary file has no declared terms", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
