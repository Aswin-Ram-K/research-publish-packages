"""E7's pin arms: the pin API, the two-tier todo, and the window-pressure fold.

Two defects were found by driving the real ``PinnedArmState`` and are pinned
here so they cannot come back:

D1  ``pin(..., supersedes=pid)`` did ``int(supersedes)``, so passing back the id
    ``pin()`` itself returns (``"P2"``) raised
    ``ValueError: invalid literal for int() with base 10: 'P2'``.  The API must
    accept what it hands out.

D2  ``_pin_tokens`` counted whitespace-separated words while the constant is
    named ``PIN_CAP_TOKENS`` and the design calls it a token budget.  A
    200-character unbroken pin therefore cost 1 "token", and 200 such writes
    were admitted against a 512 cap.  The cap is now measured with the
    compiler's own ``_estimate_tokens`` (``CHARS_PER_TOKEN``), the same unit the
    window trigger uses.

Red→green, measured 2026-11-11: against the pre-fix ``arm_cd.py`` the supersede
test raises ``ValueError`` and the cap test admits all 200 writes; both pass
now.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
for p in (ENGINE_ROOT, LONGRUN):
    if p not in sys.path:
        sys.path.insert(0, p)

import arm_cd  # noqa: E402
from ptr_engine.layers import CHARS_PER_TOKEN, _estimate_tokens  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-07.v5.json")


def _fixture():
    with open(FIXTURE) as fh:
        return json.load(fh)


def _state(**kw):
    return arm_cd.PinnedArmState(fixture=_fixture(), **kw)


def test_pin_is_stamped_with_its_turn():
    st = _state()
    st.build(1, "q1")
    pid = st.pin("blocker", "the ledger refuses the write")
    assert pid == "P2", pid  # P1 is the PLAN pin
    assert st.state.pins[-1] == "P2|blocker|T1|the ledger refuses the write"


def test_supersede_accepts_the_id_pin_returns():
    """D1: ``pin()`` returns ``P<n>``; passing it back must not raise."""
    st = _state()
    st.build(1, "q1")
    pid = st.pin("blocker", "first")
    st.pin("blocker", "second", supersedes=pid)
    assert st.state.pins[-1].endswith("|supersedes P2|second"), st.state.pins[-1]
    # A bare number is still accepted.
    st.pin("blocker", "third", supersedes=2)
    assert "supersedes P2|third" in st.state.pins[-1]


def test_tool_sourced_pins_are_sanitised():
    st = _state()
    st.build(1, "q1")
    st.pin("fact", "evil\u200btext\u202ehere", source="tool")
    line = st.state.pins[-1]
    for ch in ("\u200b", "\u202e"):
        assert ch not in line, repr(line)
    assert "[source=tool]" in line


def test_retire_is_a_tombstone_not_a_deletion():
    st = _state()
    st.build(1, "q1")
    pid = st.pin("blocker", "x")
    before = list(st.state.pins)
    st.retire(pid, "resolved")
    assert st.state.pins[:len(before)] == before, "a retire must not remove or renumber"
    assert st.state.pins[-1].endswith("|%s retired: resolved" % pid)


def test_cap_is_measured_in_real_tokens():
    """D2: a 200-char unbroken pin must cost ~64 tokens, not 1."""
    st = _state()
    st.build(1, "q1")
    writes = 0
    try:
        for _ in range(200):
            st.pin("fact", "x" * 200)
            writes += 1
    except arm_cd.PinCapExceeded as exc:
        assert exc.overflow > 0
        assert "REFUSED" in str(exc)
    else:
        raise AssertionError("the cap admitted %d writes of 200 chars" % writes)
    assert writes < 20, writes
    assert arm_cd._pin_tokens(st.state.pins) <= st.pin_cap_tokens
    assert _estimate_tokens("x" * 200) > 50


def test_unknown_kind_is_refused():
    st = _state()
    st.build(1, "q1")
    try:
        st.pin("nonsense", "x")
    except ValueError as exc:
        assert "unknown pin kind" in str(exc)
    else:
        raise AssertionError("an unknown kind was admitted")


def test_plan_pin_is_written_once_and_survives_a_fold():
    st = _state()
    st.build(1, "q1")
    plan = st.plan_id
    assert plan is not None
    assert any("|goal|" in p for p in st.state.pins), st.state.pins
    st.build(2, "q2")
    assert st.plan_id == plan, "the PLAN must not be rewritten"
    assert sum(1 for p in st.state.pins if "|goal|" in p) == 1


def test_active_line_only_on_the_recency_arm():
    plain = _state(recency=False)
    recency = _state(recency=True)
    p_plain = plain.build(1, "q1")
    p_rec = recency.build(1, "q1")
    assert "ACTIVE:" not in str(p_plain)
    assert "ACTIVE:" in str(p_rec)
    assert len(p_rec) > len(p_plain)


def test_pins_block_absent_when_empty():
    """A no-pin arm must keep byte-identical prefix bytes."""
    st = _state()
    st.build(1, "q1")
    # The PLAN pin is written on the first build, so PINS is present; a state
    # with no pins at all must render no PINS key.
    from ptr_engine.layers import CompactionState, compile_prompt
    bare = CompactionState()
    prompt = compile_prompt({"system": "s", "run_id": "r"}, bare, epoch=0,
                            journal=[], work="w")
    assert "PINS" not in prompt.layer_tokens, prompt.layer_tokens


def test_window_pressure_folds_before_the_interval():
    """The design's trigger is window pressure, not a turn count."""
    st = _state(fold_at_fraction=0.70)
    assert st.fold_at_tokens == int(_fixture()["window_tokens"] * 0.70)
    # No turn interval: a fixed interval folds a prompt that never needed to
    # fold, and on a 45 k-token L0 a 24-turn interval would always win.
    assert st.compact_every is None
    assert st.state.fold_at_tokens == st.fold_at_tokens
    # A caller that names an interval gets it back as a floor.
    floored = _state(fold_at_fraction=0.70, compact_every=24)
    assert floored.compact_every == 24
    assert floored.fold_at_tokens == st.fold_at_tokens
