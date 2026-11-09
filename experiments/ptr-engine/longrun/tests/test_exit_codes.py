#!/usr/bin/env python3
"""test_exit_codes.py - the test that would have caught BOTH exit-code holes.

THE MEASUREMENT THAT OPENED THIS (HARNESS-MAP-V2): the conductor could raise
{0,1,2,3,4,5,6,7,8,9,11} while its documented table disagreed in both directions --
code 7 (record) was declared and raised by NOTHING (the record stage's OSError escaped
as an undeclared 1), and code 1 was raised by that escape path while no table entry
said what 1 meant.

The guard is a SOURCE SCAN, not a hand-written list: it parses cell.py, collects every
integer handed to an exit/abort call (`Abort(...)`, `_enforce(..., code)`, `sys.exit(...)`,
`raise SystemExit(...)`), plus every integer literal `main()` returns (0 and the declared
internal-error 1), plus the documented propagation set (`exit_codes.RUNNER_CODES`, which
`stage_run` turns into `Abort(rc, ...)`), and asserts SET EQUALITY with
`exit_codes.EXIT_TABLE`. Extra code -> fails naming it. Declared code nothing raises ->
fails naming it. Both directions are covered because it is equality, not containment.

Red->green, demonstrated in `test_red_green_extra_exit_code_is_caught` and runnable from
a shell as:
    cp cell.py /tmp/red-cell.py && echo 'sys.exit(12)' >> /tmp/red-cell.py
    CELL_EXIT_SCAN_PATH=/tmp/red-cell.py python3 tests/test_exit_codes.py   # FAILS: 12
    python3 tests/test_exit_codes.py                                       # passes

Offline: no request, no network, no git.
"""
import ast
import io
import os
import re
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
CELL = os.path.join(LONGRUN, "cell.py")
sys.path.insert(0, LONGRUN)

import cell          # noqa: E402  (path set above: the conductor under test)
import exit_codes    # noqa: E402


def _int_const(node):
    return (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool))


def _callee(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return "%s.%s" % (_callee(func.value), func.attr)
    if isinstance(func, ast.Call):
        return _callee(func.func)
    return ""


def scan_exit_sites(path):
    """-> ({code: [(line, what), ...]}, source_text). Raises nothing; pure parse."""
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src, filename=path)
    sites = {}

    def add(code, line, what):
        sites.setdefault(code, []).append((line, what))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _callee(node.func)
        if name == "Abort" and node.args and _int_const(node.args[0]):
            add(node.args[0].value, node.lineno, "Abort(%d, ...)" % node.args[0].value)
        elif name == "_enforce" and len(node.args) >= 3 and _int_const(node.args[2]):
            # _enforce(verdict, stage, code) -> raise Abort(code, ...)
            add(node.args[2].value, node.lineno, "_enforce(..., %d)" % node.args[2].value)
        elif name in ("sys.exit", "SystemExit") and node.args and _int_const(node.args[0]):
            add(node.args[0].value, node.lineno, "%s(%d)" % (name, node.args[0].value))
    # main()'s integer returns ARE exit codes: sys.exit(main()) is the only exit line.
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name == "main":
            for node in ast.walk(fn):
                if isinstance(node, ast.Return) and node.value is not None \
                        and _int_const(node.value):
                    add(node.value.value, node.lineno, "main() return %d" % node.value.value)
    return sites, src


def mapped_targets():
    """Codes the conductor reaches through `RUNNER_MAPPED_TO_CELL`, not through a literal.

    Code 14 is raised as `Abort(exit_codes.EXIT_CAPGATE_UNRECORDED, ...)` -- a module
    ATTRIBUTE, not an int literal, so the AST scan cannot see it; the declared remap is
    the machine-readable claim instead. Like `RUNNER_CODES`, it is only counted while
    `cell.py` actually carries the mapping (asserted in the reachability test).
    """
    return set(exit_codes.RUNNER_MAPPED_TO_CELL.values())


def const_name(code):
    for key, value in vars(exit_codes).items():
        if key.startswith("EXIT_") and isinstance(value, int) and value == code:
            return key
    return None


def scan_target():
    """The file under scan. Cell tests can point it at a mutant (red run)."""
    return os.environ.get("CELL_EXIT_SCAN_PATH") or CELL


