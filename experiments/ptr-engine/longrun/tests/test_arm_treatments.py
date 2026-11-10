#!/usr/bin/env python3
"""ARM-TREATMENTS-FIRE — the three treatments must fire OFFLINE. Zero requests.

    python3 experiments/ptr-engine/longrun/tests/test_arm_treatments.py
    .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_arm_treatments.py -q

WHY: `orchestration/handoffs/ARM-INTEGRITY.json` measured, over the whole 788-row
corpus, `digest_rows 0 of 788`, `evicted_gt0_rows 0 of 192`, `lease_values [1]`. Three
of the four arms ran their CONTROL path for every turn of every grid: grow never
evicted, compact never digested, reopen never reopened. A treatment that cannot be made
to fire offline is one the grid cannot measure, so these tests force each predicate with
the runner's OWN `Planner` + `make_row` and assert the row marker is non-zero.

Each test is RED against the frozen fixture (wall_tokens=65536, lease_reopen_turns
absent) and GREEN only when the trigger input is changed — which is exactly the claim
`experiments/ptr-engine/measure/ARM-TREATMENTS.json` makes.

The fixture variant is built IN MEMORY: no file under tasks-v5/ or tasks-v6/ is edited,
and no row is appended to the corpus. `make_row` is the production writer, so `evicted`
and `lease` here are the same fields a live row carries.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)                       # experiments/ptr-engine/longrun
PTR = os.path.dirname(LONG)                        # experiments/ptr-engine
TOOLS = os.path.join(PTR, "tools")
MEASURE = os.path.join(PTR, "measure")
sys.path.insert(0, LONG)
sys.path.insert(0, TOOLS)

import arm_treatments_probe as P  # noqa: E402  (the probe; offline by construction)
import run_longrun as R           # noqa: E402

HORIZON = 48
WALL_NOW = 65536


def _evidence():
    return json.load(open(os.path.join(MEASURE, "ARM-TREATMENTS.json"), encoding="utf-8"))


# --------------------------------------------------------------- the RED baseline
def test_corpus_markers_are_zero_today():
    """The measured problem: no row in the pinned grid corpus carries a live marker."""
    ev = _evidence()["markers_today"]
    assert ev["evicted_gt0"] == 0, ev
    assert ev["lease_gt1"] == 0, ev
    assert ev["digest_rows"] == 0, ev


def test_frozen_fixture_fires_nothing_at_48_turns():
    """RED: the shipped trigger inputs (65536 wall, no lease key) fire none of the three."""
    fx = P._variant(WALL_NOW, None)
    for arm in ("transcript-grow", "transcript-compact", "lease-reopen"):
        planner = R.Planner(arm, fx, dry_run=True)
        fired = {"evicted": 0, "digest": 0, "lease": 1}
        evicted_stamps = []
        for t in range(1, HORIZON + 1):
            info = planner.build(t)
            evicted_stamps.append(info["evicted"])
            if info["evicted"] is not None:
                fired["evicted"] = max(fired["evicted"], info["evicted"])
            fired["digest"] += 1 if info["digest_request"] is not None else 0
            fired["lease"] = max(fired["lease"], info.get("lease") or 1)
            planner.record(t, P.ANS)
        if arm == "transcript-grow":
            # the arm MEASURES eviction: 0 is a measurement here
            assert fired["evicted"] == 0, (arm, fired)
        else:
            # no eviction concept -> null, never 0: 0 would assert a measurement
            # nobody made (the same ABSENT != 0 rule the masking arm broke)
            assert evicted_stamps == [None] * len(evicted_stamps), (arm, evicted_stamps)
        assert fired["digest"] == 0, (arm, fired)
        assert fired["lease"] == 1, (arm, fired)


# ------------------------------------------------------------ the three GREEN proofs
def test_grow_evicts_and_the_row_says_so():
    fx, _planner, row = P.force("transcript-grow", 12)
    assert fx["wall_tokens"] < WALL_NOW
    assert row is not None and row["evicted"] > 0, row
    assert row["evicted"] == 1 and row["kind"] == "turn", row
    assert row["turn"] == 12 and row["arm"] == "transcript-grow", row


def test_compact_emits_a_digest_row():
    _fx, _planner, row = P.force("transcript-compact", 12)
    assert row is not None, "no digest row produced"
    assert row["kind"] == "digest", row          # the ONLY row-level marker compaction has
    assert row["turn"] == 12 and row["arm"] == "transcript-compact", row


def test_lease_reopens_when_the_fixture_declares_it():
    fx, _planner, row = P.force("lease-reopen", 12, wall=WALL_NOW, lease_turns=[12])
    assert fx["lease_reopen_turns"] == [12]
    assert row is not None and row["lease"] >= 2, row
    assert row["turn"] == 12 and row["lease"] == 2, row


# ------------------------------------------------------- envelope arithmetic, pinned
def test_envelope_arithmetic_is_the_documented_one():
    """The G4 arithmetic quoted in ARM-TREATMENTS.md, recomputed from the rows."""
    env = _evidence()["envelope"]
    g = env["wall_arithmetic"]["G4-RUN-C-V2/transcript-grow"]
    assert g["prompt_T1"] == 2114 and g["slope"] == 684.362, g
    assert g["wall_for_T24"] == 17853 and g["wall_for_T48"] == 34278, g
    assert g["turns_needed_at_wall_65536"] == 94, g
    assert env["observed_max_prompt"]["prompt_tokens"] == 34279, env["observed_max_prompt"]
    assert env["observed_max_prompt"]["turn"] == 48
    c = env["wall_arithmetic"]["G4-RUN-C-V2/transcript-compact"]
    assert c["turns_needed_at_wall_65536"] == 847, c


def test_price_is_six_requests_not_a_new_horizon():
    p = _evidence()["price"]
    assert p["a_star_published"] == 792 and p["a_star_recomputed"] == 792, p
    assert p["firing_grid_48"] == 798 and p["delta_48"] == 6, p


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
