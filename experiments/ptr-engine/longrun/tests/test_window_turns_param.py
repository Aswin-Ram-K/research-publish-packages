#!/usr/bin/env python3
"""E3 readiness: the masking window is a parameter, default byte-identical.

PREREG-SPCC §E3 asks whether the distance cliff is POSITION or EVICTION, with the
body retained and no masking.  Before this unit the window was a module constant
(``arm_cd.py:39``) read directly at the cutoff (``arm_cd.py:173``), so no cell
could force retention: every arm-C run masked at ``intro+4`` and the two
explanations were indistinguishable.

This file pins the four properties the change must have:

1. the default window is still 4, and a run that never names it produces
   BYTE-IDENTICAL prompts to the pre-change code (the 30 sha256 values below were
   captured from ``git show HEAD:experiments/ptr-engine/longrun/arm_cd.py``
   driven by the same 30-turn stub);
2. a window of 200 masks nothing across a 100-turn stub, and ``masked_rows``
   stays 0 on every row;
3. a window of 4 still masks at ``intro+4`` exactly as today;
4. ``evicted`` still equals ``masked_rows`` for the masking arm.

Offline: no socket, no model, no row file, no git.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
for _p in (LONGRUN, ENGINE_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd  # noqa: E402
import run_longrun as R  # noqa: E402

TURNS = 30

#: sha256 of each of the 30 prompts a no-flag arm-C ``Planner`` produced BEFORE
#: this unit, captured from ``git show HEAD:.../longrun/arm_cd.py`` driven by the
#: same 30-turn stub (tool output on every third turn, starting at T1).  A change
#: to the default window, the cutoff, the marker format or the turn rendering
#: breaks this list.
PRE_CHANGE_SHAS = [
    "8f593bdc8505f338ddee8c1345e1eb1910a85fc5dfc4249baa6ce399580ad587",
    "97f3a30ab19170fc2dbbc7bbc406ae5fd6c0395939ec6c6b048a5b4d39027f92",
    "00820bf134f2335471ce633f5ddf98ba37063cd3b924c21ebc555bf5b13a53c9",
    "d605ec1b57b96d05ba89892f68918c8c1a3b2665f045c8daa3b6abdc2b1ceb0d",
    "a1dfe1c3f6cdc06e65063e3c0c9ddf0a839d823eafce49d252c883d620959078",
    "ca30295e598af1dee8be37e8de25029def0421639ab98a2fba5d83720817961a",
    "a55fb2dc6bb30306b42bf8691106aaca17dab7b0ae1872f5bbde163b8549d3bb",
    "9a630d81bbda1334bb24388ef55aee2d4842a9f4e75f7d403751ec5df17c4550",
    "6ddf0a6377805311bd850ce86251b5258653618408e9161ee442ccae2384192a",
    "c62722365a445f5db876f8bf7410f8050624b9527b1c0ffa628c1a215b55406a",
    "33575b62eb7eaa1a2fb84a21aa1f867e3dff472a400019f5e868e57a8caf2ed9",
    "f3f0e8ed08322f3ef7ceca0168d001a48bb956b191a01061d3219d00c0bdb6ea",
    "9f89224efce50b5cd3c4e735a5d587e56e097e52b40082aab4affc7d9c171ebd",
    "3c7c00c92a0c8aa91a47976c556fbf3ab74e0baad16844039d973b5a376697d1",
    "133bbd203e2cf9a4fad65f1a8b379e2042317398f994ade17a3e94cff47e5889",
    "dc31e03bd0ee221f619bc869e1f111df63c82e9bfe54ad551e828daeef39afce",
    "a4bcb0eab7474b0a8384051a097e430e70252f7d85094cba7125d68f59df899e",
    "a336649c119bbab883b62ec2cefd3792c5036702dd77f50dc6c119ad0eb19fc1",
    "97cdb25001ec8eb03a7e2f2e0bec208d4fa98084b6fd36558d6f3991a3b63f0e",
    "a2b1d1ad8f0f208eb01544497b174c826129e7eff6dd0a319bee314dc5142c24",
    "951b77f8d75c46f71ec9842be4b9081eb5737b01d53901d54f8f53b2bd8a20b3",
    "0863130b71f76fe1f9b119304c4f866127fc16b8d61989cf277fa4a6b18ca09a",
    "4bdd0b21ebc06cf026b98485368fa21ff990c347d22128b2c937b918a5fa22c1",
    "e7240001654dcd107caa2590b65b22c392a13c3bf58b5ae2a224cd043133a968",
    "5db2f96cb0f8e5006f0980c8fcb7be7c7de6e760edff0af8b9f492448b6884f5",
    "96a9fd5414b25fa112e3558d1cfcdd7e06821f4adbf67fad38f702431c3a7442",
    "01ecdc6cc7ccb93a156271ada27e52bf8bbc4272b5de69afbac5f9c51c067157",
    "2166fcea5c4491e36ac5099e385f9b3a0474985a5a8946f4dd60cb0e36a6abcd",
    "cced1eb9e956136de7dafe336e2d8c434173514d8b8c247c0726ef722c777632",
    "d8026742e58e1356978bc35b9735f50eb3f58379703bf2951bbb0e1525760959",
]


def _fixture(n=TURNS):
    """A stub fixture whose tool output lands on every third turn, starting at T1."""
    turns = []
    for t in range(1, n + 1):
        tos = []
        if t % 3 == 1:
            tos = [{"doc_id": "doc-fact-01", "revision": 1,
                    "body": "VAL_A = %d" % (3000 + t)}]
        turns.append({"question": "what is VAL_A?", "tool_outputs": tos})
    return {"task_id": "e3-window-ref", "N": n, "bytes_per_token": 4.0,
            "wall_tokens": 100000, "system_prompt": "SYS",
            "items": [{"id": "doc-fact-01", "body": "VAL_A = 3000"}],
            "turns": turns, "checkpoints": []}


def _drive(window_turns=None, turns=TURNS):
    """Drive the real arm-C ``Planner`` for ``turns``; return (planner, infos)."""
    kw = {} if window_turns is None else {"window_turns": window_turns}
    planner = R.Planner(arm_cd.ARM_C, _fixture(turns), dry_run=True, **kw)
    infos = []
    for t in range(1, turns + 1):
        info = planner.build(t)
        infos.append(info)
        planner.record(t, "ANSWER: NUM %d" % (3000 + t))
    return planner, infos


def _shas(infos):
    return [hashlib.sha256(str(i["prompt"]).encode("utf-8")).hexdigest() for i in infos]


# --- 1. default is 4 and a no-flag run is byte-identical ----------------------
def test_default_window_is_4():
    assert arm_cd.WINDOW_TURNS == 4
    state = arm_cd.ArmCDState(fixture=_fixture())
    assert state.window_turns == 4
    planner, _ = _drive()
    assert planner.arm_cd.window_turns == 4


def test_no_flag_prompts_are_byte_identical_to_pre_change():
    _planner, infos = _drive()
    shas = _shas(infos)
    assert shas == PRE_CHANGE_SHAS, (
        "a run without --window-turns changed its prompts; first divergence at "
        "turn %d" % next(i + 1 for i, (a, b) in enumerate(zip(shas, PRE_CHANGE_SHAS))
                         if a != b))


# --- 2. window 200 masks nothing across 100 turns -----------------------------
def test_window_200_masks_nothing_over_100_turns():
    _planner, infos = _drive(window_turns=200, turns=100)
    assert len(infos) == 100
    assert [i["masked_rows"] for i in infos] == [0] * 100
    assert all("[MASKED" not in str(i["prompt"]) for i in infos)
    # the body is retained: the T1 tool output is still in the T100 prompt
    assert "VAL_A = 3001" in str(infos[-1]["prompt"])


# --- 3. window 4 still masks at intro+4 ---------------------------------------
def test_window_4_masks_at_intro_plus_4():
    _planner, infos = _drive(window_turns=4, turns=10)
    # T1 carries the tool output; the cutoff at t is t-4, so T1 is masked at t=5.
    assert [i["masked_rows"] for i in infos[:4]] == [0, 0, 0, 0]
    assert infos[4]["masked_rows"] == 1
    assert "[MASKED doc-fact-01@r1]" in str(infos[4]["prompt"])
    assert "VAL_A = 3001" not in str(infos[4]["prompt"])
    # T4 carries the next tool output; it is masked at t=8 (cutoff 4), not before.
    assert infos[6]["masked_rows"] == 0
    assert infos[7]["masked_rows"] == 1
    # the T1 marker stays in every later prompt and its body never comes back
    assert all("[MASKED doc-fact-01@r1]" in str(i["prompt"]) for i in infos[4:])
    assert all("VAL_A = 3001" not in str(i["prompt"]) for i in infos[4:])


# --- 4. evicted still equals masked_rows for the masking arm ------------------
def test_evicted_equals_masked_rows():
    for window in (4, 200):
        _planner, infos = _drive(window_turns=window, turns=30)
        assert [i["evicted"] for i in infos] == [i["masked_rows"] for i in infos], window