def _assert_external_owner_raises(case, code):
    """An EXTERNAL code is only as good as its owner: the module must exist, must take the
    number from the table, and must NOT re-type the literal -- a second copy of the number
    is how the table drifted in the first place."""
    owner = exit_codes.EXTERNAL_CODES[code]
    root = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
    path = os.path.join(root, owner)
    case.assertTrue(os.path.isfile(path),
                    "EXTERNAL_CODES names %r for code %d, but that file is missing"
                    % (owner, code))
    src = io.open(path, encoding="utf-8").read()
    case.assertIn("exit_codes.EXIT_TREE_MOVED", src,
                  "%s must take code %d from the table, not from a literal" % (owner, code))
    case.assertNotIn("sys.exit(13)", src,
                     "%s re-types the literal 13 instead of the declared constant" % (owner,))
    case.assertNotIn("return 13", src,
                     "%s re-types the literal 13 instead of the declared constant" % (owner,))


class ScanEqualityTests(unittest.TestCase):
    def test_source_scan_equals_declared_table(self):
        sites, src = scan_exit_sites(scan_target())
        raised = set(sites)
        # Documented propagation: stage_run() maps a runner rc to Abort(rc, ...). It is a
        # raise site, so it is declared in the table as well -- but only if cell.py still
        # actually propagates it, otherwise the set would claim codes nothing raises.
        self.assertIn("_RUNNER_CODES", src,
                      "cell.py no longer propagates the runner's codes by name; the "
                      "propagation claim in this test is stale")
        raised |= set(exit_codes.RUNNER_CODES) | mapped_targets()
        # Codes declared for a TOOL outside the conductor (13, tree-moved) are excused from
        # the cell.py side -- but only because EXTERNAL_CODES names the module that raises
        # them, and only after checking the conductor does NOT raise them (below).
        external = set(exit_codes.EXTERNAL_CODES)
        declared = set(exit_codes.EXIT_TABLE) - external

        missing = sorted(declared - raised)
        extra = sorted(raised - declared)
        # The excuse is not a laundromat: an EXTERNAL code the conductor DOES raise is a
        # collision, and it is exactly the failure this test exists to catch.
        self.assertFalse(sorted(raised & external),
                         "cell.py raises %s, which EXTERNAL_CODES declares as raised "
                         "outside the conductor; the external excuse must not hide a "
                         "conductor code" % (sorted(raised & external),))
        self.assertFalse(
            missing or extra,
            "exit codes drifted between cell.py and exit_codes.EXIT_TABLE\n"
            "  DECLARED BUT NEVER RAISED: %s\n  RAISED BUT NEVER DECLARED: %s\n"
            "  raise sites: %s"
            % ([c for c in missing], [c for c in extra],
               {c: sites[c] for c in sorted(sites)}))

    def test_every_declared_code_is_reachable_by_a_named_site(self):
        sites, src = scan_exit_sites(scan_target())
        for code in sorted(exit_codes.EXIT_TABLE):
            if code in exit_codes.RUNNER_CODES:
                self.assertIn("Abort(code, \"4/7 run\"", src,
                              "code %d rides on the runner propagation, which is gone" % code)
                continue
            if code in mapped_targets():
                name = const_name(code)
                self.assertIn("_RUNNER_MAPPED_TO_CELL = exit_codes.RUNNER_MAPPED_TO_CELL",
                              src, "cell.py no longer carries the declared remap")
                self.assertIn("Abort(exit_codes.%s" % name, src,
                              "mapped code %d has no raise site in cell.py" % code)
                continue
            if code in exit_codes.EXTERNAL_CODES:
                _assert_external_owner_raises(self, code)
                continue
            self.assertIn(code, sites, "declared code %d has no raise site" % code)
            for line, what in sites[code]:
                self.assertGreater(line, 0)
                self.assertTrue(what)

    def test_every_declared_code_names_a_condition_and_an_action(self):
        for code, spec in sorted(exit_codes.EXIT_TABLE.items()):
            with self.subTest(code=code):
                self.assertTrue(spec["name"].strip(), "code %d has no name" % code)
                self.assertGreaterEqual(len(spec["condition"].strip()), 20,
                                        "code %d has no nameable condition" % code)
                self.assertGreaterEqual(len(spec["action"].strip()), 20,
                                        "code %d has no action -- a code without an "
                                        "action is a number, not a diagnosis" % code)
                if code in exit_codes.EXTERNAL_CODES:
                    owner = exit_codes.EXTERNAL_CODES[code]
                    self.assertIn(owner.split("/")[-1], spec["raise_site"],
                                  "external code %d does not name its owner %r"
                                  % (code, owner))
                else:
                    self.assertIn("cell.py:", spec["raise_site"],
                                  "code %d does not name its raise site" % code)

    def test_table_views_are_derived_not_duplicated(self):
        # EXIT_CODES/EXIT_NAMES are views of EXIT_TABLE; a second hand-kept copy is how
        # the prose table drifted from the raised set in the first place.
        self.assertEqual(set(exit_codes.EXIT_CODES), set(exit_codes.EXIT_TABLE))
        for code, spec in exit_codes.EXIT_TABLE.items():
            self.assertEqual(exit_codes.EXIT_CODES[code], spec["meaning"])
            self.assertEqual(exit_codes.EXIT_NAMES[code], spec["name"])

    def test_docstring_and_dry_run_read_the_one_table(self):
        # The docstring's table is rendered from EXIT_TABLE at import time, so it cannot
        # say something the code does not.
        self.assertIn(exit_codes.render_table(), cell.__doc__)
        self.assertIn("exit_codes.EXIT_TABLE", cell.__doc__)
        src = io.open(CELL, encoding="utf-8").read()
        self.assertIn("exit_codes.EXIT_TABLE -- the only copy", src,
                      "the --dry-run printout no longer reads the single table")
        self.assertNotIn("FINAL EXIT-CODE TABLE (pinned;", src,
                         "the hand-typed prose table is back: it will drift again")

    def test_red_green_extra_exit_code_is_caught(self):
        """Red: a `sys.exit(17)` in a /tmp copy must fail the scan, naming 17. Green:
        the real cell.py must pass after the mutant is removed.

        17, not 13: 13 is now DECLARED (tree-moved, EXTERNAL_CODES), so using it here
        would prove the scan blind to declared-but-external codes rather than open."""
        with tempfile.TemporaryDirectory(prefix="exit-codes-red-") as tmp:
            mutant = os.path.join(tmp, "cell-mutant.py")
            with io.open(CELL, encoding="utf-8") as fh:
                body = fh.read()
            with io.open(mutant, "w", encoding="utf-8") as fh:
                fh.write(body + "\nsys.exit(17)\n")

            sites, _ = scan_exit_sites(mutant)
            declared = ((set(exit_codes.EXIT_TABLE) - set(exit_codes.EXTERNAL_CODES))
                        | set(exit_codes.RUNNER_CODES))
            self.assertIn(17, set(sites), "the scan did not see the injected sys.exit(17)")
            self.assertNotIn(17, declared)
            raised = set(sites) | set(exit_codes.RUNNER_CODES) | mapped_targets()
            self.assertTrue(raised - declared == {17},
                            "the red case must be exactly the injected 17, got %s"
                            % sorted(raised - declared))
            # green: the real conductor still agrees with the table (13 excused by owner)
            real, _ = scan_exit_sites(CELL)
            self.assertEqual((set(real) | set(exit_codes.RUNNER_CODES)
                              | mapped_targets()) - set(exit_codes.EXTERNAL_CODES),
                             set(exit_codes.EXIT_TABLE) - set(exit_codes.EXTERNAL_CODES))
            self.assertNotIn(13, set(real) | set(exit_codes.RUNNER_CODES))


