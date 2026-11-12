"""AG-01..AG-04: the stage-2 task set, its uniqueness guard, and the report.

The guard under test is the uniqueness refusal in `build_agentic_tasks`: a key that
appears twice in the snapshot is not a fact about the tree, so the builder must refuse
the task instead of writing a coin flip.

RED->GREEN (house style).  The fix is the `len(hits) != 1` refusal inside
`_unique_const` / `_unique_call`.  Reverted run, 2026-11-11, with both functions
returning `hits[0]` unconditionally:

    $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_agentic_tasks.py -q
    ...FF..
    FAILED ...::test_duplicate_key_is_refused
    Failed: DID NOT RAISE TaskRefused
    FAILED ...::test_duplicate_call_is_refused
    Failed: DID NOT RAISE TaskRefused
    2 failed, 5 passed

Restored, the same command is green (7 passed).

VOID RULE (second red->green, same file).  The rule is per mechanism: `none` is never
void (it declares no mechanism and is the baseline), `masking-no-fetch` is void only
when `evicted == 0`, the fold arms only when `compactions == 0`, and an arm with no
episode rows is void with reason `no_episode_rows`.  Reverted to the old global rule
(`compactions == 0 and evicted == 0`):

    $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_agentic_tasks.py -q
    FAILED ...::test_none_arm_is_never_void - assert True is False
    FAILED ...::test_masking_arm_voids_only_when_nothing_was_evicted
    AssertionError: assert ['compactions_zero'] == ['evicted_zero']
    FAILED ...::test_fold_arms_void_only_when_no_fold_fired - assert 0 == 1
    3 failed, 8 passed

Restored, the same command is green (11 passed).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
REPO = os.path.dirname(os.path.dirname(ENGINE))
for _p in (LONGRUN, os.path.join(LONGRUN, "tools"), os.path.join(ENGINE, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import analyze_agentic as AA          # noqa: E402
import build_agentic_tasks as B       # noqa: E402
import grade_v5 as g5                 # noqa: E402
import run_longrun as R               # noqa: E402

TASK_DIR = os.path.join(LONGRUN, "tasks-agentic")


def _scratch(prefix: str) -> str:
    """Scratch under the workspace's gitignored state/ (never /tmp, never a target)."""
    base = os.path.join(REPO, "state")
    os.makedirs(base, exist_ok=True)
    return tempfile.mkdtemp(prefix=prefix, dir=base)


def _render(expected) -> str:
    if isinstance(expected, dict):
        return "%s(%s)" % (expected["callee"],
                           ", ".join("%s=%s" % (k, v)
                                     for k, v in expected["kwargs"].items()))
    return str(expected)


def test_four_tasks_at_four_turns():
    tasks = B.build(REPO)
    assert [t["task_id"] for t in tasks] == ["AG-01", "AG-02", "AG-03", "AG-04"]
    for task in tasks:
        assert task["schema"] == "consonance.longrun-fixture/2"
        assert task["N"] == 16
        assert task["window_tokens"] == 4096
        assert [c["turn"] for c in task["checkpoints"]] == [4, 8, 12, 16]
        assert task["checkpoint_turns"] == [4, 8, 12, 16]
        assert [t["turn"] for t in task["turns"]] == list(range(1, 17))
        assert all(t["question"] for t in task["turns"])
        assert task["documents"] and task["items"]
        assert task["sources"][0]["id"] == "resolve.py"


def test_every_key_is_derived_not_written():
    """`derive_truth` re-derives each key; the documented value must be that value."""
    for task in B.build(REPO):
        truth = g5.derive_truth(task)
        assert len(truth) == 4
        for cp, cell in zip(task["checkpoints"], truth):
            assert _render(cell["expected"]) == str(cp["expected"]), cp["id"]
            assert cp["answer_form"].endswith(str(cp["expected"]))


