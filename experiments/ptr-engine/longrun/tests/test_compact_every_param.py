#!/usr/bin/env python3
"""E2 readiness: the compaction interval is a parameter and a cell dimension.

PREREG-SPCC §E2 varies ``COMPACT_EVERY`` over ``{12, 24, 48}`` on one fixture and
one arm.  Before this unit the interval was a module constant (``layers.py:30``)
read directly at the fold (``layers.py:230``), so no cell could vary it, and G3's
``n = turns x arms x reps`` (``cell.py:1259``) refused a 100-turn single-interval
cell at ``n=100 < 200``.  E2 as preregistered was unrunnable.

This file pins the four properties the change must have:

1. the default interval is still 24, and a run that never names it produces
   BYTE-IDENTICAL prompts to the pre-change code (the 30 sha256 values below were
   captured from ``git show HEAD:.../ptr_engine/layers.py`` before the edit);
2. interval 12 folds at turn 13, 24 at turn 25, 48 at turn 49;
3. a ``12,24,48`` cell is three arm-variants and G3 admits it at ``n=300``;
4. a single-interval cell is refused at ``n=100``.

Offline: no socket, no model, no row file, no git.
"""
import hashlib
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
for _p in (LONGRUN, ENGINE_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd  # noqa: E402
import cell  # noqa: E402
import run_longrun as R  # noqa: E402
from ptr_engine.layers import COMPACT_EVERY  # noqa: E402

FIXTURE = {"task_id": "e2-ref",
           "items": [{"id": "doc-fact-01", "body": "VAL_A = 3000"}]}
TURNS = 30

#: sha256 of each of the 30 prompts a no-flag ``SpccArmState`` produced BEFORE this
#: unit, captured from ``git show HEAD:experiments/ptr-engine/ptr_engine/layers.py``
#: driven by the same 30-turn stub.  A change to the default fold distance, the
#: layer join, or the journal line format breaks this list.
PRE_CHANGE_SHAS = [
    "c01ceac9fcce803b6b1ea86836947390bec0d712fb8660d503fea5b951718471",
    "d151a5850e3b11d74ce8db9d92aa0bb0996ea8a036406bf03bd45898e073f17c",
    "5bb6ac300b7a6e630c78565540277ce24f0ee3ac906ff8d83cc30330beda13d5",
    "3b67fc6d62c1dffcd7b9f84fa81c7d7533d924cb1e1b388e35def9d31f30bb54",
    "ce85888ea2811f17ca6360045419331fc784052b9e860206993edae8629911a1",
    "d6069f58db7b0cbce1d33a55d17cbda54d731be6f035ed86a9a7f38fe18cb2cc",
    "fec2c91a1b343aac3980ca7b8f04611788c9dc198e46d3fed133a8690c57f874",
    "f7aaee1db0cbbe896d1f4df3e7e8538deb1125fd6e169213be95371446987750",
    "a1aff3c9083e4bb1fbd0602d52f65dac3a78f3cb361910a471e029e266150baf",
    "9a9d14b4ef2946d7082eaab61dab704d1a29b2eb00b7d2c9c999e2cecffeb48b",
    "4d6b7447c37f1e7ffdd41a9176a3213057d29a78affad1b2511279e0d58904b7",
    "03aea49c3457ffadc79be6c60acd2a685723db562936aaf81d51b939783c61af",
    "9596732aba8307b840bf7f5ae5e99cffa6497c4dcf746b120907f2a4fdf5b64a",
    "4ba52509e7c8f7d47ea1681350ab8450c47a3524d4372638d2d1ef6c75803808",
    "bb7db03c26ba16a7dd6e110b856a943b0b52c8af4ae19ba389f8f8f50e774afa",
    "2ae1243bff794a9ca9523342ce6b72674d5e9e77b2161360a2a8d73d416200f5",
    "d537d6916eb35817ad26a799531171fff0fd66d4cb8f9ddfd11af0a460f9a07c",
    "85642f9824fc2c8f1708ebffef179913db66ec3fafe57dc7928f8305680ad2de",
    "6273b24fb09fea6d50c9975dfb68db8bd8432ced7bdf898c774df6a031f181ab",
    "c35828aa938729eebdbf0bba502eb31362bf6ca48b497aebe1b35784569d508e",
    "3a87feefd8f4bf3ff816540e2fecf1b08df9057d4940e8d4b486e3c7880d33ea",
    "6d8a72b0f3ca7715c47b9536f89da2f8bcaca89c0261ec24ea01d7e283b31334",
    "9f5d2f4d08a9e1e6343cf6a0bd6f6f694be3bf8e566b4c48c7d62e00095f7b6c",
    "e11e734b85c0fda7bc95b3ecbfadcd2c49beb0e7d192e0d4473b38eec87bfbc6",
    "b5cd6576b1ad8051a63820874933bc639f41c01b40aed6bd41c705147cb08e52",
    "ac2693743278d33fdeaa20dcfe205dfe869ac4ca2069e6b293849838e64e7635",
    "1aabfc4985c7aa2aa391b0bc1945a66227c9ea362e93eaf133bd7782f29bc086",
    "ec033166964becaaa055ff938322330604511f6cf983a63dc461f8bb0a25321f",
    "053c219801ebced8d278875d415a65b66c1aa193cfc82a6aed688a88a1026d12",
    "5cfffc5de81cf194d25c134c830fe9dba8fa3e94b48ee79b167dcc250bce3395",
]


def _drive(compact_every=None, turns=TURNS):
    """Drive the real ``SpccArmState`` for ``turns`` and return (state, shas)."""
    kw = {} if compact_every is None else {"compact_every": compact_every}
    state = arm_cd.SpccArmState(fixture=FIXTURE, **kw)
    shas = []
    for t in range(1, turns + 1):
        work = "QUESTION (T%d): what is VAL_A?" % t
        prompt = state.build(t, work)
        shas.append(hashlib.sha256(str(prompt).encode("utf-8")).hexdigest())
    return state, shas


def _first_fold_turn(interval, turns=60):
    """The turn at which the first compaction fires for ``interval``."""
    state = arm_cd.SpccArmState(fixture=FIXTURE, compact_every=interval)
    for t in range(1, turns + 1):
        state.build(t, "QUESTION (T%d): what is VAL_A?" % t)
        if state.state.compactions >= 1:
            return t
    return None


# --- 1. default is 24 and a no-flag run is byte-identical ----------------------
def test_default_interval_is_24():
    assert COMPACT_EVERY == 24
    state, _ = _drive()
    assert state.compact_every == 24
    assert state.state.compact_every == 24


def test_no_flag_prompts_are_byte_identical_to_pre_change():
    _state, shas = _drive()
    assert shas == PRE_CHANGE_SHAS, (
        "a run without --compact-every changed its prompts; first divergence at "
        "turn %d" % next(i + 1 for i, (a, b) in enumerate(zip(shas, PRE_CHANGE_SHAS))
                         if a != b))


# --- 2. the three intervals fold at the predicted turns ------------------------
def test_interval_12_compacts_at_turn_13():
    assert _first_fold_turn(12) == 13


def test_interval_24_compacts_at_turn_25():
    assert _first_fold_turn(24) == 25


def test_interval_48_compacts_at_turn_49():
    assert _first_fold_turn(48) == 49


# --- 3/4. the interval is a cell dimension and G3 sees it ----------------------
def _cfg(**kw):
    base = dict(arms="spcc", reps=1, max_turns=100, compact_every=None,
                claim_mode="E2")
    base.update(kw)
    return SimpleNamespace(**base)


def _fixture(n_cp=48, n_turns=100):
    return {"N": n_turns,
            "checkpoints": [{"id": "cp%02d" % i} for i in range(n_cp)]}


def test_three_intervals_yield_three_variants_and_n_300():
    cfg = _cfg(compact_every="12,24,48")
    intervals = R.compact_intervals(cfg)
    assert intervals == [12, 24, 48]
    cells = R.expand_cells(["spcc"], 1, intervals)
    assert len(cells) == 3, cells
    assert [c[2] for c in cells] == [12, 24, 48]
    args = R.prereg_gate_args(cfg, _fixture())
    assert args.arms == 3, args.arms
    assert args.turns == 100
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(args, _fixture())
    assert verdict["ok"] is True, verdict
    assert verdict["n"] == 300, verdict["n"]
    assert verdict["arms"] == 3, verdict["arms"]


def test_single_interval_is_refused_at_n_100():
    cfg = _cfg(compact_every="24")
    args = R.prereg_gate_args(cfg, _fixture())
    assert args.arms == 1, args.arms
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(args, _fixture())
    assert verdict["ok"] is False, verdict
    assert verdict["n"] == 100, verdict["n"]
    assert verdict["arms"] == 1, verdict["arms"]


def test_no_flag_is_one_variant_and_refused_at_n_100():
    cfg = _cfg()
    assert R.compact_intervals(cfg) == [24]
    args = R.prereg_gate_args(cfg, _fixture())
    assert args.arms == 1
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(args, _fixture())
    assert verdict["ok"] is False
    assert verdict["n"] == 100