class CodeSevenReachableTests(unittest.TestCase):
    """Code 7 was declared and raised by nothing. It is now the record stage's code."""

    def _args(self, out_dir):
        return types.SimpleNamespace(arm="X", out_dir=out_dir, fixture="F",
                                     turns=1, reps=1, offline="rows.jsonl",
                                     no_cell_handoff=True)

    def test_unwritable_out_dir_aborts_with_7_naming_the_directory(self):
        with tempfile.TemporaryDirectory(prefix="exit-codes-7-") as tmp:
            blocked = os.path.join(tmp, "not-a-dir")
            with io.open(blocked, "w", encoding="utf-8") as fh:
                fh.write("this is a file, not a record directory\n")
            with self.assertRaises(cell.Abort) as ctx:
                cell.stage_record(self._args(blocked), "S", [], {}, {"refusals": []},
                                  {"output": []}, None, {"harness_sha256": "x",
                                                         "files": {}}, None)
            exc = ctx.exception
            self.assertEqual(exc.code, 7, "stage 7 must exit 7, got %r" % (exc.code,))
            self.assertEqual(exc.stage, "7/7 record")
            self.assertIn("not-a-dir", exc.message,
                          "the refusal must name the artefact it could not write: %s"
                          % exc.message)

    def test_unwritable_record_json_aborts_with_7_naming_the_json(self):
        with tempfile.TemporaryDirectory(prefix="exit-codes-7b-") as tmp:
            # a DIRECTORY where the record file must go: open(path, "w") raises
            os.makedirs(os.path.join(tmp, "cell-X-S.json"))
            with self.assertRaises(cell.Abort) as ctx:
                cell.stage_record(self._args(tmp), "S", [], {}, {"refusals": []},
                                  {"output": []}, None, {"harness_sha256": "x",
                                                         "files": {}}, None)
            exc = ctx.exception
            self.assertEqual(exc.code, 7)
            self.assertIn("cell-X-S.json", exc.message,
                          "the refusal must name the record it could not write: %s"
                          % exc.message)
            self.assertIn("could not be written", exc.message)

    def test_code_7_is_declared_as_unwritable_artefact(self):
        spec = exit_codes.EXIT_TABLE[7]
        self.assertEqual(spec["name"], "unwritable")
        self.assertIn("record", spec["raise_site"])
        self.assertIn("stage_record", spec["raise_site"])

    def test_internal_error_code_1_has_a_real_raise_site(self):
        # 1 used to exist only as an escaped traceback. main() now catches it, names the
        # run and returns 1 deliberately.
        src = io.open(CELL, encoding="utf-8").read()
        self.assertIn("except Exception:", src)
        self.assertIn("traceback.print_exc()", src,
                      "code 1 must preserve the traceback, not swallow it")
        self.assertIn("cell: EXIT 1 -- internal error", src)
        self.assertIn(1, scan_exit_sites(CELL)[0])

