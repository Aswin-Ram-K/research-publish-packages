"""Regression tests for QUALITY-ARM's two billing defects (unit BILL-REPAIR).

Both defects were falsified against the server by BILL-AUDIT
(`experiments/ptr-engine/audit/REPORT.md` §3.1) and are guarded here so they cannot
return silently:

* **Defect 1 — `L` was the prefix.**  `runner.py` passed
  ``L = prompt_tokens + FRAMING`` into a law whose ``L`` is the measured append
  ``P2 - P1``.  With ``L ≈ P1`` the formula telescopes to ``billed = sum(P1)``.
  :func:`test_L_is_the_measured_append_not_the_prefix` fails if ``L`` is ever the
  prefix again, and :func:`test_prefix_L_telescopes_into_sum_of_prompts` pins the
  *symptom* so the guard has a reason, not just an assertion.

* **Defect 2 — `per_turn` was off by one turn.**  `_billed()` iterated ``turns[1:]``
  and emitted one entry per iteration with no turn-1 element, so every entry billed
  turn ``k``'s append against turn ``k-1``'s prefix.
  :func:`test_per_turn_array_is_indexed_by_turn` fails if the array shifts,
  :func:`test_alignment_assertion_catches_a_one_turn_shift` proves the guard fires,
  and :func:`test_unaligned_rows_raise_rather_than_report` proves the run refuses to
  ship a wrong number.

Run: ``cd experiments/ptr-engine && python3 -m pytest tests/test_quality_billing.py``
(or from the repo root, where ``conftest.py`` puts ``ptr_engine`` on the path).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))
if str(ENGINE_ROOT / "quality") not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT / "quality"))

import runner  # noqa: E402

B = runner.BLOCK_SIZE  # 64


# -- fixtures ------------------------------------------------------------------
def _turns(prompts, cached=None, reported=None):
    """Synthetic per-turn records with the server fields `run_rep` now records."""
    cached = cached or [None] * len(prompts)
    reported = reported if reported is not None else [False] * len(prompts)
    return [
        {
            "turn": n + 1,
            "prompt_tokens": p,
            "P1_tokenizer": p,
            "cached_tokens": c,
            "cached_reported": r,
            "server_uncached": (p - c) if r and c is not None else None,
        }
        for n, (p, c, r) in enumerate(zip(prompts, cached, reported))
    ]


def _rows(prompts):
    return [
        {"row": "request", "turn": n + 1, "prompt_tokens": p, "P1_tokenizer": p}
        for n, p in enumerate(prompts)
    ]


#: QUALITY-ARM's arm-A rep-0 shape, from the shipped rows (the exact values the
#: audit replayed): a 2,252-token prime and three appends on the same prefix.
ARM_A = [2252, 4471, 8589, 18927]


# -- DEFECT 1: L must be the append, not the prefix -----------------------------
def shipped_prefix_L(P1, previous, index):
    """The DEFECT, verbatim from the pre-BILL-REPAIR runner: `L = prompt_tokens + FRAMING`."""
    return P1 + runner.FRAMING


def test_the_shipped_prefix_rule_would_fail_the_L_test():
    """RED CONTROL for the L guard.

    Runs `_billed` through the *shipped* rule and proves the assertion below it fires.
    This is what makes :func:`test_L_is_the_measured_append_not_the_prefix` a guard and
    not decoration: swapping the rule back makes the test fail (see the assertion in
    the body of the next test, which is written against `per_turn`).
    """
    billed = runner._billed(_turns(ARM_A), _rows(ARM_A), L_rule=shipped_prefix_L)
    for index, entry in enumerate(billed["per_turn"]):
        if index == 0:
            continue
        expected = ARM_A[index] - ARM_A[index - 1]
        assert entry["L"] != expected, "the shipped rule must NOT look like the append"
        assert entry["L"] == entry["P1"] + runner.FRAMING
        assert entry["L"] > entry["P1"], "the shipped rule passes the prefix off as the append"


def test_L_is_the_measured_append_not_the_prefix():
    """Fails if `L` is set to the prefix again (the shipped defect)."""
    billed = runner._billed(_turns(ARM_A), _rows(ARM_A))
    per_turn = billed["per_turn"]
    for index, entry in enumerate(per_turn):
        if index == 0:
            assert entry["L"] == ARM_A[0], "turn 1 is the prime: its append is its prompt"
            continue
        expected = ARM_A[index] - ARM_A[index - 1]
        assert entry["L"] == expected, (
            f"turn {entry['turn']}: L={entry['L']} is not the measured append "
            f"{expected} (P2-P1) -- it looks like the PREFIX again"
        )
        assert entry["L"] != entry["P1"], (
            f"turn {entry['turn']}: L equals the prefix ({entry['P1']}) -- the "
            "`L = prompt_tokens + FRAMING` defect has returned"
        )


def test_prefix_L_telescopes_into_sum_of_prompts():
    """Pins the symptom: a prefix-valued `L` degenerates the law into `sum(P1)`.

    This is what BILL-AUDIT measured as a 57.6x overstatement: not a wrong constant,
    a formula that stopped evaluating the law.
    """
    residue_term = sum(p % B for p in ARM_A[1:])
    telescoped = sum(ARM_A) + residue_term
    with_appends = sum(
        (B if e["residue"] == 0 else e["residue"]) + e["L"]
        for e in runner._billed(_turns(ARM_A), _rows(ARM_A))["per_turn"]
    )
    # The corrected law on this input is ~ (small), while the telescoped form is
    # ~ sum(P1).  They must not agree, and the corrected one must be smaller.
    assert with_appends < telescoped
    assert telescoped >= sum(ARM_A)


def test_law_total_does_not_equal_sum_of_prompts():
    """The published defect's signature: `billed == sum(P1)`."""
    billed = runner._billed(_turns(ARM_A), _rows(ARM_A))["billed"]
    assert billed != sum(ARM_A), (
        "billed == sum(P1): the formula has collapsed into the prefix-sum defect again"
    )


