#!/usr/bin/env python3
"""FIXTURE-TREATMENTS — the three treatments must fire INSIDE the frozen 48-turn horizon.

    python3 experiments/ptr-engine/longrun/tests/test_treatments_fire.py
    .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_treatments_fire.py -q

OFFLINE: zero inference requests.  No row is appended to any corpus and no frozen fixture is
edited; the only fixture read is `tasks-v6/LR-01.v8.json` (and v7, READ-ONLY, to prove the RED).

RED -> GREEN, quoted from this file's own run:
  * RED   v7 inputs under the declared contract (wall 65536, lease field absent) -> exits 3 for
          both growth arms and for lease-reopen (missing field), i.e. the unit card's refusal.
  * GREEN v8 (wall_tokens 3838 + wall_tokens_by_arm 10616, lease_reopen_turns [23, 40]) ->
          grow T21, compact T21, reopen T23, pointer prefix change T2 — all <= 48 — and the
          matching marker is present on the row the runner's own writer (`make_row`) emits.
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
PTR = os.path.dirname(LONG)
TOOLS = os.path.join(PTR, "tools")
sys.path.insert(0, LONG)
sys.path.insert(0, TOOLS)

import arm_treatments_probe as P  # noqa: E402  (offline fake response/cfg only)
import run_longrun as R  # noqa: E402

V8 = os.path.join(LONG, "tasks-v6", "LR-01.v8.json")
V7 = os.path.join(LONG, "tasks-v6", "LR-01.v7.json")
HORIZON = 48
V7_SHA = "42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392"
ARMS = ("transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen")
MARKER = {"transcript-grow": "grow", "transcript-compact": "wall",
          "lease-reopen": "lease", "pointer-stable": "prefix"}


def _fx(path=V8):
    return R.load_fixture(path)


def _rows(fixture, arm, upto):
    """Rows the production writer would emit, with the treatment marker beside `evicted`."""
    fx = R.fixture_for_arm(fixture, arm)
    planner = R.Planner(arm, fx, dry_run=True)
    answers = R._padding_answers(fx, upto)   # the same legal-ceiling answers the precondition uses
    cfg = P._cfg()
    out = []
    for t in range(1, upto + 1):
        info = planner.build(t)
        digest = info["digest_request"] is not None
        extra = {"lease": info.get("lease"), "evicted": info.get("evicted"),
                 "digest_at": t if digest else None}
        row = R.make_row(cfg, fx, arm, 1, P.run_id_for(1, "fixture-treatments-forced"), t,
                         P._fake_resp(R.est_tokens(info["prompt"], planner.bpt)),
                         "<offline fake answer>", "digest" if digest else "turn",
                         "off" * 20, extra)
        out.append((t, info, row))
        planner.record(t, answers[t - 1])
    return out


# --------------------------------------------------------------- GREEN: all four arms
def test_every_arm_fires_inside_the_frozen_horizon():
    fx = _fx()
    for arm in ARMS:
        rc, _lines = R.check_treatments(fx, arm, HORIZON)
        assert rc == 0, (arm, rc)
        fires = R.treatment_fire_turns(fx, arm, HORIZON)
        turn = fires[MARKER[arm]]
        assert turn is not None, (arm, fires)
        assert turn <= HORIZON, (arm, turn)


def test_the_fire_turns_are_the_documented_ones():
    fx = _fx()
    got = {arm: R.treatment_fire_turns(fx, arm, HORIZON)[MARKER[arm]] for arm in ARMS}
    assert got == {"transcript-grow": 21, "transcript-compact": 21,
                   "lease-reopen": 23, "pointer-stable": 2}, got


def test_each_marker_is_present_on_a_forced_simulation_row():
    fx = _fx()
    for arm in ARMS:
        turn = R.treatment_fire_turns(fx, arm, HORIZON)[MARKER[arm]]
        rows = _rows(fx, arm, turn)
        _t, _info, row = rows[-1]
        assert row["arm"] == arm and row["kind"] in ("turn", "digest"), row
        if arm == "transcript-grow":
            assert row["evicted"] > 0, row["evicted"]
        elif arm == "transcript-compact":
            assert row["digest_at"] == turn, row["digest_at"]
            assert any(r["kind"] == "digest" for _x, _i, r in rows), "digest rows must remain"
        elif arm == "lease-reopen":
            assert row["lease"] >= 2, row["lease"]
        else:
            prefixes = [i["prefix_sha256"] for _x, i, r in rows if i.get("prefix_sha256")]
            assert len(set(prefixes)) > 1, "the pinned prefix must move"


def test_digest_at_is_null_on_every_row_that_requested_no_digest():
    fx = _fx()
    for t, _info, row in _rows(fx, "transcript-compact", 5):
        assert row["digest_at"] is None, (t, row["digest_at"])


# --------------------------------------------------------------- RED: the three refusals
def test_red_the_frozen_v7_inputs_refuse_once_the_contract_is_declared():
    """The exact state the unit card measured, gated: v7 walls + v7's absent lease field."""
    v7 = _fx(V7)
    for arm in ("transcript-grow", "transcript-compact", "lease-reopen"):
        # frozen evidence is NOT retro-armed (asserted), but the moment a cell declares the
        # treatments contract over v7's inputs — what a re-run at the old wall would be — the
        # same three arms refuse instead of spending 48 turns on their control path.
        rc_bare, _ = R.check_treatments(v7, arm, HORIZON)
        assert rc_bare == 0, (arm, rc_bare)
        gated = dict(v7, treatments=dict(_fx()["treatments"]))
        rc, lines = R.check_treatments(gated, arm, HORIZON)
        assert rc == R.EXIT_TREATMENTS_UNREACHABLE, (arm, rc)
        assert any("TREATMENT UNREACHABLE" in line for line in lines), lines


def test_red_wall_back_to_65536_refuses_the_growth_arm():
    red = dict(_fx())
    red["wall_tokens"] = 65536
    red["wall_tokens_by_arm"] = {}
    rc, lines = R.check_treatments(red, "transcript-grow", HORIZON)
    assert rc == R.EXIT_TREATMENTS_UNREACHABLE, rc
    assert any("first FIFO truncation > 48 turns at wall_tokens=65536" in l for l in lines), lines


def test_red_missing_lease_reopen_turns_names_the_missing_field():
    red = dict(_fx())
    red.pop("lease_reopen_turns")
    rc, lines = R.check_treatments(red, "lease-reopen", HORIZON)
    assert rc == R.EXIT_TREATMENTS_UNREACHABLE, rc
    joined = "\n".join(lines)
    assert "missing fixture field 'lease_reopen_turns'" in joined, joined


# --------------------------------------------------------------- fixture / budget facts
def test_expected_digests_is_derived_and_not_the_removed_literal():
    fx = _fx()
    assert R.expected_digests(fx) == 2
    assert R.expected_digests(dict(fx, wall_tokens=65536, wall_tokens_by_arm={})) == 0
    src = open(os.path.join(LONG, "run_longrun.py"), encoding="utf-8").read()
    assert "return 2" not in src.split("def expected_digests")[1].split("def ")[0]


def test_horizon_and_v7_are_untouched():
    fx = _fx()
    assert int(fx["N"]) == HORIZON and R.HORIZON_TURNS == HORIZON
    assert int(fx["treatments"]["horizon_turns"]) == HORIZON
    raw = open(V7, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == V7_SHA, "LR-01.v7.json must stay byte-identical"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    bad = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            bad += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"{len(tests) - bad}/{len(tests)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