class ExternalCodeTests(unittest.TestCase):
    """Code 13 (tree-moved) is declared by the table and raised by a TOOL, not by cell.py.

    The scan above is set EQUALITY in both directions, so a declared code with no raise
    site in cell.py fails it. The honest resolution is not to exempt 13 silently: its
    owner is declared in `exit_codes.EXTERNAL_CODES` and the owner is checked instead.
    These tests prove the excuse is load-bearing in BOTH directions.
    """

    def test_13_is_declared_as_tree_moved(self):
        self.assertEqual(exit_codes.EXIT_TREE_MOVED, 13)
        spec = exit_codes.EXIT_TABLE[13]
        self.assertEqual(spec["name"], "tree-moved")
        self.assertIn("moved", spec["condition"])
        self.assertIn("tree_freeze.py", spec["raise_site"])
        self.assertEqual(exit_codes.EXTERNAL_CODES[13],
                         "experiments/ptr-engine/tools/tree_freeze.py")
        self.assertNotIn(13, exit_codes.RUNNER_CODES)
        self.assertNotIn(13, exit_codes.RUNNER_MAPPED_TO_CRASH)
        # a movement is not a failure: the two must not share a name
        self.assertNotEqual(exit_codes.name_of(13), exit_codes.name_of(1))

    def test_the_excuse_is_what_balances_the_scan_both_ways(self):
        sites, _ = scan_exit_sites(CELL)
        raised = set(sites) | set(exit_codes.RUNNER_CODES) | mapped_targets()
        self.assertNotIn(13, raised, "cell.py must not raise the tree-moved code")
        # WITHOUT the external declaration 13 is DECLARED-BUT-NEVER-RAISED: the
        # 'missing' direction names it. That is what the excuse suppresses, and it is
        # exactly one code -- nothing else hides behind it.
        self.assertEqual(sorted(set(exit_codes.EXIT_TABLE) - raised), [13])
        # WITH it, the cell.py side balances exactly.
        self.assertEqual(sorted((set(exit_codes.EXIT_TABLE) - set(exit_codes.EXTERNAL_CODES))
                                - raised), [])

    def test_a_fresh_undeclared_code_still_fails_while_13_is_excused(self):
        with tempfile.TemporaryDirectory(prefix="exit-codes-ext-") as tmp:
            mutant = os.path.join(tmp, "cell-mutant.py")
            with io.open(CELL, encoding="utf-8") as fh:
                body = fh.read()
            with io.open(mutant, "w", encoding="utf-8") as fh:
                fh.write(body + "\nsys.exit(17)\n")
            sites, _ = scan_exit_sites(mutant)
            raised = set(sites) | set(exit_codes.RUNNER_CODES) | mapped_targets()
            declared = set(exit_codes.EXIT_TABLE) - set(exit_codes.EXTERNAL_CODES)
            self.assertEqual(sorted(raised - declared), [17],
                             "the external excuse swallowed a genuinely undeclared code")
            # green: the real cell.py balances with 13 excused and nothing else open
            real, _ = scan_exit_sites(CELL)
            self.assertEqual(sorted((set(real) | set(exit_codes.RUNNER_CODES)
                                     | mapped_targets()) - set(exit_codes.EXIT_TABLE)), [])

    def test_external_owner_uses_the_declared_constant(self):
        owner = exit_codes.EXTERNAL_CODES[13]
        root = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
        src = io.open(os.path.join(root, owner), encoding="utf-8").read()
        self.assertIn("EXIT_TREE_MOVED = exit_codes.EXIT_TREE_MOVED", src,
                      "the tool must take 13 from the table, not from a literal")
        self.assertIn("return EXIT_TREE_MOVED if moved else EXIT_OK", src,
                      "verify() must return the declared code when a file moved")