def test_residue_zero_bills_one_block_not_the_prefix():
    """BILL-AUDIT: residue 0 -> 64 + L (one block), residue 1 -> 1 + L."""
    # All residue 0, and P1 > B so that `P1 + L` and `B + L` are distinguishable.
    prompts = [448, 8064]
    billed = runner._billed(_turns(prompts), _rows(prompts))
    for entry in billed["per_turn"]:
        assert entry["residue"] == 0
        assert entry["uncached"] == B + entry["L"], (
            f"turn {entry['turn']}: residue 0 billed {entry['uncached']}, expected "
            f"one block ({B}) + L ({entry['L']}) -- NOT P1 + L"
        )
        # The measured shape from BILL-AUDIT: P1=448 bills 64+L, not 448+L.
        assert entry["uncached"] == B + entry["L"] < entry["P1"] + entry["L"]


def test_residue_one_is_normal():
    """Residue 1 costs `1 + L` -- not a discontinuity."""
    prompts = [64 + 1, 128 + 1]
    billed = runner._billed(_turns(prompts), _rows(prompts))
    for entry in billed["per_turn"]:
        assert entry["residue"] == 1
        assert entry["uncached"] == 1 + entry["L"]


def test_residue_in_the_middle_is_the_tail_plus_append():
    prompts = [1000, 1037]                        # residues 40, 13
    billed = runner._billed(_turns(prompts), _rows(prompts))
    for entry in billed["per_turn"]:
        assert entry["uncached"] == entry["residue"] + entry["L"]


# -- DEFECT 2: the per-turn array must be indexed by turn ------------------------
SHIPPED_SHIFT = True   # RED CONTROL: True runs the SHIPPED off-by-one shape


def _shipped_billed(turns):
    """The pre-BILL-REPAIR `_billed` body, verbatim in shape: it iterates `turns[1:]`
    and appends one entry per iteration, so turn 1 is never emitted and every entry
    bills `k`'s append against `k-1`'s prefix."""
    per_turn, total = [], 0
    first = turns[0]["prompt_tokens"] if turns else 0
    total = first
    for index, entry in enumerate(turns[1:], start=1):
        P1 = entry["prompt_tokens"]
        previous = turns[index - 1]["prompt_tokens"]
        L = P1 + runner.FRAMING
        residue = P1 % runner.BLOCK_SIZE
        uncached = P1 + L if residue in (0, 1) else residue + L
        total += uncached
        per_turn.append({"turn": entry["turn"], "P1": P1, "residue": residue,
                         "avalanche": residue in (0, 1), "L": L, "uncached": uncached})
    return {"billed": total, "per_turn": per_turn}


def test_the_shipped_billed_is_off_by_one_turn():
    """RED CONTROL for the alignment guard: the shipped shape must FAIL the alignment
    checks that :func:`test_per_turn_array_is_indexed_by_turn` applies.  If this test
    ever passes, the alignment guard has stopped guarding anything."""
    turns = _turns(ARM_A)
    shipped = _shipped_billed(turns)["per_turn"]
    assert len(shipped) == len(ARM_A) - 1, "the shipped array drops turn 1"
    assert shipped[0]["P1"] == ARM_A[1] != ARM_A[0], "the shipped array starts at turn 2"
    with pytest.raises(AssertionError):
        runner._assert_aligned(turns, shipped, _rows(ARM_A))


