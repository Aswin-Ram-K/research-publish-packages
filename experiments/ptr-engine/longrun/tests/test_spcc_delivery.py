"""Offline proof that ``spcc`` keeps FIXTURE DELIVERIES and drops MODEL FETCHES.

Two different bodies reach L3 in the stable-prefix arm, and they must not be
conflated:

* a fixture-delivered tool output is transcript content -- the same body the
  ``masking-no-fetch`` arm renders inline on its delivery turn -- so it must
  persist in the L2 journal until compaction;
* a model-initiated fetch is the fetch mechanism, and the compiler invariant is
  that fetches never enter L0, L1 or L2.

No socket is opened and no model is called: every assertion runs against the
real ``arm_cd.SpccArmState`` and the real ``ptr_engine.layers.compile_prompt``.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
for _p in (LONGRUN, ENGINE_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd  # noqa: E402
from ptr_engine import layers as L  # noqa: E402
from ptr_engine.layers import COMPACT_EVERY  # noqa: E402

BODY = "DELIVERED BODY: VAL_A = 3000"
FETCHED = "FETCHED BODY: VAL_A = 3000"


def _fixture():
    return {"task_id": "spcc-delivery-fixture",
            "items": [{"id": "doc-fact-01", "body": BODY}]}


def _layers(prompt, state, work, l3_bodies=()):
    """The compiled prompt's own L0..L4 split, proven byte-exact.

    ``compile_prompt`` joins the layers with a blank line, but L0 itself
    contains a blank line (the empty tool schema), so splitting the prompt on
    "\\n\\n" cannot recover the boundaries.  Rebuild the layer texts from
    the state the compile just wrote and assert the prompt is exactly their
    join -- then the per-layer assertions below are assertions about the
    compiled prompt, not about a guess.

    PINS is a sixth block between L0 and L1, rendered only when it carries a
    pin (the fold record is a pin), so it is included only when non-empty.  The
    result is keyed by layer NAME, not by position: inserting PINS shifts every
    later index, and a positional read would silently start asserting about the
    wrong layer on the fold turn.
    """
    pins = "\n".join(str(x) for x in state.state.pins)
    named = {
        "L0": L._l0_text(state.run),
        "L1": "\n".join(L._sort_index_lines(state.state.index_lines)),
        "L2": "\n".join(str(x) for x in state.state.journal),
        "L3": str(work) + ("\n" + "\n".join(l3_bodies) if l3_bodies else ""),
        "L4": "ANSWER: NONE",
    }
    if pins:
        named["PINS"] = pins
    order = ["L0"] + (["PINS"] if pins else []) + ["L1", "L2", "L3", "L4"]
    assert str(prompt) == "\n\n".join(named[k] for k in order) + "\n", (
        "layer reconstruction mismatch")
    return named


def test_delivery_persists_in_l2_until_compaction():
    """A body delivered at turn 1 is in the prompt at turns 1-4 and gone after the fold."""
    state = arm_cd.SpccArmState(fixture=_fixture())

    state.add_delivery(BODY)
    w1 = "QUESTION (T1): what is VAL_A?"
    p1 = state.build(1, w1)
    assert BODY in _layers(p1, state, w1, (BODY,))["L3"], "delivery missing from L3 on its own turn"

    for t in (2, 3, 4):
        work = "QUESTION (T%d): restate it" % t
        p = state.build(t, work)
        layers = _layers(p, state, work)
        assert BODY in layers["L2"], "delivery missing from L2 at turn %d" % t
        assert BODY not in layers["L0"], "delivery leaked into L0 at turn %d" % t
        assert BODY not in layers["L1"], "delivery leaked into L1 at turn %d" % t

    # Walk to the fold.  The T1 line is appended on the T2 compile, so the
    # journal reaches COMPACT_EVERY lines at the start of the (COMPACT_EVERY+1)th
    # compile and the whole journal is dropped there.
    last_visible = None
    for t in range(5, COMPACT_EVERY + 2):
        work = "QUESTION (T%d): restate it" % t
        p = state.build(t, work)
        if BODY in _layers(p, state, work)["L2"]:
            last_visible = t
    assert last_visible == COMPACT_EVERY, (
        "delivery should survive through turn %d, last seen at %r"
        % (COMPACT_EVERY, last_visible))
    after = "QUESTION: after the fold"
    assert BODY not in str(state.build(COMPACT_EVERY + 2, after)), (
        "delivery survived compaction")


def test_journal_line_carries_the_delivery():
    """The queued journal line for the delivery turn contains the body text."""
    state = arm_cd.SpccArmState(fixture=_fixture())
    state.add_delivery(BODY)
    state.build(1, "QUESTION (T1): what is VAL_A?")
    assert state._pending_line is not None
    assert BODY in state._pending_line, "journal line dropped the delivery"
    assert state._pending_line.startswith("T1|user|"), state._pending_line[:20]

    state.build(2, "QUESTION (T2): restate it")
    assert any(BODY in line for line in state.state.journal), (
        "delivery never reached the journal")


def test_l2_grows_when_a_delivery_arrives():
    """L2 token count is larger with a delivery than without one."""
    plain = arm_cd.SpccArmState(fixture=_fixture())
    plain.build(1, "QUESTION (T1): what is VAL_A?")
    plain_l2 = plain.build(2, "QUESTION (T2): restate it").layer_tokens["L2"]

    delivered = arm_cd.SpccArmState(fixture=_fixture())
    delivered.add_delivery(BODY)
    delivered.build(1, "QUESTION (T1): what is VAL_A?")
    delivered_l2 = delivered.build(2, "QUESTION (T2): restate it").layer_tokens["L2"]

    assert delivered_l2 > plain_l2, (
        "L2 did not grow: plain=%d delivered=%d" % (plain_l2, delivered_l2))


def test_model_fetch_never_enters_l0_l1_l2():
    """A model-initiated fetch is L3-only, on its own turn, and never in the prefix."""
    state = arm_cd.SpccArmState(fixture=_fixture())
    state.build(1, "QUESTION (T1): what is VAL_A?")
    state.add_fetch(FETCHED)
    w2 = "QUESTION (T2): restate it"
    p2 = state.build(2, w2)
    layers = _layers(p2, state, w2, (FETCHED,))
    assert FETCHED in layers["L3"], "fetch missing from L3 on its own turn"
    for name in ("L0", "L1", "L2"):
        assert FETCHED not in layers[name], "fetch leaked into %s" % name

    p3 = state.build(3, "QUESTION (T3): restate it")
    assert FETCHED not in str(p3), "fetch survived its own turn"


def test_masking_window_is_unchanged():
    """The masking arm still carries a body for exactly WINDOW_TURNS turns."""
    assert arm_cd.WINDOW_TURNS == 4
    fx = {"task_id": "mask-window",
          "turns": [{"tool_outputs": [{"doc_id": "doc-fact-01", "revision": 1,
                                       "body": BODY}]}]}
    inside = arm_cd.ArmCDState(fixture=fx)
    masked_inside, _ = inside.mask_old_turns(4)
    assert masked_inside == 0, "turn 1 masked at turn 4, window shrank"

    outside = arm_cd.ArmCDState(fixture=fx)
    masked_outside, _ = outside.mask_old_turns(5)
    assert masked_outside == 1, "turn 1 not masked at turn 5, window grew"


if __name__ == "__main__":
    test_delivery_persists_in_l2_until_compaction()
    test_journal_line_carries_the_delivery()
    test_l2_grows_when_a_delivery_arrives()
    test_model_fetch_never_enters_l0_l1_l2()
    test_masking_window_is_unchanged()
    print("ALL OK")