RUNNER = os.path.join(LONGRUN, "run_longrun.py")
DOCS_EXIT_CODES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN))),
                               "docs", "EXIT-CODES.md")

# Functions in run_longrun.py whose return value becomes the process exit status. Named,
# not coded: if one is renamed the claim below is stale and the test says so.
RUNNER_EXIT_FUNCS = ("main", "run_cell", "report_run", "resume_start", "_cap_stop")


def scan_runner_codes(path=RUNNER):
    """-> (set of int codes run_longrun.py can exit with, {code: [lines]}).

    A bare integer `return` anywhere is NOT an exit code (`expected_digests` returns a
    COUNT of 2), so only exit-bearing functions are read, plus every `sys.exit(int)` /
    `raise SystemExit(int)` in the module and a module-level int constant bound to a local
    that an exit-bearing function returns (that is how EXIT_CAP_DIVERGENCE = 9 arrives).
    """
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src, filename=path)
    consts = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and _int_const(node.value):
            consts[node.targets[0].id] = node.value.value
    found = {}

    def add(code, line):
        found.setdefault(code, []).append(line)

    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) \
                and _callee(node.exc.func) == "SystemExit" and node.exc.args \
                and _int_const(node.exc.args[0]):
            add(node.exc.args[0].value, node.lineno)
        if isinstance(node, ast.Call) and _callee(node.func) == "sys.exit" \
                and node.args and _int_const(node.args[0]):
            add(node.args[0].value, node.lineno)

    names = set()
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name in RUNNER_EXIT_FUNCS:
            names.add(fn.name)
            for node in ast.walk(fn):
                if isinstance(node, ast.Return) and node.value is not None:
                    for sub in ast.walk(node.value):
                        if _int_const(sub):
                            add(sub.value, node.lineno)
                        elif isinstance(sub, ast.Name) and sub.id in consts:
                            add(consts[sub.id], node.lineno)
    if names != set(RUNNER_EXIT_FUNCS):
        raise AssertionError("run_longrun.py no longer defines %s; the exit scan's "
                             "assumption is stale (found %s)"
                             % (sorted(RUNNER_EXIT_FUNCS), sorted(names)))
    return set(found), found


