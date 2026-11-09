#!/usr/bin/env python3
"""test_tree_freeze.py -- the classifier, the wrapper, and the four verdicts.

THE STORY THIS SUITE REPLAYS (measured this batch): a checker reads `cell.py`, records a
digest, and by the time it finishes the file is different bytes -- so its claim names a
file that no longer exists (`V-GATE-OPERAND`); or a test goes red because ANOTHER card is
mid-edit, and the red becomes the claimant's FAIL (`SEAM-TEST-RED`). Neither is a work
failure. They are "the tree moved".

So the acceptance shape here is red->green on the classifier:

  * a file that moved mid-run is `moved` and the process exits 13 -- a distinct code,
    never 1, because "the tree moved" is not "the work failed";
  * a clean run exits 0 with verdict `pass`;
  * a non-zero command that moved nothing is `failed`;
  * a non-zero command whose inputs also moved is `failed_and_moved` -- both facts kept,
    neither substituted for the other.

Offline: no request, no network, no `git`. The moving tree is simulated in a temp dir.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
TOOLS = os.path.join(os.path.dirname(LONGRUN), "tools")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
TOOL = os.path.join(TOOLS, "tree_freeze.py")

sys.path.insert(0, LONGRUN)
sys.path.insert(0, TOOLS)

import exit_codes   # noqa: E402
import tree_freeze  # noqa: E402

CELL = os.path.join(LONGRUN, "cell.py")
RUNNER = os.path.join(LONGRUN, "run_longrun.py")
GRADE = os.path.join(LONGRUN, "grade_v5.py")
HAZARDS = (CELL, RUNNER, GRADE)

# A wrapper that edits its input 0.2 s into the run: the race, made reproducible.
MOVER = '''import sys, time
time.sleep(0.2)
path, code = sys.argv[1], int(sys.argv[2])
with open(path, "a", encoding="utf-8") as fh:
    fh.write("# moved mid-run\\n")
sys.exit(code)
'''


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _run(argv, **kwargs):
    """Call the tool's main() with stdout/stderr captured. -> (code, out, record path)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tree_freeze.main(argv)
    return code, out.getvalue(), err.getvalue()


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tree-freeze-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_freezes_the_three_hazard_files_with_their_real_digests(self):
        out = os.path.join(self.tmp, "freeze.json")
        code, text, _ = _run(["freeze", "--out", out] + list(HAZARDS))
        self.assertEqual(code, 0, text)
        doc = json.load(io.open(out, encoding="utf-8"))
        self.assertEqual([f["path"] for f in doc["files"]], list(HAZARDS))
        for entry in doc["files"]:
            self.assertEqual(entry["sha256"], _sha(entry["path"]),
                             "the freeze must record the bytes on disk, not a remembered "
                             "digest: %s" % entry["path"])
            self.assertEqual(entry["size"], os.path.getsize(entry["path"]))
            self.assertGreater(entry["mtime_ns"], 0)
        self.assertRegex(doc["tree_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(doc["at"])

    def test_refuses_a_phantom_path_and_writes_nothing(self):
        out = os.path.join(self.tmp, "freeze.json")
        code, _text, err = _run(["freeze", "--out", out, "does/not/exist.py"])
        self.assertEqual(code, tree_freeze.EXIT_USAGE, err)
        self.assertIn("does not exist", err)
        self.assertFalse(os.path.exists(out),
                         "a refused freeze must not leave a document that names a ghost")

    def test_tree_sha_is_one_identity_per_set_of_contents(self):
        # A bare `touch` moves mtime but not bytes: the identity must not change, or every
        # freeze of an untouched tree would look like a movement.
        path = os.path.join(self.tmp, "input.py")
        io.open(path, "w", encoding="utf-8").write("x = 1\n")
        first = tree_freeze.freeze([path], os.path.join(self.tmp, "a.json"))
        os.utime(path, (0, 0))
        second = tree_freeze.freeze([path], os.path.join(self.tmp, "b.json"))
        self.assertEqual(first["tree_sha256"], second["tree_sha256"])
        self.assertNotEqual(first["files"][0]["mtime_ns"], second["files"][0]["mtime_ns"])
        # ... and one appended byte must change it.
        with io.open(path, "a", encoding="utf-8") as fh:
            fh.write("y = 2\n")
        third = tree_freeze.freeze([path], os.path.join(self.tmp, "c.json"))
        self.assertNotEqual(second["tree_sha256"], third["tree_sha256"])


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tree-verify-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "input.py")
        io.open(self.path, "w", encoding="utf-8").write("answer = 42\n")
        self.freeze = os.path.join(self.tmp, "freeze.json")
        tree_freeze.freeze([self.path], self.freeze)

    def test_all_same_exits_zero_and_prints_the_four_fields(self):
        code, text, _ = _run(["verify", self.freeze])
        self.assertEqual(code, 0)
        header = text.splitlines()[0]
        self.assertEqual(header.replace(" ", ""), "path,recorded_sha,current_sha,verdict")
        row = [ln for ln in text.splitlines() if ln.startswith(self.path)][0]
        self.assertTrue(row.endswith(", same"), row)
        self.assertIn(_sha(self.path), row)

    def test_a_moved_file_exits_thirteen_not_one(self):
        with io.open(self.path, "a", encoding="utf-8") as fh:
            fh.write("# one byte more\n")
        code, text, _ = _run(["verify", self.freeze])
        self.assertEqual(code, 13, "a moved tree is not a failed command: %s" % text)
        row = [ln for ln in text.splitlines() if ln.startswith(self.path)][0]
        self.assertTrue(row.endswith(", moved"), row)
        self.assertNotEqual(_sha(self.path), row.split(", ")[1])

    def test_a_deleted_file_exits_thirteen(self):
        os.unlink(self.path)
        code, text, _ = _run(["verify", self.freeze])
        self.assertEqual(code, 13)
        self.assertIn("<absent>", text)
        self.assertTrue([ln for ln in text.splitlines()
                         if ln.startswith(self.path)][0].endswith(", deleted"))

    def test_a_bare_touch_is_reported_but_still_same(self):
        os.utime(self.path, (1, 1))
        code, text, _ = _run(["verify", self.freeze])
        self.assertEqual(code, 0, "bytes did not move, so the tree did not move")
        self.assertIn("(touched)", text)

    def test_thirteen_is_the_declared_tree_moved_code(self):
        self.assertEqual(tree_freeze.EXIT_TREE_MOVED, exit_codes.EXIT_TREE_MOVED)
        self.assertEqual(exit_codes.name_of(13), "tree-moved")
        self.assertNotEqual(exit_codes.name_of(13), exit_codes.name_of(1),
                            "movement and failure must not share a code")


class WrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tree-wrap-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "input.py")
        io.open(self.path, "w", encoding="utf-8").write("answer = 42\n")
        self.mover = os.path.join(self.tmp, "mover.py")
        io.open(self.mover, "w", encoding="utf-8").write(MOVER)
        self.rec = os.path.join(self.tmp, "record.json")

    def _wrap(self, command):
        code, text, _ = _run(["--wrap", self.rec, self.path, "--"] + command)
        record = json.load(io.open(self.rec, encoding="utf-8"))
        for key in ("command", "exit_code", "freeze_before", "freeze_after", "moved",
                    "verdict"):
            self.assertIn(key, record, "the record must carry %r" % key)
        return code, record, text

    def test_pass_clean_command_nothing_moved(self):
        code, record, text = self._wrap([sys.executable, "-c", "print('ok')"])
        self.assertEqual(code, 0, text)
        self.assertEqual(record["verdict"], "pass")
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["moved"], [])
        self.assertTrue(os.path.exists(record["freeze_before"]))
        self.assertTrue(os.path.exists(record["freeze_after"]))
        self.assertNotEqual(record["tree_sha256_after"], None)

    def test_moved_during_run_is_unstamped_not_failed(self):
        code, record, text = self._wrap([sys.executable, self.mover, self.path, "0"])
        self.assertEqual(code, 13, "a run whose inputs moved exits 13: %s" % text)
        self.assertEqual(record["verdict"], "moved_during_run")
        self.assertEqual(record["exit_code"], 0,
                         "the command SUCCEEDED; only the tree moved")
        self.assertEqual(record["moved"], [self.path])
        self.assertEqual(record["moved_detail"][0]["verdict"], "moved")
        self.assertIn("UNSTAMPED", text)
        self.assertIn("Re-run against the settled tree", text)

    def test_failed_command_with_a_still_tree(self):
        code, record, _ = self._wrap([sys.executable, "-c", "raise SystemExit(3)"])
        self.assertEqual(code, 1)
        self.assertEqual(record["verdict"], "failed")
        self.assertEqual(record["exit_code"], 3, "the command's own code is preserved")
        self.assertEqual(record["moved"], [])

    def test_failed_and_moved_keeps_both_facts(self):
        code, record, _ = self._wrap([sys.executable, self.mover, self.path, "3"])
        self.assertEqual(code, 1, "a failing command stays a failure even when it moved")
        self.assertEqual(record["verdict"], "failed_and_moved")
        self.assertEqual(record["exit_code"], 3)
        self.assertEqual(record["moved"], [self.path])

    def test_the_four_verdicts_are_distinguishable_in_json(self):
        seen = {}
        for verdict, command in (
                ("pass", [sys.executable, "-c", "print(1)"]),
                ("failed", [sys.executable, "-c", "raise SystemExit(3)"]),
                ("moved_during_run", [sys.executable, self.mover, self.path, "0"]),
                ("failed_and_moved", [sys.executable, self.mover, self.path, "3"]),
        ):
            # fresh input each time: a previous run's append is not this run's movement
            io.open(self.path, "w", encoding="utf-8").write("answer = 42\n")
            _code, record, _text = self._wrap(command)
            self.assertEqual(record["verdict"], verdict)
            seen[verdict] = (record["exit_code"], bool(record["moved"]))
        self.assertEqual(seen, {
            "pass": (0, False),
            "failed": (3, False),
            "moved_during_run": (0, True),
            "failed_and_moved": (3, True),
        }, "the four verdicts must be told apart by (exit_code, moved) alone")

    def test_the_cli_process_exits_thirteen_for_a_movement(self):
        proc = subprocess.run([sys.executable, TOOL, "--wrap", self.rec, self.path, "--",
                               sys.executable, self.mover, self.path, "0"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 13, proc.stdout + proc.stderr)


class BaselineIsTheBeforeFreezeTests(unittest.TestCase):
    """D1, induced on a /tmp tree: the AFTER freeze is never the baseline.

    V-TREE-FREEZE reproduced twice that `--wrap` classified against a fresh after-freeze,
    which refuses the path its own command just deleted: exit 2, no record, and a deletion
    that can never be a `deleted` row. Each case below fails on that old code:

      (a) delete a declared file, command exits 0 -> `deleted` row, moved_during_run, 13
      (b) create a file in a declared root, exits 0 -> `created` row, moved_during_run, 13
      (c) edit a declared file, exits 1            -> failed_and_moved, exit 1
      (d) untouched tree, exits 1                  -> failed, exit 1
      (e) a declared path missing BEFORE the run   -> refusal, command never started

    CONTRACT DECISION for (b), stated once and used by the doc as well: a path that does
    not exist cannot be DECLARED (freeze refuses it before the run, case (e)), so "the
    command created a declared file" is not expressible. Creation is witnessed instead:
    the declared ROOT (the parent directory of each declared path) is scanned before and
    after, and a new file there is a `created` row that forces `moved_during_run`. A
    creation is reported, never a silent `pass`.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tree-baseline-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.tree = os.path.join(self.tmp, "tree")
        os.makedirs(self.tree)
        self.path = os.path.join(self.tree, "input.py")
        io.open(self.path, "w", encoding="utf-8").write("answer = 42\n")
        self.rec = os.path.join(self.tmp, "record.json")

    def _wrap(self, command, paths=None):
        argv = (["--wrap", self.rec] + (paths if paths is not None else [self.path])
                + ["--"] + list(command))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = tree_freeze.main(argv)
        record = None
        if os.path.exists(self.rec):
            record = json.load(io.open(self.rec, encoding="utf-8"))
        return code, record, out.getvalue() + err.getvalue()

    def _row(self, record, path):
        rows = [r for r in record["moved_detail"] if r["path"] == path]
        self.assertEqual(len(rows), 1, "one row per path: %r" % (record["moved_detail"],))
        return rows[0]

    def test_a_deleted_declared_file_is_a_row_not_a_refusal(self):
        before = _sha(self.path)
        code, record, text = self._wrap(
            [sys.executable, "-c", "import os,sys; os.unlink(sys.argv[1])", self.path])
        self.assertEqual(code, 13, "a deleted declared path is the tree moving, not usage: " + text)
        self.assertIsNotNone(record, "a deletion must still write a record: " + text)
        self.assertEqual(record["verdict"], "moved_during_run")
        self.assertEqual(record["exit_code"], 0, "the command itself succeeded")
        self.assertEqual(record["deleted"], [self.path])
        self.assertEqual(record["moved"], [self.path])
        row = self._row(record, self.path)
        self.assertEqual(row["state"], "deleted")
        self.assertEqual(row["before"], before)
        self.assertIsNone(row["after"], "a deleted path has no after-bytes: null, not a digest")
        self.assertFalse(os.path.exists(self.path))
        after = json.load(io.open(record["freeze_after"], encoding="utf-8"))
        self.assertIn(self.path, after["absent"])
        self.assertEqual(after["baseline"], "classify(before)")
        self.assertIn("UNSTAMPED", text)

    def test_a_file_created_during_the_run_is_a_created_row_not_a_pass(self):
        new = os.path.join(self.tree, "invented.py")
        code, record, text = self._wrap(
            [sys.executable, "-c", "import sys; open(sys.argv[1],'w').write('invented = 1\\n')", new])
        self.assertEqual(code, 13, text)
        self.assertEqual(record["verdict"], "moved_during_run",
                         "a tree that grew is not a pass, even when the declared file is same")
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["created"], [new])
        row = self._row(record, new)
        self.assertEqual(row["state"], "created")
        self.assertIsNone(row["before"])
        self.assertEqual(row["after"], _sha(new))
        self.assertIn("declared set did not cover", text)
        self.assertNotIn(self.path, record["moved"],
                         "the declared file itself did not move; the CREATION did")
        self.assertNotEqual(record["tree_sha256_before"], record["tree_sha256_after"])

    def test_edit_with_command_exit_one_is_failed_and_moved(self):
        editor = "import sys; open(sys.argv[1],'a').write('# edited\\n'); raise SystemExit(int(sys.argv[2]))"
        code, record, text = self._wrap([sys.executable, "-c", editor, self.path, "1"])
        self.assertEqual(code, 1, text)
        self.assertEqual(record["verdict"], "failed_and_moved")
        self.assertEqual(record["exit_code"], 1, "the command's own exit is preserved")
        self.assertEqual(self._row(record, self.path)["state"], "moved")

    def test_untouched_tree_with_command_exit_one_is_failed(self):
        code, record, text = self._wrap([sys.executable, "-c", "raise SystemExit(1)"])
        self.assertEqual(code, 1, text)
        self.assertEqual(record["verdict"], "failed")
        self.assertEqual(record["moved_detail"], [])
        self.assertEqual(record["moved"], [])

    def test_a_declared_path_missing_before_the_run_is_refused_before_the_command(self):
        missing = os.path.join(self.tree, "never.py")
        marker = os.path.join(self.tmp, "command-ran.marker")
        code, record, text = self._wrap(
            [sys.executable, "-c", "open(sys.argv[1],'w').write('ran')", marker],
            paths=[missing])
        self.assertEqual(code, tree_freeze.EXIT_USAGE, text)
        self.assertIn("does not exist", text)
        self.assertIsNone(record, "a refused baseline must not leave a record that names a ghost")
        self.assertFalse(os.path.exists(marker),
                         "the command must not run when the baseline cannot be taken")


class VerdictMappingTests(unittest.TestCase):
    """TASK 2: four outcomes, explicitly mapped, no fifth invented."""

    def test_the_mapping_is_four_cases_and_no_fifth(self):
        table = {
            (0, False): "pass",
            (0, True): "moved_during_run",
            (1, False): "failed",
            (1, True): "failed_and_moved",
            (3, True): "failed_and_moved",
            (137, False): "failed",
            (None, False): "failed",     # could not run: a failure, never a pass
        }
        for (code, changed), verdict in table.items():
            self.assertEqual(tree_freeze.classify_verdict(code, changed), verdict,
                             "(exit %r, changed %r)" % (code, changed))
        self.assertEqual(sorted(set(table.values())), sorted(tree_freeze.VERDICTS),
                         "the table and the module must name the same four verdicts")

    def test_every_state_is_one_of_the_declared_four(self):
        self.assertEqual(set(tree_freeze.STATES), {"same", "moved", "deleted", "created"})


class InvalidDocumentTests(unittest.TestCase):
    """D2: a parseable-but-invalid document is a refusal (2), not a KeyError and not 1."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tree-invalid-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_structural_invalidity_is_refused_with_two(self):
        for index, blob in enumerate(('{}', '[]', '{"files": [{}]}', '{"files": 3}',
                                      '{"files": [{"path": 1, "sha256": "x"}]}')):
            path = os.path.join(self.tmp, "bad%d.json" % index)
            io.open(path, "w", encoding="utf-8").write(blob)
            code, _text, err = _run(["verify", path])
            self.assertEqual(code, tree_freeze.EXIT_USAGE,
                             "invalid document %r must be exit 2, not 1 (1 means the command "
                             "failed): %s" % (blob, err))
            self.assertIn("not a freeze document", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)


GIT = shutil.which("git")

ROW_MOVER = '''import sys
with open(sys.argv[1], "a", encoding="utf-8") as fh:
    fh.write("# moved mid-run\\n")
'''


def _git(repo, *args):
    return subprocess.run(["git", "--no-optional-locks", "-C", repo] + list(args),
                          capture_output=True, text=True)


class VerdictRowTests(unittest.TestCase):
    """`--verdict-row`: a PASS must NAME the tree it judged.

    THE GAP (card `WIRE-TREE-FREEZE-INTO-VERDICTS`): `orchestration_verdict` used to record a
    COMMIT sha and nothing else, while `cell.py` alone moved five times (`f17663d1` ->
    `0136052e` -> `24627d7b` -> `5a812a98` ...). A row recorded against a sha can be re-run
    tomorrow against different bytes and still read as PASS. So the row now carries the bytes
    it judged, and it REFUSES to look stampable when they moved:

      * clean tree      -> payload + `verdict=pass`, exit the COMMAND's own code;
      * path mutated    -> `UNSTAMPED: {…}`, exit 13;
      * path created    -> `created` row, `UNSTAMPED:`, exit 13;
      * empty --paths   -> exit 2, no row at all;
      * dirty tree      -> WARNING on stderr, row still printed.

    CONTRACT DECISION: `failed_and_moved` keeps exit 1 (the command's non-zero is the more
    urgent fact and no existing exit code changes); only `moved_during_run` exits 13.
    Its row is still `UNSTAMPED:` prefixed, because the bytes still moved.

    A real throwaway git repo per test, because `sha` is `git rev-parse HEAD` and dirtiness is
    only meaningful in a repository. Offline: `git init`/`commit` local, no request.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tree-row-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.here = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, self.here)
        self.path = "input.py"
        io.open(self.path, "w", encoding="utf-8").write("answer = 42\n")
        self.rec = os.path.join(self.tmp, "record.json")
        self.mover = os.path.join(self.tmp, "mover.py")
        io.open(self.mover, "w", encoding="utf-8").write(ROW_MOVER)
        if GIT:
            _git(self.repo, "init", "-q")
            _git(self.repo, "add", "-A")
            _git(self.repo, "-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "-m", "init")

    def _wrap(self, command, extra=()):
        argv = ["--wrap", self.rec] + list(extra) + ["--verdict-row", self.path,
                                                     "--"] + list(command)
        code, out, err = _run(argv)
        return code, out, err

    def _row(self, text):
        for line in text.splitlines():
            if line.startswith("{") or line.startswith("UNSTAMPED: {"):
                return line
        self.fail("no verdict row printed; stdout was:\n%s" % text)

    def _head(self):
        return _git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def test_a_clean_tree_prints_a_row_naming_the_head_and_the_commands_real_exit(self):
        code, out, err = self._wrap([sys.executable, "-c", "print('ok')"])
        self.assertEqual(code, 0, out + err)
        row = self._row(out)
        self.assertFalse(row.startswith("UNSTAMPED:"), out)
        payload = json.loads(row)
        self.assertEqual(sorted(payload), ["command", "exitCode", "sha"])
        self.assertEqual(payload["exitCode"], 0, "the COMMAND's exit, never the wrapper's")
        self.assertEqual(payload["sha"], self._head())
        self.assertIn(sys.executable, payload["command"],
                      "the command string is the one that was run, verbatim")
        self.assertIn("-c", payload["command"],
                      "the command string keeps the flags it was run with")
        human = [ln for ln in out.splitlines() if ln.startswith("verdict=")]
        self.assertEqual(len(human), 1, out)
        before = _sha(self.path)
        self.assertIn("verdict=pass", human[0])
        self.assertIn("%s:%s->%s" % (self.path, before, before), human[0])

    def test_a_path_mutated_by_the_command_is_an_unstamped_row_not_a_fail(self):
        before = _sha(self.path)
        code, out, err = self._wrap([sys.executable, self.mover, self.path])
        self.assertEqual(code, 13, "moved bytes -> 13, never 1: " + out + err)
        row = self._row(out)
        self.assertTrue(row.startswith("UNSTAMPED: "), out)
        payload = json.loads(row[len("UNSTAMPED: "):])
        self.assertEqual(payload["exitCode"], 0, "the command succeeded; only the tree moved")
        self.assertEqual(payload["sha"], self._head())
        human = [ln for ln in out.splitlines() if ln.startswith("verdict=")][0]
        self.assertIn("verdict=moved_during_run", human)
        self.assertIn("%s:%s->" % (self.path, before), human)
        self.assertNotIn("FAIL", human)

    def test_a_path_created_by_the_command_is_a_created_row_and_unstamped(self):
        command = [sys.executable, "-c",
                   "open('new_file.py','w').write('x = 1\\n')"]
        code, out, err = self._wrap(command)
        self.assertEqual(code, 13, out + err)
        row = self._row(out)
        self.assertTrue(row.startswith("UNSTAMPED: "), out)
        json.loads(row[len("UNSTAMPED: "):])
        human = [ln for ln in out.splitlines() if ln.startswith("verdict=")][0]
        self.assertIn("verdict=moved_during_run", human)
        self.assertIn("new_file.py:created (", human)
        self.assertEqual(json.load(io.open(self.rec, encoding="utf-8"))["created"],
                         [os.path.join(self.repo, "new_file.py")])

    def test_empty_paths_is_refused_with_two_and_prints_no_row(self):
        code, out, err = _run(["--wrap", self.rec, "--verdict-row", "--",
                               sys.executable, "-c", "print('ok')"])
        self.assertEqual(code, 2, out + err)
        self.assertEqual(self._row_lines(out), [])
        self.assertIn("no bytes", out + err)
        self.assertFalse(os.path.exists(self.rec), "a refused run writes no record")

    def test_a_dirty_tree_warns_on_stderr_and_still_prints_the_row(self):
        with io.open(self.path, "a", encoding="utf-8") as fh:
            fh.write("# uncommitted\n")
        code, out, err = self._wrap([sys.executable, "-c", "print('ok')"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("WARNING: dirty tree at HEAD %s" % self._head(), err)
        self.assertIn("does not contain these bytes", err)
        self.assertEqual(json.loads(self._row(out))["sha"], self._head(),
                         "the warning does not suppress the row")

    def test_failed_and_moved_still_exits_one_and_still_says_unstamped(self):
        code, out, err = self._wrap([sys.executable, "-c",
                                     "import subprocess,sys;"
                                     "subprocess.call([sys.executable, %r, sys.argv[1]]);"
                                     "raise SystemExit(3)" % self.mover, self.path])
        self.assertEqual(code, 1, "a failing command stays a failure: " + out + err)
        row = self._row(out)
        self.assertTrue(row.startswith("UNSTAMPED: "), out)
        self.assertEqual(json.loads(row[len("UNSTAMPED: "):])["exitCode"], 3)

    def _row_lines(self, text):
        return [ln for ln in text.splitlines()
                if ln.startswith("{") or ln.startswith("UNSTAMPED: {")]


class OneCommandRowFormTests(VerdictRowTests):
    """The acceptance shape the card names: no OUT, `--path` repeated, `--verdict-row` last.

    `--verdict-row` is the verb here; the record lands in a temp file because the ROW, not
    the record, is the deliverable.
    """

    def _wrap(self, command, extra=()):
        argv = ["--path", self.path, "--verdict-row", "--"] + list(command)
        code, out, err = _run(argv)
        return code, out, err

    def test_a_path_created_by_the_command_is_a_created_row_and_unstamped(self):
        # inherited shape, minus the record read: this form names no OUT, so the ROW is
        # the only artefact (the record lives in a temp file the caller never sees).
        command = [sys.executable, "-c", "open('new_file.py','w').write('x = 1\\n')"]
        code, out, err = self._wrap(command)
        self.assertEqual(code, 13, out + err)
        row = self._row(out)
        self.assertTrue(row.startswith("UNSTAMPED: "), out)
        json.loads(row[len("UNSTAMPED: "):])
        human = [ln for ln in out.splitlines() if ln.startswith("verdict=")][0]
        self.assertIn("verdict=moved_during_run", human)
        self.assertIn("new_file.py:created (", human)

    def test_the_one_command_form_prints_the_same_row(self):
        code, out, err = self._wrap([sys.executable, "-c", "print('ok')"])
        self.assertEqual(code, 0, out + err)
        payload = json.loads(self._row(out))
        self.assertEqual(payload["exitCode"], 0)
        self.assertEqual(payload["sha"], self._head())