def test_committed_tasks_load_and_match_a_fresh_build():
    """The committed set cannot drift from the tree it was derived from."""
    for task in B.build(REPO):
        path = os.path.join(TASK_DIR, "%s.json" % task["fixture_version"])
        with open(path, "rb") as fh:
            assert fh.read() == B.serialise(task), (
                "%s is stale; rebuild with build_agentic_tasks.py" % task["task_id"])
        loaded = R.load_fixture(path)
        assert loaded["task_id"] == task["task_id"]
        assert len(R.index_lines(loaded).strip().splitlines()) == len(task["documents"])


def test_duplicate_key_is_refused():
    """Red->green: a second definition of the same control must refuse the task."""
    root = _scratch("agentic-dup-")
    try:
        for spec in B.TASKS:
            dst = os.path.join(root, spec["file"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(REPO, spec["file"]), dst)
        err = os.path.join(root, B.ERRORS_PY)
        os.makedirs(os.path.dirname(err), exist_ok=True)
        shutil.copyfile(os.path.join(REPO, B.ERRORS_PY), err)
        dst = os.path.join(root, B.TASKS[0]["file"])
        with open(dst, "a", encoding="utf-8") as fh:
            fh.write("\nDEFAULT_MAX_FILES = 20000\n")
        with pytest.raises(B.TaskRefused) as exc:
            B.build(root)
        assert "not unique" in str(exc.value)
        assert "DEFAULT_MAX_FILES" in str(exc.value)
        out = os.path.join(root, "out")
        assert B.main(["--root", root, "--out", out]) == 1
        assert not os.path.exists(out)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_duplicate_call_is_refused():
    """Red->green: two calls of the same attribute in one function is not a fact."""
    with pytest.raises(B.TaskRefused) as exc:
        B._unique_call({("f", "g"): [("a.py", 1), ("a.py", 2)]}, "f", "g")
    assert "not unique" in str(exc.value)
    assert "f.g" in str(exc.value)
    with pytest.raises(B.TaskRefused):
        B._unique_const({}, "MISSING")


def _row(arm, rep, compactions, oks, evicted=0, billed=1000, out=100):
    return {"task": "AG-01", "arm": arm, "rep": rep, "solved": all(oks),
            "checkpoints": [{"step": (i + 1) * 4, "expected": "x", "answer": "x",
                             "ok": ok} for i, ok in enumerate(oks)],
            "steps_used": 16, "requests": 12, "refetch_count": 2,
            "compactions": compactions, "evicted": evicted, "prompt_tokens_max": 3000,
            "billed_tokens": billed, "completion_tokens": out}


def _report(rows):
    root = _scratch("agentic-rows-")
    try:
        path = os.path.join(root, "rows.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        out = os.path.join(root, "AGENTIC-test.json")
        assert AA.main(["--rows", path, "--out", out]) == 0
        with open(out, encoding="utf-8") as fh:
            return json.load(fh)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_none_arm_is_never_void():
    """Red->green: the baseline declares no mechanism, so it cannot fail to fire one.

    Under the old global rule (`compactions == 0 and evicted == 0`) both of these
    episodes were void, which deleted the control every other arm is compared against.
    """
    result = _report([_row("none", 1, 0, [True, True, True, True], evicted=0),
                      _row("none", 2, 0, [True, False, True, True], evicted=0)])
    arm = result["arms"]["none"]
    assert arm["fold_mechanism"] == "none"
    assert arm["void"] is False
    assert arm["void_episodes"] == 0
    assert arm["checkpoints_n"] == 8
    assert arm["checkpoints_ok"] == 7
    assert arm["checkpoint_accuracy"] == pytest.approx(7 / 8)
    assert arm["cost_units"] == pytest.approx(2 * (1000 + 3 * 100))


def test_masking_arm_voids_only_when_nothing_was_evicted():
    """Red->green: masking declares eviction, so `compactions == 0` is not its failure."""
    result = _report([_row("masking-no-fetch", 1, 0, [True] * 4, evicted=0),
                      _row("masking-no-fetch", 2, 0, [True, True, False, True], evicted=8)])
    arm = result["arms"]["masking-no-fetch"]
    assert arm["fold_mechanism"] == "eviction"
    assert arm["void_episodes"] == 1
    assert arm["void_reasons"] == ["evicted_zero"]
    assert arm["checkpoints_n"] == 4
    assert arm["checkpoints_ok"] == 3


def test_fold_arms_void_only_when_no_fold_fired():
    """Red->green: a fold arm with evictions but no fold is void; with a fold it is not."""
    result = _report([_row("pinned", 1, 0, [True] * 4, evicted=8),
                      _row("pinned", 2, 1, [True, True, True, False], evicted=8),
                      _row("compact", 1, 0, [True] * 4, evicted=8)])
    pinned = result["arms"]["pinned"]
    assert pinned["fold_mechanism"] == "fold"
    assert pinned["void_episodes"] == 1
    assert pinned["void_reasons"] == ["compactions_zero"]
    assert pinned["checkpoints_n"] == 4
    assert pinned["checkpoints_ok"] == 3
    compact = result["arms"]["compact"]
    assert compact["void"] is True
    assert compact["cost_basis"] == "no_live_episodes"
    assert "VOID" in "\n".join(AA.table(result))


def test_arm_with_no_episode_rows_is_void():
    """An arm that wrote only per-request rows has no episode to report."""
    result = _report([{"run_id": "r1", "arm": "bounded-context-fetch",
                       "task_id": "AG-01", "rep": 1, "step": 1, "kind": "work",
                       "prompt_tokens": 100, "tool_calls": [], "fold_event": False,
                       "verified": None}])
    arm = result["arms"]["bounded-context-fetch"]
    assert arm["void"] is True
    assert arm["void_reasons"] == ["no_episode_rows"]
    assert arm["cost_basis"] == "no_episode_rows"
    assert arm["checkpoint_accuracy"] is None


def test_analyzer_reports_void_not_a_data_point():
    result = _report([_row("compact", 1, 2, [True, True, True, False]),
                      _row("compact", 2, 3, [True, True, True, True]),
                      _row("pinned", 1, 0, [True, True, True, True]),   # fold never fired
                      _row("pinned", 2, 2, [True, False, True, False])])
    compact = result["arms"]["compact"]
    assert compact["void_episodes"] == 0
    assert compact["checkpoints_n"] == 8
    assert compact["checkpoints_ok"] == 7
    assert compact["checkpoint_accuracy"] == pytest.approx(7 / 8)
    assert compact["cost_units"] == pytest.approx(2 * (1000 + 3 * 100))
    assert compact["cost_units_per_verified_success"] == pytest.approx(2600 / 7)
    assert compact["mean_refetch_count"] == pytest.approx(2.0)

    pinned = result["arms"]["pinned"]
    assert pinned["void_episodes"] == 1
    assert pinned["void_reasons"] == ["compactions_zero"]
    assert pinned["checkpoints_n"] == 4          # the void row is excluded
    assert pinned["checkpoints_ok"] == 2
    assert pinned["checkpoint_accuracy"] == pytest.approx(0.5)
    assert pinned["cost_units"] == pytest.approx(1300)
    assert pinned["mean_compactions"] == pytest.approx(2.0)

    text = "\n".join(AA.table(result))
    assert "solved rate is NOT reported" in text


def test_all_void_arm_is_reported_void():
    root = _scratch("agentic-void-")
    try:
        path = os.path.join(root, "rows.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(_row("mask", 1, 0, [True, True, True, True])) + "\n")
        out = os.path.join(root, "AGENTIC-void.json")
        assert AA.main(["--rows", path, "--out", out]) == 0
        with open(out, encoding="utf-8") as fh:
            result = json.load(fh)
        arm = result["arms"]["mask"]
        assert arm["void"] is True
        assert arm["checkpoint_accuracy"] is None
        assert arm["cost_units"] is None
        assert arm["cost_basis"] == "no_live_episodes"
        assert "VOID" in "\n".join(AA.table(result))
    finally:
        shutil.rmtree(root, ignore_errors=True)
