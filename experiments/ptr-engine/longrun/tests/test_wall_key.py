#!/usr/bin/env python3
"""RUNNER-WALL-KEY — the runner must read the PER-ARM wall, never the top-level one.

`tasks-v6/LR-01.v8.json` declares BOTH `wall_tokens: 3838` (top level) and
`wall_tokens_by_arm: {<arm>: 10616}`. 3838 sits below v8's own first prompt (3848), so a
path that falls back to it fires the wall/compact treatment at ~turn 2 and makes
`transcript-grow` and `transcript-compact` behave like each other.

Offline: zero requests (the planner is pure; the dry run prints request bodies and sends
nothing).

RED -> GREEN, quoted from this file's own run:
  * RED   before RUNNER-WALL-KEY: `wall_for_arm` returned the top-level 3838 for an arm
          absent from `wall_tokens_by_arm` (silent fallback) and the dry-run manifest
          freeze recorded `design_cap_tokens=3838` / `fixture.wall_tokens=3838` for a cell
          the dry run built at 10616.
  * GREEN after: the 10x discriminating fixture reads 38380 for every arm; v8 as shipped
          reads 10616 for every arm with grow T21 / compact T21 / lease T23; an arm missing
          from a non-empty `wall_tokens_by_arm` refuses instead of running at 3838; the
          dry-run manifest records the wall the cell actually runs at.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
sys.path.insert(0, LONG)

import run_longrun as R  # noqa: E402

V8 = os.path.join(LONG, "tasks-v6", "LR-01.v8.json")
ARMS = ("transcript-grow", "transcript-compact", "lease-reopen", "pointer-stable")
TOP_LEVEL = 3838


def _v8():
    return R.load_fixture(V8)


def _pad(fx, t):
    pads = R.answer_padding_by_turn(fx) or []
    n = int(pads[t - 1]) if t - 1 < len(pads) else R.answer_padding_tokens(fx)
    return "a" * max(1, int(n * float(fx["bytes_per_token"])))


def _first_fire(fixture, arm):
    """First turn the wall/eviction treatment fires, on the planner the runner builds."""
    fx = R.fixture_for_arm(fixture, arm)
    planner = R.Planner(arm, fx, dry_run=True)
    for t in range(1, int(fixture["N"]) + 1):
        info = planner.build(t)
        if arm == "transcript-grow" and info.get("evicted"):
            return t
        if info.get("digest_request") is not None:
            return t
        planner.record(t, _pad(fx, t))
    return None


# ------------------------------------------------------ 1. the discriminating fixture
def test_discriminating_fixture_reads_per_arm_not_the_top_level_key():
    """top 3838 vs by_arm 38380 (10x): every arm must take 38380."""
    fx = _v8()
    fx["wall_tokens"] = TOP_LEVEL
    fx["wall_tokens_by_arm"] = {a: 38380 for a in ARMS}
    for arm in ARMS:
        arm_fx = R.fixture_for_arm(fx, arm)
        assert int(arm_fx["wall_tokens"]) == 38380, (arm, arm_fx["wall_tokens"])
        assert R.Planner(arm, arm_fx, dry_run=True).wall_tokens == 38380, arm
        assert R.wall_for_arm(fx, arm) == 38380, arm
        # 38380 is above the whole 48-turn growth: nothing fires, so the 10x value is
        # distinguishable from 3838 (which fires at T2, below) by the fire turn alone.
        assert _first_fire(fx, arm) is None, (arm, _first_fire(fx, arm))


def test_top_level_only_fixture_still_works_and_fires_at_turn_2():
    """The legacy shape (no by_arm) keeps working — and 3838 IS the turn-2 wall."""
    fx = _v8()
    fx["wall_tokens"] = TOP_LEVEL
    fx.pop("wall_tokens_by_arm", None)
    assert R.wall_for_arm(fx, "transcript-grow") == TOP_LEVEL
    assert _first_fire(fx, "transcript-grow") == 2
    assert _first_fire(fx, "transcript-compact") == 2


# ------------------------------------------------------ 2. v8 as shipped
def test_v8_as_shipped_reads_10616_for_all_four_arms():
    fx = _v8()
    assert int(fx["wall_tokens"]) == TOP_LEVEL          # the trap is still in the file
    assert set(fx["wall_tokens_by_arm"]) >= set(ARMS)   # ...and covered per arm
    for arm in ARMS:
        assert R.wall_for_arm(fx, arm) == 10616, arm
        assert int(R.fixture_for_arm(fx, arm)["wall_tokens"]) == 10616, arm
    fires = {a: R.treatment_fire_turns(fx, a, R.HORIZON_TURNS) for a in ARMS}
    assert fires["transcript-grow"]["grow"] == 21, fires["transcript-grow"]
    assert fires["transcript-compact"]["wall"] == 21, fires["transcript-compact"]
    assert fires["lease-reopen"]["lease"] == 23, fires["lease-reopen"]
    assert fires["pointer-stable"]["prefix"] == 2, fires["pointer-stable"]
    for arm in ARMS:
        assert fires[arm]["wall_tokens"] == 10616, arm
        assert fires[arm]["ok"], (arm, fires[arm]["reasons"])


# ------------------------------------------- 3. no silent fallback for a missing arm
def test_arm_missing_from_a_declared_by_arm_block_does_not_fall_back_to_3838():
    """The trap: by_arm is declared but an arm is absent -> it must NOT run at 3838."""
    fx = _v8()
    fx["wall_tokens"] = TOP_LEVEL
    fx["wall_tokens_by_arm"] = {a: 10616 for a in ARMS if a != "transcript-grow"}
    try:
        got = R.wall_for_arm(fx, "transcript-grow")
    except R.FixtureError as exc:
        assert "transcript-grow" in str(exc) and "wall_tokens_by_arm" in str(exc), str(exc)
    else:  # pragma: no cover - this is the RED branch
        raise AssertionError(
            "wall_for_arm silently fell back to the top-level %r for transcript-grow; "
            "the arm would fire the wall at T2 instead of T21" % (got,))
    try:
        R.fixture_for_arm(fx, "transcript-grow")
    except R.FixtureError:
        pass
    else:  # pragma: no cover - RED
        raise AssertionError("fixture_for_arm did not refuse the missing per-arm wall")


def test_loader_accepts_a_fixture_that_declares_only_wall_tokens_by_arm():
    """A future fixture may drop the top-level key entirely; the loader must follow."""
    fx = {k: v for k, v in _v8().items() if not k.startswith("_")}
    fx.pop("wall_tokens", None)
    tmp = tempfile.mkdtemp(prefix="wallkey-")
    try:
        path = os.path.join(tmp, "byarm-only.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(fx, fh)
        loaded = R.load_fixture(path)
        assert R.wall_for_arm(loaded, "transcript-grow") == 10616
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({k: v for k, v in fx.items() if k != "wall_tokens_by_arm"}, fh)
        try:
            R.load_fixture(path)
        except R.FixtureError as exc:
            assert "wall_tokens" in str(exc), str(exc)
        else:  # pragma: no cover - RED
            raise AssertionError("loader accepted a fixture with no wall at all")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------- 4. the dry-run manifest freezes the RUN wall
def test_dry_run_manifest_records_the_per_arm_wall_not_the_top_level_one():
    """build_manifest must be handed the arm's fixture, or provenance says 3838 at 10616."""
    tmp = tempfile.mkdtemp(prefix="wallkey-manifest-")
    try:
        argv = ["--dry-run", "--temperature", "0", "--fixture", V8,
                "--arms", "pointer-stable,transcript-compact",
                "--reps", "1", "--manifest-dir", tmp,
                "--rows", os.path.join(tmp, "rows.jsonl")]
        rc = R.main(argv)
        assert rc == 0, rc
        manifests = [os.path.join(tmp, n) for n in os.listdir(tmp) if n.endswith(".json")]
        assert len(manifests) == 2, manifests
        for path in manifests:
            doc = json.load(open(path, encoding="utf-8"))
            assert doc["engine_flags"]["design_cap_tokens"] == 10616, (path, doc["engine_flags"])
            assert doc["fixture"]["wall_tokens"] == 10616, (path, doc["fixture"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    import traceback
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception:
                failed += 1
                print("FAIL", name)
                traceback.print_exc()
    sys.exit(1 if failed else 0)