class RunnerPropagationTests(unittest.TestCase):
    """Both directions between run_longrun.py's real exits and the propagation table.

    Without this, `RUNNER_CODES` is taken on faith: a declared propagated code the runner
    stopped returning (7, once the record stage was the only thing raising it) would still
    be counted as 'raised', and the equality test above would pass while lying.
    """

    def test_every_propagated_code_is_really_returned_by_the_runner(self):
        codes, where = scan_runner_codes()
        phantom = sorted(set(exit_codes.RUNNER_CODES) - codes)
        self.assertFalse(
            phantom, "RUNNER_CODES declares %s as propagated, but run_longrun.py no longer "
                     "exits with them; the cell would propagate a code that cannot occur "
                     "(runner exits seen: %s)" % (phantom, sorted(codes)))

    def test_every_runner_code_is_propagated_or_explicitly_remapped(self):
        codes, where = scan_runner_codes()
        # 0 is success: the conductor's own 0, never a propagated runner failure.
        self.assertNotIn(0, exit_codes.RUNNER_CODES,
                         "0 must not be a propagated runner code")
        unaccounted = sorted((codes - {0}) - set(exit_codes.RUNNER_CODES)
                             - set(exit_codes.RUNNER_MAPPED_TO_CRASH))
        self.assertFalse(
            unaccounted,
            "run_longrun.py can exit with %s, but the conductor neither propagates them "
            "nor declares what they become; stage_run() would silently report them as 5 "
            "(runner-crash). Declare the mapping in exit_codes.RUNNER_MAPPED_TO_CRASH."
            % (unaccounted,))

    def test_the_remap_matches_what_stage_run_actually_does(self):
        src = io.open(CELL, encoding="utf-8").read()
        self.assertIn("code = _runner_exit_code(rc)", src,
                      "stage_run() no longer uses the declared propagation rule")
        self.assertIn("_RUNNER_MAPPED_TO_CELL = exit_codes.RUNNER_MAPPED_TO_CELL",
                      src, "stage_run()'s remap is not the declared one")
        self.assertIn("_RUNNER_CODES = exit_codes.RUNNER_CODES", src,
                      "cell.py keeps a second copy of the runner codes")
        # 9 belongs to the seam at CELL level; the runner must not be able to reach it.
        self.assertNotIn(9, exit_codes.RUNNER_CODES)
        self.assertIn(9, exit_codes.RUNNER_MAPPED_TO_CRASH,
                      "the runner's EXIT_CAP_DIVERGENCE=9 collision must stay declared")


    def test_every_runner_exit_constant_is_declared(self):
        """The scan is a lower bound: it reads returns inside named functions, so a code that
        travels through a tuple (EXIT_CAP_DIVERGENCE does) is invisible to it. The runner's own
        EXIT_* constants are the second, name-level key: a new one must be declared here."""
        tree = ast.parse(io.open(RUNNER, encoding="utf-8").read())
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) and _int_const(node.value):
                consts[node.targets[0].id] = node.value.value
        declared = set(exit_codes.RUNNER_CODES) | set(exit_codes.RUNNER_MAPPED_TO_CRASH)
        named = {k: v for k, v in consts.items() if "EXIT" in k}
        undeclared = {n: v for n, v in named.items() if v not in declared}
        self.assertFalse(undeclared,
                         "run_longrun.py declares %s, which the conductor neither propagates "
                         "nor maps; declare them in exit_codes.RUNNER_CODES or "
                         "RUNNER_MAPPED_TO_CRASH" % (undeclared,))
        self.assertIn("EXIT_CAP_DIVERGENCE", named,
                      "the runner's cap-divergence constant is gone; re-check the 9 collision")
        self.assertEqual(named["EXIT_CAP_DIVERGENCE"], 9)
        self.assertIn(9, exit_codes.RUNNER_MAPPED_TO_CRASH)


class DocsTableTests(unittest.TestCase):
    """docs/EXIT-CODES.md is the human table; it must be a VIEW of the module."""

    ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*`([a-z0-9-]+)`\s*\|", re.M)

    def test_doc_table_matches_the_module_exactly(self):
        text = io.open(DOCS_EXIT_CODES, encoding="utf-8").read()
        rows = {int(code): name for code, name in self.ROW.findall(text)}
        declared = {code: spec["name"] for code, spec in exit_codes.EXIT_TABLE.items()}
        self.assertTrue(rows, "no machine-readable rows found in docs/EXIT-CODES.md")
        self.assertEqual(rows, declared,
                         "docs/EXIT-CODES.md disagrees with exit_codes.EXIT_TABLE\n"
                         "  only in the doc: %s\n  only in the module: %s\n  name differs: %s"
                         % (sorted(set(rows) - set(declared)),
                            sorted(set(declared) - set(rows)),
                            {c: (rows[c], declared[c]) for c in set(rows) & set(declared)
                             if rows[c] != declared[c]}))

    def test_doc_names_every_stage_module_and_the_9_collision(self):
        text = io.open(DOCS_EXIT_CODES, encoding="utf-8").read()
        for needed in ("run_longrun.py", "grade_v5.py", "analyze_stats.py",
                       "EXIT_CAP_DIVERGENCE", "GATE-CHAIN"):
            self.assertIn(needed, text,
                          "docs/EXIT-CODES.md does not mention %r: a reader cannot tell "
                          "which module exits with what" % needed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