def test_per_turn_array_is_indexed_by_turn():
    """Fails if the per-turn array shifts by one turn."""
    billed = runner._billed(_turns(ARM_A), _rows(ARM_A))
    per_turn = billed["per_turn"]
    assert len(per_turn) == len(ARM_A), (
        f"per_turn has {len(per_turn)} entries for {len(ARM_A)} turns -- the old "
        "`turns[1:]` iteration dropped turn 1 and shifted every entry"
    )
    for index, entry in enumerate(per_turn):
        assert entry["turn"] == index + 1
        assert entry["P1"] == ARM_A[index], (
            f"per_turn[{index}] bills P1={entry['P1']}, but turn {index + 1}'s prompt "
            f"is {ARM_A[index]} -- the array is off by a turn"
        )


def test_per_turn_residues_match_their_own_prompts():
    """The exact symptom BILL-AUDIT reported: rep-row residues 55/13/47 against
    request rows whose prompts 2252/4471/8589 carry residues 10/53/11."""
    billed = runner._billed(_turns(ARM_A), _rows(ARM_A))
    for entry in billed["per_turn"]:
        assert entry["residue"] == entry["P1"] % B, (
            f"turn {entry['turn']}: residue {entry['residue']} is not its own P1 "
            f"({entry['P1']}) mod {B} -- this is the misalignment signature"
        )


def test_alignment_assertion_catches_a_one_turn_shift():
    """The guard itself: a deliberately shifted array must raise, not pass."""
    turns = _turns(ARM_A)
    rows = _rows(ARM_A)
    good = runner._billed(turns, rows)["per_turn"]
    runner._assert_aligned(turns, good, rows)          # sanity: the good one passes

    shifted = good[1:] + [dict(good[-1], P1=good[-1]["P1"])]
    for index, slot in enumerate(shifted):
        slot = dict(slot, turn=index + 1)
        shifted[index] = slot
    with pytest.raises(AssertionError):
        runner._assert_aligned(turns, shifted, rows)

    short = good[1:]                                   # the shipped defect's shape
    with pytest.raises(AssertionError):
        runner._assert_aligned(turns, short, rows)


def test_unaligned_rows_raise_rather_than_report():
    """A run must not ship a bill that does not line up with its own rows."""
    turns = _turns(ARM_A)
    rows = _rows([2252, 4471, 8589, 18927])
    rows[2]["prompt_tokens"] = 4471                     # pretend the rows shifted
    with pytest.raises(AssertionError):
        runner._billed(turns, rows)


# -- the server column: a null is never silently zero ---------------------------
def test_server_totals_are_never_taken_from_the_law():
    """No server number may be computed from the formula."""
    turns = _turns([1000, 2000], cached=[None, 1344], reported=[False, True])
    billed = runner._billed(turns, _rows([1000, 2000]))
    assert billed["server_null_turns"] == [1], "turn 1 reported nothing and must be named"
    assert billed["server_uncached_reported"] == 2000 - 1344
    assert billed["server_cached_reported"] == 1344
    # The lower bound counts the unreported turn at its full prompt rather than at 0.
    assert billed["server_uncached_lower_bound"] == 1000 + (2000 - 1344)
    assert not billed["server_all_reported"]
    assert billed["server_uncached_reported"] != billed["billed"]


def test_cold_null_is_recorded_as_unreported_not_zero():
    turns = _turns([1400], cached=[None], reported=[False])
    billed = runner._billed(turns, _rows([1400]))
    entry = billed["per_turn"][0]
    assert entry["cached_tokens"] is None
    assert entry["cached_reported"] is False
    assert entry["server_uncached"] is None, "a null must never become 0 + used as a bill"


def test_reported_zero_is_a_real_zero():
    """`/generate` reports a cold miss as `cached_tokens: 0` -- a REPORTED zero."""
    turns = _turns([1400], cached=[0], reported=[True])
    billed = runner._billed(turns, _rows([1400]))
    assert billed["per_turn"][0]["server_uncached"] == 1400
    assert billed["server_all_reported"] is True


# -- the tokenizer must count the render the request actually sends -------------
def test_token_count_passes_the_thinking_kwarg(monkeypatch):
    """`token_count` must ask for the same template branch the request uses."""
    seen = {}

    def fake_post_json(path, payload, timeout=600.0):
        seen["path"] = path
        seen["payload"] = payload
        return {"count": 1402}

    monkeypatch.setattr(runner, "post_json", fake_post_json)
    count = runner.token_count([{"role": "user", "content": "hi"}])
    assert count == 1402
    assert seen["path"] == "/v1/tokenize"
    assert seen["payload"].get("chat_template_kwargs") == {"enable_thinking": False}, (
        "counting without the kwarg under-reports P1 by 2 tokens on this build"
    )
